const LOCALE = 'pt-MZ';

/** 1234.5 -> "1 234,50 MT" */
export function formatMoney(value: number | string, currency = 'MZN'): string {
  return new Intl.NumberFormat(LOCALE, { style: 'currency', currency }).format(Number(value));
}

/** "2026-11-23" -> "23/11/2026" */
export function formatDate(value: string | Date): string {
  return new Intl.DateTimeFormat(LOCALE, { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(value));
}
