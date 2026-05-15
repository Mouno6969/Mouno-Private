package com.mouno.forwarder;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.database.ContentObserver;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Telephony;
import android.service.notification.NotificationListenerService;

public class ForwarderForegroundService extends Service {
    private static final String CHANNEL_ID = "forwarder_background";
    private static final int NOTIFICATION_ID = 6969;
    private static final long FLUSH_INTERVAL_MS = 60_000L;
    private static final long INBOX_POLL_INTERVAL_MS = 15_000L;
    private static final long INBOX_OBSERVER_DEBOUNCE_MS = 2_000L;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable scanInbox = () -> ForwarderClient.scanSmsInbox(ForwarderForegroundService.this, false, null);
    private final Runnable pollInbox = new Runnable() {
        @Override
        public void run() {
            scanInbox.run();
            handler.postDelayed(this, INBOX_POLL_INTERVAL_MS);
        }
    };
    private final Runnable keepAlive = new Runnable() {
        @Override
        public void run() {
            if (wakeLock == null || !wakeLock.isHeld()) acquireWakeLock();
            ForwarderClient.scheduleRetry(ForwarderForegroundService.this);
            ForwardingStats.recordPhoneEvent(ForwarderForegroundService.this, "Background service alive");
            scanInbox.run();
            ForwarderClient.flushQueue(ForwarderForegroundService.this);
            requestNotificationListenerRebind();
            handler.postDelayed(this, FLUSH_INTERVAL_MS);
        }
    };
    private final ContentObserver inboxObserver = new ContentObserver(handler) {
        @Override
        public void onChange(boolean selfChange) {
            onChange(selfChange, null);
        }

        @Override
        public void onChange(boolean selfChange, Uri uri) {
            DebugLog.append(ForwarderForegroundService.this, "SMS inbox observer changed");
            handler.removeCallbacks(scanInbox);
            handler.postDelayed(scanInbox, INBOX_OBSERVER_DEBOUNCE_MS);
        }
    };
    private boolean inboxObserverRegistered;
    private PowerManager.WakeLock wakeLock;

    static boolean start(Context context) {
        Intent intent = new Intent(context.getApplicationContext(), ForwarderForegroundService.class);
        try {
            DebugLog.append(context, "Foreground service start requested");
            if (Build.VERSION.SDK_INT >= 26) {
                context.getApplicationContext().startForegroundService(intent);
            } else {
                context.getApplicationContext().startService(intent);
            }
            return true;
        } catch (Exception exc) {
            ForwardingStats.recordFailure(context, "Background service start failed: " + exc.getClass().getSimpleName());
            ForwarderClient.scheduleRetry(context);
            ForwarderClient.scheduleNetworkFlush(context);
            return false;
        }
    }

    @Override
    public void onCreate() {
        super.onCreate();
        DebugLog.append(this, "Foreground service created");
        createChannel();
        startForeground(NOTIFICATION_ID, notification());
        acquireWakeLock();
        registerInboxObserver();
        handler.post(keepAlive);
        handler.post(pollInbox);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        DebugLog.append(this, "Foreground service onStartCommand");
        ForwarderClient.scheduleRetry(this);
        registerInboxObserver();
        scanInbox.run();
        handler.removeCallbacks(pollInbox);
        handler.postDelayed(pollInbox, INBOX_POLL_INTERVAL_MS);
        ForwarderClient.flushQueue(this);
        requestNotificationListenerRebind();
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        DebugLog.append(this, "Foreground service destroyed");
        handler.removeCallbacks(keepAlive);
        handler.removeCallbacks(pollInbox);
        handler.removeCallbacks(scanInbox);
        unregisterInboxObserver();
        releaseWakeLock();
        ForwarderClient.scheduleRetry(this);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationChannel channel = new NotificationChannel(
            CHANNEL_ID,
            "SCB Forwarder background",
            NotificationManager.IMPORTANCE_LOW
        );
        channel.setDescription("Keeps bKash forwarding active in the background");
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (manager != null) manager.createNotificationChannel(channel);
    }

    private Notification notification() {
        Intent openIntent = new Intent(this, MainActivity.class);
        PendingIntent contentIntent = PendingIntent.getActivity(this, 0, openIntent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
            ? new Notification.Builder(this, CHANNEL_ID)
            : new Notification.Builder(this);
        builder.setSmallIcon(android.R.drawable.stat_notify_sync)
            .setContentTitle("SCB-Forwarder running")
            .setContentText("Polling bKash SMS inbox every 15 seconds")
            .setContentIntent(contentIntent)
            .setOngoing(true)
            .setShowWhen(false);
        if (Build.VERSION.SDK_INT < 26) builder.setPriority(Notification.PRIORITY_LOW);
        return builder.build();
    }

    private void acquireWakeLock() {
        try {
            PowerManager powerManager = (PowerManager) getSystemService(POWER_SERVICE);
            if (powerManager == null) return;
            wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "MounoForwarder:BackgroundForwarding");
            wakeLock.setReferenceCounted(false);
            wakeLock.acquire(10 * 60_000L);
            DebugLog.append(this, "Background forwarding wake lock active");
        } catch (Exception exc) {
            ForwardingStats.recordFailure(this, "Wake lock failed: " + exc.getClass().getSimpleName());
        }
    }

    private void releaseWakeLock() {
        try {
            if (wakeLock != null && wakeLock.isHeld()) wakeLock.release();
        } catch (Exception ignored) {
        }
        wakeLock = null;
    }

    private void requestNotificationListenerRebind() {
        if (Build.VERSION.SDK_INT >= 24) {
            NotificationListenerService.requestRebind(new ComponentName(this, BkashNotificationListener.class));
        }
    }

    private void registerInboxObserver() {
        if (inboxObserverRegistered) return;
        try {
            getContentResolver().registerContentObserver(Telephony.Sms.CONTENT_URI, true, inboxObserver);
            inboxObserverRegistered = true;
            ForwardingStats.recordPhoneEvent(this, "SMS inbox observer active");
        } catch (Exception exc) {
            ForwardingStats.recordFailure(this, "SMS inbox observer failed: " + exc.getClass().getSimpleName());
        }
    }

    private void unregisterInboxObserver() {
        if (!inboxObserverRegistered) return;
        try {
            getContentResolver().unregisterContentObserver(inboxObserver);
        } catch (Exception ignored) {
        }
        inboxObserverRegistered = false;
    }
}
