package com.mouno.forwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class RetryReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        ForwarderClient.scanSmsInbox(context, false, null);
        ForwarderClient.flushQueue(context);
        ForwarderClient.scheduleRetry(context);
    }
}
