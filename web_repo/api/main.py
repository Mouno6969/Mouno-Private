import os
from flask import send_from_directory
from app import app as api_app

frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "build"))

# Serve React static files
@api_app.route('/', defaults={'path': ''})
@api_app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(frontend_folder, path)):
        return send_from_directory(frontend_folder, path)

    if "." not in path:
        return send_from_directory(frontend_folder, 'index.html')

    return f"Not Found: {path}", 404

if __name__ == '__main__':
    api_app.run(host='0.0.0.0', port=5001)
