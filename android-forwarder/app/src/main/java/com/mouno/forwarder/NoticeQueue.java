package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Set;

final class NoticeQueue {
    private static final String PREFS = "forwarder_queue";
    private static final String KEY = "notices";

    private NoticeQueue() {}

    static synchronized void enqueue(Context context, JSONObject notice) {
        Set<String> rows = snapshot(context);
        rows.add(Base64.encodeToString(notice.toString().getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP));
        save(context, rows);
    }

    static synchronized boolean enqueueSync(Context context, JSONObject notice) {
        Set<String> rows = snapshot(context);
        rows.add(Base64.encodeToString(notice.toString().getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP));
        return saveSync(context, rows);
    }

    static synchronized Set<String> snapshot(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        return new LinkedHashSet<>(prefs.getStringSet(KEY, Collections.emptySet()));
    }

    static synchronized void save(Context context, Set<String> rows) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putStringSet(KEY, new LinkedHashSet<>(rows)).apply();
    }

    static synchronized boolean saveSync(Context context, Set<String> rows) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putStringSet(KEY, new LinkedHashSet<>(rows)).commit();
    }

    static synchronized int count(Context context) {
        return snapshot(context).size();
    }

    static synchronized String latestSummary(Context context) {
        String latest = "";
        long latestReceivedAt = -1L;
        for (String row : snapshot(context)) {
            try {
                JSONObject notice = decode(row);
                long receivedAt = notice.optLong("received_at", 0L);
                if (notice.optBoolean("parsed_bkash", false) && receivedAt >= latestReceivedAt) {
                    latestReceivedAt = receivedAt;
                    latest = notice.optString("trx_id", "") + " / " + notice.optDouble("amount_bdt", 0) + " BDT / " + notice.optString("notice_sender", "");
                }
            } catch (Exception ignored) {
            }
        }
        return latest;
    }

    static JSONObject decode(String row) throws Exception {
        byte[] bytes = Base64.decode(row, Base64.NO_WRAP);
        return new JSONObject(new String(bytes, StandardCharsets.UTF_8));
    }

    static SharedPreferences prefsForUpdates(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
