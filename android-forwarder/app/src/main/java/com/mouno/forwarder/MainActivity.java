package com.mouno.forwarder;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkRequest;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public class MainActivity extends Activity {
    private TextView status;
    private EditText serverInput;
    private EditText sellerTokenInput;
    private EditText secretInput;
    private CheckBox sellerModeInput;
    private ConnectivityManager.NetworkCallback networkCallback;

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

        serverInput = new EditText(this);
        serverInput.setHint("https://your-bot-server.example.com");
        serverInput.setSingleLine(true);
        serverInput.setText(ForwarderConfig.baseUrl(this));
        layout.addView(serverInput);

        sellerModeInput = new CheckBox(this);
        sellerModeInput.setText("Seller mode (use Seller SMS token)");
        sellerModeInput.setChecked(ForwarderConfig.isSellerMode(this));
        sellerModeInput.setOnCheckedChangeListener((buttonView, isChecked) -> updateModeFields());
        layout.addView(sellerModeInput);

        sellerTokenInput = new EditText(this);
        sellerTokenInput.setHint("Seller SMS token");
        sellerTokenInput.setSingleLine(true);
        sellerTokenInput.setText(ForwarderConfig.sellerToken(this));
        layout.addView(sellerTokenInput);

        secretInput = new EditText(this);
        secretInput.setHint("Admin FORWARDER_SECRET");
        secretInput.setSingleLine(true);
        secretInput.setText(ForwarderConfig.forwarderSecret(this));
        layout.addView(secretInput);

        updateModeFields();

        Button saveButton = new Button(this);
        saveButton.setText("Save Forwarder Config");
        saveButton.setOnClickListener(v -> saveConfig());
        layout.addView(saveButton);

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
        registerConnectivityFlush();
        ForwarderClient.scheduleRetry(this);
        ForwarderClient.flushQueue(this);
    }

    private String statusText() {
        return "Mouno Forwarder\n\n"
            + "Server: " + ForwarderConfig.baseUrl(this) + "\n"
            + "Mode: " + (ForwarderConfig.isSellerMode(this) ? "seller" : "main/admin") + "\n"
            + "Seller token: " + (ForwarderConfig.sellerToken(this).isEmpty() ? "not set" : "configured") + "\n"
            + "Admin secret: " + (ForwarderConfig.hasForwarderSecret(this) ? "configured" : "not set") + "\n"
            + "SMS: " + (BuildConfig.FORWARD_SMS ? "on" : "off") + "\n"
            + "Notifications: " + (BuildConfig.FORWARD_NOTIFICATIONS ? "on" : "off") + "\n"
            + "Offline parsed bKash notices: " + BkashNoticeHistory.totalParsed(this) + "\n"
            + "Queued notices waiting upload: " + NoticeQueue.count(this) + "\n"
            + "Latest parsed: " + latestParsedText() + "\n"
            + "Configured: " + (ForwarderConfig.isConfigured(this) ? "yes" : "no - save URL and required token/secret") + "\n\n"
            + "Sellers use Seller mode with SMS token. Main/admin phone uses main/admin mode with FORWARDER_SECRET. The app parses trusted bKash notices on-device, stores them if offline, and uploads them when internet returns.";
    }

    private String latestParsedText() {
        String queued = NoticeQueue.latestSummary(this);
        if (!queued.isEmpty()) return queued + " (queued)";
        String last = BkashNoticeHistory.lastSummary(this);
        return last.isEmpty() ? "none" : last;
    }

    private void saveConfig() {
        ForwarderConfig.save(this, serverInput.getText().toString(), sellerModeInput.isChecked(), sellerTokenInput.getText().toString(), secretInput.getText().toString());
        status.setText(statusText() + "\nSaved.");
        updateModeFields();
        ForwarderClient.flushQueue(this);
    }

    private void updateModeFields() {
        if (sellerTokenInput == null || secretInput == null || sellerModeInput == null) return;
        boolean sellerMode = sellerModeInput.isChecked();
        sellerTokenInput.setEnabled(sellerMode);
        secretInput.setEnabled(!sellerMode);
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

    private void registerConnectivityFlush() {
        if (Build.VERSION.SDK_INT < 21 || networkCallback != null) return;
        ConnectivityManager manager = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
        if (manager == null) return;
        networkCallback = new ConnectivityManager.NetworkCallback() {
            @Override
            public void onAvailable(Network network) {
                ForwarderClient.flushQueue(MainActivity.this);
                runOnUiThread(() -> {
                    if (status != null) status.setText(statusText() + "\nInternet available. Retry started.");
                });
            }
        };
        try {
            manager.registerNetworkCallback(new NetworkRequest.Builder().build(), networkCallback);
        } catch (Exception exc) {
            networkCallback = null;
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (Build.VERSION.SDK_INT >= 21 && networkCallback != null) {
            ConnectivityManager manager = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
            try {
                if (manager != null) manager.unregisterNetworkCallback(networkCallback);
            } catch (Exception ignored) {
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (status != null) status.setText(statusText());
    }
}
