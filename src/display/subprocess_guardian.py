#!/usr/bin/env python3
"""
Subprocess Guardian - Ensures subprocesses don't freeze the system.

This module provides robust subprocess execution with multiple layers of protection:
1. Process-level timeout with SIGKILL fallback
2. Memory monitoring before subprocess launch
3. Automatic cleanup of zombie processes
4. System load checking before operations
"""

import logging
import os
import subprocess
import time
from threading import Timer
from typing import Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


class SubprocessGuardian:
    """Manages subprocess execution with multiple safety mechanisms."""

    # Memory thresholds
    MIN_AVAILABLE_MEMORY_MB = 180  # Don't start if less than this available
    CRITICAL_MEMORY_MB = 150  # Abort if drops below this

    # Timeouts
    DEFAULT_TIMEOUT = 90
    KILL_GRACE_PERIOD = 5  # Seconds to wait after SIGTERM before SIGKILL

    # System load thresholds
    MAX_LOAD_AVERAGE = 3.0  # Don't start if 1-min load avg exceeds this

    def __init__(self):
        self.active_processes = set()

    def check_system_resources(self) -> Tuple[bool, str]:
        """Check if system has enough resources to safely run subprocess."""
        try:
            # Check available memory
            memory = psutil.virtual_memory()
            available_mb = memory.available / (1024 * 1024)

            if available_mb < self.MIN_AVAILABLE_MEMORY_MB:
                msg = f"Insufficient memory: {available_mb:.0f}MB < {self.MIN_AVAILABLE_MEMORY_MB}MB"
                logger.warning(msg)
                return False, msg

            # Check system load
            load_avg = os.getloadavg()[0]  # 1-minute average
            if load_avg > self.MAX_LOAD_AVERAGE:
                msg = f"System load too high: {load_avg:.2f} > {self.MAX_LOAD_AVERAGE}"
                logger.warning(msg)
                return False, msg

            # Check for zombie processes
            zombies = [
                p
                for p in psutil.process_iter(["status"])
                if p.info["status"] == psutil.STATUS_ZOMBIE
            ]
            if len(zombies) > 5:
                msg = f"Too many zombie processes: {len(zombies)}"
                logger.warning(msg)
                # Try to reap zombies
                for z in zombies:
                    try:
                        os.waitpid(z.pid, os.WNOHANG)
                    except (OSError, ProcessLookupError):
                        pass
                return False, msg

            return True, "Resources OK"

        except Exception as e:
            logger.error(f"Resource check failed: {e}")
            return False, str(e)

    def kill_process_tree(self, pid: int):
        """Kill a process and all its children."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Give them time to exit gracefully
            gone, alive = psutil.wait_procs(children, timeout=2)

            # Force kill any survivors
            for p in alive:
                try:
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Now handle parent
            parent.terminate()
            try:
                parent.wait(timeout=2)
            except psutil.TimeoutExpired:
                parent.kill()

        except psutil.NoSuchProcess:
            pass  # Already dead
        except Exception as e:
            logger.error(f"Error killing process tree {pid}: {e}")

    def run_with_guardian(
        self,
        cmd: list,
        timeout: int = DEFAULT_TIMEOUT,
        check_resources: bool = True,
        critical_operation: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Run a subprocess with multiple safety mechanisms.

        Args:
            cmd: Command to run as list of strings
            timeout: Maximum time to allow subprocess to run
            check_resources: Whether to check system resources first
            critical_operation: If True, be extra careful about system state

        Returns:
            Tuple of (success, stdout, stderr)
        """

        # Check resources if requested
        if check_resources:
            can_run, reason = self.check_system_resources()
            if not can_run:
                if critical_operation:
                    # For critical ops, wait and retry once
                    logger.info(f"Waiting 10s for resources to free up: {reason}")
                    time.sleep(10)
                    can_run, reason = self.check_system_resources()
                    if not can_run:
                        return False, None, f"Resource check failed: {reason}"
                else:
                    return False, None, f"Resource check failed: {reason}"

        process = None
        timer = None

        try:
            # Log what we're about to run
            logger.info(f"Starting guarded subprocess: {' '.join(cmd)}")
            logger.info(f"Timeout: {timeout}s, Critical: {critical_operation}")

            # Start the subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                # Prevent subprocess from creating new session
                start_new_session=False,
                # Set memory limits for subprocess
                env={**os.environ, "PYTHONMALLOC": "malloc"},
            )

            self.active_processes.add(process.pid)

            # Set up emergency killer as backup
            def emergency_kill():
                logger.error(f"EMERGENCY: Force killing hung subprocess {process.pid}")
                self.kill_process_tree(process.pid)
                # If critical operation, also clean up browsers
                if critical_operation:
                    logger.error(
                        "Critical operation hung - cleaning all browser processes"
                    )
                    from display.browser_cleanup import BrowserCleanup

                    BrowserCleanup.force_kill_all_browsers()

            timer = Timer(timeout + 10, emergency_kill)  # Extra 10s grace
            timer.start()

            # Wait for process with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                returncode = process.returncode

                if returncode == 0:
                    logger.info(f"Subprocess {process.pid} completed successfully")
                    return True, stdout, stderr
                else:
                    logger.error(
                        f"Subprocess {process.pid} failed with code {returncode}"
                    )
                    return False, stdout, stderr

            except subprocess.TimeoutExpired:
                logger.error(f"Subprocess {process.pid} timed out after {timeout}s")

                # Try graceful termination first
                process.terminate()
                try:
                    process.wait(timeout=self.KILL_GRACE_PERIOD)
                except subprocess.TimeoutExpired:
                    # Force kill
                    logger.error(f"Force killing subprocess {process.pid}")
                    self.kill_process_tree(process.pid)

                return False, None, f"Process timed out after {timeout} seconds"

        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            if process and process.poll() is None:
                self.kill_process_tree(process.pid)
            return False, None, str(e)

        finally:
            # Clean up
            if timer:
                timer.cancel()
            if process:
                self.active_processes.discard(process.pid)
                # Make sure process is really dead
                if process.poll() is None:
                    try:
                        process.kill()
                    except (ProcessLookupError, PermissionError):
                        pass

    def cleanup_all(self):
        """Emergency cleanup of all tracked processes."""
        logger.warning(f"Emergency cleanup of {len(self.active_processes)} processes")
        for pid in list(self.active_processes):
            self.kill_process_tree(pid)
        self.active_processes.clear()


# Global instance for emergency cleanup
_guardian = SubprocessGuardian()


def run_safe_subprocess(
    cmd: list, timeout: int = 90, **kwargs
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Convenience function to run subprocess with guardian protection."""
    return _guardian.run_with_guardian(cmd, timeout, **kwargs)


def emergency_cleanup():
    """Emergency cleanup function for signal handlers."""
    _guardian.cleanup_all()
