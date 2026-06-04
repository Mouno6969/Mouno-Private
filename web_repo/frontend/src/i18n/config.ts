import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: {
    translation: {
      "welcome": "Welcome to MounoWeb",
      "buy": "Buy Crypto",
      "swap": "Swap & Bridge",
      "wallet": "Personal Wallet",
      "gift": "Gift Codes",
      "referral": "Referrals",
      "orders": "Order History",
      "support": "AI Support",
      "login": "Login",
      "register": "Register",
      "logout": "Logout",
      "username": "Username",
      "password": "Password",
      "connect_telegram": "Connect Telegram",
      "connected": "Connected",
      "not_connected": "Not Connected",
      "rates": "Live Rates",
      "bdt_amount": "Amount in BDT",
      "crypto_amount": "Amount in USDC/USDT",
      "network": "Network",
      "wallet_address": "Wallet Address",
      "trx_id": "bKash Transaction ID",
      "submit_order": "Submit Order",
      "pending_orders": "Pending Orders",
      "completed_orders": "Completed Orders",
      "status": "Status",
      "date": "Date",
      "total_spent": "Total Spent",
      "order_count": "Total Orders",
      "copy_success": "Copied to clipboard!",
      "footer_text": "© 2026 Mouno. All rights reserved.",
      "send_bdt": "Send BDT to:",
      "after_payment": "After payment, submit the TrxID below.",
    }
  },
  bn: {
    translation: {
      "welcome": "বিজিসি ক্রিপ্টোতে স্বাগতম",
      "buy": "ক্রিপ্টো কিনুন",
      "swap": "সোয়াপ ও ব্রিজ",
      "wallet": "পার্সোনাল ওয়ালেট",
      "gift": "গিফট কোড",
      "referral": "রেফারেল",
      "orders": "অর্ডার হিস্ট্রি",
      "support": "এআই সাপোর্ট",
      "login": "লগইন",
      "register": "রেজিস্ট্রেশন",
      "logout": "লগআউট",
      "username": "ইউজারনেম",
      "password": "পাসওয়ার্ড",
      "connect_telegram": "টেলিগ্রাম কানেক্ট",
      "connected": "কানেক্টেড",
      "not_connected": "কানেক্টেড নেই",
      "rates": "লাইভ রেট",
      "bdt_amount": "টাকার পরিমাণ (BDT)",
      "crypto_amount": "ক্রিপ্টো পরিমাণ (USDC/USDT)",
      "network": "নেটওয়ার্ক",
      "wallet_address": "ওয়ালেট এড্রেস",
      "trx_id": "বিকাশ ট্রানজেকশন আইডি",
      "submit_order": "অর্ডার সাবমিট করুন",
      "pending_orders": "পেন্ডিং অর্ডার",
      "completed_orders": "সম্পন্ন অর্ডার",
      "status": "অবস্থা",
      "date": "তারিখ",
      "total_spent": "মোট খরচ",
      "order_count": "মোট অর্ডার",
      "copy_success": "কপি হয়েছে!",
      "footer_text": "© ২০২৪ বিজিসি প্রাইভেট। সর্বস্বত্ব সংরক্ষিত।",
      "send_bdt": "টাকা পাঠান এই নম্বরে:",
      "after_payment": "পেমেন্ট করার পর নিচের বক্সে TrxID দিন।",
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'bn',
    interpolation: {
      escapeValue: false,
    }
  });

export default i18n;
