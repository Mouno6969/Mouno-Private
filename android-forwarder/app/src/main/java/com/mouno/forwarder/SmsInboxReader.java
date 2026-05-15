package com.mouno.forwarder;

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

final class SmsInboxReader {
    private static final String PREFS = "sms_inbox_poll";
    private static final String KEY_SEEN_TRX_IDS = "seen_trx_ids";
    private static final Uri SMS_INBOX = Uri.parse("content://sms/inbox");
    private static final String[] PROJECTION = new String[]{"address", "body", "date"};
    private static final long LOOKBACK_MS = 15 * 60_000L;
    private static final long FUTURE_SKEW_MS = 60_000L;
    private static final long POLL_LOOKBACK_MS = 30 * 60_000L;
    private static final int MAX_ROWS = 40;
    private static final int MAX_FORWARD_PER_POLL = 5;

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

    static void pollAndForward(Context context) {
        Context appContext = context.getApplicationContext();
        new Thread(() -> pollAndForwardNow(appContext)).start();
    }

    private static void pollAndForwardNow(Context context) {
        if (!canReadSms(context)) {
            ForwardingStats.recordPhoneEvent(context, "SMS inbox poll skipped: READ_SMS permission missing");
            return;
        }
        List<SmsNotice> notices = latestUnseenPaymentNotices(context);
        Collections.reverse(notices);
        for (SmsNotice notice : notices) {
            if (markSeen(context, notice.parsed.trxId)) {
                ForwardingStats.recordPhoneEvent(context, "SMS inbox poll payment captured: " + notice.parsed.summary());
                ForwarderClient.queueSms(context, notice.address, notice.body);
            }
        }
    }

    private static List<SmsNotice> latestUnseenPaymentNotices(Context context) {
        List<SmsNotice> notices = new ArrayList<>();
        long since = Math.max(0L, System.currentTimeMillis() - POLL_LOOKBACK_MS);
        try (Cursor cursor = context.getApplicationContext().getContentResolver().query(
            SMS_INBOX,
            PROJECTION,
            "date>=?",
            new String[]{String.valueOf(since)},
            "date DESC"
        )) {
            if (cursor == null) return notices;
            int addressIndex = cursor.getColumnIndex("address");
            int bodyIndex = cursor.getColumnIndex("body");
            int rows = 0;
            while (cursor.moveToNext() && rows++ < MAX_ROWS && notices.size() < MAX_FORWARD_PER_POLL) {
                String address = addressIndex >= 0 ? cursor.getString(addressIndex) : "";
                if (!isTrustedBkashSender(address)) continue;
                String body = bodyIndex >= 0 ? cursor.getString(bodyIndex) : "";
                BkashNoticeParser.Parsed parsed = BkashNoticeParser.parse(body);
                if (parsed != null && !isSeen(context, parsed.trxId)) notices.add(new SmsNotice(address, body, parsed));
            }
        } catch (Exception exc) {
            ForwardingStats.recordFailure(context, "SMS inbox poll failed: " + exc.getClass().getSimpleName());
        }
        return notices;
    }

    private static boolean canReadSms(Context context) {
        return Build.VERSION.SDK_INT < 23 || context.checkSelfPermission(Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED;
    }

    private static boolean isSeen(Context context, String trxId) {
        return prefs(context).getStringSet(KEY_SEEN_TRX_IDS, Collections.emptySet()).contains(trxId);
    }

    private static synchronized boolean markSeen(Context context, String trxId) {
        SharedPreferences prefs = prefs(context);
        Set<String> seen = new HashSet<>(prefs.getStringSet(KEY_SEEN_TRX_IDS, Collections.emptySet()));
        if (!seen.add(trxId)) return false;
        return prefs.edit().putStringSet(KEY_SEEN_TRX_IDS, seen).commit();
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static boolean isTrustedBkashSender(String sender) {
        String value = sender == null ? "" : sender.trim().toLowerCase(Locale.ROOT);
        return value.equals("bkash") || value.equals("16247") || value.contains("bkash");
    }

    private static final class SmsNotice {
        final String address;
        final String body;
        final BkashNoticeParser.Parsed parsed;

        SmsNotice(String address, String body, BkashNoticeParser.Parsed parsed) {
            this.address = address;
            this.body = body;
            this.parsed = parsed;
        }
    }
}
