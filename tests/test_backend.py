"""
Backend tests for Flask API endpoints
"""
import sys
import os
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from app import app


def test_health_endpoint():
    """Test the /api/health endpoint"""
    with app.test_client() as client:
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


def test_hello_endpoint():
    """Test the /api/hello endpoint"""
    with app.test_client() as client:
        response = client.get('/api/hello')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['message'] == 'Hello from the backend!'
        assert 'version' in data


def test_cors_headers():
    """Test that CORS headers are present"""
    with app.test_client() as client:
        response = client.get('/api/health')
        
        # CORS should allow any origin in development
        assert 'Access-Control-Allow-Origin' in response.headers


if __name__ == '__main__':
    # Run tests manually
    print("Running backend tests...")
    
    try:
        test_health_endpoint()
        print("✓ test_health_endpoint passed")
    except AssertionError as e:
        print(f"✗ test_health_endpoint failed: {e}")
    
    try:
        test_hello_endpoint()
        print("✓ test_hello_endpoint passed")
    except AssertionError as e:
        print(f"✗ test_hello_endpoint failed: {e}")
    
    try:
        test_cors_headers()
        print("✓ test_cors_headers passed")
    except AssertionError as e:
        print(f"✗ test_cors_headers failed: {e}")
    
    print("\nDone!")
