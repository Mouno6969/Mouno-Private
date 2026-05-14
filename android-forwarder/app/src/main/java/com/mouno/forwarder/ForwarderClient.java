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
            }
        });
    }

    static void flushQueue(Context context) {
        flushQueue(context, null);
    }

    static void flushQueue(Context context, Runnable onComplete) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            flushQueueNow(appContext);
            if (onComplete != null) new Handler(Looper.getMainLooper()).post(onComplete);
        });
    }

    static void flushQueueSync(Context context) {
        flushQueueNow(context.getApplicationContext());
    }

    interface HealthCallback {
        void onResult(HealthResult result);
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

    static void scheduleRetry(Context context) {
        Intent intent = new Intent(context, RetryReceiver.class);
        PendingIntent pendingIntent = PendingIntent.getBroadcast(context, 101, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager != null) {
            alarmManager.setInexactRepeating(AlarmManager.RTC_WAKEUP, System.currentTimeMillis() + 60_000L, 5 * 60_000L, pendingIntent);
        }
    }

    static void scheduleNetworkFlush(Context context) {
        JobScheduler scheduler = (JobScheduler) context.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        if (scheduler == null) return;
        JobInfo job = new JobInfo.Builder(NETWORK_FLUSH_JOB_ID, new ComponentName(context, NetworkFlushJobService.class))
            .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
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
            return new HealthResult(true, false, false, "Save server URL and required token/secret first");
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
            return new HealthResult(true, false, false, exc.getClass().getSimpleName() + ": " + exc.getMessage());
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
                ForwardingStats.recordFailure(context, "HTTP " + code + " from " + endpoint + " endpoint");
            }
            return ok;
        } catch (Exception exc) {
            ForwardingStats.recordFailure(context, exc.getClass().getSimpleName() + ": " + exc.getMessage());
            return false;
        } finally {
            if (connection != null) connection.disconnect();
        }
    }
}
