# Parallel Processing Guide

## Overview

The OmmSai prescription extractor now supports **parallel processing** to dramatically speed up large batch operations. This is essential for processing 15,000+ files efficiently.

## Performance Comparison

| Mode | Workers | 15,000 Files | 1,000 Files |
|------|---------|--------------|-------------|
| **Sequential (Old)** | 1 | ~125 hours | ~8 hours |
| **Conservative** | 5 | ~25 hours | ~1.6 hours |
| **Recommended** | 10 | ~12.5 hours | ~50 minutes |
| **Aggressive** | 20 | ~6.25 hours | ~25 minutes |
| **Maximum** | 50 | ~2.5 hours | ~10 minutes |

## Quick Start

### Test First (IMPORTANT!)

Always test with a small batch before processing your full dataset:

```bash
# Test with 5 files using 2 workers
python test_parallel.py --test-size 5 --workers 2

# Review output in test_parallel_output.json
# Check cost estimate
# Verify extraction quality
```

### Run Full Processing

```bash
# Recommended for 15,000 files (10 workers)
python main_cli.py --workers 10

# For faster processing (20 workers - more aggressive)
python main_cli.py --workers 20

# Conservative approach (5 workers - safer)
python main_cli.py --workers 5
```

## Features

### 1. Concurrent Processing ⚡

Process multiple files simultaneously using ThreadPoolExecutor:
- Download files in parallel
- Process with Claude AI concurrently
- Thread-safe result saving

### 2. Checkpoint/Resume 💾

Automatically saves progress every 100 files:
- Resume from failures or interruptions
- Skip already processed files
- Track failed files separately

```bash
# Resume from checkpoint
python main_cli.py --resume

# Custom checkpoint file
python main_cli.py --checkpoint my_checkpoint.json
```

### 3. Rate Limiting 🛡️

Automatic rate limit handling:
- Respects API rate limits
- Exponential backoff on errors
- Retry failed requests (up to 3 times)

### 4. Progress Tracking 📊

Real-time statistics:
- Files per minute throughput
- Estimated time to completion (ETA)
- Success/partial/failed counts
- API token usage and costs

### 5. Cost Estimation 💰

Track and estimate API costs:
- Current cost (so far)
- Estimated total cost
- Token usage breakdown

## CLI Options

### Basic Usage

```bash
python main_cli.py [OPTIONS]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--folder-id` | `-f` | Google Drive folder ID | From settings |
| `--output` | `-o` | Output JSON file | `extracted_prescriptions.json` |
| `--workers` | `-w` | Number of parallel workers | `10` |
| `--sequential` | `-s` | Use sequential mode (old behavior) | Parallel enabled |
| `--resume` | `-r` | Resume from checkpoint | Disabled |
| `--checkpoint` | `-c` | Custom checkpoint file | `processing_checkpoint.json` |

### Examples

```bash
# Default: 10 workers, parallel mode
python main_cli.py

# 20 workers for faster processing
python main_cli.py --workers 20

# Sequential mode (old behavior)
python main_cli.py --sequential

# Resume interrupted job
python main_cli.py --resume

# Custom folder with 15 workers
python main_cli.py --folder-id YOUR_ID --workers 15

# Custom output file
python main_cli.py --output results.json --workers 10
```

## Choosing Worker Count

### Factors to Consider

1. **API Rate Limits**
   - Google Drive: ~100 requests/minute
   - Claude API: ~50 requests/minute
   - More workers = higher rate limit risk

2. **Network Bandwidth**
   - Downloading PDFs concurrently
   - More workers = more bandwidth needed

3. **System Resources**
   - Each worker uses memory
   - Typical: 50-100MB per worker

4. **Processing Time**
   - Download: ~1-2 seconds per file
   - Claude processing: ~3-8 seconds per file
   - Total: ~5-10 seconds per file

### Recommendations

| Files | Workers | Reasoning |
|-------|---------|-----------|
| < 100 | 2-5 | Test, small batches |
| 100-1,000 | 5-10 | Balanced speed/safety |
| 1,000-5,000 | 10-15 | Moderate scale |
| 5,000-15,000 | 10-20 | **Your use case** |
| 15,000+ | 15-30 | Large scale (monitor closely) |

**For 15,000 files: Start with 10 workers, increase to 15-20 if stable.**

## Monitoring Progress

### Real-Time Stats

During processing, you'll see:

```
Progress: 100/15000 (0.7%) | Throughput: 8.5 files/min | ETA: 29 hours 24 minutes
Progress: 200/15000 (1.3%) | Throughput: 9.2 files/min | ETA: 26 hours 51 minutes
```

### Checkpoints

Progress saved automatically every 100 files:
- `processing_checkpoint.json` contains state
- Resume anytime with `--resume`
- Export failed files: check checkpoint file

### Logs

Monitor the console output for:
- ✓ Successful processing
- ⚠ Rate limit warnings
- ✗ Failed files

## Handling Failures

### Resume from Checkpoint

If processing is interrupted:

```bash
# Resume where it left off
python main_cli.py --resume
```

### Reprocess Failed Files

1. Check `processing_checkpoint.json` for failed files
2. Extract failed file IDs
3. Reprocess specific files manually or:

```bash
# Start fresh (clears checkpoint)
rm processing_checkpoint.json
python main_cli.py
```

### Rate Limit Errors

If you see rate limit errors:

```bash
# Reduce workers
python main_cli.py --workers 5

# Or use sequential mode
python main_cli.py --sequential
```

## Cost Management

### Estimate Before Processing

