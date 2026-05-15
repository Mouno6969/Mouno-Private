package com.mouno.forwarder;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class RetryReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        Context appContext = context.getApplicationContext();
        BroadcastReceiver.PendingResult pendingResult = goAsync();
        new Thread(() -> {
            DebugLog.append(appContext, "Background scan alarm fired");
            try {
                ForwarderForegroundService.start(appContext);
                int queued = ForwarderClient.scanSmsInboxForBackgroundAlarm(appContext);
                DebugLog.append(appContext, "Background scan alarm finished queued=" + queued + " queue=" + NoticeQueue.count(appContext));
            } finally {
                ForwarderClient.scheduleRetry(appContext);
                pendingResult.finish();
            }
        }).start();
    }
}
