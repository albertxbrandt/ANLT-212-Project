/** Display helpers shared by the screens. Prediction math stays on the server. */

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

export function parseISODate(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number)
  return new Date(year, month - 1, day)
}

export function todayIso(now = new Date()) {
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  return `${now.getFullYear()}-${month}-${day}`
}

/** Whole days from today until an ISO date. Negative when that date has passed. */
export function daysUntil(isoDate, today = todayIso()) {
  const msPerDay = 24 * 60 * 60 * 1000
  return Math.round((parseISODate(isoDate) - parseISODate(today)) / msPerDay)
}

export function expiryLabel(isoDate, today = todayIso()) {
  const days = daysUntil(isoDate, today)
  if (days === 0) return "Expires today"
  if (days === 1) return "Expires tomorrow"
  if (days > 1) return `Expires in ${days} days`
  if (days === -1) return "Expired yesterday"
  return `Expired ${Math.abs(days)} days ago`
}

/** Badge tone for a lot. Use-soon covers the same 7-day line as restock warnings. */
export function lotTone(isoDate, today = todayIso()) {
  const days = daysUntil(isoDate, today)
  if (days < 0) return "expired"
  if (days <= 7) return "expiring"
  return "ok"
}

export function formatQty(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return ""
  return String(Math.round(number * 100) / 100)
}

export function formatRate(rate, unit) {
  if (rate == null) return "No recent use"
  return `${formatQty(rate)} ${unit}/day`
}

export function formatPercent(share) {
  if (share == null) return "n/a"
  return `${Math.round(share * 100)}%`
}

export function formatWeek(isoDate) {
  const parsed = parseISODate(isoDate)
  return `${MONTHS[parsed.getMonth()]} ${parsed.getDate()}`
}

/** Width of a bar as a percent of the largest value, clamped to 0–100. */
export function barPercent(value, max) {
  const top = Number(max)
  if (!top || top < 0) return 0
  const ratio = Math.max(0, Number(value)) / top
  return Math.max(0, Math.min(100, Math.round(ratio * 100)))
}
