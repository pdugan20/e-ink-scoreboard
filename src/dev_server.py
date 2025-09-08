#!/usr/bin/env python3
"""
Development server with hot reloading for testing E-Ink Scoreboard
Run with: python dev_server.py
Then open: http://localhost:5000
"""

import glob
import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS

# Import our modular API components
from api.scores_api import fetch_mlb_games, fetch_nfl_games
from api.screensaver_api import get_screensaver_data
from api.static_files import setup_static_routes

app = Flask(__name__)
CORS(app)  # Enable CORS for development

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track file modification times for hot reload
file_timestamps = {}


def get_file_timestamp(filepath):
    try:
        return os.path.getmtime(filepath)
    except OSError:
        return 0


def get_files_to_watch():
    """Get all files to watch using glob patterns"""
    patterns = [
        "src/preview.html",
        "src/static/styles/*.css",
        "src/static/js/*.js",
        "src/static/js/constants/*.js",
    ]

    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))

    return files


def check_files_changed():
    """Check if any watched files have changed"""
    files_to_watch = get_files_to_watch()
    changed = False

    for filepath in files_to_watch:
        if os.path.exists(filepath):
            current_time = get_file_timestamp(filepath)
            last_time = file_timestamps.get(filepath, 0)

            if current_time > last_time:
                file_timestamps[filepath] = current_time
                changed = True
                logger.info(f"File changed: {filepath}")

    return changed


@app.route("/")
def index():
    """Serve the preview HTML with hot reload script injected"""
    try:
        with open("src/preview.html") as f:
            html_content = f.read()

        # Inject hot reload script
        hot_reload_script = """
        <script>
        // Hot reload functionality
        let reloadIndicator = null;

        function showReloadIndicator(message, isError = false) {
            if (!reloadIndicator) {
                reloadIndicator = document.createElement('div');
                reloadIndicator.className = 'reload-indicator';
                document.body.appendChild(reloadIndicator);
            }
            reloadIndicator.textContent = message;
            reloadIndicator.className = 'reload-indicator show' + (isError ? ' error' : '');
            setTimeout(() => {
                if (reloadIndicator) reloadIndicator.classList.remove('show');
            }, 2000);
        }

        function checkForUpdates() {
            fetch('/check-updates')
                .then(response => response.json())
                .then(data => {
                    if (data.changed) {
                        showReloadIndicator('Reloading...', false);
                        setTimeout(() => location.reload(), 500);
                    }
                })
                .catch(err => {
                    console.log('Hot reload check failed:', err);
                });
        }

        // Check for updates every 1 second
        setInterval(checkForUpdates, 1000);

        // Show indicator on initial load
        document.addEventListener('DOMContentLoaded', () => {
            showReloadIndicator('Hot reload active', false);
        });
        </script>
        """

        # Insert before closing </body> tag
        html_content = html_content.replace("</body>", hot_reload_script + "</body>")

        return html_content
    except FileNotFoundError:
        return "src/preview.html not found", 404


@app.route("/display")
def display():
    """Serve clean display HTML for screenshots (no dev UI)"""
    try:
        with open("src/display.html") as f:
            return f.read()
    except FileNotFoundError:
        return "Display template not found", 404


@app.route("/check-updates")
def check_updates():
    """Endpoint to check if files have changed"""
    changed = check_files_changed()
    return jsonify({"changed": changed})


@app.route("/api/scores/<league>")
def get_scores(league):
    """Fetch live scores for the specified league"""
    try:
        if league == "MLB":
            return jsonify(fetch_mlb_games())
        elif league == "NFL":
            return jsonify(fetch_nfl_games())
        else:
            return jsonify({"error": "Invalid league"}), 400
    except Exception as e:
        logger.error(f"Error fetching scores: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/screensaver/<league>")
def get_screensaver(league):
    """Fetch screensaver article for favorite team in specified league"""
    try:
        article_data = get_screensaver_data(league)
        return jsonify(article_data)
    except Exception as e:
        logger.error(f"Error fetching screensaver data for {league}: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="E-Ink Scoreboard Development Server")
    parser.add_argument(
        "--port", type=int, default=5001, help="Port to run the server on"
    )
    args = parser.parse_args()

    # Setup static file routes
    setup_static_routes(app)

    # Initialize file timestamps
    for filepath in get_files_to_watch():
        if os.path.exists(filepath):
            file_timestamps[filepath] = get_file_timestamp(filepath)

    print("\nE-Ink Scoreboard Dev Server (Hot Reload)")
    print("=" * 50)
    print(f"Open in browser: http://localhost:{args.port}")
    print("API endpoints:")
    print(f"  - http://localhost:{args.port}/api/scores/MLB")
    print(f"  - http://localhost:{args.port}/api/scores/NFL")
    print(f"  - http://localhost:{args.port}/api/screensaver/MLB")
    print("\n✨ Hot reload enabled:")
    print(
        "  - Edit src/preview.html, CSS in src/static/styles/, or JS in src/static/js/"
    )
    print("  - Browser will auto-refresh on save")
    print("=" * 50)
    print("\nPress Ctrl+C to stop\n")

    # Suppress werkzeug INFO logs for check-updates endpoint only
    import logging

    werkzeug_logger = logging.getLogger("werkzeug")

    class SuppressCheckUpdates(logging.Filter):
        def filter(self, record):
            return "GET /check-updates HTTP" not in record.getMessage()

    werkzeug_logger.addFilter(SuppressCheckUpdates())

    app.run(
        debug=True, port=args.port, use_reloader=False
    )  # Disable Flask's reloader since we have our own
