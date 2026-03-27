"""
Software update API endpoints for checking and applying updates.

Provides GET /api/update/status to check for available updates
and POST /api/update/apply to run the upgrade script.
"""

import logging
import os
import subprocess

from flask import Blueprint, jsonify, request

from api.auth import login_required, validate_csrf_token

logger = logging.getLogger(__name__)

update_bp = Blueprint("update", __name__)

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPGRADE_SCRIPT = os.path.join(PROJECT_DIR, "scripts", "upgrade.sh")


def _git(*args, timeout=30):
    """Run a git command in the project directory and return stdout."""
    result = subprocess.run(
        ["/usr/bin/git", "-C", PROJECT_DIR] + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result


@update_bp.route("/api/update/status", methods=["GET"])
def update_status():
    """Check for available updates by comparing HEAD to origin/main."""
    try:
        # Fetch latest from origin (skip if caller just wants cached status)
        skip_fetch = request.args.get("cached") == "true"
        if not skip_fetch:
            fetch_result = _git("fetch", "origin", timeout=30)
            if fetch_result.returncode != 0:
                logger.warning(
                    "git fetch failed: %s", fetch_result.stderr.strip()
                )

        # Get current commit
        head = _git("rev-parse", "--short", "HEAD")
        if head.returncode != 0:
            return jsonify({"error": "Failed to get current commit"}), 500
        current_commit = head.stdout.strip()

        # Get current commit date
        date_result = _git("log", "-1", "--format=%ci", "HEAD")
        current_date = ""
        if date_result.returncode == 0:
            # Parse "2026-03-26 10:30:00 -0400" to "Mar 26, 2026"
            raw = date_result.stdout.strip()
            if raw:
                from datetime import datetime

                try:
                    dt = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
                    current_date = dt.strftime("%b %d, %Y")
                except ValueError:
                    current_date = raw[:10]

        # Count commits behind origin/main
        behind = _git("rev-list", "--count", "HEAD..origin/main")
        commits_behind = 0
        if behind.returncode == 0:
            commits_behind = int(behind.stdout.strip())

        # Get latest commit on origin/main
        origin_head = _git("rev-parse", "--short", "origin/main")
        latest_commit = ""
        if origin_head.returncode == 0:
            latest_commit = origin_head.stdout.strip()

        return jsonify(
            {
                "update_available": commits_behind > 0,
                "current_commit": current_commit,
                "current_date": current_date,
                "latest_commit": latest_commit,
                "commits_behind": commits_behind,
            }
        )

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Git command timed out"}), 504
    except Exception as e:
        logger.error("Error checking update status: %s", e)
        return jsonify({"error": str(e)}), 500


@update_bp.route("/api/update/apply", methods=["POST"])
@login_required
def apply_update():
    """Run the upgrade script to pull latest code and restart services."""
    try:
        if not validate_csrf_token():
            return jsonify({"error": "Invalid CSRF token"}), 403

        if not os.path.isfile(UPGRADE_SCRIPT):
            return jsonify({"error": "Upgrade script not found"}), 404

        # Capture current commit before upgrade
        head_before = _git("rev-parse", "--short", "HEAD")
        old_version = head_before.stdout.strip() if head_before.returncode == 0 else ""

        logger.info("Starting software update from %s", old_version)

        # Run upgrade script with extended timeout (deps + playwright can be slow)
        result = subprocess.run(
            ["/bin/bash", UPGRADE_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=PROJECT_DIR,
        )

        # Capture new commit after upgrade
        head_after = _git("rev-parse", "--short", "HEAD")
        new_version = head_after.stdout.strip() if head_after.returncode == 0 else ""

        if result.returncode == 0:
            logger.info("Software update complete: %s -> %s", old_version, new_version)
            return jsonify(
                {
                    "status": "ok",
                    "output": result.stdout,
                    "old_version": old_version,
                    "new_version": new_version,
                }
            )
        else:
            logger.error("Upgrade script failed: %s", result.stderr)
            return (
                jsonify(
                    {
                        "status": "error",
                        "output": result.stdout,
                        "error": result.stderr or "Upgrade script failed",
                    }
                ),
                500,
            )

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Upgrade timed out (5 min limit)"}), 504
    except Exception as e:
        logger.error("Error applying update: %s", e)
        return jsonify({"error": str(e)}), 500
