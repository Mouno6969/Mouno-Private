package com.mouno.forwarder;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.app.job.JobInfo;
import android.app.job.JobScheduler;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

final class ForwarderClient {
    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();
    private static final int NETWORK_FLUSH_JOB_ID = 202;
    private static final int BACKGROUND_SCAN_ALARM_REQUEST_CODE = 101;
    private static final long BACKGROUND_SCAN_INTERVAL_MS = 5 * 60_000L;

    private ForwarderClient() {}

    static void sendSms(Context context, String sender, String body) {
        sendSms(context, sender, body, null);
    }

    static void sendSms(Context context, String sender, String body, Runnable onComplete) {
        if (!BuildConfig.FORWARD_SMS) {
            if (onComplete != null) onComplete.run();
            return;
        }
        send(context, "sms", "sms", sender, body, onComplete);
    }

    static boolean queueSms(Context context, String sender, String body) {
        if (!BuildConfig.FORWARD_SMS) return false;
        return queueNotice(context, "sms", "sms", sender, body, "SMS", true);
    }

    static boolean queueSmsFromInboxScan(Context context, String sender, String body) {
        if (!BuildConfig.FORWARD_SMS) return false;
        return queueNotice(context, "sms", "sms_inbox", sender, body, "SMS inbox", false);
    }

    static boolean queueNotification(Context context, String appName, String title, String text) {
        if (!BuildConfig.FORWARD_NOTIFICATIONS) return false;
        return queueNotice(context, "notification", appName, title, text, "Notification", true);
    }

    static void sendNotification(Context context, String appName, String title, String text) {
        sendNotification(context, appName, title, text, null);
    }

    static void sendNotification(Context context, String appName, String title, String text, Runnable onComplete) {
        if (!BuildConfig.FORWARD_NOTIFICATIONS) {
            if (onComplete != null) onComplete.run();
            return;
        }
        send(context, "notification", appName, title, text, onComplete);
    }

    static void send(Context context, String endpoint, String source, String title, String text) {
        send(context, endpoint, source, title, text, null);
    }

