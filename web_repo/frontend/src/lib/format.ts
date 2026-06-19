// Shared formatting helpers for money, crypto amounts, and locale-aware grouping.
//
// English uses international grouping (1,234,567); Bengali uses the Indian
// numbering system (lakh/crore: 12,34,567). We drive grouping off the active
// i18n language so the same value reads naturally in both.

type Lang = 'en' | 'bn' | string;

function localeFor(lang: Lang): string {
  return lang === 'bn' ? 'en-IN' : 'en-US';
}

/** Format a BDT (taka) amount with locale-aware grouping and the ৳ symbol. */
export function formatBDT(value: number | string | null | undefined, lang: Lang = 'en'): string {
  const n = typeof value === 'string' ? Number(value) : value;
  if (n == null || !Number.isFinite(n)) return '৳—';
  return `৳${n.toLocaleString(localeFor(lang), { maximumFractionDigits: 2 })}`;
}

/** Format a plain number with locale-aware grouping (no currency symbol). */
export function formatNumber(
  value: number | string | null | undefined,
  lang: Lang = 'en',
  maximumFractionDigits = 2,
): string {
  const n = typeof value === 'string' ? Number(value) : value;
  if (n == null || !Number.isFinite(n)) return '—';
  return n.toLocaleString(localeFor(lang), { maximumFractionDigits });
}

/**
 * Format a crypto amount. Stablecoins read fine at 2dp, but small-unit assets
 * need more precision, so we keep up to `maxDp` significant decimals and trim
 * trailing zeros. Grouping is locale-aware for the integer part.
 */
export function formatCrypto(
  value: number | string | null | undefined,
  lang: Lang = 'en',
  maxDp = 8,
): string {
  const n = typeof value === 'string' ? Number(value) : value;
  if (n == null || !Number.isFinite(n)) return '—';
  const dp = Math.abs(n) >= 1 ? 4 : maxDp;
  const fixed = n.toLocaleString(localeFor(lang), { maximumFractionDigits: dp });
  return fixed;
}
