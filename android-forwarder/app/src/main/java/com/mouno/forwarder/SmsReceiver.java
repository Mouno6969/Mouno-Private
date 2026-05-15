package com.mouno.forwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;

import java.util.Locale;

public class SmsReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        BroadcastReceiver.PendingResult pendingResult = goAsync();
        try {
            DebugLog.append(context, "SMS receiver fired");
            Bundle bundle = intent.getExtras();
            if (bundle == null) {
                DebugLog.append(context, "SMS receiver ignored: empty bundle");
                return;
            }
            Object[] pdus = (Object[]) bundle.get("pdus");
            if (pdus == null || pdus.length == 0) {
                DebugLog.append(context, "SMS receiver ignored: no pdus");
                return;
            }
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
            DebugLog.append(context, "SMS receiver parsed=" + (parsed != null) + " trustedSender=" + isTrustedBkashSender(sender) + " bkashIdentity=" + hasBkashIdentity(text));
            if (parsed != null && (isTrustedBkashSender(sender) || hasBkashIdentity(text))) {
                String smsSender = sender;
                final boolean[] queued = new boolean[]{false};
                boolean accepted = BkashPaymentDeduper.enqueueIfNew(context, parsed, () -> {
                    queued[0] = ForwarderClient.queueSms(context, smsSender, text);
                    return queued[0];
                });
                if (!accepted) {
                    DebugLog.append(context, "SMS receiver duplicate/not queued");
                    ForwardingStats.recordPhoneEvent(context, "SMS payment ignored: duplicate payment notice");
                    return;
                }
                ForwardingStats.recordPhoneEvent(context, "SMS payment captured");
                if (queued[0]) {
                    DebugLog.append(context, "SMS receiver queued payment and starting foreground service");
                    ForwarderForegroundService.start(context);
                }
                return;
            }
            if (isTrustedBkashSender(sender) || isBkashNotice(text)) {
                DebugLog.append(context, "SMS receiver ignored: not parseable payment trustedSender=" + isTrustedBkashSender(sender));
                ForwardingStats.recordPhoneEvent(context, "SMS ignored before send: not a parseable payment from " + sender);
            }
        } finally {
            pendingResult.finish();
        }
    }

    private static boolean isTrustedBkashSender(String sender) {
        String value = sender == null ? "" : sender.trim().toLowerCase(Locale.ROOT);
        return value.equals("bkash") || value.equals("16247") || value.contains("bkash");
    }

    private static boolean isBkashNotice(String text) {
        String lower = text == null ? "" : text.toLowerCase(Locale.ROOT);
        return lower.contains("bkash") || lower.contains("trxid") || lower.contains("trx id") || lower.contains("txnid") || lower.contains("txn id") || text.contains("বিকাশ");
    }

    private static boolean hasBkashIdentity(String text) {
        String lower = text == null ? "" : text.toLowerCase(Locale.ROOT);
        return lower.contains("bkash") || text.contains("বিকাশ");
    }
}