```bash
# Test with 10 files
python test_parallel.py --test-size 10

# Check cost estimate
# Multiply by (total_files / 10) for full estimate
```

### Typical Costs (Claude Sonnet 4.5)

- **Per file**: ~$0.02-0.05
- **1,000 files**: ~$20-50
- **15,000 files**: ~$300-750

Actual costs depend on:
- PDF size and complexity
- Handwriting legibility
- Fields extracted

### Monitor During Processing

The CLI shows cost estimates:
```
Cost Estimate
=============
Current Cost: $15.23
Estimated Total Cost: $456.90
Input Tokens: 1,234,567
Output Tokens: 345,678
```

## Best Practices

### 1. Always Test First

```bash
# Test with 5-10 files
python test_parallel.py --test-size 10 --workers 2

# Review results before full run
cat test_parallel_output.json
```

### 2. Start Conservative

```bash
# First run: 5 workers
python main_cli.py --workers 5

# If stable, increase to 10
python main_cli.py --workers 10 --resume
```

### 3. Monitor Progress

- Check console output regularly
- Watch for rate limit warnings
- Note throughput (files/min)

### 4. Use Checkpointing

```bash
# Always enable checkpointing for large batches
# (enabled by default)
python main_cli.py --workers 10
```

### 5. Plan for Long Runs

For 15,000 files with 10 workers (~12 hours):
- Run on stable machine/server
- Use `tmux` or `screen` to prevent disconnection
- Enable auto-resume on failure

```bash
# Using tmux
tmux new -s prescription_processing
python main_cli.py --workers 10
# Detach: Ctrl+b, then d
# Reattach: tmux attach -t prescription_processing
```

## Troubleshooting

### Issue: Rate Limit Errors

**Symptoms**: "429 Too Many Requests", "Rate limit exceeded"

**Solutions**:
```bash
# Reduce workers
python main_cli.py --workers 5

# Add delays (edit settings.py)
RETRY_BASE_DELAY = 2  # Increase from 1
```

### Issue: Slow Processing

**Symptoms**: Throughput < 1 file/min

**Solutions**:
- Check network speed
- Verify API keys are valid
- Increase workers if < 10
- Check system resources (CPU, memory)

### Issue: High Failure Rate

**Symptoms**: Many "failed" status files

**Solutions**:
- Check PDF quality (some may be corrupt)
- Review Claude API errors in logs
- Verify prompt is working (test with `test_parallel.py`)

### Issue: Out of Memory

**Symptoms**: Python crashes, memory errors

**Solutions**:
```bash
# Reduce workers
python main_cli.py --workers 5

# Process in smaller batches
# Use multiple folders/runs
```

## Configuration

### Customize Settings

Edit `getGoogleFiles/config/settings.py`:

```python
# Parallel Processing
MAX_WORKERS = 10              # Default workers
MAX_WORKERS_LIMIT = 50        # Maximum allowed

# Checkpoint
CHECKPOINT_BATCH_SIZE = 100   # Save every N files

# Retry Logic
RETRY_ATTEMPTS = 3            # Max retry attempts
RETRY_BASE_DELAY = 1          # Initial delay (seconds)
RETRY_MAX_DELAY = 60          # Max delay (seconds)

# Rate Limits
GOOGLE_DRIVE_RATE_LIMIT = 100  # Requests/minute
CLAUDE_RATE_LIMIT = 50         # Requests/minute
```

## Advanced Usage

### Custom Progress Callback

Implement custom progress tracking in code:

```python
from getGoogleFiles.core import ParallelProcessor

def my_callback(stats):
    print(f"Custom: {stats['processed']}/{stats['total']}")

processor = ParallelProcessor(
    google_service=google_service,
    claude_processor=claude_processor,
    max_workers=10,
    progress_callback=my_callback
)
```

### Export Failed Files

From checkpoint manager:

```python
from getGoogleFiles.utils import CheckpointManager

checkpoint = CheckpointManager()
checkpoint.export_failed_files('failed_files.json')
```

## Performance Tuning

### For Maximum Speed

```bash
# 20-30 workers
python main_cli.py --workers 20

# Monitor for rate limits
# Be prepared to reduce if errors occur
```

### For Maximum Reliability

```bash
# 5 workers, sequential if needed
python main_cli.py --workers 5

# Enable checkpointing (default)
# Retry logic handles transient errors
```

### For Cost Optimization

```bash
# Test extensively first
python test_parallel.py --test-size 20 --workers 2

# Review cost per file
# Optimize prompt if needed
# Use sequential for testing
```

## FAQ

**Q: How many workers should I use for 15,000 files?**
A: Start with 10, monitor for 30 minutes, increase to 15-20 if stable.

**Q: Can I pause and resume?**
A: Yes! Press Ctrl+C to stop, then run with `--resume` to continue.

**Q: What happens if my computer restarts?**
A: Progress is saved every 100 files. Resume with `--resume` flag.

**Q: How do I know if I'm hitting rate limits?**
A: Watch for "429" errors or "rate limit" warnings in console output.

**Q: Can I process overnight?**
A: Yes! Use `tmux` or `screen` to keep it running even if disconnected.

**Q: Is parallel processing safe?**
A: Yes! Thread-safe implementation with proper locking and error handling.

---

**Ready to process 15,000 files?**

1. Test: `python test_parallel.py --test-size 10 --workers 2`
2. Review test results
3. Run: `python main_cli.py --workers 10`
4. Monitor progress
5. Resume if needed: `python main_cli.py --resume --workers 10`

**Estimated time for 15,000 files with 10 workers: ~12 hours**
