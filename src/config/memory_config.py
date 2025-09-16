"""
Memory configuration constants for Pi Zero with 400MB total RAM.
"""

# Memory thresholds in MB (adjusted for Pi Zero W with 512MB RAM)
MEMORY_RECOMMENDED_MB = 120  # Ideal memory for safe operation
MEMORY_MINIMUM_MB = 80  # Absolute minimum with emergency recovery
MEMORY_STARTUP_WAIT_MB = 100  # Wait for this much memory on startup

# Browser memory limits
BROWSER_JS_HEAP_MB = 96  # JavaScript heap size limit (reduced for Pi Zero)
