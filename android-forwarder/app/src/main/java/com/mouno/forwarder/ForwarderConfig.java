package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;
import android.provider.Settings;

final class ForwarderConfig {
    private static final String PREFS = "forwarder_config";
    private static final String KEY_SERVER_BASE_URL = "server_base_url";
    private static final String KEY_SELLER_TOKEN = "seller_token";

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

    static boolean isConfigured(Context context) {
        String base = baseUrl(context);
        return !base.isEmpty() && !base.contains("YOUR_SERVER") && (!sellerToken(context).isEmpty() || hasForwarderSecret());
    }

    static String endpoint(Context context, String kind) {
        String seller = sellerToken(context);
        if (!seller.isEmpty()) return baseUrl(context) + "/seller/" + seller + "/" + kind;
        return baseUrl(context) + "/" + kind;
    }

    static void save(Context context, String serverBaseUrl, String sellerToken) {
        prefs(context).edit()
            .putString(KEY_SERVER_BASE_URL, serverBaseUrl == null ? "" : serverBaseUrl.trim())
            .putString(KEY_SELLER_TOKEN, sellerToken == null ? "" : sellerToken.trim())
            .apply();
    }

    static String deviceId(Context context) {
        String id = Settings.Secure.getString(context.getContentResolver(), Settings.Secure.ANDROID_ID);
        return id == null ? "android" : id;
    }

    static boolean hasForwarderSecret() {
        String secret = BuildConfig.FORWARDER_SECRET == null ? "" : BuildConfig.FORWARDER_SECRET.trim();
        return !secret.isEmpty() && !secret.contains("CHANGE_ME");
    }

    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }
}
