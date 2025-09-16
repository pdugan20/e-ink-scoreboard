"""
Enhanced browser cleanup and memory recovery for Pi Zero.
"""

import logging
import subprocess
import time

import psutil

logger = logging.getLogger(__name__)


class BrowserCleanup:
    """Aggressive browser cleanup for memory-constrained environments."""

    @staticmethod
    def force_kill_all_browsers():
        """Force kill ALL browser processes immediately."""
        killed_count = 0
        try:
            # Kill Playwright node processes specifically
            for process_name in ["chromium", "chrome", "playwright", "node"]:
                try:
                    # Kill processes containing playwright in path
                    if process_name == "node":
                        subprocess.run(
                            ["pkill", "-9", "-f", "playwright/driver/node"],
                            capture_output=True,
                            timeout=5,
                        )
                    else:
                        subprocess.run(
                            ["pkill", "-9", "-f", process_name],
                            capture_output=True,
                            timeout=5,
                        )
                    killed_count += 1
                except Exception:
                    pass

            # Also kill by process iteration as backup
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    name = proc.info["name"].lower() if proc.info["name"] else ""
                    cmdline = " ".join(proc.info["cmdline"] or []).lower()

                    # Check for browser processes AND playwright node processes
                    is_browser = any(
                        b in name or b in cmdline
                        for b in ["chromium", "chrome", "playwright"]
                    )
                    is_playwright_node = "node" in name and "playwright" in cmdline

                    if is_browser or is_playwright_node:
                        proc.kill()  # Direct SIGKILL
                        killed_count += 1
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

            if killed_count > 0:
                logger.info(f"Force killed {killed_count} browser processes")
                time.sleep(1)  # Let OS reclaim memory

        except Exception as e:
            logger.error(f"Error in force kill: {e}")

        return killed_count

    @staticmethod
    def emergency_memory_recovery():
        """Emergency memory recovery when critically low."""
        try:
            # 1. Kill all browsers
            BrowserCleanup.force_kill_all_browsers()

            # 2. Clear page cache
            try:
                subprocess.run(["sync"], timeout=5)
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("1")  # Clear page cache
            except Exception:
                pass  # May not have permissions

            # 3. Force garbage collection
            import gc

            gc.collect()

            # 4. Kill zombie processes
            try:
                subprocess.run(
                    ["killall", "-9", "defunct"], capture_output=True, timeout=5
                )
            except Exception:
                pass

            # Check recovered memory
            mem = psutil.virtual_memory()
            available_mb = mem.available / 1024 / 1024
            logger.info(
                f"Emergency recovery complete. Available memory: {available_mb:.0f}MB"
            )

            return available_mb

        except Exception as e:
            logger.error(f"Emergency recovery failed: {e}")
            return 0

    @staticmethod
    def monitor_and_kill_timeout(pid, timeout_seconds=30):
        """Monitor a process and kill if it exceeds timeout."""
        try:
            proc = psutil.Process(pid)
            proc.wait(timeout=timeout_seconds)
        except psutil.TimeoutExpired:
            logger.warning(
                f"Process {pid} exceeded {timeout_seconds}s timeout, killing..."
            )
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process already gone
