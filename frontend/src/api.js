/**
 * The only module that talks to the Flask API.
 * Pass a fake client to createApi in unit tests.
 */

import axios from "axios"

export function messageFromError(error) {
  const apiMessage = error?.response?.data?.error
  if (typeof apiMessage === "string" && apiMessage) return apiMessage
  return "Could not reach the server."
}

export function createApi(http = axios.create({ baseURL: "/api" })) {
  const read = (path, params) => http.get(path, { params }).then((response) => response.data)
  const send = (method, path, body) => http[method](path, body).then((response) => response.data)

  return {
    getLocations: () => read("/locations"),
    createLocation: (body) => send("post", "/locations", body),
    updateLocation: (id, body) => send("put", `/locations/${id}`, body),
    deleteLocation: (id) => http.delete(`/locations/${id}`),
    getProducts: () => read("/products"),
    createProduct: (body) => send("post", "/products", body),
    updateProduct: (id, body) => send("put", `/products/${id}`, body),
    deleteProduct: (id) => http.delete(`/products/${id}`),
    getInventory: (locationId) => read("/inventory", locationId ? { location_id: locationId } : {}),
    stock: (body) => send("post", "/inventory/stock", body),
    consume: (lotId, quantity) => send("post", "/inventory/consume", { lot_id: lotId, quantity }),
    waste: (lotId, quantity, notes) => send("post", "/inventory/waste", { lot_id: lotId, quantity, notes }),
    move: (lotId, locationId) => send("post", "/inventory/move", { lot_id: lotId, location_id: locationId }),
    getInsights: () => read("/insights"),
  }
}

export const api = createApi()
