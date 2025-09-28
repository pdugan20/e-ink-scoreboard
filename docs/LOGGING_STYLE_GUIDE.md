# Logging Style Guide

## General Principles

- Be concise but informative
- Use consistent formatting
- Include relevant context without being verbose

## Message Format Standards

### Action States

#### Starting an action

```python
logger.info("Starting display refresh")  # No "..." at the end
```

#### Action completed

```python
logger.info("Display refresh completed")  # Simple past tense
```

#### Action failed

```python
logger.error("Display refresh failed")  # No need for "ERROR:" prefix
```

### Including Variables

#### Use dash (-) for primary context

```python
logger.info(f"Loading page - {url}")
logger.info(f"Config parsed - URL: {url}")
logger.info(f"Screenshot saved - {path}")
```

#### Use colon (:) for counts/statistics

```python
logger.info(f"Game state: {active} active, {scheduled} scheduled, {final} final")
logger.info(f"Memory available: {mb}MB")
```

### Error Messages

#### With exception details

```python
logger.error(f"Failed to connect - {e}")  # Include exception after dash
```

#### Without exception (when context is clear)

```python
logger.error("Connection timeout")  # Simple description
```

### Resource/Status Reporting

#### Memory and system resources

```python
logger.info(f"Memory available: {mb}MB")
logger.info(f"System load: {load}")
```

#### Timing information

```python
logger.info(f"Operation completed in {seconds}s")
logger.info(f"Next check in {interval} seconds")
```

## Log Levels

### DEBUG

- Detailed diagnostic information
- Loop iterations, intermediate values
- Not shown in production

```python
logger.debug(f"Checking game {game_id}")
```

### INFO

- Normal program flow
- State changes
- Important milestones

```python
logger.info("Server ready")
logger.info("Starting screenshot capture")
```

### WARNING

- Recoverable issues
- Degraded functionality
- Resource concerns

```python
logger.warning("Low memory - proceeding with caution")
logger.warning("API rate limit approaching")
```

### ERROR

- Failed operations
- Exceptions that affect functionality
- Need attention but not fatal

```python
logger.error("Screenshot failed after 3 retries")
logger.error(f"API request failed - {e}")
```

### CRITICAL

- System-level failures
- Unrecoverable errors
- Service stopping conditions

```python
logger.critical("Out of memory - shutting down")
logger.critical("Configuration file missing")
```

## Special Contexts

### Subprocess/Worker Logs

Worker logs use simple format since parent adds prefix:

```python
# In worker
logger.info("Launching browser")  # Becomes: [WORKER-ERR] Launching browser
```

### Resource Snapshots

Use structured format for machine parsing:

```python
logger.info(f"RESOURCE_SNAPSHOT: {json.dumps(snapshot_dict)}")
```

### Startup/Shutdown

Use clear markers:

```python
logger.info("="*80)
logger.info("SYSTEM STARTING")
logger.info("="*80)
```

## What NOT to Do

### Avoid redundancy

```python
# Bad
logger.error("ERROR: Failed to connect")  # ERROR is already in the level

# Good
logger.error("Failed to connect")
```

### Avoid excessive punctuation

```python
# Bad
logger.info("Starting process...")  # Ellipsis unnecessary
logger.info("Process complete!!!")  # Excessive exclamation

# Good
logger.info("Starting process")
logger.info("Process complete")
```

### Avoid mixing styles

```python
# Bad - inconsistent variable formatting
logger.info(f"Loading: {url}")
logger.info(f"Saved to {path}")
logger.info(f"Memory={mb}MB")

# Good - consistent dash separator
logger.info(f"Loading - {url}")
logger.info(f"Saved - {path}")
logger.info(f"Memory available: {mb}MB")
```

## Examples

### Full operation flow

```python
logger.info("Starting display update")
logger.info(f"Loading URL - {url}")
logger.debug(f"Browser args - {args}")
logger.info("Browser launched")
logger.info("Page loaded")
logger.info("Content detected")
logger.info(f"Screenshot saved - {path}")
logger.info("Display updated")
```

### Error handling flow

```python
logger.warning("Low memory detected")
logger.info("Attempting cleanup")
logger.info(f"Memory recovered: {mb}MB")
logger.error(f"Operation failed - {e}")
logger.info("Retrying in 10 seconds")
```
