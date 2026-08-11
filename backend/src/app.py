import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    from datetime import datetime
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/hello', methods=['GET'])
def hello():
    """Hello world endpoint"""
    return jsonify({
        'message': 'Hello from the backend!',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n{'='*50}")
    print(f"Starting Flask on http://localhost:{port}")
    print(f"{'='*50}\n")
    app.run(host='localhost', port=port, debug=True)
