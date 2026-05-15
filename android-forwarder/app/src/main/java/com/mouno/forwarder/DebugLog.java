package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;

import java.text.DateFormat;
import java.util.Date;

final class DebugLog {
    private static final String PREFS = "forwarder_debug_log";
    private static final String KEY_LOG = "log";
    private static final String KEY_UPDATED_AT = "updated_at";
    private static final int MAX_CHARS = 24_000;

    private DebugLog() {}

    static synchronized void append(Context context, String event) {
        Context appContext = context.getApplicationContext();
        SharedPreferences prefs = prefs(appContext);
        long now = System.currentTimeMillis();
        String line = formatTime(now) + "  " + clean(event);
        String current = prefs.getString(KEY_LOG, "");
        String updated = current == null || current.isEmpty() ? line : line + "\n" + current;
        if (updated.length() > MAX_CHARS) updated = updated.substring(0, MAX_CHARS);
        prefs.edit()
            .putString(KEY_LOG, updated)
            .putLong(KEY_UPDATED_AT, now)
            .apply();
    }

    static String text(Context context) {
        String log = prefs(context).getString(KEY_LOG, "");
        return log == null || log.trim().isEmpty() ? "No debug events yet." : log;
    }

    static void clear(Context context) {
        prefs(context).edit().remove(KEY_LOG).remove(KEY_UPDATED_AT).apply();
        append(context, "Debug log cleared");
    }

    static String updatedAtText(Context context) {
        long updatedAt = prefs(context).getLong(KEY_UPDATED_AT, 0L);
        return updatedAt <= 0L ? "never" : formatTime(updatedAt);
    }

    static SharedPreferences prefsForUpdates(Context context) {
        return prefs(context);
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static String clean(String event) {
        String value = event == null ? "unknown" : event.trim().replaceAll("\\s+", " ");
        if (value.isEmpty()) return "unknown";
        return value.length() > 240 ? value.substring(0, 240) : value;
    }

    private static String formatTime(long millis) {
        return DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.MEDIUM).format(new Date(millis));
    }
}
