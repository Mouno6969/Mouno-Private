package com.mouno.forwarder;

import android.content.Context;
import android.provider.Settings;

final class ForwarderConfig {
    private ForwarderConfig() {}

    static String baseUrl() {
        String value = BuildConfig.SERVER_BASE_URL == null ? "" : BuildConfig.SERVER_BASE_URL.trim();
        while (value.endsWith("/")) value = value.substring(0, value.length() - 1);
        return value;
    }

    static boolean isConfigured() {
        String base = baseUrl();
        return !base.isEmpty() && !base.contains("YOUR_SERVER") && !BuildConfig.FORWARDER_SECRET.contains("CHANGE_ME");
    }

    static String endpoint(String kind) {
        String seller = BuildConfig.SELLER_TOKEN == null ? "" : BuildConfig.SELLER_TOKEN.trim();
        if (!seller.isEmpty()) return baseUrl() + "/seller/" + seller + "/" + kind;
        return baseUrl() + "/" + kind;
    }

    static String deviceId(Context context) {
        String id = Settings.Secure.getString(context.getContentResolver(), Settings.Secure.ANDROID_ID);
        return id == null ? "android" : id;
    }
}
