# Unit testing for PantryPal

Date: 2026-10-07

Add unit tests so the inventory build can be checked without clicking through the app and without a running server.

## Backend

- `tests/test_rules.py` tests the rate, days of cover, suggested purchase, waste share, and week buckets as plain functions.
- `tests/test_inventory.py` tests stocking, shelf-life expiry, use, waste, move, delete guards, and insights on a private SQLite database.
- `tests/test_backend.py` tests HTTP status codes, JSON errors, and a seeded database. It does not repeat the math cases.

Pytest is listed in `backend/requirements-dev.txt`. Each service test opens its own database. `conftest.py` puts `backend/src` on the path once.

## Frontend

Vitest tests in `frontend/src/test/` cover:

- date and quantity formatting
- the API client, using a fake HTTP object passed into `createApi`
- the status badge, the loading hook, and the home screen with a fake insights payload

## How to run

`npm test` from the repository root runs pytest and Vitest.

`npm run check` runs those tests and then `vite build`.

`test.bat` installs the test tools, runs both suites, and builds the frontend on Windows.
