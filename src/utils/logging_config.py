"""
Comprehensive logging configuration for e-ink display system with resource monitoring.
"""

import logging
import logging.handlers
import os
from datetime import datetime

import psutil


class ResourceMonitoringFormatter(logging.Formatter):
    """Custom formatter that includes system resource information."""

    def format(self, record):
        # Add system resource info to log record
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            record.memory_rss = f"{memory_info.rss / 1024 / 1024:.1f}MB"
            record.memory_percent = f"{process.memory_percent():.1f}%"
            record.cpu_percent = f"{process.cpu_percent():.1f}%"

            # System-wide memory
            sys_memory = psutil.virtual_memory()
            record.sys_memory_available = f"{sys_memory.available / 1024 / 1024:.0f}MB"
            record.sys_memory_percent = f"{sys_memory.percent:.1f}%"

        except Exception:
            # Fallback if psutil fails
            record.memory_rss = "N/A"
            record.memory_percent = "N/A"
            record.cpu_percent = "N/A"
            record.sys_memory_available = "N/A"
            record.sys_memory_percent = "N/A"

        return super().format(record)


def count_browser_processes():
    """Count running browser processes that might be hanging."""
    try:
        # Look for chromium, chrome, and playwright processes
        browser_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = proc.info["name"].lower()
                cmdline = " ".join(proc.info["cmdline"] or []).lower()

                if any(
                    browser in name for browser in ["chromium", "chrome", "playwright"]
                ) or any(
                    browser in cmdline
                    for browser in ["chromium", "chrome", "playwright"]
                ):
                    browser_processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "cmdline": " ".join(proc.info["cmdline"] or [])[
                                :100
                            ],  # Truncate long cmdlines
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return browser_processes
    except Exception as e:
        return [f"Error counting processes: {e}"]


def setup_logging(config):
    """Setup comprehensive logging with rotation and resource monitoring."""
    logging_config = config.get("logging", {})

    # Create logs directory if it doesn't exist
    log_file = logging_config.get("log_file", "/tmp/eink_display.log")
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)

    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set logging level
    level = getattr(logging, logging_config.get("level", "INFO").upper())
    root_logger.setLevel(level)

    # Create rotating file handler
    max_bytes = (
        logging_config.get("max_log_size_mb", 50) * 1024 * 1024
    )  # Convert MB to bytes
    backup_count = logging_config.get("backup_count", 5)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )

    # Create console handler
    console_handler = logging.StreamHandler()

    # Create formatters
    detailed_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "MEM: %(memory_rss)s (%(memory_percent)s) - "
        "CPU: %(cpu_percent)s - "
        "SYS_MEM: %(sys_memory_available)s free (%(sys_memory_percent)s used) - "
        "%(message)s"
    )

    simple_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Apply formatters
    if logging_config.get("log_memory_usage", True):
        file_formatter = ResourceMonitoringFormatter(detailed_format)
        console_formatter = ResourceMonitoringFormatter(simple_format)
    else:
        file_formatter = logging.Formatter(simple_format)
        console_formatter = logging.Formatter(simple_format)

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"EINK DISPLAY SYSTEM STARTING - {datetime.now()}")
    logger.info(f"Logging to: {log_file}")
    logger.info(f"Log level: {logging_config.get('level', 'INFO')}")
    logger.info(f"PID: {os.getpid()}")

    # Log initial system state
    try:
        sys_info = {
            "total_memory": f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB",
            "cpu_count": psutil.cpu_count(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
        logger.info(f"System info: {sys_info}")

        if logging_config.get("log_browser_processes", True):
            browser_procs = count_browser_processes()
            logger.info(f"Initial browser processes: {len(browser_procs)} found")
            for proc in browser_procs[:5]:  # Log first 5 to avoid spam
                logger.debug(f"  Browser process: {proc}")

    except Exception as e:
        logger.warning(f"Could not log system info: {e}")

    logger.info("=" * 80)

    return logger


def log_resource_snapshot(logger, context=""):
    """Log a detailed snapshot of current system resources."""
    try:
        process = psutil.Process()
        sys_memory = psutil.virtual_memory()

        snapshot = {
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "process_memory_rss": f"{process.memory_info().rss / 1024 / 1024:.1f}MB",
            "process_memory_percent": f"{process.memory_percent():.1f}%",
            "process_cpu_percent": f"{process.cpu_percent():.1f}%",
            "system_memory_available": f"{sys_memory.available / 1024 / 1024:.0f}MB",
            "system_memory_percent": f"{sys_memory.percent:.1f}%",
            "system_load_avg": (
                f"{os.getloadavg()}" if hasattr(os, "getloadavg") else "N/A"
            ),
        }

        logger.info(f"RESOURCE_SNAPSHOT: {snapshot}")

        # Log browser processes if requested
        browser_procs = count_browser_processes()
        if browser_procs:
            logger.info(f"Browser processes ({len(browser_procs)}): {browser_procs}")

    except Exception as e:
        logger.warning(f"Failed to log resource snapshot: {e}")


def log_before_screenshot(logger):
    """Log system state before taking screenshot."""
    log_resource_snapshot(logger, "BEFORE_SCREENSHOT")


def log_after_screenshot(logger, success=True):
    """Log system state after taking screenshot."""
    context = "AFTER_SCREENSHOT_SUCCESS" if success else "AFTER_SCREENSHOT_FAILURE"
    log_resource_snapshot(logger, context)


def log_browser_cleanup(logger, cleanup_details=None):
    """Log browser process cleanup details."""
    log_resource_snapshot(logger, "BROWSER_CLEANUP")
    if cleanup_details:
        logger.info(f"Browser cleanup details: {cleanup_details}")
