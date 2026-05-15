package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONObject;

import java.text.DateFormat;
import java.util.Date;

final class ForwardingStats {
    private static final String PREFS = "forwarding_stats";
    private static final String KEY_SUCCESS_COUNT = "success_count";
    private static final String KEY_FAILURE_COUNT = "failure_count";
    private static final String KEY_LAST_FORWARDED_AT = "last_forwarded_at";
    private static final String KEY_LAST_SOURCE = "last_source";
    private static final String KEY_LAST_ERROR = "last_error";
    private static final String KEY_LAST_PAYMENT_STATUS = "last_payment_status";
    private static final String KEY_LAST_PAYMENT_MESSAGE = "last_payment_message";
    private static final String KEY_LAST_TRX_ID = "last_trx_id";
    private static final String KEY_LAST_AMOUNT_BDT = "last_amount_bdt";
    private static final String KEY_LAST_PHONE_EVENT = "last_phone_event";
    private static final String KEY_LAST_PHONE_EVENT_AT = "last_phone_event_at";

    private ForwardingStats() {}

    static void recordSuccess(Context context, String endpoint, JSONObject ack) {
        DebugLog.append(context, "Forward success: " + sourceLabel(endpoint));
        SharedPreferences prefs = prefs(context);
        SharedPreferences.Editor editor = prefs.edit()
            .putInt(KEY_SUCCESS_COUNT, prefs.getInt(KEY_SUCCESS_COUNT, 0) + 1)
            .putLong(KEY_LAST_FORWARDED_AT, System.currentTimeMillis())
            .putString(KEY_LAST_SOURCE, sourceLabel(endpoint));
        if (ack != null) {
            editor.putString(KEY_LAST_PAYMENT_STATUS, ack.optString("payment_status", "accepted"))
                .putString(KEY_LAST_PAYMENT_MESSAGE, ack.optString("message", statusHelp(ack.optString("payment_status", "accepted"))))
                .putString(KEY_LAST_TRX_ID, ack.optString("trx_id", ""))
                .putString(KEY_LAST_AMOUNT_BDT, ack.has("amount_bdt") ? ack.optString("amount_bdt") : "");
        } else {
            editor.putString(KEY_LAST_PAYMENT_STATUS, "accepted")
                .putString(KEY_LAST_PAYMENT_MESSAGE, statusHelp("accepted"))
                .putString(KEY_LAST_TRX_ID, "")
                .putString(KEY_LAST_AMOUNT_BDT, "");
        }
        editor.apply();
    }

    static void recordFailure(Context context, String error) {
        DebugLog.append(context, "Forward failure: " + failureLogLabel(error));
        SharedPreferences prefs = prefs(context);
        prefs.edit()
            .putInt(KEY_FAILURE_COUNT, prefs.getInt(KEY_FAILURE_COUNT, 0) + 1)
            .putString(KEY_LAST_ERROR, clean(error))
            .apply();
    }

    static void recordPhoneEvent(Context context, String event) {
        DebugLog.append(context, "Phone event: " + phoneEventLogLabel(event));
        prefs(context).edit()
            .putString(KEY_LAST_PHONE_EVENT, clean(event))
            .putLong(KEY_LAST_PHONE_EVENT_AT, System.currentTimeMillis())
            .apply();
    }

    static String summary(Context context) {
        SharedPreferences prefs = prefs(context);
        return "Forwarded: " + prefs.getInt(KEY_SUCCESS_COUNT, 0) + "\n"
            + "Failed/queued attempts: " + prefs.getInt(KEY_FAILURE_COUNT, 0) + "\n"
            + "Last forwarded notice time: " + formatTime(prefs.getLong(KEY_LAST_FORWARDED_AT, 0L)) + "\n"
            + "Last source: " + value(prefs.getString(KEY_LAST_SOURCE, ""), "none") + "\n"
            + "Last phone event: " + value(prefs.getString(KEY_LAST_PHONE_EVENT, ""), "none") + " at " + formatTime(prefs.getLong(KEY_LAST_PHONE_EVENT_AT, 0L)) + "\n"
            + "Queue count: " + NoticeQueue.count(context) + "\n"
            + "Last error message: " + value(prefs.getString(KEY_LAST_ERROR, ""), "none");
    }

    static String paymentSummary(Context context) {
        SharedPreferences prefs = prefs(context);
        String status = prefs.getString(KEY_LAST_PAYMENT_STATUS, "");
        return "Outcome: " + friendlyStatus(status) + "\n"
            + "Meaning: " + value(prefs.getString(KEY_LAST_PAYMENT_MESSAGE, ""), "No payment ACK received yet") + "\n"
            + "TrxID: " + value(prefs.getString(KEY_LAST_TRX_ID, ""), "none") + "\n"
            + "Amount: " + value(prefs.getString(KEY_LAST_AMOUNT_BDT, ""), "none") + " BDT";
    }

    static String lastPaymentStatus(Context context) {
        return prefs(context).getString(KEY_LAST_PAYMENT_STATUS, "");
    }

    private static String sourceLabel(String endpoint) {
        return "sms".equalsIgnoreCase(endpoint) ? "SMS" : "Notification";
    }

    private static String friendlyStatus(String status) {
        String value = status == null ? "" : status.trim();
        if (value.equals("matched_order")) return "✅ matched order / অর্ডার ম্যাচ হয়েছে";
        if (value.equals("duplicate")) return "♻️ duplicate / আগেই প্রসেস হয়েছে";
        if (value.equals("manual_review")) return "⚠️ manual review / অ্যাডমিন যাচাই দরকার";
        if (value.equals("ignored")) return "⏭️ ignored / payment notice না";
        if (value.equals("parsed")) return "📥 parsed / payment পড়া হয়েছে";
        if (value.equals("accepted")) return "📤 accepted / server নিয়েছে";
        return value.isEmpty() ? "none" : value;
    }

    private static String statusHelp(String status) {
        String value = status == null ? "" : status.trim();
        if (value.equals("matched_order")) return "Server found the matching order and processed it.";
        if (value.equals("duplicate")) return "This TrxID was already recorded, so server ignored the repeat notice.";
        if (value.equals("manual_review")) return "Server parsed the payment, but admin/seller must review before completion.";
        if (value.equals("ignored")) return "Server received the message, but it was not a supported payment notice.";
        if (value.equals("parsed")) return "Server parsed the payment, but no waiting order matched yet.";
        return "Server accepted the notice.";
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

    private static String failureLogLabel(String error) {
        String value = clean(error);
        int detailStart = value.indexOf(':');
        if (detailStart > 0) value = value.substring(0, detailStart).trim();
        return value.isEmpty() ? "unknown error" : value;
    }

    private static String phoneEventLogLabel(String event) {
        String value = clean(event);
        int senderStart = value.indexOf(" from ");
        if (senderStart >= 0) value = value.substring(0, senderStart) + " from [redacted]";
        return value;
    }

    private static String value(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value;
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    static SharedPreferences prefsForUpdates(Context context) {
        return prefs(context);
    }
}
