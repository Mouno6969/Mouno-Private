package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.Locale;
import java.util.Map;

final class BkashPaymentDeduper {
    private static final String PREFS = "bkash_payment_dedupe";
    private static final String KEY_PREFIX = "trx:";
    private static final long RETENTION_MS = 7L * 24L * 60L * 60L * 1000L;

    private BkashPaymentDeduper() {}

    interface EnqueueAction {
        boolean enqueue();
    }

    static synchronized boolean enqueueIfNew(Context context, BkashNoticeParser.Parsed parsed, EnqueueAction action) {
        String trxId = normalize(parsed);
        if (trxId.isEmpty()) return action.enqueue();
        SharedPreferences prefs = prefs(context);
        String key = KEY_PREFIX + trxId;
        long now = System.currentTimeMillis();
        if (prefs.contains(key) && now - prefs.getLong(key, 0L) <= RETENTION_MS) return false;
        if (!action.enqueue()) return false;
        SharedPreferences.Editor editor = prefs.edit().putLong(key, now);
        pruneExpired(prefs, editor, now);
        if (!editor.commit()) prefs.edit().putLong(key, now).apply();
        return true;
    }

    private static void pruneExpired(SharedPreferences prefs, SharedPreferences.Editor editor, long now) {
        for (Map.Entry<String, ?> entry : prefs.getAll().entrySet()) {
            Object value = entry.getValue();
            if (entry.getKey().startsWith(KEY_PREFIX) && value instanceof Long && now - (Long) value > RETENTION_MS) {
                editor.remove(entry.getKey());
            }
        }
    }

    private static String normalize(BkashNoticeParser.Parsed parsed) {
        return parsed == null || parsed.trxId == null ? "" : parsed.trxId.trim().toUpperCase(Locale.ROOT);
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
