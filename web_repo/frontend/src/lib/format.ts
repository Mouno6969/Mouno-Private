// Shared formatting helpers for money, crypto amounts, and locale-aware grouping.
//
// English uses international grouping (1,234,567); Bengali uses the Indian
// numbering system (lakh/crore: 12,34,567). We drive grouping off the active
// i18n language so the same value reads naturally in both.

type Lang = 'en' | 'bn' | string;

function localeFor(lang: Lang): string {
  return lang === 'bn' ? 'en-IN' : 'en-US';
}

/** Parse to a finite number, treating empty strings as missing (not 0). */
function toNumber(value: number | string | null | undefined): number | null {
  if (value == null) return null;
  if (typeof value === 'string') {
    if (value.trim() === '') return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  return Number.isFinite(value) ? value : null;
}

/** Format a BDT (taka) amount with locale-aware grouping and the ৳ symbol. */
export function formatBDT(value: number | string | null | undefined, lang: Lang = 'en'): string {
  const n = toNumber(value);
  if (n == null) return '৳—';
  return `৳${n.toLocaleString(localeFor(lang), { maximumFractionDigits: 2 })}`;
}

/** Format a plain number with locale-aware grouping (no currency symbol). */
export function formatNumber(
  value: number | string | null | undefined,
  lang: Lang = 'en',
  maximumFractionDigits = 2,
): string {
  const n = toNumber(value);
  if (n == null) return '—';
  return n.toLocaleString(localeFor(lang), { maximumFractionDigits });
}

/**
 * Format a crypto amount. Whole-ish values (>= 1, e.g. stablecoins) read fine
 * with a few decimals; sub-unit assets need more precision. We cap decimals at
 * `maxDp` and let toLocaleString trim trailing zeros, with locale-aware grouping
 * for the integer part.
 */
export function formatCrypto(
  value: number | string | null | undefined,
  lang: Lang = 'en',
  maxDp = 8,
): string {
  const n = toNumber(value);
  if (n == null) return '—';
  const dp = Math.abs(n) >= 1 ? Math.min(4, maxDp) : maxDp;
  return n.toLocaleString(localeFor(lang), { maximumFractionDigits: dp });
}
