package com.mouno.forwarder;

import android.app.Notification;
import android.content.ComponentName;
import android.os.Build;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

import java.util.Locale;

public class BkashNotificationListener extends NotificationListenerService {
    @Override
    public void onListenerConnected() {
        super.onListenerConnected();
        DebugLog.append(this, "Notification listener connected");
        ForwardingStats.recordPhoneEvent(this, "Notification listener connected");
        ForwarderForegroundService.start(this);
    }

    @Override
    public void onListenerDisconnected() {
        DebugLog.append(this, "Notification listener disconnected");
        ForwardingStats.recordPhoneEvent(this, "Notification listener disconnected; rebind requested");
        if (Build.VERSION.SDK_INT >= 24) {
            requestRebind(new ComponentName(this, BkashNotificationListener.class));
        }
        super.onListenerDisconnected();
    }

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null || sbn.getNotification() == null) return;
        String packageName = sbn.getPackageName() == null ? "" : sbn.getPackageName().toLowerCase(Locale.ROOT);
        Notification notification = sbn.getNotification();
        Bundle extras = notification.extras;
        String title = value(extras, Notification.EXTRA_TITLE);
        String text = value(extras, Notification.EXTRA_TEXT);
        String bigText = value(extras, Notification.EXTRA_BIG_TEXT);
        String textLines = textLines(extras);
        String subText = value(extras, Notification.EXTRA_SUB_TEXT);
        String summary = value(extras, Notification.EXTRA_SUMMARY_TEXT);
        String all = (title + " " + text + " " + bigText + " " + textLines + " " + subText + " " + summary).trim();
        BkashNoticeParser.Parsed parsed = BkashNoticeParser.parse(all);
        if (isTrustedBkashPackage(packageName) || isTrustedSmsPackage(packageName)) {
            DebugLog.append(this, "Notification posted package=" + packageName + " parsed=" + (parsed != null) + " trustedTitle=" + isTrustedBkashSender(title) + " bkashIdentity=" + hasBkashIdentity(all));
        }
        if (isTrustedBkashPackage(packageName) && parsed != null) {
            final boolean[] queued = new boolean[]{false};
            boolean accepted = BkashPaymentDeduper.enqueueIfNew(this, parsed, () -> {
                queued[0] = ForwarderClient.queueNotification(this, sbn.getPackageName(), title, all);
                return queued[0];
            });
            if (!accepted) {
                DebugLog.append(this, "Notification duplicate/not queued");
                ForwardingStats.recordPhoneEvent(this, "bKash app notification ignored: duplicate payment notice");
                return;
            }
            ForwardingStats.recordPhoneEvent(this, "bKash app notification payment captured");
            if (queued[0]) {
                DebugLog.append(this, "bKash notification queued and starting foreground service");
                ForwarderForegroundService.start(this);
            }
        } else if (isTrustedSmsPackage(packageName) && parsed != null && (isTrustedBkashSender(title) || hasBkashIdentity(all))) {
            final boolean[] queued = new boolean[]{false};
            boolean accepted = BkashPaymentDeduper.enqueueIfNew(this, parsed, () -> {
                queued[0] = ForwarderClient.queueNotification(this, "sms_notification", title, all);
                return queued[0];
            });
            if (!accepted) {
                DebugLog.append(this, "SMS notification duplicate/not queued");
                ForwardingStats.recordPhoneEvent(this, "SMS notification ignored: duplicate payment notice");
                return;
            }
            ForwardingStats.recordPhoneEvent(this, "SMS notification payment captured");
            if (queued[0]) {
                DebugLog.append(this, "SMS notification queued and starting foreground service");
                ForwarderForegroundService.start(this);
            }
        } else if (isTrustedBkashPackage(packageName) || (isTrustedSmsPackage(packageName) && isTrustedBkashSender(title))) {
            DebugLog.append(this, "Notification ignored before send: package=" + packageName);
            ForwardingStats.recordPhoneEvent(this, "Notification ignored before send: not a parseable payment");
        }
    }

    private static boolean isTrustedBkashPackage(String packageName) {
        String value = packageName == null ? "" : packageName.trim().toLowerCase(Locale.ROOT);
        return value.equals("com.bkash.customerapp")
            || value.equals("com.bkash.merchantapp")
            || value.equals("com.bkash.businessapp");
    }

    private static boolean isTrustedSmsPackage(String packageName) {
        String value = packageName == null ? "" : packageName.trim().toLowerCase(Locale.ROOT);
        return value.equals("com.google.android.apps.messaging")
            || value.equals("com.samsung.android.messaging")
            || value.equals("com.android.mms")
            || value.equals("com.android.messaging")
            || value.equals("com.miui.mms")
            || value.equals("com.coloros.mms")
            || value.equals("com.oplus.mms");
    }

    private static boolean isTrustedBkashSender(String sender) {
        String value = sender == null ? "" : sender.trim().toLowerCase(Locale.ROOT);
        return value.contains("bkash") || value.contains("16247");
    }

    private static boolean hasBkashIdentity(String text) {
        String lower = text == null ? "" : text.toLowerCase(Locale.ROOT);
        return lower.contains("bkash") || text.contains("বিকাশ");
    }

    private static String value(Bundle extras, String key) {
        if (extras == null) return "";
        CharSequence value = extras.getCharSequence(key);
        return value == null ? "" : value.toString();
    }

    private static String textLines(Bundle extras) {
        if (extras == null) return "";
        CharSequence[] lines = extras.getCharSequenceArray(Notification.EXTRA_TEXT_LINES);
        if (lines == null || lines.length == 0) return "";
        StringBuilder builder = new StringBuilder();
        for (CharSequence line : lines) {
            if (line != null) builder.append(' ').append(line);
        }
        return builder.toString();
    }
}
