import { render, screen } from "@testing-library/react"
import { expect, test, vi } from "vitest"
import { api } from "../api.js"
import StatusBadge from "../components/StatusBadge.jsx"
import { useAsync } from "../hooks.js"
import Home from "../views/Home.jsx"

vi.mock("../api.js", () => ({
  api: {
    getInsights: vi.fn(),
    getLocations: vi.fn(),
  },
  messageFromError: (error) => error.message || "Could not reach the server.",
}))

function Probe({ loader }) {
  const state = useAsync(loader, [])
  if (state.loading) return <p>Loading</p>
  if (state.error) return <p>{state.error}</p>
  return <p>{state.data}</p>
}

test("status badge names the shelf tone", () => {
  render(<StatusBadge tone="expiring" />)
  expect(screen.getByText("Use soon")).toBeInTheDocument()
})

test("useAsync renders loaded data", async () => {
  render(<Probe loader={() => Promise.resolve("Rice")} />)
  expect(await screen.findByText("Rice")).toBeInTheDocument()
})

test("useAsync renders a failure", async () => {
  render(<Probe loader={() => Promise.reject(new Error("nope"))} />)
  expect(await screen.findByText("nope")).toBeInTheDocument()
})

test("home shows server restock and expiry rows", async () => {
  api.getInsights.mockResolvedValue({
    summary: {
      active_lots: 2,
      products_on_hand: 2,
      expiring_soon: 1,
      restock_needed: 1,
      waste_events_this_month: 1,
    },
    expiring: [{
      id: 1,
      product_name: "Spinach",
      quantity_remaining: 1,
      unit: "bag",
      expires_on: "2026-10-08",
      location_name: "Fridge",
    }],
    restock: [{
      product_id: 2,
      name: "Milk",
      unit: "gal",
      on_hand: 0.5,
      suggested_quantity: 1,
      reasons: ["Below par"],
    }],
    waste_this_month: [],
  })

  render(<Home />)
  expect(await screen.findByText("Items on hand")).toBeInTheDocument()
  expect(screen.getByText("Milk")).toBeInTheDocument()
  expect(screen.getByText("Spinach")).toBeInTheDocument()
  expect(screen.getByText("Buy 1 gal")).toBeInTheDocument()
  expect(screen.getByText("1 waste entry this month.")).toBeInTheDocument()
})
