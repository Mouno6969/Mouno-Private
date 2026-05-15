package com.mouno.forwarder;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.os.Build;
import android.provider.Telephony;

import java.util.Locale;

final class SmsInboxReader {
    private static final long LOOKBACK_MS = 7L * 24L * 60L * 60L * 1000L;
    private static final int MAX_ROWS = 200;

    private SmsInboxReader() {}

    static int queueRecentPaymentNotices(Context context, boolean recordNoNew) {
        Context appContext = context.getApplicationContext();
        if (!canReadSms(appContext)) {
            if (recordNoNew) ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan skipped: READ_SMS permission missing");
            return 0;
        }
        int queued = 0;
        String[] projection = new String[]{Telephony.Sms.ADDRESS, Telephony.Sms.BODY, Telephony.Sms.DATE};
        String selection = Telephony.Sms.DATE + ">=?";
        String[] selectionArgs = new String[]{String.valueOf(System.currentTimeMillis() - LOOKBACK_MS)};
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
            int rows = 0;
            while (cursor.moveToNext() && rows++ < MAX_ROWS) {
                String sender = addressIndex >= 0 ? cursor.getString(addressIndex) : "sms_inbox";
                String text = bodyIndex >= 0 ? cursor.getString(bodyIndex) : "";
                BkashNoticeParser.Parsed parsed = BkashNoticeParser.parse(text);
                if (parsed == null || (!isTrustedBkashSender(sender) && !isBkashNotice(text))) continue;
                String smsSender = sender == null || sender.trim().isEmpty() ? "sms_inbox" : sender;
                final boolean[] saved = new boolean[]{false};
                boolean accepted = BkashPaymentDeduper.enqueueIfNew(appContext, parsed, () -> {
                    saved[0] = ForwarderClient.queueSms(appContext, smsSender, text);
                    return saved[0];
                });
                if (accepted && saved[0]) queued++;
            }
        } catch (Exception exc) {
            ForwardingStats.recordFailure(appContext, "SMS inbox scan failed: " + exc.getClass().getSimpleName());
            return queued;
        }
        if (queued > 0) {
            ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan queued " + queued + " payment notice(s)");
            ForwarderForegroundService.start(appContext);
        } else if (recordNoNew) {
            ForwardingStats.recordPhoneEvent(appContext, "SMS inbox scan found no new payment notices");
        }
        return queued;
    }

    private static boolean canReadSms(Context context) {
        return Build.VERSION.SDK_INT < 23 || context.checkSelfPermission(Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED;
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
