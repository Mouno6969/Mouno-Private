package com.mouno.forwarder;

import android.Manifest;
import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkRequest;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int PRIMARY = Color.rgb(49, 46, 129);
    private static final int PRIMARY_LIGHT = Color.rgb(224, 231, 255);
    private static final int SUCCESS = Color.rgb(22, 163, 74);
    private static final int WARNING = Color.rgb(217, 119, 6);
    private static final int ERROR = Color.rgb(220, 38, 38);
    private static final long STATUS_REFRESH_INTERVAL_MS = 1_500L;

    private TextView configDetails;
    private TextView forwardingDetails;
    private TextView queueDetails;
    private TextView retryStatus;
    private TextView healthStatus;
    private EditText serverInput;
    private EditText sellerTokenInput;
    private EditText secretInput;
    private CheckBox sellerModeInput;
    private ConnectivityManager.NetworkCallback networkCallback;
    private final Handler statusRefreshHandler = new Handler(Looper.getMainLooper());
    private final SharedPreferences.OnSharedPreferenceChangeListener statusChangeListener = (preferences, key) -> statusRefreshHandler.post(this::refreshStatus);
    private final Runnable statusRefreshRunnable = new Runnable() {
        @Override
        public void run() {
            refreshStatus();
            statusRefreshHandler.postDelayed(this, STATUS_REFRESH_INTERVAL_MS);
        }
    };
    private SharedPreferences forwardingStatsPrefs;
    private SharedPreferences noticeQueuePrefs;
    private SharedPreferences noticeHistoryPrefs;
    private boolean statusListenersRegistered;
    private int backgroundColor;
    private int cardColor;
    private int textColor;
    private int mutedTextColor;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        applyPalette();

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(backgroundColor);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = dp(20);
        layout.setPadding(pad, pad, pad, pad);
        scroll.addView(layout);

        TextView title = new TextView(this);
        title.setText("Mouno Forwarder");
        title.setTextColor(isDarkMode() ? PRIMARY_LIGHT : PRIMARY);
        title.setTextSize(28);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        layout.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("bKash SMS/notification parsing, queueing, and delivery status");
        subtitle.setTextColor(mutedTextColor);
        subtitle.setTextSize(14);
        subtitle.setPadding(0, dp(4), 0, dp(16));
        layout.addView(subtitle);

        LinearLayout configCard = card(layout, "Configuration", PRIMARY);
        serverInput = input("https://your-bot-server.example.com", ForwarderConfig.baseUrl(this));
        configCard.addView(serverInput);

        sellerModeInput = new CheckBox(this);
        sellerModeInput.setText("Seller mode (use Seller SMS token)");
        sellerModeInput.setTextColor(textColor);
        sellerModeInput.setChecked(ForwarderConfig.isSellerMode(this));
        sellerModeInput.setOnCheckedChangeListener((buttonView, isChecked) -> updateModeFields());
        configCard.addView(sellerModeInput);

        sellerTokenInput = input("Seller SMS token", ForwarderConfig.sellerToken(this));
        configCard.addView(sellerTokenInput);

        secretInput = input("Admin FORWARDER_SECRET", ForwarderConfig.forwarderSecret(this));
        configCard.addView(secretInput);

        Button saveButton = primaryButton("Save Forwarder Config");
        saveButton.setOnClickListener(v -> saveConfig());
        configCard.addView(saveButton);

        Button checkButton = actionButton("Check server", v -> checkServer());
        configCard.addView(checkButton);

        healthStatus = bodyText();
        healthStatus.setTextColor(mutedTextColor);
        healthStatus.setText("Server health: not checked yet.");
        configCard.addView(healthStatus);
        updateModeFields();

        LinearLayout statusCard = card(layout, "Forwarding stats", SUCCESS);
        forwardingDetails = bodyText();
        statusCard.addView(forwardingDetails);

        LinearLayout queueCard = card(layout, "Offline queue", WARNING);
        queueDetails = bodyText();
        queueCard.addView(queueDetails);

        Button retryButton = primaryButton("Retry queued notices now");
        retryButton.setOnClickListener(v -> retryQueuedNotices());
        queueCard.addView(retryButton);

        retryStatus = bodyText();
        retryStatus.setTextColor(mutedTextColor);
        queueCard.addView(retryStatus);

        LinearLayout setupCard = card(layout, "Phone setup", PRIMARY);
        setupCard.addView(actionButton("Allow SMS Permission", v -> requestSmsPermissions()));
        setupCard.addView(actionButton("Enable Notification Access", v -> startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))));
        setupCard.addView(actionButton("Open Battery Optimization Settings", v -> openBatterySettings()));

        configDetails = bodyText();
        setupCard.addView(configDetails);

        LinearLayout batteryCard = card(layout, "Battery/autostart guide", WARNING);
        TextView batteryGuide = bodyText();
        batteryGuide.setText(batteryGuideText());
        batteryCard.addView(batteryGuide);
        batteryCard.addView(actionButton("Open App Settings", v -> openAppSettings()));
        batteryCard.addView(actionButton("Open Autostart/Battery Settings", v -> openAutostartSettings()));

        setContentView(scroll);
        refreshStatus();
        requestSmsPermissions();
        registerConnectivityFlush();
        ForwarderClient.scheduleRetry(this);
        ForwarderClient.flushQueue(this, this::refreshStatus);
    }

    private void applyPalette() {
        boolean dark = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
        backgroundColor = dark ? Color.rgb(15, 23, 42) : Color.rgb(248, 250, 252);
        cardColor = dark ? Color.rgb(30, 41, 59) : Color.WHITE;
        textColor = dark ? Color.rgb(241, 245, 249) : Color.rgb(15, 23, 42);
        mutedTextColor = dark ? Color.rgb(148, 163, 184) : Color.rgb(71, 85, 105);
    }

    private LinearLayout card(LinearLayout parent, String title, int accentColor) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(14), dp(16), dp(14));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(cardColor);
        bg.setCornerRadius(dp(18));
        bg.setStroke(dp(1), withAlpha(accentColor, 70));
        card.setBackground(bg);

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, 0, 0, dp(14));
        parent.addView(card, params);

        TextView header = new TextView(this);
        header.setText(title);
        header.setTextColor(accentColor);
        header.setTextSize(18);
        header.setTypeface(Typeface.DEFAULT_BOLD);
        header.setPadding(0, 0, 0, dp(10));
        card.addView(header);
        return card;
    }

    private EditText input(String hint, String value) {
        EditText input = new EditText(this);
        input.setHint(hint);
        input.setSingleLine(true);
        input.setText(value);
        input.setTextColor(textColor);
        input.setHintTextColor(mutedTextColor);
        input.setTextSize(15);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(isDarkMode() ? Color.rgb(15, 23, 42) : Color.rgb(248, 250, 252));
        bg.setCornerRadius(dp(12));
        bg.setStroke(dp(1), isDarkMode() ? Color.rgb(71, 85, 105) : Color.rgb(203, 213, 225));
        input.setBackground(bg);
        input.setPadding(dp(12), dp(8), dp(12), dp(8));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, 0, 0, dp(10));
        input.setLayoutParams(params);
        return input;
    }

    private Button primaryButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextColor(Color.WHITE);
        button.setTextSize(14);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(PRIMARY);
        bg.setCornerRadius(dp(14));
        button.setBackground(bg);
        button.setPadding(dp(12), dp(8), dp(12), dp(8));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, dp(6), 0, dp(4));
        button.setLayoutParams(params);
        return button;
    }

    private Button actionButton(String label, View.OnClickListener listener) {
        Button button = primaryButton(label);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(PRIMARY_LIGHT);
        bg.setCornerRadius(dp(14));
        button.setBackground(bg);
        button.setTextColor(PRIMARY);
        button.setOnClickListener(listener);
        return button;
    }

    private TextView bodyText() {
        TextView text = new TextView(this);
        text.setTextColor(textColor);
        text.setTextSize(15);
        text.setLineSpacing(dp(2), 1.0f);
        return text;
    }

    private void refreshStatus() {
        if (forwardingDetails != null) {
            forwardingDetails.setText(ForwardingStats.summary(this));
            forwardingDetails.setTextColor(NoticeQueue.count(this) > 0 ? WARNING : SUCCESS);
        }
        if (queueDetails != null) {
            queueDetails.setText("Queue count: " + NoticeQueue.count(this) + "\n"
                + "Offline parsed bKash notices: " + BkashNoticeHistory.totalParsed(this) + "\n"
                + "Latest parsed: " + latestParsedText());
            queueDetails.setTextColor(NoticeQueue.count(this) > 0 ? WARNING : SUCCESS);
        }
        if (configDetails != null) {
            configDetails.setText("Configured: " + (ForwarderConfig.isConfigured(this) ? "yes" : "no - save URL and required token/secret") + "\n"
                + "Mode: " + (ForwarderConfig.isSellerMode(this) ? "seller" : "main/admin") + "\n"
                + "SMS: " + (BuildConfig.FORWARD_SMS ? "on" : "off") + " · Notifications: " + (BuildConfig.FORWARD_NOTIFICATIONS ? "on" : "off") + "\n"
                + "Keep this app installed, allow permissions, enable notification access, and disable battery restrictions.");
            configDetails.setTextColor(ForwarderConfig.isConfigured(this) ? SUCCESS : ERROR);
        }
    }

    private String latestParsedText() {
        String queued = NoticeQueue.latestSummary(this);
        if (!queued.isEmpty()) return queued + " (queued)";
        String last = BkashNoticeHistory.lastSummary(this);
        return last.isEmpty() ? "none" : last;
    }

    private void retryQueuedNotices() {
        int queuedBefore = NoticeQueue.count(this);
        retryStatus.setTextColor(WARNING);
        retryStatus.setText("Retry started. Queue before retry: " + queuedBefore + ".");
        ForwarderClient.flushQueue(this, () -> {
            refreshStatus();
            int queuedNow = NoticeQueue.count(this);
            retryStatus.setTextColor(queuedNow == 0 ? SUCCESS : WARNING);
            retryStatus.setText("Retry finished. Queue now: " + queuedNow + ".");
        });
    }

    private void checkServer() {
        ForwarderConfig.save(this, serverInput.getText().toString(), sellerModeInput.isChecked(), sellerTokenInput.getText().toString(), secretInput.getText().toString());
        updateModeFields();
        refreshStatus();
        healthStatus.setTextColor(WARNING);
        healthStatus.setText("Checking internet, server, and token/secret...");
        ForwarderClient.checkHealth(this, result -> {
            healthStatus.setTextColor(result.internetOk && result.serverReachable && result.authOk ? SUCCESS : ERROR);
            healthStatus.setText("Internet: " + statusText(result.internetOk) + "\n"
                + "Server reachable: " + statusText(result.serverReachable) + "\n"
                + "Token/secret: " + statusText(result.authOk) + "\n"
                + "Details: " + result.message);
            refreshStatus();
        });
    }

    private void saveConfig() {
        ForwarderConfig.save(this, serverInput.getText().toString(), sellerModeInput.isChecked(), sellerTokenInput.getText().toString(), secretInput.getText().toString());
        updateModeFields();
        refreshStatus();
        retryStatus.setTextColor(SUCCESS);
        retryStatus.setText("Config saved.");
        ForwarderClient.flushQueue(this, this::refreshStatus);
    }

    private String statusText(boolean ok) {
        return ok ? "OK" : "FAILED";
    }

    private void updateModeFields() {
        if (sellerTokenInput == null || secretInput == null || sellerModeInput == null) return;
        boolean sellerMode = sellerModeInput.isChecked();
        sellerTokenInput.setEnabled(sellerMode);
        secretInput.setEnabled(!sellerMode);
        sellerTokenInput.setAlpha(sellerMode ? 1.0f : 0.5f);
        secretInput.setAlpha(sellerMode ? 0.5f : 1.0f);
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
            startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
        } catch (Exception exc) {
            openAppSettings();
        }
    }

    private void openAppSettings() {
        try {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
            intent.setData(Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        } catch (Exception exc) {
            startActivity(new Intent(Settings.ACTION_SETTINGS));
        }
    }

    private void openAutostartSettings() {
        String manufacturer = Build.MANUFACTURER == null ? "" : Build.MANUFACTURER.toLowerCase();
        Intent[] intents;
        if (manufacturer.contains("xiaomi") || manufacturer.contains("redmi") || manufacturer.contains("poco")) {
            intents = new Intent[]{
                componentIntent("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"),
                componentIntent("com.miui.securitycenter", "com.miui.powercenter.PowerSettings")
            };
        } else if (manufacturer.contains("oppo") || manufacturer.contains("realme") || manufacturer.contains("oneplus")) {
            intents = new Intent[]{
                componentIntent("com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity"),
                componentIntent("com.oppo.safe", "com.oppo.safe.permission.startup.StartupAppListActivity"),
                componentIntent("com.coloros.oppoguardelf", "com.coloros.powermanager.fuelgaue.PowerUsageModelActivity")
            };
        } else if (manufacturer.contains("vivo") || manufacturer.contains("iqoo")) {
            intents = new Intent[]{
                componentIntent("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"),
                componentIntent("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity"),
                componentIntent("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.BgStartUpManager")
            };
        } else if (manufacturer.contains("samsung")) {
            intents = new Intent[]{
                componentIntent("com.samsung.android.lool", "com.samsung.android.sm.ui.battery.BatteryActivity"),
                componentIntent("com.samsung.android.sm", "com.samsung.android.sm.ui.battery.BatteryActivity")
            };
        } else if (manufacturer.contains("huawei") || manufacturer.contains("honor")) {
            intents = new Intent[]{
                componentIntent("com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"),
                componentIntent("com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity")
            };
        } else {
            intents = new Intent[0];
        }

        for (Intent intent : intents) {
            try {
                startActivity(intent);
                return;
            } catch (Exception ignored) {
            }
        }
        openBatterySettings();
    }

    private Intent componentIntent(String packageName, String className) {
        Intent intent = new Intent();
        intent.setComponent(new ComponentName(packageName, className));
        return intent;
    }

    private String batteryGuideText() {
        return "Forwarding miss কমাতে app background-এ চালু রাখতে হবে।\n\n"
            + "Your phone: " + manufacturerLabel() + "\n"
            + manufacturerGuide() + "\n\n"
            + "সব ফোনে করুন:\n"
            + "1) Battery optimization: Not optimized/Unrestricted\n"
            + "2) Autostart/Auto launch: Allow\n"
            + "3) Background data/activity: Allow\n"
            + "4) Notification access/SMS permission: On\n"
            + "5) Recent apps screen-এ Mouno Forwarder lock করে রাখুন যদি option থাকে।";
    }

    private String manufacturerGuide() {
        String manufacturer = Build.MANUFACTURER == null ? "" : Build.MANUFACTURER.toLowerCase();
        if (manufacturer.contains("xiaomi") || manufacturer.contains("redmi") || manufacturer.contains("poco")) {
            return "Xiaomi/Redmi/Poco: Security app > Autostart > Mouno Forwarder On; Battery saver > No restrictions.";
        }
        if (manufacturer.contains("oppo") || manufacturer.contains("realme") || manufacturer.contains("oneplus")) {
            return "Oppo/Realme/OnePlus: Phone Manager/Settings > App management > Auto launch On; Battery > Allow background activity.";
        }
        if (manufacturer.contains("vivo") || manufacturer.contains("iqoo")) {
            return "Vivo/iQOO: i Manager > App manager > Autostart On; Battery > Background power consumption allowed.";
        }
        if (manufacturer.contains("samsung")) {
            return "Samsung: Settings > Battery > Background usage limits > Never sleeping apps > add Mouno Forwarder; Battery usage > Unrestricted.";
        }
        if (manufacturer.contains("huawei") || manufacturer.contains("honor")) {
            return "Huawei/Honor: Phone Manager > App launch > Manage manually > Auto-launch, Secondary launch, Run in background On.";
        }
        return "Settings search করুন: Autostart, Auto launch, Battery optimization, Background activity — সব জায়গায় Mouno Forwarder allow করুন.";
    }

    private String manufacturerLabel() {
        String manufacturer = Build.MANUFACTURER == null || Build.MANUFACTURER.trim().isEmpty() ? "Unknown" : Build.MANUFACTURER.trim();
        String model = Build.MODEL == null || Build.MODEL.trim().isEmpty() ? "" : " " + Build.MODEL.trim();
        return manufacturer + model;
    }

    private void registerConnectivityFlush() {
        if (Build.VERSION.SDK_INT < 21 || networkCallback != null) return;
        ConnectivityManager manager = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
        if (manager == null) return;
        networkCallback = new ConnectivityManager.NetworkCallback() {
            @Override
            public void onAvailable(Network network) {
                runOnUiThread(() -> {
                    refreshStatus();
                    if (retryStatus != null) {
                        retryStatus.setTextColor(SUCCESS);
                        retryStatus.setText("Internet available. Retry started.");
                    }
                });
                ForwarderClient.flushQueue(MainActivity.this, MainActivity.this::refreshStatus);
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
        statusRefreshHandler.removeCallbacks(statusRefreshRunnable);
        unregisterRealtimeStatusUpdates();
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
        registerRealtimeStatusUpdates();
        refreshStatus();
        statusRefreshHandler.removeCallbacks(statusRefreshRunnable);
        statusRefreshHandler.postDelayed(statusRefreshRunnable, STATUS_REFRESH_INTERVAL_MS);
    }

    @Override
    protected void onPause() {
        super.onPause();
        statusRefreshHandler.removeCallbacks(statusRefreshRunnable);
        unregisterRealtimeStatusUpdates();
    }

    private void registerRealtimeStatusUpdates() {
        if (statusListenersRegistered) return;
        forwardingStatsPrefs = ForwardingStats.prefsForUpdates(this);
        noticeQueuePrefs = NoticeQueue.prefsForUpdates(this);
        noticeHistoryPrefs = BkashNoticeHistory.prefsForUpdates(this);
        forwardingStatsPrefs.registerOnSharedPreferenceChangeListener(statusChangeListener);
        noticeQueuePrefs.registerOnSharedPreferenceChangeListener(statusChangeListener);
        noticeHistoryPrefs.registerOnSharedPreferenceChangeListener(statusChangeListener);
        statusListenersRegistered = true;
    }

    private void unregisterRealtimeStatusUpdates() {
        if (!statusListenersRegistered) return;
        if (forwardingStatsPrefs != null) forwardingStatsPrefs.unregisterOnSharedPreferenceChangeListener(statusChangeListener);
        if (noticeQueuePrefs != null) noticeQueuePrefs.unregisterOnSharedPreferenceChangeListener(statusChangeListener);
        if (noticeHistoryPrefs != null) noticeHistoryPrefs.unregisterOnSharedPreferenceChangeListener(statusChangeListener);
        statusListenersRegistered = false;
    }

    private boolean isDarkMode() {
        return (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
    }

    private int withAlpha(int color, int alpha) {
        return Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color));
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
