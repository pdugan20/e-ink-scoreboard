"""
Display preview API endpoint.

Allows pushing a preview image to the e-ink display from the web settings panel.
Supports live scores, test data, and screensaver modes with auto-revert.
"""

import logging
import os
import subprocess
import sys
import threading

from flask import Blueprint, jsonify, request

from api.auth import login_required, validate_csrf_token

logger = logging.getLogger(__name__)

display_bp = Blueprint("display", __name__)

# Track active preview for cancellation
_active_timer = None
_timer_lock = threading.Lock()

VALID_MODES = {"live", "test", "screensaver"}


@display_bp.route("/api/display/preview", methods=["POST"])
@login_required
def preview_display():
    """Push a preview image to the e-ink display with auto-revert."""
    try:
        if not validate_csrf_token():
            return jsonify({"error": "Invalid CSRF token"}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        mode = data.get("mode", "live")
        if mode not in VALID_MODES:
            return (
                jsonify(
                    {
                        "error": f"Invalid mode: {mode}. Must be one of: {sorted(VALID_MODES)}"
                    }
                ),
                400,
            )

        revert_delay = min(max(int(data.get("revert_in", 60)), 30), 300)

        # Build the display URL for this mode
        if mode == "live":
            url = "http://localhost:5001/display"
        else:
            url = f"http://localhost:5001/display?mode={mode}"

        # Run eink_display.py as subprocess (non-blocking)
        project_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        display_script = os.path.join(project_dir, "src", "eink_display.py")
        config_path = os.path.join(project_dir, "src", "eink_config.json")

        cmd = [
            sys.executable,
            display_script,
            "--once",
            "--force",
            "--config",
            config_path,
            "--url",
            url,
        ]

        logger.info(f"Starting display preview: mode={mode}, revert_in={revert_delay}s")
        subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Schedule auto-revert
        _schedule_revert(revert_delay, project_dir, display_script, config_path)

        return jsonify({"status": "ok", "mode": mode, "revert_in": revert_delay})

    except Exception as e:
        logger.error(f"Error starting display preview: {e}")
        return jsonify({"error": str(e)}), 500


def _schedule_revert(delay, project_dir, display_script, config_path):
    """Schedule a normal display refresh to revert the preview."""
    global _active_timer

    with _timer_lock:
        # Cancel any existing revert timer
        if _active_timer is not None:
            _active_timer.cancel()
            logger.info("Cancelled previous revert timer")

        def _run_revert():
            logger.info("Reverting display to normal refresh")
            cmd = [
                sys.executable,
                display_script,
                "--once",
                "--force",
                "--config",
                config_path,
            ]
            try:
                subprocess.Popen(
                    cmd,
                    cwd=project_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                logger.error(f"Error reverting display: {e}")

        _active_timer = threading.Timer(delay, _run_revert)
        _active_timer.daemon = True
        _active_timer.start()
        logger.info(f"Revert scheduled in {delay}s")
