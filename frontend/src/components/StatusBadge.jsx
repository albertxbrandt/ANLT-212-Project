const LABELS = {
  ok: "Fresh",
  expiring: "Use soon",
  expired: "Expired",
  low: "Low",
  wasted: "Wasted",
}

export default function StatusBadge({ tone }) {
  return <span className={`badge badge-${tone}`}>{LABELS[tone] || tone}</span>
}
