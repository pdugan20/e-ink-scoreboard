"""
WiFi management API endpoints.

Provides network scanning, connection status, and WiFi switching
via nmcli (NetworkManager CLI).
"""

import logging
import re
import subprocess

from flask import Blueprint, jsonify, request

from api.auth import login_required, validate_csrf_token

logger = logging.getLogger(__name__)

wifi_bp = Blueprint("wifi", __name__)


def _nmcli_available():
    """Check if nmcli is installed."""
    try:
        subprocess.run(
            ["nmcli", "--version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except FileNotFoundError:
        return False


@wifi_bp.route("/api/wifi/status", methods=["GET"])
def wifi_status():
    """Return current WiFi connection info."""
    try:
        if not _nmcli_available():
            return jsonify({"error": "nmcli not available"}), 503

        # Get active WiFi connection
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "con", "show", "--active"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        connections = []
        for line in result.stdout.strip().splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[2] in ("802-11-wireless", "wifi"):
                connections.append({"name": parts[0], "device": parts[1]})

        # Get IP address
        ip_result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        ip_address = (
            ip_result.stdout.strip().split()[0] if ip_result.stdout.strip() else None
        )

        return jsonify(
            {
                "connected": len(connections) > 0,
                "network": connections[0]["name"] if connections else None,
                "device": connections[0]["device"] if connections else None,
                "ip_address": ip_address,
            }
        )

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Command timed out"}), 504
    except Exception as e:
        logger.error(f"Error getting WiFi status: {e}")
        return jsonify({"error": str(e)}), 500


@wifi_bp.route("/api/wifi/networks", methods=["GET"])
def wifi_networks():
    """Scan and return available WiFi networks."""
    try:
        if not _nmcli_available():
            return jsonify({"error": "nmcli not available"}), 503

        # Rescan first
        subprocess.run(
            ["nmcli", "dev", "wifi", "rescan"],
            capture_output=True,
            timeout=15,
        )

        # List networks
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "dev", "wifi", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        networks = []
        seen_ssids = set()
        for line in result.stdout.strip().splitlines():
            parts = line.split(":")
            if len(parts) >= 4:
                ssid = parts[0].strip()
                if not ssid or ssid in seen_ssids:
                    continue
                seen_ssids.add(ssid)
                networks.append(
                    {
                        "ssid": ssid,
                        "signal": int(parts[1]) if parts[1].isdigit() else 0,
                        "security": parts[2] if parts[2] else "Open",
                        "active": parts[3] == "*",
                    }
                )

        # Sort by signal strength descending
        networks.sort(key=lambda n: n["signal"], reverse=True)

        return jsonify({"networks": networks})

    except subprocess.TimeoutExpired:
        return jsonify({"error": "WiFi scan timed out"}), 504
    except Exception as e:
        logger.error(f"Error scanning WiFi: {e}")
        return jsonify({"error": str(e)}), 500


# Validate SSID: printable characters, reasonable length
_SSID_PATTERN = re.compile(r"^[\x20-\x7E]{1,32}$")


@wifi_bp.route("/api/wifi/connect", methods=["POST"])
@login_required
def wifi_connect():
    """Connect to a WiFi network."""
    try:
        if not validate_csrf_token():
            return jsonify({"error": "Invalid CSRF token"}), 403

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        ssid = data.get("ssid", "").strip()
        password = data.get("password", "")

        if not ssid:
            return jsonify({"error": "SSID is required"}), 400

        if not _SSID_PATTERN.match(ssid):
            return jsonify({"error": "Invalid SSID"}), 400

        if not _nmcli_available():
            return jsonify({"error": "nmcli not available"}), 503

        logger.info(f"Connecting to WiFi network: {ssid}")

        # Build command -- password is passed as an argument (not shell-expanded)
        cmd = ["sudo", "nmcli", "dev", "wifi", "connect", ssid]
        if password:
            cmd.extend(["password", password])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return jsonify({"status": "ok", "ssid": ssid})
        else:
            error_msg = (
                result.stderr.strip() or result.stdout.strip() or "Connection failed"
            )
            logger.error(f"WiFi connection failed: {error_msg}")
            return jsonify({"error": error_msg}), 500

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Connection timed out"}), 504
    except Exception as e:
        logger.error(f"Error connecting to WiFi: {e}")
        return jsonify({"error": str(e)}), 500
