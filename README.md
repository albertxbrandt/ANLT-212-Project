# AI GENERATED SLOP tread carefully.

# Simple Start - React + Flask

A minimal full-stack web application template with React frontend and Flask backend. A blank slate to build from.

## Project Structure

```
simple-start/
├── frontend/              # React application
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── App.css        # Application styles
│   │   ├── main.jsx       # Entry point
│   │   ├── index.css      # Global styles
│   │   └── components/    # Add your components here
│   ├── package.json
│   └── vite.config.ts
├── backend/              # Flask Python application
│   ├── src/
│   │   └── app.py        # Flask app with basic endpoints
│   ├── requirements.txt  # Python dependencies
│   └── .env              # Environment variables
├── interface/            # Python interface layer (starter templates)
│   ├── Process.py        # Base Process class
│   ├── Component.py      # Base Component class
│   ├── Page.py           # Base Page class
├── tests/                # Test files
└── package.json          # Root scripts
```

## Features

- **React + Vite** - Fast, modern frontend development
- **Flask** - Lightweight Python web framework  
- **CORS Enabled** - Frontend can communicate with backend
- **Minimal Setup** - Ready to customize and build upon
- **Python Interface** - Starter templates for Process, Component, Page patterns

## Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Create `.env` file from template:
```bash
cp .env.example .env
```

3. Update `.env` with your MongoDB connection string:
```
MONGODB_URI=mongodb://localhost:27017/simple_start
FLASK_ENV=development
FLASK_DEBUG=True
```

### Frontend Setup

1. Install Node dependencies:
```bash
cd frontend
npm install
```

## Development

Run both backend (Flask) and frontend (React) concurrently:

```bash
npm run dev
```

This will:
- Start Flask backend on `http://localhost:5000`
- Start React frontend on `http://localhost:5173`
- React proxy sends `/api/*` requests to Flask backend

### Individual Commands

- **Backend only**: `npm run dev:backend`
  - Flask runs on port 5000 with hot reload
  
- **Frontend only**: `npm run dev:frontend`
  - React runs on port 5173 with Vite

## Architecture

The application uses a three-layer architecture:

1. **Process** - Discrete business logic operations
   - Located in `interface/Process.py`
   - Execute specific tasks
   - Can be combined into workflows

2. **Component** - Logical containers for Processes
   - Located in `interface/Component.py`
   - Manage multiple processes
   - Connect frontend and backend
   - Maintain component state

3. **Page** - Top-level UI containers with Tabs
   - Located in `interface/Page.py`
   - Organize components into tabs
   - Manage navigation and active tab

## API Endpoints

### Health Check
```
GET /api/health
```
Returns backend status and timestamp.

### Get Page Structure
```
GET /api/pages/import
```
Returns the complete page structure with tabs, components, and processes.

### Execute Process
```
POST /api/execute-process
Content-Type: application/json

{
  "tabName": "IESP Import",
  "componentName": "IESPImporter",
  "processName": "get_files_from_folder",
  "data": { "folder_path": "/path/to/files" }
}
```

Returns updated component state with process results.

## Example Usage

See `backend/interface/example_usage.py` for an example of building a Page with tabs, components, and processes.

## Build for Production

```bash
npm run build
```

This builds the React frontend to `frontend/dist/`.

## MongoDB Setup

### Local MongoDB
```bash
# Windows
mongod

# macOS/Linux
brew services start mongodb-community
```

### Remote MongoDB
Update `MONGODB_URI` in `.env` with your connection string:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name
```

## Troubleshooting

### Backend not connecting
- Check if Flask is running: `http://localhost:5000/api/health`
- Verify `MONGODB_URI` in `.env`
- Check Python version: `python --version` (should be 3.8+)

### Frontend can't reach backend
- Ensure both are running: Flask on 5000, React on 5173
- Check browser console for CORS errors
- Verify `/api` proxy in `frontend/vite.config.ts`

### MongoDB connection error
- Check if MongoDB is running
- Verify connection string in `.env`
- Test connection: `mongosh` or `mongo` CLI
