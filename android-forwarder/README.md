# SCB-Forwarder

Custom Android app for forwarding bKash SMS and app notifications to the bot webhook.

## Configure

The APK uses a fixed server URL: `https://cryptobuybot6969.duckdns.org`. Users cannot edit the server URL inside the app. After installing it, choose the right mode:

Main/admin bKash phone:

```text
Seller mode: off
Admin token: same FORWARDER_SECRET as the bot server .env
```

Approved seller phone:

```text
Seller mode: on
Seller token: token shown in Seller Center
```

The app saves only the selected mode and token on the phone. Seller mode posts to `/seller/<token>/sms` and `/seller/<token>/notification`; main/admin mode posts to `/sms` and `/notification` with `X-Forwarder-Token`.

## Build/run

Build `android-forwarder/` with Android Studio or run the GitHub Actions workflow **Build Android Forwarder APK**, install the app on the Android phone that receives bKash SMS/notifications, then:

1. Choose seller or main/admin mode, enter the required token, then tap **Save setup / সেটআপ সেভ করুন**.
2. Tap **Allow SMS Permission**.
3. Tap **Enable Notification Access** and enable **SCB-Forwarder**.
4. Tap **Start Background Service** and keep the persistent **SCB-Forwarder running** notification visible.
5. Open battery settings from the app and disable battery restrictions/autostart blocking.
6. Keep the app installed. It parses matching SMS/notifications from trusted bKash sources on the phone, stores parsed notices locally if the phone is offline, and retries queued uploads every 5 minutes.

The app only forwards SMS from trusted bKash senders (`bKash`/`16247`) and app notifications from known official bKash packages (`com.bKash.customerapp`, `com.bKash.merchantapp`, `com.bkash.businessapp`). The bot still deduplicates by TrxID, so forwarding both SMS and notification is safe.
Offline parsing only happens inside the Android app; bot order matching still runs after the phone regains internet and uploads the queued notice.
The app status screen shows forwarding stats, last forwarded time, last SMS/notification source, queue count, last error, and a **Retry queued notices now** button.
The status UI uses rounded Material-style cards with indigo, green, amber, and red status colors plus light/dark theme resources.

Seller setup guide: [`SELLER_SETUP_GUIDE_BN_EN.md`](SELLER_SETUP_GUIDE_BN_EN.md).
