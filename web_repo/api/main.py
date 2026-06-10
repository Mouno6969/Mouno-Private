import os
from flask import send_from_directory, jsonify
from app import app as api_app, socketio

frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "build"))

# Serve React static files
@api_app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])
@api_app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def serve(path):
    # Never serve the SPA for API calls: return a clear JSON 404 instead so
    # the frontend can show a meaningful error instead of silently failing.
    if path.startswith('api/') or path == 'api':
        return jsonify({'message': f'API endpoint not found: /{path}'}), 404

    if path != "" and os.path.exists(os.path.join(frontend_folder, path)):
        return send_from_directory(frontend_folder, path)

    if "." not in path:
        return send_from_directory(frontend_folder, 'index.html')

    return f"Not Found: {path}", 404

if __name__ == '__main__':
    socketio.run(api_app, host='0.0.0.0', port=5001)
