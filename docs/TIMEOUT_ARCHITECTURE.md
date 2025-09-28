# Screenshot Timeout Architecture

## Overview

The screenshot system uses a multi-layered timeout strategy to ensure reliable operation on resource-constrained devices like the Raspberry Pi Zero while preventing system hangs and zombie processes.

## Timeout Hierarchy

### 1. Parent Process (subprocess_guardian.py)

- **Timeout: 150 seconds**
- **Role**: Ultimate safety net
- **Location**: `src/display/subprocess_guardian.py`
- **Behavior**:
  - Launches the screenshot worker subprocess
  - Monitors execution time
  - Force kills the subprocess if it exceeds 150 seconds
  - Has an emergency killer set for timeout + 10 seconds (160s total)

### 2. Worker Process (screenshot_worker.py)

- **Timeout: 145 seconds** (5 seconds less than parent)
- **Role**: Graceful shutdown before parent force-kill
- **Location**: `src/display/screenshot_worker.py`
- **Behavior**:
  - Sets internal alarm for 145 seconds
  - Exits cleanly if timeout is reached
  - Does NOT force-kill browsers (prevents zombie processes)
  - Allows parent to handle cleanup properly

### 3. Browser Operations

These timeouts control individual browser operations within the worker:

#### Page Load Timeout

- **Timeout: 60 seconds**
- **Purpose**: Maximum time to load the display page
- **Usage**: `page.goto(..., timeout=60000)`

#### Default Page Timeout

- **Timeout: 30 seconds**
- **Purpose**: Default for all page operations
- **Usage**: `page.set_default_timeout(30000)`

#### Content Detection

- **Timeout: 20 seconds**
- **Purpose**: Wait for game cards to appear
- **Usage**: `page.wait_for_selector(..., timeout=20000)`

#### JavaScript Fallback

- **Timeout: 10 seconds**
- **Purpose**: Additional wait if content not immediately found
- **Usage**: `page.wait_for_timeout(10000)`

## Why This Architecture?

### Problem 1: Slow Hardware

The Raspberry Pi Zero has limited CPU and memory, causing:

- Slow browser startup (10-20 seconds)
- Slow page rendering (20-40 seconds)
- Slow JavaScript execution

**Solution**: Generous timeouts (150s total) give the Pi Zero enough time to complete operations.

### Problem 2: Zombie Processes

When the worker times out and force-kills browsers, it can leave zombie processes that:

- Consume memory
- Increase system load
- Prevent future screenshots

**Solution**: Worker exits cleanly without force-killing. Parent process handles cleanup properly.

### Problem 3: System Hangs

Without timeouts, a hung browser could freeze the entire system.

**Solution**: Multiple timeout layers ensure something will eventually kill a hung process:

1. Worker timeout (145s) - clean exit
2. Parent timeout (150s) - force kill
3. Emergency timeout (160s) - nuclear option

## Timeout Flow Example

```
Time    Event
----    -----
0s      Parent launches worker subprocess
0s      Worker sets 145s alarm
1s      Browser launches
5s      Browser navigates to page
25s     Page starts loading (slow Pi Zero)
45s     Page finishes loading
50s     Screenshot taken
52s     Browser closes
53s     Worker exits successfully
        (Parent timeout never triggered)
```

## Failed Scenario Example

```
Time    Event
----    -----
0s      Parent launches worker subprocess
0s      Worker sets 145s alarm
1s      Browser launches
5s      Browser navigates to page
25s     Page starts loading
145s    WORKER TIMEOUT - clean exit
146s    Parent detects subprocess exit with error
150s    Parent timeout (would force-kill if still running)
        Parent initiates retry
```

## Configuration Notes

### For Raspberry Pi Zero (512MB RAM)

- Use current settings (150s/145s)
- Ensures enough time for slow operations
- Prevents premature timeouts

### For Raspberry Pi 3/4 (1GB+ RAM)

- Could reduce to 90s/85s
- Faster hardware needs less time
- Quicker failure detection

### For Development (Desktop)

- Could reduce to 30s/25s
- Fast hardware for quick iteration
- Rapid timeout for debugging

## Memory and Load Thresholds

The subprocess guardian also checks system resources before starting:

- **Minimum Memory**: 100MB available
- **Maximum Load**: 5.0 (1-minute average)

These prevent screenshot attempts when the system is under stress.

## Retry Logic

If a screenshot fails:

1. First retry after 10 seconds
2. Second retry after 10 seconds
3. Third retry after 10 seconds
4. After 3 failures, waits until next refresh interval (6 minutes)

## Debugging Timeout Issues

### Symptoms of Timeout Problems

1. **"Worker process timeout" errors**
   - Worker is timing out before completion
   - Increase worker timeout (but keep less than parent)

2. **"Force killed 4 browser processes" repeatedly**
   - Browsers not closing properly
   - Check browser cleanup logic

3. **"Subprocess timed out after X seconds"**
   - Parent killing worker
   - Increase parent timeout

### Log Locations

- Main log: `~/logs/eink_display.log`
- System log: `sudo journalctl -u sports-display.service -f`

### Monitoring Commands

```bash
# Watch for timeout errors
tail -f ~/logs/eink_display.log | grep -i timeout

# Check browser processes
ps aux | grep -E 'chromium|playwright'

# Monitor system load
top
```

## Future Improvements

1. **Adaptive Timeouts**: Adjust based on historical performance
2. **Progressive Loading**: Take screenshot of partial content if full page times out
3. **Browser Reuse**: Keep browser instance alive between screenshots (with periodic restarts)
4. **Timeout Telemetry**: Log timeout margins to optimize values

## Summary

The timeout architecture balances:

- **Reliability**: Multiple safety nets prevent hangs
- **Performance**: Generous timeouts for slow hardware
- **Cleanliness**: Proper cleanup prevents zombie processes
- **Observability**: Clear logging for debugging

The key principle: Give slow hardware enough time to succeed, but always have a way to recover from failure.
