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
import android.provider.Telephony;
import android.service.notification.NotificationListenerService;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class ForwarderForegroundService extends Service {
    private static final String CHANNEL_ID = "forwarder_background_persistent";
    private static final int NOTIFICATION_ID = 6969;
    private static final long FLUSH_INTERVAL_MS = 60_000L;
    private static final long INBOX_POLL_INTERVAL_MS = 15_000L;
    private static final long INBOX_OBSERVER_DEBOUNCE_MS = 2_000L;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable scanInbox = () -> ForwarderClient.scanSmsInboxFromForegroundService(ForwarderForegroundService.this);
    private ScheduledExecutorService serviceScheduler;
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
        registerInboxObserver();
        startServiceScheduler();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        DebugLog.append(this, "Foreground service onStartCommand");
        ForwarderClient.scheduleRetry(this);
        registerInboxObserver();
        startServiceScheduler();
        scanInbox.run();
        ForwarderClient.flushQueue(this);
        requestNotificationListenerRebind();
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        DebugLog.append(this, "Foreground service destroyed");
        handler.removeCallbacks(scanInbox);
        stopServiceScheduler();
        unregisterInboxObserver();
        ForwarderClient.scheduleRetry(this);
        super.onDestroy();
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        DebugLog.append(this, "Foreground service task removed; delayed retry scheduled");
        ForwarderClient.scheduleRetry(this);
        super.onTaskRemoved(rootIntent);
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
            NotificationManager.IMPORTANCE_DEFAULT
        );
        channel.setDescription("Foreground service requested; allow battery/autostart for reliable forwarding");
        channel.setSound(null, null);
        channel.enableVibration(false);
        channel.setShowBadge(false);
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
            .setContentText("Background SMS scan active")
            .setContentIntent(contentIntent)
            .setCategory(Notification.CATEGORY_SERVICE)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setShowWhen(false);
        if (Build.VERSION.SDK_INT >= 31) builder.setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE);
        if (Build.VERSION.SDK_INT < 26) builder.setPriority(Notification.PRIORITY_HIGH);
        return builder.build();
    }

    private void startServiceScheduler() {
        if (serviceScheduler != null && !serviceScheduler.isShutdown()) return;
        serviceScheduler = Executors.newSingleThreadScheduledExecutor();
        serviceScheduler.scheduleWithFixedDelay(() -> {
            DebugLog.append(ForwarderForegroundService.this, "Foreground service scheduler poll fired");
            scanInbox.run();
        }, 0, INBOX_POLL_INTERVAL_MS, TimeUnit.MILLISECONDS);
        serviceScheduler.scheduleWithFixedDelay(() -> {
            ForwarderClient.scheduleRetry(ForwarderForegroundService.this);
            ForwardingStats.recordPhoneEvent(ForwarderForegroundService.this, "Foreground service scheduler keep-alive tick; battery/autostart still required for reliable forwarding");
            ForwarderClient.flushQueue(ForwarderForegroundService.this);
            requestNotificationListenerRebind();
        }, 0, FLUSH_INTERVAL_MS, TimeUnit.MILLISECONDS);
    }

    private void stopServiceScheduler() {
        if (serviceScheduler == null) return;
        serviceScheduler.shutdownNow();
        serviceScheduler = null;
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
