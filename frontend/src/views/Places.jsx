import { useState } from "react"
import { api, messageFromError } from "../api.js"
import ErrorBanner from "../components/ErrorBanner.jsx"
import Field from "../components/Field.jsx"

const KINDS = [
  ["fridge", "Fridge"],
  ["freezer", "Freezer"],
  ["pantry", "Pantry"],
  ["other", "Other"],
]

const EMPTY = { id: null, name: "", kind: "pantry" }

export default function Places({ locations, onChange }) {
  const [form, setForm] = useState(EMPTY)
  const [notice, setNotice] = useState("")

  async function save(event) {
    event.preventDefault()
    setNotice("")
    const body = { name: form.name, kind: form.kind }
    try {
      if (form.id) await api.updateLocation(form.id, body)
      else await api.createLocation(body)
      setForm(EMPTY)
      onChange()
    } catch (error) {
      setNotice(messageFromError(error))
    }
  }

  async function remove(location) {
    setNotice("")
    try {
      await api.deleteLocation(location.id)
      if (form.id === location.id) setForm(EMPTY)
      onChange()
    } catch (error) {
      setNotice(messageFromError(error))
    }
  }

  return (
    <section>
      <h2>Places</h2>
      <p className="lede">Fridge, freezer, pantry, or anywhere else food sits.</p>
      <ErrorBanner message={notice} />
      <form className="form-grid" onSubmit={save}>
        <Field label="Name">
          <input
            required
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
          />
        </Field>
        <Field label="Kind">
          <select value={form.kind} onChange={(event) => setForm({ ...form, kind: event.target.value })}>
            {KINDS.map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </Field>
        <button className="primary" type="submit">{form.id ? "Save place" : "Add place"}</button>
      </form>
      <ul className="records">
        {locations.map((location) => (
          <li key={location.id}>
            <div>
              <strong>{location.name}</strong>
              <span className="muted">{location.kind}</span>
            </div>
            <div className="row-actions">
              <button type="button" onClick={() => setForm(location)}>Edit</button>
              <button type="button" onClick={() => remove(location)}>Remove</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
