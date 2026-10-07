import { api } from "../api.js"
import ErrorBanner from "../components/ErrorBanner.jsx"
import StatusBadge from "../components/StatusBadge.jsx"
import { expiryLabel, formatQty, lotTone } from "../format.js"
import { useAsync } from "../hooks.js"

export default function Home() {
  const { data, loading, error } = useAsync(() => api.getInsights(), [])
  const summary = data?.summary

  return (
    <section>
      <h2>At a glance</h2>
      {loading && <p className="muted">Checking the shelves…</p>}
      <ErrorBanner message={error} />
      {summary && (
        <>
          <div className="stats">
            <Stat label="Items on hand" value={summary.active_lots} />
            <Stat label="Products stocked" value={summary.products_on_hand} />
            <Stat label="Use soon" value={summary.expiring_soon} />
            <Stat label="Buy again" value={summary.restock_needed} />
          </div>
          <div className="split">
            <article className="panel">
              <h3>Expiring within 7 days</h3>
              {data.expiring.length === 0 && <p className="muted">Nothing is due this week.</p>}
              <ul className="plain">
                {data.expiring.map((lot) => (
                  <li key={lot.id}>
                    <div>
                      <strong>{lot.product_name}</strong>
                      <span className="muted">
                        {formatQty(lot.quantity_remaining)} {lot.unit} · {lot.location_name}
                      </span>
                    </div>
                    <StatusBadge tone={lotTone(lot.expires_on)} />
                    <span>{expiryLabel(lot.expires_on)}</span>
                  </li>
                ))}
              </ul>
            </article>
            <article className="panel">
              <h3>Plan the next shop</h3>
              {data.restock.length === 0 && <p className="muted">Nothing looks short.</p>}
              <ul className="plain">
                {data.restock.map((row) => (
                  <li key={row.product_id}>
                    <div>
                      <strong>{row.name}</strong>
                      <span className="muted">{row.reasons.join(" · ")}</span>
                    </div>
                    <span>
                      Buy {formatQty(row.suggested_quantity)} {row.unit}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="muted waste-note">
                {summary.waste_events_this_month === 0
                  ? "No waste recorded this month."
                  : `${summary.waste_events_this_month} waste ${summary.waste_events_this_month === 1 ? "entry" : "entries"} this month.`}
              </p>
            </article>
          </div>
        </>
      )}
    </section>
  )
}

function Stat({ label, value }) {
  return (
    <article className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}
