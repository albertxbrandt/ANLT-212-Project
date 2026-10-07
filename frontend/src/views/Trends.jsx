import { api } from "../api.js"
import ErrorBanner from "../components/ErrorBanner.jsx"
import { barPercent, formatPercent, formatQty, formatRate, formatWeek } from "../format.js"
import { useAsync } from "../hooks.js"

export default function Trends() {
  const { data, loading, error } = useAsync(() => api.getInsights(), [])
  const weeks = data?.usage_by_week || []
  const max = Math.max(0, ...weeks.map((week) => week.consumed))

  return (
    <section>
      <h2>Trends</h2>
      <p className="lede">
        Use rate is the amount consumed in the last 28 days, divided by the days from the first of those uses through today.
        A product is short when it is under par, or when less than 7 days of cover remain.
      </p>
      {loading && <p className="muted">Adding up the log…</p>}
      <ErrorBanner message={error} />
      {data && (
        <>
          <article className="panel">
            <h3>Household use, last 8 weeks</h3>
            {weeks.map((week) => (
              <div className="bar-row" key={week.week_start}>
                <span>{formatWeek(week.week_start)}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${barPercent(week.consumed, max)}%` }} />
                </div>
                <span>{formatQty(week.consumed)}</span>
              </div>
            ))}
          </article>
          <article className="panel">
            <h3>What to buy</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>On hand</th>
                    <th>Daily use</th>
                    <th>Days left</th>
                    <th>Buy</th>
                  </tr>
                </thead>
                <tbody>
                  {data.replenishment.map((row) => (
                    <tr key={row.product_id} className={row.restock ? "short" : undefined}>
                      <td>{row.name}</td>
                      <td>{formatQty(row.on_hand)} {row.unit}</td>
                      <td>{formatRate(row.daily_rate, row.unit)}</td>
                      <td>{row.days_of_cover == null ? "n/a" : formatQty(row.days_of_cover)}</td>
                      <td>{row.restock ? `${formatQty(row.suggested_quantity)} ${row.unit}` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
          <article className="panel">
            <h3>Waste</h3>
            {data.waste.length === 0 && <p className="muted">No waste has been recorded.</p>}
            <ul className="plain">
              {data.waste.map((row) => (
                <li key={row.product_id}>
                  <strong>{row.name}</strong>
                  <span>
                    Used {formatQty(row.consumed)} {row.unit} · wasted {formatQty(row.wasted)} {row.unit} · {formatPercent(row.waste_share)}
                  </span>
                </li>
              ))}
            </ul>
          </article>
        </>
      )}
    </section>
  )
}
