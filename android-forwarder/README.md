# Mouno Android Forwarder

Custom Android app for forwarding bKash SMS and app notifications to the bot webhook.

## Configure

The APK can be built once and shared with approved sellers. After installing it, each seller enters:

```text
Server URL: https://your-bot-server.example.com
Seller SMS token: token shown in Seller Center
```

The app saves those values on the phone and posts to `/seller/<token>/sms` and `/seller/<token>/notification`. Do not put the global `FORWARDER_SECRET` in a public APK.

## Build/run

Build `android-forwarder/` with Android Studio or run the GitHub Actions workflow **Build Android Forwarder APK**, install the app on the Android phone that receives bKash SMS/notifications, then:

1. Enter the public server URL and seller SMS token, then tap **Save Server & Seller Token**.
2. Tap **Allow SMS Permission**.
3. Tap **Enable Notification Access** and enable **Mouno bKash Forwarder**.
4. Open battery settings from the app and disable battery restrictions/autostart blocking.
5. Keep the app installed. It forwards matching SMS/notifications and retries queued notices every 5 minutes.

The bot still deduplicates by TrxID, so forwarding both SMS and notification is safe.
