# Tests

Simple starter tests for the backend and frontend.

## Backend Tests

Run Python backend tests:

```bash
cd ..
python -m pytest tests/test_backend.py -v
```

Or run directly with Python:

```bash
python tests/test_backend.py
```

### Requirements

Install pytest for more advanced testing:

```bash
pip install pytest
```

## Frontend Tests

For now, basic JavaScript tests are provided. For more advanced testing with React Testing Library:

```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom
npm test
```

## Test Files

- `test_backend.py` - Tests Flask API endpoints (health, hello, CORS)
- `test_frontend.js` - Basic frontend tests
