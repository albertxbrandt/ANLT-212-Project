import { useState } from "react"
import { api, messageFromError } from "../api.js"
import ErrorBanner from "../components/ErrorBanner.jsx"
import Field from "../components/Field.jsx"
import { useAsync } from "../hooks.js"

const EMPTY = {
  id: null,
  name: "",
  category: "",
  unit: "",
  shelfLife: "",
  par: "",
  placeId: "",
}

export default function Goods({ locations }) {
  const [form, setForm] = useState(EMPTY)
  const [notice, setNotice] = useState("")
  const catalog = useAsync(() => api.getProducts(), [])

  function edit(product) {
    setForm({
      id: product.id,
      name: product.name,
      category: product.category,
      unit: product.unit,
      shelfLife: String(product.shelf_life_days),
      par: String(product.par_quantity),
      placeId: product.preferred_location_id ? String(product.preferred_location_id) : "",
    })
  }

  async function save(event) {
    event.preventDefault()
    setNotice("")
    const body = {
      name: form.name,
      category: form.category,
      unit: form.unit,
      shelf_life_days: Number(form.shelfLife),
      par_quantity: Number(form.par),
      preferred_location_id: form.placeId ? Number(form.placeId) : null,
    }
    try {
      if (form.id) await api.updateProduct(form.id, body)
      else await api.createProduct(body)
      setForm(EMPTY)
      catalog.reload()
    } catch (error) {
      setNotice(messageFromError(error))
    }
  }

  async function remove(product) {
    setNotice("")
    try {
      await api.deleteProduct(product.id)
      if (form.id === product.id) setForm(EMPTY)
      catalog.reload()
    } catch (error) {
      setNotice(messageFromError(error))
    }
  }

  const products = catalog.data || []

  return (
    <section>
      <h2>Goods</h2>
      <p className="lede">Shelf life and the par level are what restocking uses later.</p>
      <ErrorBanner message={notice || catalog.error} />
      <form className="form-grid" onSubmit={save}>
        <Field label="Name">
          <input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
        </Field>
        <Field label="Category">
          <input required value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} />
        </Field>
        <Field label="Unit">
          <input required value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })} />
        </Field>
        <Field label="Shelf life (days)">
          <input
            required
            min="0"
            step="1"
            type="number"
            value={form.shelfLife}
            onChange={(event) => setForm({ ...form, shelfLife: event.target.value })}
          />
        </Field>
        <Field label="Par level">
          <input
            required
            min="0"
            step="any"
            type="number"
            value={form.par}
            onChange={(event) => setForm({ ...form, par: event.target.value })}
          />
        </Field>
        <Field label="Usual place">
          <select value={form.placeId} onChange={(event) => setForm({ ...form, placeId: event.target.value })}>
            <option value="">None</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>{location.name}</option>
            ))}
          </select>
        </Field>
        <button className="primary" type="submit">{form.id ? "Save product" : "Add product"}</button>
      </form>
      {catalog.loading && <p className="muted">Loading the catalog…</p>}
      <ul className="records">
        {products.map((product) => (
          <li key={product.id}>
            <div>
              <strong>{product.name}</strong>
              <span className="muted">
                {product.category} · {product.shelf_life_days} days · par {product.par_quantity} {product.unit}
              </span>
            </div>
            <div className="row-actions">
              <button type="button" onClick={() => edit(product)}>Edit</button>
              <button type="button" onClick={() => remove(product)}>Remove</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
