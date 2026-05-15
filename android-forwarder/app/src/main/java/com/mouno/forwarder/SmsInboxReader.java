package com.mouno.forwarder;

import android.content.Context;
import android.database.Cursor;
import android.net.Uri;

import java.util.Locale;

final class SmsInboxReader {
    private static final Uri SMS_INBOX = Uri.parse("content://sms/inbox");
    private static final String[] PROJECTION = new String[]{"address", "body", "date"};
    private static final long LOOKBACK_MS = 15 * 60_000L;
    private static final long FUTURE_SKEW_MS = 60_000L;
    private static final int MAX_ROWS = 40;

    private SmsInboxReader() {}

    static String latestPaymentNotice(Context context, long notificationTimeMillis) {
        long postedAt = notificationTimeMillis > 0L ? notificationTimeMillis : System.currentTimeMillis();
        long since = Math.max(0L, postedAt - LOOKBACK_MS);
        long until = postedAt + FUTURE_SKEW_MS;
        try (Cursor cursor = context.getApplicationContext().getContentResolver().query(
            SMS_INBOX,
            PROJECTION,
            "date>=? AND date<=?",
            new String[]{String.valueOf(since), String.valueOf(until)},
            "date DESC"
        )) {
            if (cursor == null) return "";
            int addressIndex = cursor.getColumnIndex("address");
            int bodyIndex = cursor.getColumnIndex("body");
            int rows = 0;
            while (cursor.moveToNext() && rows++ < MAX_ROWS) {
                String address = addressIndex >= 0 ? cursor.getString(addressIndex) : "";
                if (!isTrustedBkashSender(address)) continue;
                String body = bodyIndex >= 0 ? cursor.getString(bodyIndex) : "";
                if (BkashNoticeParser.parse(body) != null) return body;
            }
        } catch (Exception exc) {
            ForwardingStats.recordFailure(context, "SMS inbox fallback failed: " + exc.getClass().getSimpleName());
        }
        return "";
    }

    private static boolean isTrustedBkashSender(String sender) {
        String value = sender == null ? "" : sender.trim().toLowerCase(Locale.ROOT);
        return value.equals("bkash") || value.equals("16247") || value.contains("bkash");
    }
}
