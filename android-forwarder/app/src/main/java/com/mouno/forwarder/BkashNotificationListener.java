package com.mouno.forwarder;

import android.app.Notification;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

public class BkashNotificationListener extends NotificationListenerService {
    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        if (sbn == null || sbn.getNotification() == null) return;
        String packageName = sbn.getPackageName() == null ? "" : sbn.getPackageName().toLowerCase();
        Notification notification = sbn.getNotification();
        Bundle extras = notification.extras;
        String title = value(extras, Notification.EXTRA_TITLE);
        String text = value(extras, Notification.EXTRA_TEXT);
        String bigText = value(extras, Notification.EXTRA_BIG_TEXT);
        String all = (title + " " + text + " " + bigText).trim();
        String lower = all.toLowerCase();
        if (packageName.contains("bkash") || lower.contains("bkash") || lower.contains("trxid") || lower.contains("txnid") || all.contains("বিকাশ")) {
            ForwarderClient.sendNotification(this, sbn.getPackageName(), title, all);
        }
    }

    private static String value(Bundle extras, String key) {
        if (extras == null) return "";
        CharSequence value = extras.getCharSequence(key);
        return value == null ? "" : value.toString();
    }
}
