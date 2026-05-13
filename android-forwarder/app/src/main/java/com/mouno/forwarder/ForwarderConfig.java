package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;
import android.provider.Settings;

final class ForwarderConfig {
    private static final String PREFS = "forwarder_config";
    private static final String KEY_SERVER_BASE_URL = "server_base_url";
    private static final String KEY_SELLER_TOKEN = "seller_token";
    private static final String KEY_FORWARDER_SECRET = "forwarder_secret";
    private static final String KEY_SELLER_MODE = "seller_mode";

    private ForwarderConfig() {}

    static String baseUrl(Context context) {
        String configured = prefs(context).getString(KEY_SERVER_BASE_URL, "");
        String value = configured == null || configured.trim().isEmpty() ? BuildConfig.SERVER_BASE_URL : configured;
        value = value == null ? "" : value.trim();
        while (value.endsWith("/")) value = value.substring(0, value.length() - 1);
        return value;
    }

    static String sellerToken(Context context) {
        String configured = prefs(context).getString(KEY_SELLER_TOKEN, "");
        String value = configured == null || configured.trim().isEmpty() ? BuildConfig.SELLER_TOKEN : configured;
        return value == null ? "" : value.trim();
    }

    static String forwarderSecret(Context context) {
        String configured = prefs(context).getString(KEY_FORWARDER_SECRET, "");
        String value = configured == null || configured.trim().isEmpty() ? BuildConfig.FORWARDER_SECRET : configured;
        return value == null ? "" : value.trim();
    }

    static boolean isSellerMode(Context context) {
        return prefs(context).getBoolean(KEY_SELLER_MODE, true);
    }

    static boolean isConfigured(Context context) {
        String base = baseUrl(context);
        if (base.isEmpty() || base.contains("YOUR_SERVER")) return false;
        return isSellerMode(context) ? !sellerToken(context).isEmpty() : hasForwarderSecret(context);
    }

    static String endpoint(Context context, String kind) {
        String seller = isSellerMode(context) ? sellerToken(context) : "";
        if (!seller.isEmpty()) return baseUrl(context) + "/seller/" + seller + "/" + kind;
        return baseUrl(context) + "/" + kind;
    }

    static void save(Context context, String serverBaseUrl, boolean sellerMode, String sellerToken, String forwarderSecret) {
        prefs(context).edit()
            .putString(KEY_SERVER_BASE_URL, serverBaseUrl == null ? "" : serverBaseUrl.trim())
            .putBoolean(KEY_SELLER_MODE, sellerMode)
            .putString(KEY_SELLER_TOKEN, sellerToken == null ? "" : sellerToken.trim())
            .putString(KEY_FORWARDER_SECRET, forwarderSecret == null ? "" : forwarderSecret.trim())
            .apply();
    }

    static String deviceId(Context context) {
        String id = Settings.Secure.getString(context.getContentResolver(), Settings.Secure.ANDROID_ID);
        return id == null ? "android" : id;
    }

    static boolean hasForwarderSecret(Context context) {
        String secret = forwarderSecret(context);
        return !secret.isEmpty() && !secret.contains("CHANGE_ME");
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
