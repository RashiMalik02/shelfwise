const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
const inrPrecise = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2 });
const count = new Intl.NumberFormat('en-IN');
const compact = new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 });

export const money = (value) => inr.format(value ?? 0);
export const price = (value) => inrPrecise.format(value ?? 0);
export const units = (value) => count.format(value ?? 0);
export const compactMoney = (value) => `₹${compact.format(value ?? 0)}`;

export function timeAgo(iso, now = Date.now()) {
  // The API returns UTC; SQLite in tests drops the offset, so treat bare timestamps as UTC.
  const stamp = /Z|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`;
  const seconds = Math.max(0, Math.round((now - new Date(stamp).getTime()) / 1000));
  if (seconds < 45) return 'just now';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
}

// How many units to receive to get back to twice the reorder level.
export function suggestedReorder(product) {
  return Math.max(product.reorder_level * 2 - product.quantity, 1);
}
