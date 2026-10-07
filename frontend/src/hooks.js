import { useEffect, useState } from "react"
import { messageFromError } from "./api.js"

/**
 * Load data for a screen.
 *
 * loader is called again when deps change or when reload() is used.
 * The loader function itself is not a dependency, so callers pass the
 * values the request actually depends on.
 */
export function useAsync(loader, deps) {
  const [tick, setTick] = useState(0)
  const [state, setState] = useState({ loading: true, error: "", data: null })

  useEffect(() => {
    let active = true
    setState((current) => ({ ...current, loading: true, error: "" }))
    loader()
      .then((data) => {
        if (active) setState({ loading: false, error: "", data })
      })
      .catch((error) => {
        if (active) setState({ loading: false, error: messageFromError(error), data: null })
      })
    return () => {
      active = false
    }
  }, [...deps, tick])

  return {
    ...state,
    reload: () => setTick((value) => value + 1),
  }
}
