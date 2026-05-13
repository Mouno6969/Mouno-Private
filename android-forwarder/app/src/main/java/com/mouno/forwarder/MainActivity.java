package com.mouno.forwarder;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = 32;
        layout.setPadding(pad, pad, pad, pad);

        status = new TextView(this);
        status.setTextSize(16);
        status.setText(statusText());
        layout.addView(status);

        Button smsButton = new Button(this);
        smsButton.setText("Allow SMS Permission");
        smsButton.setOnClickListener(v -> requestSmsPermissions());
        layout.addView(smsButton);

        Button notificationButton = new Button(this);
        notificationButton.setText("Enable Notification Access");
        notificationButton.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)));
        layout.addView(notificationButton);

        Button batteryButton = new Button(this);
        batteryButton.setText("Open Battery Optimization Settings");
        batteryButton.setOnClickListener(v -> openBatterySettings());
        layout.addView(batteryButton);

        Button retryButton = new Button(this);
        retryButton.setText("Retry queued notices now");
        retryButton.setOnClickListener(v -> {
            ForwarderClient.flushQueue(this);
            status.setText(statusText() + "\nRetry started.");
        });
        layout.addView(retryButton);

        setContentView(layout);
        requestSmsPermissions();
        ForwarderClient.scheduleRetry(this);
        ForwarderClient.flushQueue(this);
    }

    private String statusText() {
        return "Mouno Forwarder\n\n"
            + "Server: " + ForwarderConfig.baseUrl() + "\n"
            + "Seller token: " + (BuildConfig.SELLER_TOKEN == null || BuildConfig.SELLER_TOKEN.isEmpty() ? "main bot" : "configured") + "\n"
            + "SMS: " + (BuildConfig.FORWARD_SMS ? "on" : "off") + "\n"
            + "Notifications: " + (BuildConfig.FORWARD_NOTIFICATIONS ? "on" : "off") + "\n"
            + "Configured: " + (ForwarderConfig.isConfigured() ? "yes" : "no - edit gradle.properties") + "\n\n"
            + "Keep this app installed, allow permissions, enable notification access, and disable battery restrictions.";
    }

    private void requestSmsPermissions() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.RECEIVE_SMS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECEIVE_SMS, Manifest.permission.READ_SMS}, 10);
        }
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 11);
        }
    }

    private void openBatterySettings() {
        try {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
            intent.setData(Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        } catch (Exception exc) {
            startActivity(new Intent(Settings.ACTION_SETTINGS));
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (status != null) status.setText(statusText());
    }
}
