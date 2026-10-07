import { useState } from "react"
import { api, messageFromError } from "../api.js"
import ErrorBanner from "../components/ErrorBanner.jsx"
import Field from "../components/Field.jsx"
import LocationChips from "../components/LocationChips.jsx"
import StatusBadge from "../components/StatusBadge.jsx"
import { expiryLabel, formatQty, lotTone, todayIso } from "../format.js"
import { useAsync } from "../hooks.js"

const EMPTY_STOCK = {
  productId: "",
  locationId: "",
  quantity: "",
  addedOn: todayIso(),
  expiresOn: "",
}

export default function Inventory({ locations }) {
  const [placeId, setPlaceId] = useState(null)
  const [form, setForm] = useState(EMPTY_STOCK)
  const [notice, setNotice] = useState("")
  const products = useAsync(() => api.getProducts(), [])
  const inventory = useAsync(() => api.getInventory(placeId), [placeId])

  async function addStock(event) {
    event.preventDefault()
    setNotice("")
    try {
      await api.stock({
        product_id: Number(form.productId),
        location_id: Number(form.locationId),
        quantity: Number(form.quantity),
        added_on: form.addedOn,
        expires_on: form.expiresOn || null,
      })
      setForm({ ...EMPTY_STOCK, addedOn: todayIso() })
      inventory.reload()
    } catch (error) {
      setNotice(messageFromError(error))
    }
  }

  const lots = inventory.data || []
  const catalog = products.data || []

  return (
    <section>
      <h2>Inventory</h2>
      <LocationChips locations={locations} selected={placeId} onSelect={setPlaceId} />
      <ErrorBanner message={notice || inventory.error || products.error} />
      <form className="form-grid" onSubmit={addStock}>
        <Field label="Product">
          <select
            required
            value={form.productId}
            onChange={(event) => setForm({ ...form, productId: event.target.value })}
          >
            <option value="">Choose</option>
            {catalog.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Place">
          <select
            required
            value={form.locationId}
            onChange={(event) => setForm({ ...form, locationId: event.target.value })}
          >
            <option value="">Choose</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Quantity">
          <input
            required
            min="0"
            step="any"
            type="number"
            value={form.quantity}
            onChange={(event) => setForm({ ...form, quantity: event.target.value })}
          />
        </Field>
        <Field label="Stocked on">
          <input
            required
            type="date"
            value={form.addedOn}
            onChange={(event) => setForm({ ...form, addedOn: event.target.value })}
          />
        </Field>
        <Field label="Expires (optional)">
          <input
            type="date"
            value={form.expiresOn}
            onChange={(event) => setForm({ ...form, expiresOn: event.target.value })}
          />
        </Field>
        <button className="primary" type="submit">Add stock</button>
      </form>
      <p className="hint">Leave expiry blank to use the product's shelf life.</p>
      {inventory.loading && <p className="muted">Loading the shelves…</p>}
      {!inventory.loading && lots.length === 0 && <p className="muted">This place is empty.</p>}
      <ul className="lots">
        {lots.map((lot) => (
          <LotRow
            key={lot.id}
            lot={lot}
            locations={locations}
            onDone={inventory.reload}
            onError={setNotice}
          />
        ))}
      </ul>
    </section>
  )
}

function LotRow({ lot, locations, onDone, onError }) {
  const [mode, setMode] = useState(null)
  const [quantity, setQuantity] = useState(String(Math.min(1, lot.quantity_remaining)))
  const [notes, setNotes] = useState("")
  const elsewhere = locations.filter((location) => location.id !== lot.location_id)
  const [destination, setDestination] = useState(elsewhere[0]?.id || "")

  async function submit(event) {
    event.preventDefault()
    try {
      if (mode === "use") await api.consume(lot.id, Number(quantity))
      if (mode === "waste") await api.waste(lot.id, Number(quantity), notes)
      if (mode === "move") await api.move(lot.id, Number(destination))
      setMode(null)
      onError("")
      onDone()
    } catch (error) {
      onError(messageFromError(error))
    }
  }

  return (
    <li className="lot">
      <div className="lot-main">
        <div>
          <strong>{lot.product_name}</strong>
          <span className="muted">{lot.location_name}</span>
        </div>
        <span>
          {formatQty(lot.quantity_remaining)} {lot.unit}
        </span>
        <StatusBadge tone={lotTone(lot.expires_on)} />
        <span>{expiryLabel(lot.expires_on)}</span>
      </div>
      <div className="row-actions">
        <button type="button" onClick={() => setMode(mode === "use" ? null : "use")}>Use</button>
        <button type="button" onClick={() => setMode(mode === "waste" ? null : "waste")}>Waste</button>
        <button type="button" onClick={() => setMode(mode === "move" ? null : "move")} disabled={!elsewhere.length}>
          Move
        </button>
      </div>
      {mode && (
        <form className="inline-form" onSubmit={submit}>
          {mode !== "move" && (
            <Field label="Quantity">
              <input
                required
                min="0"
                step="any"
                type="number"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
              />
            </Field>
          )}
          {mode === "waste" && (
            <Field label="Note">
              <input value={notes} onChange={(event) => setNotes(event.target.value)} />
            </Field>
          )}
          {mode === "move" && (
            <Field label="New place">
              <select value={destination} onChange={(event) => setDestination(event.target.value)}>
                {elsewhere.map((location) => (
                  <option key={location.id} value={location.id}>{location.name}</option>
                ))}
              </select>
            </Field>
          )}
          <button className="primary" type="submit">Save</button>
        </form>
      )}
    </li>
  )
}
