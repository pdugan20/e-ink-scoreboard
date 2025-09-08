"""
Static file serving routes for development server.
"""

import os

from flask import send_from_directory


def setup_static_routes(app):
    """Setup static file serving routes"""

    @app.route("/static/<path:filename>")
    def static_files(filename):
        """Serve static files"""
        # Get absolute path relative to src directory
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_path = os.path.join(src_dir, "static")
        return send_from_directory(static_path, filename)

    @app.route("/static/test-data/<filename>")
    def test_data_files(filename):
        """Serve test data files"""
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_data_path = os.path.join(src_dir, "test-data")
        return send_from_directory(test_data_path, filename)

    @app.route("/assets/<path:filename>")
    def asset_files(filename):
        """Serve asset files (logos, etc.)"""
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        asset_path = os.path.join(src_dir, "assets")
        return send_from_directory(asset_path, filename)

    @app.route("/src/config/<filename>")
    def config_files(filename):
        """Serve config files"""
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(src_dir, "config")
        return send_from_directory(config_path, filename)
