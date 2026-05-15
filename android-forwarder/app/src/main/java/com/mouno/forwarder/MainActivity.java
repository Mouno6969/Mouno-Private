package com.mouno.forwarder;

import android.Manifest;
import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkRequest;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int PRIMARY = Color.rgb(49, 46, 129);
    private static final int PRIMARY_LIGHT = Color.rgb(224, 231, 255);
    private static final int ACCENT = Color.rgb(14, 165, 233);
    private static final int SUCCESS = Color.rgb(22, 163, 74);
    private static final int WARNING = Color.rgb(217, 119, 6);
    private static final int ERROR = Color.rgb(220, 38, 38);
    private static final long STATUS_REFRESH_INTERVAL_MS = 1_500L;

    private TextView configDetails;
    private TextView paymentOutcomeDetails;
    private TextView forwardingDetails;
    private TextView debugLogLiveStatus;
    private TextView debugLogDetails;
    private TextView queueDetails;
    private TextView retryStatus;
    private TextView healthStatus;
    private EditText sellerTokenInput;
    private EditText secretInput;
    private RadioButton sellerModeInput;
    private RadioButton adminModeInput;
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
    private SharedPreferences debugLogPrefs;
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

        LinearLayout hero = heroCard(layout);
        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.app_logo);
        logo.setAdjustViewBounds(true);
        logo.setScaleType(ImageView.ScaleType.CENTER_CROP);
        LinearLayout.LayoutParams logoParams = new LinearLayout.LayoutParams(dp(72), dp(72));
        logoParams.setMargins(0, 0, 0, dp(12));
        hero.addView(logo, logoParams);

        TextView title = new TextView(this);
        title.setText("SCB Forwarder");
        title.setTextColor(Color.WHITE);
        title.setTextSize(28);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        hero.addView(title);

        TextView subtitle = new TextView(this);
        subtitle.setText("Real-time bKash payment forwarding and server ACK tracking");
        subtitle.setTextColor(Color.rgb(219, 234, 254));
        subtitle.setTextSize(14);
        subtitle.setPadding(0, dp(4), 0, 0);
        hero.addView(subtitle);

        LinearLayout configCard = card(layout, "Setup / সেটআপ", PRIMARY);
        TextView serverText = bodyText();
        serverText.setText("Server: " + ForwarderConfig.baseUrl(this) + "\nসার্ভার লিংক fixed — app থেকে change করা যাবে না।");
        serverText.setTextColor(SUCCESS);
        configCard.addView(serverText);

        RadioGroup modeGroup = new RadioGroup(this);
        modeGroup.setOrientation(RadioGroup.VERTICAL);
        modeGroup.setPadding(0, 0, 0, dp(8));

        sellerModeInput = modeOption("Seller phone / সেলার ফোন");
        adminModeInput = modeOption("Admin/main phone / অ্যাডমিন ফোন");
        modeGroup.addView(sellerModeInput);
        modeGroup.addView(adminModeInput);
        if (ForwarderConfig.isSellerMode(this)) {
            sellerModeInput.setChecked(true);
        } else {
            adminModeInput.setChecked(true);
        }
        modeGroup.setOnCheckedChangeListener((group, checkedId) -> updateModeFields());
        configCard.addView(modeGroup);

        sellerTokenInput = input("Seller token / সেলার token", ForwarderConfig.sellerToken(this));
        configCard.addView(sellerTokenInput);

        secretInput = input("Admin token / অ্যাডমিন token", ForwarderConfig.forwarderSecret(this));
        configCard.addView(secretInput);

        Button saveButton = primaryButton("Save setup / সেটআপ সেভ করুন");
        saveButton.setOnClickListener(v -> saveConfig());
        configCard.addView(saveButton);

        Button checkButton = actionButton("Check server", v -> checkServer());
        configCard.addView(checkButton);

        healthStatus = bodyText();
        healthStatus.setTextColor(mutedTextColor);
        healthStatus.setText("Server health / সার্ভার চেক: not checked yet");
        configCard.addView(healthStatus);
        updateModeFields();

        LinearLayout paymentCard = card(layout, "Payment outcome / পেমেন্ট ফলাফল", ACCENT);
        paymentOutcomeDetails = bodyText();
        paymentOutcomeDetails.setTypeface(Typeface.DEFAULT_BOLD);
        paymentCard.addView(paymentOutcomeDetails);

        LinearLayout statusCard = card(layout, "Delivery stats / ডেলিভারি স্ট্যাটাস", SUCCESS);
        forwardingDetails = bodyText();
        statusCard.addView(forwardingDetails);

        LinearLayout debugCard = card(layout, "Live admin activity log / লাইভ অ্যাডমিন লগ", ERROR);
        TextView debugHelp = bodyText();
        debugHelp.setText("App-এর realtime activity/error এখানে auto update হবে: SMS receiver, notification listener, queue, retry, flush, HTTP post, service start/stop. Sensitive message/body details redacted থাকবে।");
        debugHelp.setTextColor(mutedTextColor);
        debugCard.addView(debugHelp);
        debugLogLiveStatus = bodyText();
        debugLogLiveStatus.setTypeface(Typeface.DEFAULT_BOLD);
        debugCard.addView(debugLogLiveStatus);
        debugCard.addView(actionButton("Clear debug log", v -> clearDebugLog()));
        debugLogDetails = bodyText();
        debugLogDetails.setTextSize(12);
        debugLogDetails.setTypeface(Typeface.MONOSPACE);
        debugCard.addView(debugLogDetails);

        LinearLayout queueCard = card(layout, "Offline queue / অফলাইন কিউ", WARNING);
        queueDetails = bodyText();
        queueCard.addView(queueDetails);

        Button retryButton = primaryButton("Retry queued notices now");
        retryButton.setOnClickListener(v -> retryQueuedNotices());
        queueCard.addView(retryButton);

        Button scanInboxButton = primaryButton("Scan SMS inbox now / SMS inbox স্ক্যান করুন");
        scanInboxButton.setOnClickListener(v -> scanSmsInboxNow());
        queueCard.addView(scanInboxButton);

        retryStatus = bodyText();
        retryStatus.setTextColor(mutedTextColor);
        queueCard.addView(retryStatus);

        LinearLayout setupCard = card(layout, "Phone setup / ফোন সেটআপ", PRIMARY);
        setupCard.addView(actionButton("Allow SMS Permission", v -> requestSmsPermissions()));
        setupCard.addView(actionButton("Enable Notification Access", v -> {
            DebugLog.append(this, "Notification access settings opened");
            startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS));
        }));
        setupCard.addView(actionButton("Start Background Service", v -> startBackgroundService()));
        setupCard.addView(actionButton("Allow Unrestricted Battery", v -> requestIgnoreBatteryOptimizations()));
        setupCard.addView(actionButton("Open Battery Optimization Settings", v -> openBatterySettings()));

        configDetails = bodyText();
        setupCard.addView(configDetails);

        LinearLayout batteryCard = card(layout, "Battery/autostart guide / ব্যাটারি গাইড", WARNING);
        TextView batteryGuide = bodyText();
        batteryGuide.setText(batteryGuideText());
        batteryCard.addView(batteryGuide);
        batteryCard.addView(actionButton("Open App Settings", v -> openAppSettings()));
        batteryCard.addView(actionButton("Open Autostart/Battery Settings", v -> openAutostartSettings()));

        setContentView(scroll);
        DebugLog.append(this, "Admin UI opened; background service starting");
        refreshStatus();
        requestSmsPermissions();
        ForwarderForegroundService.start(this);
        if (hasSmsPermissions()) ForwarderClient.scanSmsInbox(this, false, this::onInboxScanFinished);
        registerConnectivityFlush();
        ForwarderClient.scheduleRetry(this);
        ForwarderClient.flushQueue(this, this::refreshStatus);
    }

    private void applyPalette() {
        boolean dark = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
        backgroundColor = dark ? Color.rgb(2, 6, 23) : Color.rgb(241, 245, 249);
        cardColor = dark ? Color.rgb(15, 23, 42) : Color.WHITE;
        textColor = dark ? Color.rgb(241, 245, 249) : Color.rgb(15, 23, 42);
        mutedTextColor = dark ? Color.rgb(148, 163, 184) : Color.rgb(71, 85, 105);
    }

    private LinearLayout heroCard(LinearLayout parent) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(18), dp(18), dp(18));
        GradientDrawable bg = new GradientDrawable(GradientDrawable.Orientation.TL_BR, new int[]{PRIMARY, ACCENT});
        bg.setCornerRadius(dp(22));
        card.setBackground(bg);
        if (Build.VERSION.SDK_INT >= 21) card.setElevation(dp(3));

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, 0, 0, dp(16));
        parent.addView(card, params);
        return card;
    }

    private LinearLayout card(LinearLayout parent, String title, int accentColor) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(16), dp(16), dp(16));
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(cardColor);
        bg.setCornerRadius(dp(18));
        bg.setStroke(dp(1), isDarkMode() ? withAlpha(accentColor, 110) : Color.rgb(226, 232, 240));
        card.setBackground(bg);
        if (Build.VERSION.SDK_INT >= 21) card.setElevation(dp(2));

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, 0, 0, dp(14));
        parent.addView(card, params);

        TextView header = new TextView(this);
        header.setText(title);
        header.setTextColor(accentColor);
        header.setTextSize(17);
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
        bg.setColor(isDarkMode() ? Color.rgb(2, 6, 23) : Color.rgb(248, 250, 252));
        bg.setCornerRadius(dp(12));
        bg.setStroke(dp(1), isDarkMode() ? Color.rgb(71, 85, 105) : Color.rgb(203, 213, 225));
        input.setBackground(bg);
        input.setPadding(dp(12), dp(8), dp(12), dp(8));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, 0, 0, dp(10));
        input.setLayoutParams(params);
        return input;
    }

    private RadioButton modeOption(String label) {
        RadioButton option = new RadioButton(this);
        option.setText(label);
        option.setTextColor(textColor);
        option.setTextSize(15);
        option.setPadding(0, dp(2), 0, dp(2));
        return option;
    }

    private Button primaryButton(String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextColor(Color.WHITE);
        button.setTextSize(14);
        button.setBackground(buttonBackground(PRIMARY, withAlpha(Color.WHITE, 90)));
        button.setMinHeight(dp(48));
        button.setPadding(dp(12), dp(8), dp(12), dp(8));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        params.setMargins(0, dp(6), 0, dp(4));
        button.setLayoutParams(params);
        return button;
    }

    private Button actionButton(String label, View.OnClickListener listener) {
        Button button = primaryButton(label);
        button.setBackground(buttonBackground(isDarkMode() ? Color.rgb(30, 41, 59) : PRIMARY_LIGHT, withAlpha(PRIMARY, 90)));
        button.setTextColor(isDarkMode() ? Color.WHITE : PRIMARY);
        button.setOnClickListener(listener);
        return button;
    }

    private RippleDrawable buttonBackground(int color, int rippleColor) {
        GradientDrawable content = new GradientDrawable();
        content.setColor(color);
        content.setCornerRadius(dp(14));
        GradientDrawable mask = new GradientDrawable();
        mask.setColor(Color.WHITE);
        mask.setCornerRadius(dp(14));
        return new RippleDrawable(ColorStateList.valueOf(rippleColor), content, mask);
    }

    private TextView bodyText() {
        TextView text = new TextView(this);
        text.setTextColor(textColor);
        text.setTextSize(15);
        text.setLineSpacing(dp(3), 1.0f);
        return text;
    }

    private void refreshStatus() {
        if (paymentOutcomeDetails != null) {
            paymentOutcomeDetails.setText(ForwardingStats.paymentSummary(this));
            paymentOutcomeDetails.setTextColor(paymentStatusColor(ForwardingStats.lastPaymentStatus(this)));
        }
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
            configDetails.setText("Status: " + (ForwarderConfig.isConfigured(this) ? "Ready to forward / ফরওয়ার্ড করার জন্য প্রস্তুত" : "Not ready / প্রস্তুত নয় - token save করুন") + "\n"
                + "Mode: " + (ForwarderConfig.isSellerMode(this) ? "seller" : "main/admin") + "\n"
                + "SMS: " + (BuildConfig.FORWARD_SMS ? "on" : "off") + " · Notifications: " + (BuildConfig.FORWARD_NOTIFICATIONS ? "on" : "off") + "\n"
                + "Battery optimization: " + batteryOptimizationStatusText() + "\n"
                + "Background: foreground service requested/running notification visible.\n"
                + "Battery optimization/autostart permission is still required for reliable forwarding.");
            configDetails.setTextColor(ForwarderConfig.isConfigured(this) ? SUCCESS : ERROR);
        }
        if (debugLogDetails != null) {
            debugLogDetails.setText(DebugLog.text(this));
            debugLogDetails.setTextColor(textColor);
        }
        if (debugLogLiveStatus != null) {
            int queueCount = NoticeQueue.count(this);
            debugLogLiveStatus.setText("LIVE · auto-refresh " + (STATUS_REFRESH_INTERVAL_MS / 1000.0) + "s · last event " + DebugLog.updatedAtText(this) + "\n"
                + "Queue: " + queueCount + " · SMS permission: " + statusText(hasSmsPermissions()) + " · Config: " + statusText(ForwarderConfig.isConfigured(this)));
            debugLogLiveStatus.setTextColor(queueCount > 0 ? WARNING : SUCCESS);
        }
    }

    private void clearDebugLog() {
        DebugLog.clear(this);
        refreshStatus();
    }

    private String latestParsedText() {
        String queued = NoticeQueue.latestSummary(this);
        if (!queued.isEmpty()) return queued + " (queued)";
        String last = BkashNoticeHistory.lastSummary(this);
        return last.isEmpty() ? "none" : last;
    }

    private void retryQueuedNotices() {
        int queuedBefore = NoticeQueue.count(this);
        DebugLog.append(this, "Manual retry tapped. Queue before=" + queuedBefore);
        retryStatus.setTextColor(WARNING);
        retryStatus.setText("Retry started. Queue before retry: " + queuedBefore + ".");
        ForwarderClient.flushQueue(this, () -> {
            refreshStatus();
            int queuedNow = NoticeQueue.count(this);
            DebugLog.append(MainActivity.this, "Manual retry finished. Queue now=" + queuedNow);
            retryStatus.setTextColor(queuedNow == 0 ? SUCCESS : WARNING);
            retryStatus.setText("Retry finished. Queue now: " + queuedNow + ".");
        });
    }

    private void scanSmsInboxNow() {
        DebugLog.append(this, "Manual SMS inbox scan tapped");
        requestSmsPermissions();
        if (!hasSmsPermissions()) {
            retryStatus.setTextColor(WARNING);
            retryStatus.setText("Allow SMS permission first, then tap Scan SMS inbox again.");
            return;
        }
        retryStatus.setTextColor(WARNING);
        retryStatus.setText("Scanning SMS inbox for bKash payments...");
        ForwarderClient.scanSmsInbox(this, true, this::onInboxScanFinished);
    }

    private void onInboxScanFinished(int queued) {
        refreshStatus();
        DebugLog.append(this, "SMS inbox scan callback queued=" + queued);
        if (retryStatus != null) {
            retryStatus.setTextColor(queued > 0 ? SUCCESS : WARNING);
            retryStatus.setText("SMS inbox scan finished. New queued/forwarded payments: " + queued + ".");
        }
    }

    private void checkServer() {
        String warning = setupValidationWarning();
        if (warning != null) {
            showSetupWarning(warning);
            return;
        }
        DebugLog.append(this, "Server health check started");
        ForwarderConfig.save(this, isSellerModeSelected(), sellerTokenInput.getText().toString(), secretInput.getText().toString());
        updateModeFields();
        refreshStatus();
        healthStatus.setTextColor(WARNING);
        healthStatus.setText("Checking internet, fixed server, and token...");
        ForwarderClient.checkHealth(this, result -> {
            DebugLog.append(MainActivity.this, "Server health result internet=" + statusText(result.internetOk) + " server=" + statusText(result.serverReachable) + " token=" + statusText(result.authOk));
            healthStatus.setTextColor(result.internetOk && result.serverReachable && result.authOk ? SUCCESS : ERROR);
            healthStatus.setText("Internet: " + statusText(result.internetOk) + "\n"
                + "Server reachable: " + statusText(result.serverReachable) + "\n"
                + "Token: " + statusText(result.authOk) + "\n"
                + "Details: " + result.message);
            refreshStatus();
        });
    }

    private void saveConfig() {
        String warning = setupValidationWarning();
        if (warning != null) {
            showSetupWarning(warning);
            return;
        }
        ForwarderConfig.save(this, isSellerModeSelected(), sellerTokenInput.getText().toString(), secretInput.getText().toString());
        DebugLog.append(this, "Setup saved mode=" + (isSellerModeSelected() ? "seller" : "admin"));
        updateModeFields();
        refreshStatus();
        healthStatus.setTextColor(SUCCESS);
        healthStatus.setText("Setup saved / সেটআপ সেভ হয়েছে.");
        retryStatus.setTextColor(SUCCESS);
        retryStatus.setText("Setup saved / সেটআপ সেভ হয়েছে.");
        ForwarderClient.flushQueue(this, this::refreshStatus);
    }

    private String statusText(boolean ok) {
        return ok ? "OK" : "FAILED";
    }

    private int paymentStatusColor(String status) {
        String value = status == null ? "" : status.trim();
        if (value.equals("matched_order") || value.equals("parsed") || value.equals("accepted")) return SUCCESS;
        if (value.equals("manual_review") || value.equals("duplicate")) return WARNING;
        if (value.equals("ignored")) return mutedTextColor;
        return textColor;
    }

    private void updateModeFields() {
        if (sellerTokenInput == null || secretInput == null || sellerModeInput == null || adminModeInput == null) return;
        boolean sellerMode = isSellerModeSelected();
        sellerTokenInput.setEnabled(sellerMode);
        secretInput.setEnabled(!sellerMode);
        sellerTokenInput.setVisibility(sellerMode ? View.VISIBLE : View.GONE);
        secretInput.setVisibility(sellerMode ? View.GONE : View.VISIBLE);
    }

    private boolean isSellerModeSelected() {
        return sellerModeInput != null && sellerModeInput.isChecked();
    }

    private String setupValidationWarning() {
        if (isSellerModeSelected()) {
            if (sellerTokenInput.getText().toString().trim().isEmpty()) {
                sellerTokenInput.requestFocus();
                return "Seller phone select করা আছে — Seller token paste করুন।";
            }
        } else if (secretInput.getText().toString().trim().isEmpty()) {
            secretInput.requestFocus();
            return "Admin/main phone select করা আছে — Admin token paste করুন।";
        }
        return null;
    }

    private void showSetupWarning(String warning) {
        DebugLog.append(this, "Setup validation blocked");
        updateModeFields();
        refreshStatus();
        healthStatus.setTextColor(ERROR);
        healthStatus.setText("⚠️ " + warning);
    }

    private void requestSmsPermissions() {
        if (Build.VERSION.SDK_INT >= 23 && !hasSmsPermissions()) {
            DebugLog.append(this, "SMS permission request shown");
            requestPermissions(new String[]{Manifest.permission.RECEIVE_SMS, Manifest.permission.READ_SMS}, 10);
            return;
        }
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            DebugLog.append(this, "Notification permission request shown");
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 11);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 10) {
            DebugLog.append(this, "SMS permission result granted=" + hasSmsPermissions());
            if (hasSmsPermissions()) {
                requestSmsPermissions();
                ForwarderClient.scanSmsInbox(this, false, this::onInboxScanFinished);
            }
        }
    }

    private boolean hasSmsPermissions() {
        return Build.VERSION.SDK_INT < 23
            || (checkSelfPermission(Manifest.permission.RECEIVE_SMS) == PackageManager.PERMISSION_GRANTED
            && checkSelfPermission(Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED);
    }

    private void openBatterySettings() {
        try {
            DebugLog.append(this, "Battery optimization settings opened");
            startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
        } catch (Exception exc) {
            DebugLog.append(this, "Battery settings fallback: " + exc.getClass().getSimpleName());
            openAppSettings();
        }
    }

    private void requestIgnoreBatteryOptimizations() {
        if (Build.VERSION.SDK_INT < 23) {
            openBatterySettings();
            return;
        }
        try {
            PowerManager powerManager = (PowerManager) getSystemService(POWER_SERVICE);
            if (powerManager != null && powerManager.isIgnoringBatteryOptimizations(getPackageName())) {
                DebugLog.append(this, "Battery optimization already unrestricted");
                openAutostartSettings();
                return;
            }
            Intent intent = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
            intent.setData(Uri.parse("package:" + getPackageName()));
            DebugLog.append(this, "Ignore battery optimization request opened");
            startActivity(intent);
        } catch (Exception exc) {
            DebugLog.append(this, "Ignore battery optimization request fallback: " + exc.getClass().getSimpleName());
            openBatterySettings();
        }
    }

    private String batteryOptimizationStatusText() {
        if (Build.VERSION.SDK_INT < 23) return "not required";
        PowerManager powerManager = (PowerManager) getSystemService(POWER_SERVICE);
        return powerManager != null && powerManager.isIgnoringBatteryOptimizations(getPackageName()) ? "OK" : "Needs allow";
    }

    private void startBackgroundService() {
        boolean started = ForwarderForegroundService.start(this);
        DebugLog.append(this, "Manual background service start result=" + started);
        ForwarderClient.scheduleRetry(this);
        refreshStatus();
        if (retryStatus != null) {
            retryStatus.setTextColor(started ? SUCCESS : ERROR);
            retryStatus.setText(started
                ? "Background service requested/running notification visible; battery/autostart permission still required for reliable forwarding."
                : "Background service could not start. Disable battery restrictions/autostart blocking, then tap Start Background Service again.");
        }
    }

    private void openAppSettings() {
        try {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
            intent.setData(Uri.parse("package:" + getPackageName()));
            DebugLog.append(this, "App settings opened");
            startActivity(intent);
        } catch (Exception exc) {
            DebugLog.append(this, "System settings fallback: " + exc.getClass().getSimpleName());
            startActivity(new Intent(Settings.ACTION_SETTINGS));
        }
    }

    private void openAutostartSettings() {
        DebugLog.append(this, "Autostart/battery settings requested");
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
                DebugLog.append(this, "Manufacturer battery settings opened");
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
            + "5) Recent apps screen-এ SCB-Forwarder lock করে রাখুন যদি option থাকে।";
    }

    private String manufacturerGuide() {
        String manufacturer = Build.MANUFACTURER == null ? "" : Build.MANUFACTURER.toLowerCase();
        if (manufacturer.contains("xiaomi") || manufacturer.contains("redmi") || manufacturer.contains("poco")) {
            return "Xiaomi/Redmi/Poco: Security app > Autostart > SCB-Forwarder On; Battery saver > No restrictions.";
        }
        if (manufacturer.contains("oppo") || manufacturer.contains("realme") || manufacturer.contains("oneplus")) {
            return "Oppo/Realme/OnePlus: Phone Manager/Settings > App management > Auto launch On; Battery > Allow background activity.";
        }
        if (manufacturer.contains("vivo") || manufacturer.contains("iqoo")) {
            return "Vivo/iQOO: i Manager > App manager > Autostart On; Battery > Background power consumption allowed.";
        }
        if (manufacturer.contains("samsung")) {
            return "Samsung: Settings > Battery > Background usage limits > Never sleeping apps > add SCB-Forwarder; Battery usage > Unrestricted.";
        }
        if (manufacturer.contains("huawei") || manufacturer.contains("honor")) {
            return "Huawei/Honor: Phone Manager > App launch > Manage manually > Auto-launch, Secondary launch, Run in background On.";
        }
        return "Settings search করুন: Autostart, Auto launch, Battery optimization, Background activity — সব জায়গায় SCB-Forwarder allow করুন.";
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
                DebugLog.append(MainActivity.this, "Network available; retrying queue");
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
            DebugLog.append(this, "Network retry watcher active");
        } catch (Exception exc) {
            DebugLog.append(this, "Network callback registration failed: " + exc.getClass().getSimpleName());
            networkCallback = null;
        }
    }

    @Override
    protected void onDestroy() {
        DebugLog.append(this, "Admin UI destroyed; background service scheduled");
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
        DebugLog.append(this, "Admin UI visible; live log refresh active");
        registerRealtimeStatusUpdates();
        refreshStatus();
        statusRefreshHandler.removeCallbacks(statusRefreshRunnable);
        statusRefreshHandler.postDelayed(statusRefreshRunnable, STATUS_REFRESH_INTERVAL_MS);
    }

    @Override
    protected void onPause() {
        super.onPause();
        DebugLog.append(this, "Admin UI hidden; foreground service requested/running notification visible; battery/autostart still required for reliable forwarding");
        ForwarderForegroundService.start(this);
        statusRefreshHandler.removeCallbacks(statusRefreshRunnable);
        unregisterRealtimeStatusUpdates();
    }

    private void registerRealtimeStatusUpdates() {
        if (statusListenersRegistered) return;
        forwardingStatsPrefs = ForwardingStats.prefsForUpdates(this);
        noticeQueuePrefs = NoticeQueue.prefsForUpdates(this);
        noticeHistoryPrefs = BkashNoticeHistory.prefsForUpdates(this);
        debugLogPrefs = DebugLog.prefsForUpdates(this);
        forwardingStatsPrefs.registerOnSharedPreferenceChangeListener(statusChangeListener);
        noticeQueuePrefs.registerOnSharedPreferenceChangeListener(statusChangeListener);
        noticeHistoryPrefs.registerOnSharedPreferenceChangeListener(statusChangeListener);
        debugLogPrefs.registerOnSharedPreferenceChangeListener(statusChangeListener);
        statusListenersRegistered = true;
    }

    private void unregisterRealtimeStatusUpdates() {
        if (!statusListenersRegistered) return;
        if (forwardingStatsPrefs != null) forwardingStatsPrefs.unregisterOnSharedPreferenceChangeListener(statusChangeListener);
        if (noticeQueuePrefs != null) noticeQueuePrefs.unregisterOnSharedPreferenceChangeListener(statusChangeListener);
        if (noticeHistoryPrefs != null) noticeHistoryPrefs.unregisterOnSharedPreferenceChangeListener(statusChangeListener);
        if (debugLogPrefs != null) debugLogPrefs.unregisterOnSharedPreferenceChangeListener(statusChangeListener);
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