    static void send(Context context, String endpoint, String source, String title, String text, Runnable onComplete) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            try {
                JSONObject notice = makeNotice(appContext, endpoint, source, title, text);
                flushQueueNow(appContext);
                if (!post(appContext, notice)) {
                    NoticeQueue.enqueue(appContext, notice);
                    BkashNoticeHistory.recordIfParsed(appContext, notice);
                    scheduleNetworkFlush(appContext);
                }
            } catch (Exception exc) {
                try {
                    JSONObject notice = makeNotice(appContext, endpoint, source, title, text);
                    NoticeQueue.enqueue(appContext, notice);
                    BkashNoticeHistory.recordIfParsed(appContext, notice);
                    scheduleNetworkFlush(appContext);
                } catch (Exception ignored) {
                }
            } finally {
                if (onComplete != null) onComplete.run();
            }
        });
    }

    static void flushQueue(Context context) {
        flushQueue(context, null);
    }

    static void flushQueue(Context context, Runnable onComplete) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            DebugLog.append(appContext, "Flush started. Queue=" + NoticeQueue.count(appContext));
            flushQueueNow(appContext);
            DebugLog.append(appContext, "Flush finished. Queue=" + NoticeQueue.count(appContext));
            if (onComplete != null) new Handler(Looper.getMainLooper()).post(onComplete);
        });
    }

    static void flushQueueSync(Context context) {
        flushQueueNow(context.getApplicationContext());
    }

    private static boolean queueNotice(Context context, String endpoint, String source, String title, String text, String label, boolean flushAfterQueue) {
        Context appContext = context.getApplicationContext();
        try {
            JSONObject notice = makeNotice(appContext, endpoint, source, title, text);
            if (!NoticeQueue.enqueueSync(appContext, notice)) {
                ForwardingStats.recordFailure(appContext, "Queue " + label + " failed: commit returned false");
                return false;
            }
            BkashNoticeHistory.recordIfParsed(appContext, notice);
            scheduleNetworkFlush(appContext);
            DebugLog.append(appContext, "Queued " + label + ". Flush after queue=" + flushAfterQueue + " queue=" + NoticeQueue.count(appContext));
            if (flushAfterQueue) flushQueue(appContext);
            return true;
        } catch (Exception exc) {
            ForwardingStats.recordFailure(appContext, "Queue " + label + " failed: " + exc.getClass().getSimpleName());
            return false;
        }
    }

    interface HealthCallback {
        void onResult(HealthResult result);
    }

    interface SmsInboxScanCallback {
        void onResult(int queued);
    }

    static final class HealthResult {
        final boolean internetOk;
        final boolean serverReachable;
        final boolean authOk;
        final String message;

        HealthResult(boolean internetOk, boolean serverReachable, boolean authOk, String message) {
            this.internetOk = internetOk;
            this.serverReachable = serverReachable;
            this.authOk = authOk;
            this.message = message;
        }
    }

    static void checkHealth(Context context, HealthCallback callback) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            HealthResult result = checkHealthSync(appContext);
            new Handler(Looper.getMainLooper()).post(() -> callback.onResult(result));
        });
    }

    static void scanSmsInbox(Context context, boolean recordNoNew, SmsInboxScanCallback callback) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            int queued = scanSmsInboxSync(appContext, recordNoNew);
            if (callback != null) new Handler(Looper.getMainLooper()).post(() -> callback.onResult(queued));
        });
    }

    static void scanSmsInboxFromForegroundService(Context context) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            DebugLog.append(appContext, "Foreground service background scan tick started");
            int queued = scanSmsInboxSync(appContext, false);
            DebugLog.append(appContext, "Foreground service background scan tick finished queued=" + queued + " queue=" + NoticeQueue.count(appContext));
        });
    }

    static int scanSmsInboxSync(Context context, boolean recordNoNew) {
        Context appContext = context.getApplicationContext();
        int queued = SmsInboxReader.queueRecentPaymentNotices(appContext, recordNoNew);
        if (queued > 0) flushQueueNow(appContext);
        return queued;
    }

    static int scanSmsInboxForBackgroundAlarm(Context context) {
        Context appContext = context.getApplicationContext();
        int queued = SmsInboxReader.queueRecentPaymentNotices(appContext, false);
        scheduleNetworkFlush(appContext);
        return queued;
    }

    static void scheduleRetry(Context context) {
        Context appContext = context.getApplicationContext();
        Intent intent = new Intent(appContext, RetryReceiver.class);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(appContext, BACKGROUND_SCAN_ALARM_REQUEST_CODE, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarmManager = (AlarmManager) appContext.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager != null) {
            long triggerAt = System.currentTimeMillis() + BACKGROUND_SCAN_INTERVAL_MS;
            try {
                if (Build.VERSION.SDK_INT >= 19) {
                    alarmManager.setWindow(AlarmManager.RTC_WAKEUP, triggerAt, BACKGROUND_SCAN_INTERVAL_MS, pendingIntent);
                } else {
                    alarmManager.set(AlarmManager.RTC_WAKEUP, triggerAt, pendingIntent);
                }
            } catch (Exception exc) {
                ForwardingStats.recordFailure(appContext, "Background scan alarm schedule failed: " + exc.getClass().getSimpleName());
            }
        }
        scheduleNetworkFlush(appContext);
    }

    static void scheduleNetworkFlush(Context context) {
        JobScheduler scheduler = (JobScheduler) context.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        if (scheduler == null) return;
        JobInfo job = new JobInfo.Builder(NETWORK_FLUSH_JOB_ID, new ComponentName(context, NetworkFlushJobService.class))
            .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
            .setMinimumLatency(0)
            .setPersisted(true)
            .build();
        scheduler.schedule(job);
    }

    private static void flushQueueNow(Context context) {
        Set<String> current = NoticeQueue.snapshot(context);
        if (current.isEmpty()) return;
        Set<String> failed = new LinkedHashSet<>();
        for (String row : current) {
            try {
                if (!post(context, NoticeQueue.decode(row))) failed.add(row);
            } catch (Exception exc) {
                failed.add(row);
            }
        }
        NoticeQueue.save(context, failed);
        if (!failed.isEmpty()) scheduleNetworkFlush(context);
    }

    private static HealthResult checkHealthSync(Context context) {
        boolean internetOk = hasInternet(context);
        if (!internetOk) {
            return new HealthResult(false, false, false, "No active internet connection");
        }
        if (!ForwarderConfig.isConfigured(context)) {
            return new HealthResult(true, false, false, "Save the required token first");
        }

        HttpURLConnection connection = null;
        try {
            URL url = new URL(healthEndpoint(context));
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(8_000);
            connection.setReadTimeout(8_000);
            connection.setRequestProperty("Accept", "application/json");
            if (!ForwarderConfig.isSellerMode(context) && ForwarderConfig.hasForwarderSecret(context)) {
                connection.setRequestProperty("X-Forwarder-Token", ForwarderConfig.forwarderSecret(context));
            }
            int code = connection.getResponseCode();
            String body = readResponse(connection, code).trim();
            JSONObject json = body.startsWith("{") ? new JSONObject(body) : new JSONObject();
            boolean reachable = code > 0;
            boolean authOk = json.optBoolean("auth_ok", code >= 200 && code < 300);
            String message = json.optString("message", code >= 200 && code < 300 ? "Server health check passed" : "HTTP " + code);
            if (code == 404) message = "Health endpoint not found. Check URL or update server code.";
            return new HealthResult(true, reachable, authOk, message + " (HTTP " + code + ")");
        } catch (Exception exc) {
            return new HealthResult(true, false, false, exc.getClass().getSimpleName());
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static boolean hasInternet(Context context) {
        ConnectivityManager manager = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        if (manager == null) return false;
        Network network = manager.getActiveNetwork();
        if (network == null) return false;
        NetworkCapabilities capabilities = manager.getNetworkCapabilities(network);
        return capabilities != null && capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET);
    }

    private static String healthEndpoint(Context context) throws Exception {
        String base = ForwarderConfig.baseUrl(context);
        if (ForwarderConfig.isSellerMode(context)) {
            return base + "/seller/" + URLEncoder.encode(ForwarderConfig.sellerToken(context), "UTF-8") + "/health";
        }
        return base + "/forwarder-health";
    }

    private static String readResponse(HttpURLConnection connection, int code) throws Exception {
        InputStream stream = code >= 200 && code < 400 ? connection.getInputStream() : connection.getErrorStream();
        if (stream == null) return "";
        StringBuilder builder = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) builder.append(line);
        }
        return builder.toString();
    }

    private static JSONObject makeNotice(Context context, String endpoint, String source, String title, String text) throws Exception {
        JSONObject json = new JSONObject();
        json.put("endpoint", endpoint);
        json.put("source", source == null ? "android" : source);
        json.put("title", title == null ? "" : title);
        json.put("text", text == null ? "" : text);
        json.put("device_id", ForwarderConfig.deviceId(context));
        json.put("received_at", System.currentTimeMillis());
        BkashNoticeParser.Parsed parsed = BkashNoticeParser.parse(text);
        if (parsed != null) {
            json.put("parsed_bkash", true);
            json.put("amount_bdt", parsed.amountBdt);
            json.put("trx_id", parsed.trxId);
            json.put("notice_sender", parsed.sender);
            if (parsed.noticeTime != null) json.put("notice_datetime", parsed.noticeTime);
        }
        return json;
    }

    private static boolean post(Context context, JSONObject notice) {
        if (!ForwarderConfig.isConfigured(context)) {
            ForwardingStats.recordFailure(context, "Forwarder is not configured");
            return false;
        }
        HttpURLConnection connection = null;
        try {
            String endpoint = notice.optString("endpoint", "notification");
            URL url = new URL(ForwarderConfig.endpoint(context, endpoint));
            DebugLog.append(context, "HTTP post start endpoint=" + endpoint);
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setConnectTimeout(10_000);
            connection.setReadTimeout(10_000);
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            if (!ForwarderConfig.isSellerMode(context) && ForwarderConfig.hasForwarderSecret(context)) {
                connection.setRequestProperty("X-Forwarder-Token", ForwarderConfig.forwarderSecret(context));
            }
            byte[] body = notice.toString().getBytes(StandardCharsets.UTF_8);
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream stream = connection.getOutputStream()) {
                stream.write(body);
            }
            int code = connection.getResponseCode();
            String responseBody = readResponse(connection, code).trim();
            boolean ok = code >= 200 && code < 300;
            if (ok) {
                JSONObject ack = null;
                try {
                    ack = responseBody.startsWith("{") ? new JSONObject(responseBody) : null;
                } catch (Exception ignored) {
                }
                ForwardingStats.recordSuccess(context, endpoint, ack);
            } else {
                DebugLog.append(context, "HTTP post failed code=" + code + " endpoint=" + endpoint);
                ForwardingStats.recordFailure(context, "HTTP " + code + " from " + endpoint + " endpoint");
            }
            return ok;
        } catch (Exception exc) {
            DebugLog.append(context, "HTTP post exception endpoint=" + notice.optString("endpoint", "notification") + " error=" + exc.getClass().getSimpleName());
            ForwardingStats.recordFailure(context, "HTTP post exception: " + exc.getClass().getSimpleName());
            return false;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }
}
