package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

final class BkashNoticeHistory {
    private static final String PREFS = "bkash_notice_history";
    private static final String KEY_TOTAL_PARSED = "total_parsed";
    private static final String KEY_LAST_SUMMARY = "last_summary";
    private static final String KEY_LAST_AT = "last_at";

    private BkashNoticeHistory() {}

    static void recordIfParsed(Context context, JSONObject notice) {
        if (!notice.optBoolean("parsed_bkash", false)) return;
        String summary = notice.optString("trx_id", "") + " / " + notice.optDouble("amount_bdt", 0) + " BDT / " + notice.optString("notice_sender", "");
        SharedPreferences prefs = prefs(context);
        prefs.edit()
            .putInt(KEY_TOTAL_PARSED, prefs.getInt(KEY_TOTAL_PARSED, 0) + 1)
            .putString(KEY_LAST_SUMMARY, summary)
            .putLong(KEY_LAST_AT, System.currentTimeMillis())
            .apply();
    }

    static int totalParsed(Context context) {
        return prefs(context).getInt(KEY_TOTAL_PARSED, 0);
    }

    static String lastSummary(Context context) {
        String summary = prefs(context).getString(KEY_LAST_SUMMARY, "");
        return summary == null ? "" : summary;
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    static SharedPreferences prefsForUpdates(Context context) {
        return prefs(context);
    }
}
