# Docker Image Optimization for Koyeb

## Problem
The Docker image was too large (3430 MiB) exceeding Koyeb's limit (2048 MiB).

## Solution
Optimized the Dockerfile and dependencies to reduce image size significantly.

## Changes Made

### 1. Removed PyTorch from Runtime Dependencies
- **Before**: `torch>=2.0.0` was required (~2GB)
- **After**: PyTorch is optional, excluded from runtime requirements
- **Impact**: Saves ~2GB of image size
- **Note**: Code already handles missing PyTorch gracefully with `HAS_TORCH` checks

### 2. Created `requirements-runtime.txt`
- New file with all dependencies except PyTorch
- Used in Dockerfile for production builds
- Original `requirements.txt` kept for development

### 3. Enhanced `.dockerignore`
Excluded unnecessary files from Docker build:
- Training scripts (`train_lstm*.py`, `backtester.py`)
- Documentation files (`*.md`)
- Log files (`*.log`)
- Service files (`*.service`)
- Cache files (`news_cache/*.json`)
- State files (`state.json`)
- Docker config files

### 4. Optimized Dockerfile
- Removed unnecessary build tools (g++, make) - only kept gcc
- Added cleanup steps to remove temporary files
- Used `--no-install-recommends` for apt packages
- Added `pip cache purge` to reduce image size

## Expected Image Size
- **Before**: ~3430 MiB (with PyTorch)
- **After**: ~500-800 MiB (without PyTorch)
- **Reduction**: ~75-85% smaller

## If You Need PyTorch (LSTM Predictions)

If you need LSTM predictions, you can add PyTorch CPU-only version (~500MB):

```dockerfile
# Add after pip install requirements-runtime.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
```

This will add ~500MB but keep the image under 2048 MiB limit.

## Verification

To test the image size locally:

```bash
docker build -t pirho-bot:test .
docker images pirho-bot:test
```

The image should now be under 2048 MiB and deployable on Koyeb.

