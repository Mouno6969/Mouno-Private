package com.mouno.forwarder;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.service.notification.NotificationListenerService;

public class ForwarderForegroundService extends Service {
    private static final String CHANNEL_ID = "forwarder_background";
    private static final int NOTIFICATION_ID = 6969;
    private static final long FLUSH_INTERVAL_MS = 5 * 60_000L;
    private static final long SMS_POLL_INTERVAL_MS = 15_000L;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable keepAlive = new Runnable() {
        @Override
        public void run() {
            try {
                ForwarderClient.scheduleRetry(ForwarderForegroundService.this);
                ForwarderClient.flushQueue(ForwarderForegroundService.this);
                requestNotificationListenerRebind();
            } catch (Exception exc) {
                ForwardingStats.recordFailure(ForwarderForegroundService.this, "Background keepalive failed: " + exc.getClass().getSimpleName());
            }
            handler.postDelayed(this, FLUSH_INTERVAL_MS);
        }
    };
    private final Runnable smsPoller = new Runnable() {
        @Override
        public void run() {
            try {
                SmsInboxReader.pollAndForward(ForwarderForegroundService.this);
            } catch (Exception exc) {
                ForwardingStats.recordFailure(ForwarderForegroundService.this, "SMS poller failed: " + exc.getClass().getSimpleName());
            }
            handler.postDelayed(this, SMS_POLL_INTERVAL_MS);
        }
    };

    static boolean start(Context context) {
        Intent intent = new Intent(context.getApplicationContext(), ForwarderForegroundService.class);
        try {
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
        try {
            createChannel();
            startForeground(NOTIFICATION_ID, notification());
        } catch (Exception exc) {
            ForwardingStats.recordFailure(this, "Background service foreground failed: " + exc.getClass().getSimpleName());
            ForwarderClient.scheduleRetry(this);
            ForwarderClient.scheduleNetworkFlush(this);
            stopSelf();
            return;
        }
        handler.post(keepAlive);
        handler.post(smsPoller);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        try {
            ForwarderClient.scheduleRetry(this);
            ForwarderClient.flushQueue(this);
            requestNotificationListenerRebind();
        } catch (Exception exc) {
            ForwardingStats.recordFailure(this, "Background service command failed: " + exc.getClass().getSimpleName());
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacks(keepAlive);
        handler.removeCallbacks(smsPoller);
        try {
            ForwarderClient.scheduleRetry(this);
        } catch (Exception exc) {
            ForwardingStats.recordFailure(this, "Background service destroy retry failed: " + exc.getClass().getSimpleName());
        }
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
            .setContentText("Listening for bKash SMS/notifications")
            .setContentIntent(contentIntent)
            .setOngoing(true)
            .setShowWhen(false);
        if (Build.VERSION.SDK_INT < 26) builder.setPriority(Notification.PRIORITY_LOW);
        return builder.build();
    }

    private void requestNotificationListenerRebind() {
        if (Build.VERSION.SDK_INT >= 24) {
            try {
                NotificationListenerService.requestRebind(new ComponentName(this, BkashNotificationListener.class));
            } catch (Exception exc) {
                ForwardingStats.recordFailure(this, "Notification listener rebind failed: " + exc.getClass().getSimpleName());
            }
        }
    }
}
