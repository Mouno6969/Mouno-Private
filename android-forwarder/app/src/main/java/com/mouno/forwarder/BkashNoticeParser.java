package com.mouno.forwarder;

import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class BkashNoticeParser {
    private static final Pattern BKASH_MARKER = Pattern.compile("\\b(bkash)\\b|বিকাশ", Pattern.CASE_INSENSITIVE);
    private static final Pattern TRANSACTION_MARKER = Pattern.compile("\\bTrx\\s*ID\\b|\\bTxn\\s*ID\\b|Transaction ID", Pattern.CASE_INSENSITIVE);
    private static final Pattern[] AMOUNT_PATTERNS = new Pattern[]{
        Pattern.compile("You have received\\s*(?:Tk|BDT|৳)\\s*([\\d,]+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(?:received|Receive Money|Payment Received|Cash In)\\D{0,20}(?:Tk|BDT|৳)\\s*([\\d,]+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(?:Tk|BDT|৳)\\s*([\\d,]+(?:\\.\\d+)?)\\D{0,40}(?:received|Receive Money|Payment Received|Cash In)", Pattern.CASE_INSENSITIVE)
    };
    private static final Pattern[] TRX_PATTERNS = new Pattern[]{
        Pattern.compile("\\bTrx\\s*ID\\s*[:#-]?\\s*([A-Z0-9]+)", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\bTxn\\s*ID\\s*[:#-]?\\s*([A-Z0-9]+)", Pattern.CASE_INSENSITIVE),
        Pattern.compile("Transaction\\s*ID\\s*[:#-]?\\s*([A-Z0-9]+)", Pattern.CASE_INSENSITIVE)
    };
    private static final Pattern[] SENDER_PATTERNS = new Pattern[]{
        Pattern.compile("from\\s*(\\d{10,14})", Pattern.CASE_INSENSITIVE),
        Pattern.compile("Sender\\s*[:#-]?\\s*(\\d{10,14})", Pattern.CASE_INSENSITIVE)
    };
    private static final Pattern[] DATETIME_PATTERNS = new Pattern[]{
        Pattern.compile("at\\s*(\\d{2}/\\d{2}/\\d{4}\\s+\\d{2}:\\d{2})", Pattern.CASE_INSENSITIVE),
        Pattern.compile("(\\d{2}/\\d{2}/\\d{4}\\s+\\d{2}:\\d{2})", Pattern.CASE_INSENSITIVE)
    };

    private BkashNoticeParser() {}

    static Parsed parse(String text) {
        String compact = compact(text);
        if (compact.isEmpty()) return null;
        if (!BKASH_MARKER.matcher(compact).find() && !TRANSACTION_MARKER.matcher(compact).find()) return null;
        Double amount = amount(compact);
        String trxId = first(compact, TRX_PATTERNS);
        if (amount == null || trxId == null || trxId.isEmpty()) return null;
        String sender = first(compact, SENDER_PATTERNS);
        String noticeTime = first(compact, DATETIME_PATTERNS);
        return new Parsed(amount, trxId.toUpperCase(Locale.ROOT), sender == null ? "bkash_app" : sender, noticeTime);
    }

    private static String compact(String text) {
        return text == null ? "" : text.trim().replaceAll("\\s+", " ");
    }

    private static Double amount(String text) {
        String raw = first(text, AMOUNT_PATTERNS);
        if (raw == null) return null;
        try {
            return Double.parseDouble(raw.replace(",", ""));
        } catch (NumberFormatException exc) {
            return null;
        }
    }

    private static String first(String text, Pattern[] patterns) {
        for (Pattern pattern : patterns) {
            Matcher matcher = pattern.matcher(text);
            if (matcher.find()) return matcher.group(1);
        }
        return null;
    }

    static final class Parsed {
        final double amountBdt;
        final String trxId;
        final String sender;
        final String noticeTime;

        Parsed(double amountBdt, String trxId, String sender, String noticeTime) {
            this.amountBdt = amountBdt;
            this.trxId = trxId;
            this.sender = sender;
            this.noticeTime = noticeTime;
        }

        String summary() {
            return trxId + " / " + amountBdt + " BDT / " + sender;
        }
    }
}
