import { expect, test, vi } from "vitest"
import { createApi, messageFromError } from "../api.js"

function fakeHttp() {
  return {
    get: vi.fn().mockResolvedValue({ data: [{ id: 1, name: "Fridge" }] }),
    post: vi.fn().mockResolvedValue({ data: { id: 9 } }),
    put: vi.fn().mockResolvedValue({ data: { id: 9 } }),
    delete: vi.fn().mockResolvedValue({ data: "" }),
  }
}

test("messageFromError prefers the server message", () => {
  expect(messageFromError({ response: { data: { error: "That is more than what is left" } } }))
    .toBe("That is more than what is left")
  expect(messageFromError(new Error("offline"))).toBe("Could not reach the server.")
})

test("location and inventory calls use the shared client", async () => {
  const http = fakeHttp()
  const client = createApi(http)

  await expect(client.getLocations()).resolves.toEqual([{ id: 1, name: "Fridge" }])
  expect(http.get).toHaveBeenCalledWith("/locations", { params: undefined })

  await client.getInventory(3)
  expect(http.get).toHaveBeenCalledWith("/inventory", { params: { location_id: 3 } })

  await client.stock({ product_id: 2, quantity: 1 })
  expect(http.post).toHaveBeenCalledWith("/inventory/stock", { product_id: 2, quantity: 1 })

  await client.consume(4, 0.5)
  expect(http.post).toHaveBeenCalledWith("/inventory/consume", { lot_id: 4, quantity: 0.5 })
})
