package com.mouno.forwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        ForwarderForegroundService.start(context);
        ForwarderClient.scheduleRetry(context);
        ForwarderClient.scanSmsInbox(context, false, null);
        ForwarderClient.flushQueue(context);
    }
}
