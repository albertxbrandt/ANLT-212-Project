# PantryPal household inventory

Date: 2026-10-07

Build a household inventory system on the React and Flask starter. Keep `frontend/`, `backend/`, one `start.bat`, and this `plans/` folder. Use SQLite.

One household, no login. The unused `interface/` stubs stay in the repo and are not part of the app.

## Data model

SQLite file `backend/data/household.db`, overridable with `DATABASE_PATH`.

- locations — name and kind (`fridge`, `freezer`, `pantry`, `other`)
- products — lasting item, shelf-life days, par quantity, usual place
- lots — one stocking, with quantity remaining, expiry, and status (`active`, `depleted`, `wasted`)
- events — `stocked`, `consumed`, `wasted`, `moved`

Expiry defaults to the stocked date plus the product shelf life. Using the last of a lot marks it depleted. Wasting the last of a lot marks it wasted. Expired lots stay visible until the user records use or waste.

## Prediction and waste

Computed from the event log.

- Daily use rate = quantity consumed over the last 28 days, divided by the inclusive days from the first of those events through today.
- Days of cover = quantity on hand / rate.
- Suggest a restock when on-hand is below par, or days of cover are under 7.
- Suggested buy quantity is enough to reach par, or a 14-day supply, whichever is larger.
- No consumption history: compare with par only, and show the rate as unknown.

An empty database is seeded with Fridge, Freezer, and Pantry, a small catalog, several weeks of use, one lot expiring soon, and one product below par. Seeding runs only when `products` is empty.

## Structure

- `backend/src/db.py` — connection, schema, seed. Parameterized queries.
- `backend/src/inventory.py` — rules. No Flask imports.
- `backend/src/app.py` — parse JSON, call the service, return JSON.
- `frontend/src/api.js` — the only module that calls the API.
- `frontend/src/views/` — Home, Inventory, Places, Goods, Trends.
- Shared form, badge, and error pieces live in `frontend/src/components/`.

Days of cover and suggested buy quantity are displayed from `/api/insights`. The browser does not recompute them.

Public modules and functions have a short docstring. The 28-day rate, the 7-day restock line, and the default expiry are explained where they are calculated.
