package com.mouno.forwarder;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;

import org.json.JSONObject;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

final class ForwarderClient {
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();

    private ForwarderClient() {}

    static void sendSms(Context context, String sender, String body) {
        if (!BuildConfig.FORWARD_SMS) return;
        send(context, "sms", "sms", sender, body);
    }

    static void sendNotification(Context context, String appName, String title, String text) {
        if (!BuildConfig.FORWARD_NOTIFICATIONS) return;
        send(context, "notification", appName, title, text);
    }

    static void send(Context context, String endpoint, String source, String title, String text) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            try {
                flushQueueNow(appContext);
                JSONObject notice = makeNotice(appContext, endpoint, source, title, text);
                if (!post(notice)) NoticeQueue.enqueue(appContext, notice);
            } catch (Exception exc) {
                try {
                    NoticeQueue.enqueue(appContext, makeNotice(appContext, endpoint, source, title, text));
                } catch (Exception ignored) {
                }
            }
        });
    }

    static void flushQueue(Context context) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> flushQueueNow(appContext));
    }

    static void scheduleRetry(Context context) {
        Intent intent = new Intent(context, RetryReceiver.class);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(context, 101, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager != null) {
            alarmManager.setInexactRepeating(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + 60_000L, 5 * 60_000L, pendingIntent);
        }
    }

    private static void flushQueueNow(Context context) {
        Set<String> current = NoticeQueue.snapshot(context);
        if (current.isEmpty()) return;
        Set<String> failed = new LinkedHashSet<>();
        for (String row : current) {
            try {
                if (!post(NoticeQueue.decode(row))) failed.add(row);
            } catch (Exception exc) {
                failed.add(row);
            }
        }
        NoticeQueue.save(context, failed);
    }

    private static JSONObject makeNotice(Context context, String endpoint, String source, String title, String text) throws Exception {
        JSONObject json = new JSONObject();
        json.put("endpoint", endpoint);
        json.put("source", source == null ? "android" : source);
        json.put("title", title == null ? "" : title);
        json.put("text", text == null ? "" : text);
        json.put("device_id", ForwarderConfig.deviceId(context));
        json.put("received_at", System.currentTimeMillis());
        if (BuildConfig.SELLER_TOKEN != null && !BuildConfig.SELLER_TOKEN.trim().isEmpty()) json.put("seller_token", BuildConfig.SELLER_TOKEN.trim());
        return json;
    }

    private static boolean post(JSONObject notice) {
        if (!ForwarderConfig.isConfigured()) return false;
        HttpURLConnection connection = null;
        try {
            String endpoint = notice.optString("endpoint", "notification");
            URL url = new URL(ForwarderConfig.endpoint(endpoint));
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(10_000);
            connection.setReadTimeout(10_000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            connection.setRequestProperty("X-Forwarder-Token", BuildConfig.FORWARDER_SECRET);
            byte[] body = notice.toString().getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream stream = connection.getOutputStream()) {
                stream.write(body);
            }
            int code = connection.getResponseCode();
            return code >= 200 && code < 300;
        } catch (Exception exc) {
            return false;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }
}
