package com.mouno.forwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.telephony.SmsMessage;

import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

public class SmsReceiver extends BroadcastReceiver {
    private static final long ASYNC_FINISH_TIMEOUT_MS = 8_000L;

    @Override
    public void onReceive(Context context, Intent intent) {
        BroadcastReceiver.PendingResult pendingResult = goAsync();
        boolean finishNow = true;
        try {
            Bundle bundle = intent.getExtras();
            if (bundle == null) return;
            Object[] pdus = (Object[]) bundle.get("pdus");
            if (pdus == null || pdus.length == 0) return;
            String format = bundle.getString("format");
            StringBuilder body = new StringBuilder();
            String sender = "sms";
            for (Object pdu : pdus) {
                SmsMessage message = SmsMessage.createFromPdu((byte[]) pdu, format);
                if (message == null) continue;
                if (message.getOriginatingAddress() != null) sender = message.getOriginatingAddress();
                body.append(message.getMessageBody());
            }
            String text = body.toString();
            BkashNoticeParser.Parsed parsed = BkashNoticeParser.parse(text);
            if (isTrustedBkashSender(sender) && parsed != null) {
                ForwardingStats.recordPhoneEvent(context, "SMS payment captured: " + parsed.summary());
                finishNow = false;
                Runnable finish = finishWithTimeout(pendingResult);
                ForwarderClient.queueSms(context, sender, text, finish);
                ForwarderForegroundService.start(context);
                return;
            }
            if (isTrustedBkashSender(sender) || isBkashNotice(text)) {
                ForwardingStats.recordPhoneEvent(context, "SMS ignored before send: not a parseable payment from " + sender);
            }
        } finally {
            if (finishNow) pendingResult.finish();
        }
    }

    private static Runnable finishWithTimeout(BroadcastReceiver.PendingResult pendingResult) {
        AtomicBoolean finished = new AtomicBoolean(false);
        Handler handler = new Handler(Looper.getMainLooper());
        Runnable finish = () -> {
            if (finished.compareAndSet(false, true)) pendingResult.finish();
        };
        handler.postDelayed(finish, ASYNC_FINISH_TIMEOUT_MS);
        return () -> handler.post(finish);
    }

    private static boolean isTrustedBkashSender(String sender) {
        String value = sender == null ? "" : sender.trim().toLowerCase(Locale.ROOT);
        return value.equals("bkash") || value.equals("16247");
    }

    private static boolean isBkashNotice(String text) {
        String lower = text == null ? "" : text.toLowerCase(Locale.ROOT);
        return lower.contains("bkash") || lower.contains("trxid") || lower.contains("trx id") || lower.contains("txnid") || lower.contains("txn id") || text.contains("বিকাশ");
    }
}
