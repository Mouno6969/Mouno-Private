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
    private static final String KEY_LAST_AUTO_SCAN_ID = "last_auto_scan_id";
    private static final long MANUAL_LOOKBACK_MS = 24L * 60L * 60L * 1000L;
    private static final int MAX_CURSOR_ROWS = 300;
    private static final int MAX_AUTO_QUEUED = 5;
    private static final int MAX_MANUAL_QUEUED = 25;

    private SmsInboxReader() {}

    static int queueRecentPaymentNotices(Context context, boolean recordNoNew) {
        Context appContext = context.getApplicationContext();
        if (!canReadSms(appContext)) {
            DebugLog.append(appContext, "SMS inbox scan skipped: READ_SMS missing");
            if (recordNoNew) ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan skipped: READ_SMS permission missing");
            return 0;
        }
        long now = System.currentTimeMillis();
        DebugLog.append(appContext, "SMS inbox scan started manual=" + recordNoNew);
        boolean manualScan = recordNoNew;
        SharedPreferences prefs = prefs(appContext);
        if (!manualScan && !prefs.contains(KEY_LAST_AUTO_SCAN_AT)) {
            prefs.edit()
                .putLong(KEY_LAST_AUTO_SCAN_AT, now)
                .putLong(KEY_LAST_AUTO_SCAN_ID, -1L)
                .apply();
            return 0;
        }
        long since = manualScan ? now - MANUAL_LOOKBACK_MS : prefs.getLong(KEY_LAST_AUTO_SCAN_AT, now);
        long lastAutoId = manualScan ? -1L : prefs.getLong(KEY_LAST_AUTO_SCAN_ID, -1L);
        int maxQueued = manualScan ? MAX_MANUAL_QUEUED : MAX_AUTO_QUEUED;
        int queued = 0;
        long latestSeenAt = -1L;
        long latestSeenId = -1L;
        String[] projection = new String[]{Telephony.Sms._ID, Telephony.Sms.ADDRESS, Telephony.Sms.BODY, Telephony.Sms.DATE};
        String selection = manualScan
            ? Telephony.Sms.DATE + ">=?"
            : "(" + Telephony.Sms.DATE + ">? OR (" + Telephony.Sms.DATE + "=? AND " + Telephony.Sms._ID + ">?))";
        String[] selectionArgs = manualScan
            ? new String[]{String.valueOf(since)}
            : new String[]{String.valueOf(since), String.valueOf(since), String.valueOf(lastAutoId)};
        try (Cursor cursor = appContext.getContentResolver().query(
            Telephony.Sms.Inbox.CONTENT_URI,
            projection,
            selection,
            selectionArgs,
            Telephony.Sms.DATE + " ASC, " + Telephony.Sms._ID + " ASC"
        )) {
            if (cursor == null) return 0;
            int idIndex = cursor.getColumnIndex(Telephony.Sms._ID);
            int addressIndex = cursor.getColumnIndex(Telephony.Sms.ADDRESS);
            int bodyIndex = cursor.getColumnIndex(Telephony.Sms.BODY);
            int dateIndex = cursor.getColumnIndex(Telephony.Sms.DATE);
            int rows = 0;
            boolean exhausted = false;
            while (rows < MAX_CURSOR_ROWS && queued < maxQueued) {
                if (!cursor.moveToNext()) {
                    exhausted = true;
                    break;
                }
                rows++;
                long rowId = idIndex >= 0 ? cursor.getLong(idIndex) : rows;
                String sender = addressIndex >= 0 ? cursor.getString(addressIndex) : "sms_inbox";
                String text = bodyIndex >= 0 ? cursor.getString(bodyIndex) : "";
                long receivedAt = dateIndex >= 0 ? cursor.getLong(dateIndex) : now;
                latestSeenAt = receivedAt;
                latestSeenId = rowId;
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
            if (!manualScan && latestSeenAt >= 0L) {
                prefs.edit()
                    .putLong(KEY_LAST_AUTO_SCAN_AT, latestSeenAt)
                    .putLong(KEY_LAST_AUTO_SCAN_ID, latestSeenId)
                    .apply();
            }
        } catch (Exception exc) {
            ForwardingStats.recordFailure(appContext, "SMS inbox scan failed: " + exc.getClass().getSimpleName());
            return queued;
        }
        if (queued > 0) {
            DebugLog.append(appContext, "SMS inbox scan queued " + queued + " payment notice(s)");
            ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan queued " + queued + " payment notice(s)");
        } else if (recordNoNew) {
            DebugLog.append(appContext, "SMS inbox scan found no new payment notices");
            ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan found no new payment notices");
        } else {
            DebugLog.append(appContext, "SMS inbox scan finished. queued=0");
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
