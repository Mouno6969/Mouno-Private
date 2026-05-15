package com.mouno.forwarder;

import android.app.job.JobParameters;
import android.app.job.JobService;

public class NetworkFlushJobService extends JobService {
    @Override
    public boolean onStartJob(JobParameters params) {
        new Thread(() -> {
            ForwarderClient.scanSmsInbox(this, false, null);
            ForwarderClient.flushQueueSync(this);
            jobFinished(params, false);
        }).start();
        return true;
    }

    @Override
    public boolean onStopJob(JobParameters params) {
        return true;
    }
}
