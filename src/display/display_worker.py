#!/usr/bin/env python3
"""
Subprocess worker for updating the e-ink display in isolation.
This runs in a separate process that can be killed if SPI I/O hangs,
preventing the main process from freezing on kernel-level SPI lockups.
"""

import json
import logging
import os
import signal
import sys

# Add parent directory to path so we can import display module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging - simple format since parent adds [WORKER] prefix
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

logger.info("Display worker process started")


def timeout_handler(signum, frame):
    """Handle timeout by exiting cleanly."""
    logger.error("Display worker timeout - exiting")
    sys.exit(1)


def update_display(config_json):
    """Update the e-ink display in an isolated process."""
    logger.info("Parsing config")
    config = json.loads(config_json)

    screenshot_path = config["screenshot_path"]
    apply_dithering = config.get("apply_dithering", False)
    saturation = config.get("dither_saturation", 0.8)

    # Set internal timeout (85 seconds - less than parent's 90s)
    # This ensures clean exit before parent kills us
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(85)
    logger.info("Timeout alarm set for 85 seconds")

    try:
        from PIL import Image

        logger.info(f"Opening image: {screenshot_path}")
        img = Image.open(screenshot_path)

        # Initialize Inky display
        logger.info("Initializing Inky display")
        try:
            from inky.auto import auto  # type: ignore

            inky = auto()
            logger.info(f"Auto-detected display: {inky.width}x{inky.height}")
        except Exception as e:
            logger.warning(
                f"Auto-detection failed ({e}), trying Inky Impression 7.3..."
            )
            from inky import Inky_Impressions_7  # type: ignore

            inky = Inky_Impressions_7()
            logger.info(f"Initialized Impression 7.3: {inky.width}x{inky.height}")

        # Resize if needed
        target_size = (inky.width, inky.height)
        if img.size != target_size:
            img = img.resize(target_size, Image.LANCZOS)
            logger.info(f"Resized image to {target_size}")

        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Apply dithering using Inky's palette
        if apply_dithering:
            img = _apply_dithering(img, inky, saturation)

        # Set image and push to display (this is the blocking SPI call)
        logger.info("Sending image to e-ink display...")
        inky.set_image(img)
        inky.show()

        signal.alarm(0)
        logger.info("Display update complete")
        return 0

    except Exception as e:
        logger.error(f"Display update failed: {e}")
        signal.alarm(0)
        return 1


def _apply_dithering(img, inky, saturation):
    """Apply e-ink dithering using Inky's palette."""
    from PIL import Image

    try:
        palette = inky._palette_blend(saturation, dtype="uint24")

        # Try hitherdither for better quality
        try:
            import hitherdither

            hither_palette = hitherdither.palette.Palette(palette)
            dithered = hitherdither.ordered.bayer.bayer_dithering(
                img, hither_palette, thresholds=[64, 64, 64], order=8
            )
            logger.info(f"Applied Bayer dithering with {len(palette)} colors")
            return dithered.convert("RGB")
        except ImportError:
            # Fallback to Pillow quantization
            dithered = img.quantize(colors=6, dither=Image.Dither.FLOYDSTEINBERG)
            logger.info("Applied Floyd-Steinberg dithering (Pillow fallback)")
            return dithered.convert("RGB")

    except Exception as e:
        logger.warning(f"Dithering failed, using original image: {e}")
        return img


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: display_worker.py <config_json>", file=sys.stderr)
        sys.exit(1)

    sys.exit(update_display(sys.argv[1]))
