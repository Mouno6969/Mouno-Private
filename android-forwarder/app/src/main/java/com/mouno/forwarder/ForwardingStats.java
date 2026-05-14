package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;

import java.text.DateFormat;
import java.util.Date;

final class ForwardingStats {
    private static final String PREFS = "forwarding_stats";
    private static final String KEY_SUCCESS_COUNT = "success_count";
    private static final String KEY_FAILURE_COUNT = "failure_count";
    private static final String KEY_LAST_FORWARDED_AT = "last_forwarded_at";
    private static final String KEY_LAST_SOURCE = "last_source";
    private static final String KEY_LAST_ERROR = "last_error";

    private ForwardingStats() {}

    static void recordSuccess(Context context, String endpoint) {
        SharedPreferences prefs = prefs(context);
        prefs.edit()
            .putInt(KEY_SUCCESS_COUNT, prefs.getInt(KEY_SUCCESS_COUNT, 0) + 1)
            .putLong(KEY_LAST_FORWARDED_AT, System.currentTimeMillis())
            .putString(KEY_LAST_SOURCE, sourceLabel(endpoint))
            .apply();
    }

    static void recordFailure(Context context, String error) {
        SharedPreferences prefs = prefs(context);
        prefs.edit()
            .putInt(KEY_FAILURE_COUNT, prefs.getInt(KEY_FAILURE_COUNT, 0) + 1)
            .putString(KEY_LAST_ERROR, clean(error))
            .apply();
    }

    static String summary(Context context) {
        SharedPreferences prefs = prefs(context);
        return "Forwarded: " + prefs.getInt(KEY_SUCCESS_COUNT, 0) + "\n"
            + "Failed/queued attempts: " + prefs.getInt(KEY_FAILURE_COUNT, 0) + "\n"
            + "Last forwarded notice time: " + formatTime(prefs.getLong(KEY_LAST_FORWARDED_AT, 0L)) + "\n"
            + "Last source: " + value(prefs.getString(KEY_LAST_SOURCE, ""), "none") + "\n"
            + "Queue count: " + NoticeQueue.count(context) + "\n"
            + "Last error message: " + value(prefs.getString(KEY_LAST_ERROR, ""), "none");
    }

    private static String sourceLabel(String endpoint) {
        return "sms".equalsIgnoreCase(endpoint) ? "SMS" : "Notification";
    }

    private static String formatTime(long millis) {
        if (millis <= 0L) return "never";
        return DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.MEDIUM).format(new Date(millis));
    }

    private static String clean(String error) {
        String value = error == null ? "unknown error" : error.trim();
        if (value.isEmpty()) return "unknown error";
        return value.length() > 160 ? value.substring(0, 160) : value;
    }

    private static String value(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value;
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
