# PantryPal

A household inventory tracker. Record what is in the fridge, freezer, and pantry, follow each item from stocking through use or waste, and see what is about to expire or run out.

## Requirements

- Python 3.8+
- Node.js 16+ and npm

The database is SQLite. The file is created at `backend/data/household.db` the first time the API starts. No separate database server is required.

## Run both apps

On Windows, double-click or run:

```bat
start.bat
```

That opens the API on http://localhost:5000 and the React app on http://localhost:5173.

On macOS or Linux:

```bash
pip install -r backend/requirements.txt
cd backend && python src/app.py
```

```bash
cd frontend && npm install && npm run dev
```

From the project root, `npm install` then `npm run dev` starts both if `python` is on your PATH.

The first launch loads a demo household so the home screen and trends are not empty. Set `INVENTORY_SEED=0` to start blank. See `backend/.env.example`.

## Test the build

Unit tests do not need the servers to be running.

```bash
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
npm install
npm test
npm run build
```

`npm test` runs the Python unit tests and the Vitest unit tests. `npm run check` runs those tests and then builds the frontend. On Windows, `test.bat` does the same install, test, and build steps.

- `tests/test_rules.py` checks the replenishment math with no database.
- `tests/test_inventory.py` checks stocking, use, waste, moves, and insights on a private SQLite database.
- `tests/test_backend.py` checks HTTP status codes and a seeded API.
- `frontend/src/test/` checks formatting, the API client, and the home screen.

## What the prediction does

Daily use is the amount consumed in the last 28 days, divided by the number of days from the first of those uses through today. Days of cover is the quantity on hand divided by that rate. PantryPal suggests a purchase when the quantity is below the product's par level, or when fewer than 7 days of cover remain. The suggested amount is enough to reach par, or a 14-day supply, whichever is larger.

## Layout

```
frontend/     React screens
backend/      Flask routes, inventory rules, SQLite
plans/        Dated plans
tests/        Python unit tests
start.bat     Starts the API and the UI
test.bat      Runs unit tests and the frontend build
```

`backend/src/db.py` opens SQLite and creates tables. `backend/src/inventory.py` applies the household rules. `backend/src/app.py` only translates HTTP into those rules. The React app calls the API through `frontend/src/api.js`.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Process is up |
| GET, POST | `/api/locations` | List or add a place |
| PUT, DELETE | `/api/locations/<id>` | Rename or remove a place |
| GET, POST | `/api/products` | List or add a product |
| PUT, DELETE | `/api/products/<id>` | Edit or remove a product |
| GET | `/api/inventory?location_id=` | Items currently stored |
| POST | `/api/inventory/stock` | Add an item |
| POST | `/api/inventory/consume` | Use some of an item |
| POST | `/api/inventory/waste` | Throw some of an item away |
| POST | `/api/inventory/move` | Move an item |
| GET | `/api/insights` | Expiry, restock, use, and waste |

Errors return `{ "error": "..." }` with status 400, 404, or 409.
