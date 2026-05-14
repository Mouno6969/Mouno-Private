package com.mouno.forwarder;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import android.provider.Settings;

final class ForwarderConfig {
    private static final String PREFS = "forwarder_config";
    private static final String KEY_SELLER_TOKEN = "seller_token";
    private static final String KEY_FORWARDER_SECRET = "forwarder_secret";
    private static final String KEY_SELLER_MODE = "seller_mode";

    private ForwarderConfig() {}

    static String baseUrl(Context context) {
        String value = BuildConfig.SERVER_BASE_URL;
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
        SharedPreferences preferences = prefs(context);
        if (preferences.contains(KEY_SELLER_MODE)) return preferences.getBoolean(KEY_SELLER_MODE, true);
        if (!sellerToken(context).isEmpty()) return true;
        if (hasForwarderSecret(context)) return false;
        return true;
    }

    static boolean isConfigured(Context context) {
        String base = baseUrl(context);
        if (base.isEmpty() || base.contains("YOUR_SERVER") || !isBaseUrlValid(base)) return false;
        return isSellerMode(context) ? !sellerToken(context).isEmpty() : hasForwarderSecret(context);
    }

    static boolean isBaseUrlValid(String baseUrl) {
        String value = baseUrl == null ? "" : baseUrl.trim();
        if (value.isEmpty() || value.matches(".*\\s+.*")) return false;
        Uri uri = Uri.parse(value);
        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase();
        if (!("https".equals(scheme) || "http".equals(scheme)) || uri.getHost() == null || uri.getHost().trim().isEmpty()) return false;
        if (uri.getQuery() != null || uri.getFragment() != null) return false;
        String path = uri.getPath() == null ? "" : uri.getPath().toLowerCase();
        while (path.endsWith("/") && path.length() > 1) path = path.substring(0, path.length() - 1);
        return !(path.equals("/seller")
            || path.startsWith("/seller/")
            || path.endsWith("/sms")
            || path.endsWith("/notification")
            || path.endsWith("/bkash-notification")
            || path.endsWith("/forwarder-health"));
    }

    static String endpoint(Context context, String kind) {
        String seller = isSellerMode(context) ? sellerToken(context) : "";
        if (!seller.isEmpty()) return baseUrl(context) + "/seller/" + seller + "/" + kind;
        return baseUrl(context) + "/" + kind;
    }

    static void save(Context context, boolean sellerMode, String sellerToken, String forwarderSecret) {
        prefs(context).edit()
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
