import { useEffect, useState } from "react"
import { api, messageFromError } from "./api.js"
import ErrorBanner from "./components/ErrorBanner.jsx"
import Goods from "./views/Goods.jsx"
import Home from "./views/Home.jsx"
import Inventory from "./views/Inventory.jsx"
import Places from "./views/Places.jsx"
import Trends from "./views/Trends.jsx"
import "./App.css"

const VIEWS = [
  ["home", "Home"],
  ["inventory", "Inventory"],
  ["places", "Places"],
  ["goods", "Goods"],
  ["trends", "Trends"],
]

export default function App() {
  const [view, setView] = useState("home")
  const [locations, setLocations] = useState([])
  const [locationError, setLocationError] = useState("")

  function refreshLocations() {
    api.getLocations()
      .then((rows) => {
        setLocations(rows)
        setLocationError("")
      })
      .catch((error) => setLocationError(messageFromError(error)))
  }

  useEffect(() => {
    refreshLocations()
  }, [])

  return (
    <div className="app">
      <header className="mast">
        <div>
          <p className="eyebrow">Household inventory</p>
          <h1>PantryPal</h1>
          <p className="tagline">What is in the house, how long it will keep, and what to buy before it runs out.</p>
        </div>
        <nav className="nav" aria-label="Sections">
          {VIEWS.map(([id, label]) => (
            <button
              key={id}
              type="button"
              aria-current={view === id ? "page" : undefined}
              onClick={() => setView(id)}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        <ErrorBanner message={locationError} />
        {view === "home" && <Home />}
        {view === "inventory" && <Inventory locations={locations} />}
        {view === "places" && <Places locations={locations} onChange={refreshLocations} />}
        {view === "goods" && <Goods locations={locations} />}
        {view === "trends" && <Trends />}
      </main>
    </div>
  )
}
