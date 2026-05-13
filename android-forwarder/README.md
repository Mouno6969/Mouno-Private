# Mouno Android Forwarder

Custom Android app for forwarding bKash SMS and app notifications to the bot webhook.

## Configure

Edit `android-forwarder/gradle.properties` before building:

```properties
FORWARDER_SERVER_BASE_URL=https://your-bot-server.example.com
FORWARDER_SECRET=same-secret-as-bot-env
FORWARDER_SELLER_TOKEN=
FORWARDER_SMS=true
FORWARDER_NOTIFICATIONS=true
```

Set the same secret in the bot server `.env`:

```env
FORWARDER_SECRET=same-secret-as-bot-env
```

Leave `FORWARDER_SELLER_TOKEN` empty for the main bot bKash number. For a seller-specific app build, set it to that seller's `sms_token`; the app will post to `/seller/<token>/sms` and `/seller/<token>/notification`.

## Build/run

Open `android-forwarder/` in Android Studio, install the app on the Android phone that receives bKash SMS/notifications, then:

1. Tap **Allow SMS Permission**.
2. Tap **Enable Notification Access** and enable **Mouno bKash Forwarder**.
3. Open battery settings from the app and disable battery restrictions/autostart blocking.
4. Keep the app installed. It forwards matching SMS/notifications and retries queued notices every 5 minutes.

The bot still deduplicates by TrxID, so forwarding both SMS and notification is safe.
