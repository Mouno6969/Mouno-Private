package com.mouno.forwarder;

import android.Manifest;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.os.Build;
import android.provider.Telephony;

import java.util.Locale;

final class SmsInboxReader {
    private static final String PREFS = "sms_inbox_reader";
    private static final String KEY_LAST_AUTO_SCAN_AT = "last_auto_scan_at";
    private static final long MANUAL_LOOKBACK_MS = 24L * 60L * 60L * 1000L;
    private static final int MAX_CURSOR_ROWS = 300;
    private static final int MAX_AUTO_QUEUED = 5;
    private static final int MAX_MANUAL_QUEUED = 25;

    private SmsInboxReader() {}

    static int queueRecentPaymentNotices(Context context, boolean recordNoNew) {
        Context appContext = context.getApplicationContext();
        if (!canReadSms(appContext)) {
            if (recordNoNew) ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan skipped: READ_SMS permission missing");
            return 0;
        }
        long now = System.currentTimeMillis();
        boolean manualScan = recordNoNew;
        SharedPreferences prefs = prefs(appContext);
        if (!manualScan && !prefs.contains(KEY_LAST_AUTO_SCAN_AT)) {
            prefs.edit().putLong(KEY_LAST_AUTO_SCAN_AT, now).apply();
            return 0;
        }
        long since = manualScan ? now - MANUAL_LOOKBACK_MS : prefs.getLong(KEY_LAST_AUTO_SCAN_AT, now);
        int maxQueued = manualScan ? MAX_MANUAL_QUEUED : MAX_AUTO_QUEUED;
        int queued = 0;
        long latestSeenAt = since;
        String[] projection = new String[]{Telephony.Sms.ADDRESS, Telephony.Sms.BODY, Telephony.Sms.DATE};
        String selection = Telephony.Sms.DATE + ">=?";
        String[] selectionArgs = new String[]{String.valueOf(since)};
        try (Cursor cursor = appContext.getContentResolver().query(
            Telephony.Sms.Inbox.CONTENT_URI,
            projection,
            selection,
            selectionArgs,
            Telephony.Sms.DATE + " DESC"
        )) {
            if (cursor == null) return 0;
            int addressIndex = cursor.getColumnIndex(Telephony.Sms.ADDRESS);
            int bodyIndex = cursor.getColumnIndex(Telephony.Sms.BODY);
            int dateIndex = cursor.getColumnIndex(Telephony.Sms.DATE);
            int rows = 0;
            while (cursor.moveToNext() && rows++ < MAX_CURSOR_ROWS && queued < maxQueued) {
                String sender = addressIndex >= 0 ? cursor.getString(addressIndex) : "sms_inbox";
                String text = bodyIndex >= 0 ? cursor.getString(bodyIndex) : "";
                long receivedAt = dateIndex >= 0 ? cursor.getLong(dateIndex) : now;
                if (receivedAt > latestSeenAt) latestSeenAt = receivedAt;
                BkashNoticeParser.Parsed parsed = BkashNoticeParser.parse(text);
                if (parsed == null || (!isTrustedBkashSender(sender) && !isBkashNotice(text))) continue;
                String smsSender = sender == null || sender.trim().isEmpty() ? "sms_inbox" : sender;
                final boolean[] saved = new boolean[]{false};
                boolean accepted = BkashPaymentDeduper.enqueueIfNew(appContext, parsed, () -> {
                    saved[0] = ForwarderClient.queueSmsFromInboxScan(appContext, smsSender, text);
                    return saved[0];
                });
                if (accepted && saved[0]) queued++;
            }
        } catch (Exception exc) {
            ForwardingStats.recordFailure(appContext, "SMS inbox scan failed: " + exc.getClass().getSimpleName());
            return queued;
        } finally {
            if (!manualScan) prefs.edit().putLong(KEY_LAST_AUTO_SCAN_AT, Math.max(now, latestSeenAt)).apply();
        }
        if (queued > 0) {
            ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan queued " + queued + " payment notice(s)");
        } else if (recordNoNew) {
            ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan found no new payment notices");
        }
        return queued;
    }

    private static boolean canReadSms(Context context) {
        return Build.VERSION.SDK_INT < 23 || context.checkSelfPermission(Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED;
    }

    private static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private static boolean isTrustedBkashSender(String sender) {
        String value = sender == null ? "" : sender.trim().toLowerCase(Locale.ROOT);
        return value.equals("bkash") || value.equals("16247") || value.contains("bkash");
    }

    private static boolean isBkashNotice(String text) {
        String lower = text == null ? "" : text.toLowerCase(Locale.ROOT);
        return lower.contains("bkash") || lower.contains("trxid") || lower.contains("trx id") || lower.contains("txnid") || lower.contains("txn id") || text.contains("বিকাশ");
    }
}
