import { expect, test } from "vitest"
import {
  barPercent,
  daysUntil,
  expiryLabel,
  formatPercent,
  formatQty,
  formatRate,
  formatWeek,
  lotTone,
} from "../format.js"

const TODAY = "2026-10-07"

test("daysUntil counts whole calendar days", () => {
  expect(daysUntil("2026-10-10", TODAY)).toBe(3)
  expect(daysUntil("2026-10-06", TODAY)).toBe(-1)
})

test("expiry labels name today, tomorrow, and past dates", () => {
  expect(expiryLabel(TODAY, TODAY)).toBe("Expires today")
  expect(expiryLabel("2026-10-08", TODAY)).toBe("Expires tomorrow")
  expect(expiryLabel("2026-10-10", TODAY)).toBe("Expires in 3 days")
  expect(expiryLabel("2026-10-06", TODAY)).toBe("Expired yesterday")
  expect(expiryLabel("2026-10-04", TODAY)).toBe("Expired 3 days ago")
})

test("lot tone matches the seven-day use-soon line", () => {
  expect(lotTone("2026-10-06", TODAY)).toBe("expired")
  expect(lotTone("2026-10-14", TODAY)).toBe("expiring")
  expect(lotTone("2026-10-15", TODAY)).toBe("ok")
})

test("quantities, rates, percents, and weeks format for the screen", () => {
  expect(formatQty(2)).toBe("2")
  expect(formatQty(1.256)).toBe("1.26")
  expect(formatQty("nope")).toBe("")
  expect(formatRate(null, "gal")).toBe("No recent use")
  expect(formatRate(0.5, "gal")).toBe("0.5 gal/day")
  expect(formatPercent(0.25)).toBe("25%")
  expect(formatPercent(null)).toBe("n/a")
  expect(formatWeek("2026-10-05")).toBe("Oct 5")
})

test("bar widths stay inside the track", () => {
  expect(barPercent(0, 0)).toBe(0)
  expect(barPercent(2, 4)).toBe(50)
  expect(barPercent(8, 4)).toBe(100)
})
