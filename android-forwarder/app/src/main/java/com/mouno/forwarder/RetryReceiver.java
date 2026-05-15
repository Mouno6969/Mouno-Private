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
        ForwarderForegroundService.start(appContext);
        ForwarderClient.scanSmsInbox(appContext, false, queued -> ForwarderClient.flushQueue(appContext, () -> {
            ForwarderClient.scheduleRetry(appContext);
            DebugLog.append(appContext, "Background retry receiver finished queued=" + queued);
            pendingResult.finish();
        }));
    }
}
