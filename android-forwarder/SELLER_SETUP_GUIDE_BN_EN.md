# SCB-Forwarder seller setup guide / SCB-Forwarder সেলার সেটআপ গাইড

## English

### 1. Install the APK

Install **SCB-Forwarder** on the phone that receives the seller bKash SMS or bKash app notifications.

### 2. Save setup

1. Open **SCB-Forwarder**.
2. Confirm the fixed server shown in the app: `https://cryptobuybot6969.duckdns.org`.
3. Turn on **Seller mode / সেলার মোড**.
4. Paste the **Seller token** from Seller Center.
5. Tap **Save setup / সেটআপ সেভ করুন**.
6. When setup is correct, the app shows **Ready to forward / ফরওয়ার্ড করার জন্য প্রস্তুত**.

### 3. Check server

Tap **Check server**. The app will show:

- Internet: whether the phone has internet.
- Server reachable: whether the fixed bot server opens.
- Token: whether the seller token is accepted.

If token fails, copy the Seller token again from Seller Center and save setup again.

### 4. Allow phone permissions

1. Tap **Allow SMS Permission**.
2. Tap **Enable Notification Access** and enable **SCB-Forwarder**.
3. Keep SMS and notification forwarding enabled if you want both sources. Forwarding both is safe because the bot deduplicates by TrxID.

### 5. Battery and autostart settings

Android phones often stop background apps. In the app, open **Battery/autostart guide** and follow the guide for your phone brand.

- Xiaomi/Redmi/Poco: Security app > Autostart > SCB-Forwarder On; Battery saver > No restrictions.
- Oppo/Realme/OnePlus: Phone Manager/Settings > App management > Auto launch On; Battery > Allow background activity.
- Vivo/iQOO: i Manager > App manager > Autostart On; Battery > Background power consumption allowed.
- Samsung: Settings > Battery > Background usage limits > Never sleeping apps > add SCB-Forwarder; Battery usage > Unrestricted.
- Huawei/Honor: Phone Manager > App launch > Manage manually > Auto-launch, Secondary launch, Run in background On.
- Other phones: search Settings for Autostart, Auto launch, Battery optimization, Background activity, then allow SCB-Forwarder everywhere.

### 6. Confirm forwarding

- **Forwarding stats / ফরওয়ার্ড স্ট্যাটাস** shows successful and failed/queued attempts.
- **Offline queue / অফলাইন কিউ** shows notices waiting for internet/server retry.
- If the phone was offline, queued notices upload automatically when internet returns. You can also tap **Retry queued notices now**.

## বাংলা

### ১. APK ইনস্টল করুন

যে ফোনে সেলারের bKash SMS বা bKash app notification আসে, সেই ফোনে **SCB-Forwarder** ইনস্টল করুন।

### ২. সেটআপ সেভ করুন

1. **SCB-Forwarder** app খুলুন।
2. app-এ fixed server দেখাবে: `https://cryptobuybot6969.duckdns.org`।
3. **Seller mode / সেলার মোড** অন করুন।
4. Seller Center থেকে **Seller token** কপি করে paste করুন।
5. **Save setup / সেটআপ সেভ করুন** চাপুন।
6. সব ঠিক থাকলে app দেখাবে **Ready to forward / ফরওয়ার্ড করার জন্য প্রস্তুত**।

### ৩. সার্ভার চেক করুন

**Check server** চাপুন। App আলাদা করে দেখাবে:

- Internet: ফোনে internet আছে কি না।
- Server reachable: fixed bot server reachable কি না।
- Token: seller token ঠিক আছে কি না।

Token fail হলে Seller Center থেকে Seller token আবার কপি করে setup save করুন।

### ৪. ফোন permission allow করুন

1. **Allow SMS Permission** চাপুন।
2. **Enable Notification Access** চাপুন এবং **SCB-Forwarder** enable করুন।
3. SMS আর notification দুইটাই forward করলে সমস্যা নেই, bot TrxID দিয়ে duplicate বাদ দেয়।

### ৫. Battery/autostart setting ঠিক করুন

অনেক Android ফোন background app বন্ধ করে দেয়। App-এর **Battery/autostart guide** খুলে আপনার ফোন brand অনুযায়ী setting করুন।

- Xiaomi/Redmi/Poco: Security app > Autostart > SCB-Forwarder On; Battery saver > No restrictions.
- Oppo/Realme/OnePlus: Phone Manager/Settings > App management > Auto launch On; Battery > Allow background activity.
- Vivo/iQOO: i Manager > App manager > Autostart On; Battery > Background power consumption allowed.
- Samsung: Settings > Battery > Background usage limits > Never sleeping apps > SCB-Forwarder add করুন; Battery usage > Unrestricted.
- Huawei/Honor: Phone Manager > App launch > Manage manually > Auto-launch, Secondary launch, Run in background On.
- অন্য ফোন: Settings-এ Autostart, Auto launch, Battery optimization, Background activity search করে SCB-Forwarder সব জায়গায় allow করুন।

### ৬. Forwarding confirm করুন

- **Forwarding stats / ফরওয়ার্ড স্ট্যাটাস** successful এবং failed/queued attempts দেখাবে।
- **Offline queue / অফলাইন কিউ** internet/server না থাকলে pending notice দেখাবে।
- ফোন offline থাকলে internet ফিরে এলে queued notice নিজে upload হবে। চাইলে **Retry queued notices now** চাপতে পারেন।
