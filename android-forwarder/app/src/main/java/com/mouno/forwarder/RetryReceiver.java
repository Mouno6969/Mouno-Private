package com.mouno.forwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class RetryReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        Context appContext = context.getApplicationContext();
        BroadcastReceiver.PendingResult pendingResult = goAsync();
        DebugLog.append(appContext, "Background retry receiver fired");
        try {
            ForwarderForegroundService.start(appContext);
            ForwarderClient.scanSmsInbox(appContext, false, null);
            ForwarderClient.flushQueue(appContext, () -> DebugLog.append(appContext, "Background retry flush finished"));
            ForwarderClient.scheduleRetry(appContext);
            DebugLog.append(appContext, "Background retry receiver scheduled work");
        } finally {
            pendingResult.finish();
        }
    }
}
