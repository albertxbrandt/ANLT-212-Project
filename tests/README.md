# Tests

Unit tests run without starting Flask or Vite.

```bash
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
python -m pytest tests -q
```

From the repository root, `npm test` runs these tests and the frontend Vitest suite. `test.bat` does that and then builds the frontend.

- `test_rules.py` — replenishment math
- `test_inventory.py` — items, shelf life, waste, and insights on SQLite
- `test_backend.py` — HTTP status codes

Frontend tests live in `frontend/src/test/` and run with `npm test` inside `frontend/`.
