# PiLab Test Script - 10-Minute Interval Capture & Supabase Sync

This is the first official PiLab test script that captures images every 10 minutes, saves them locally, and uploads them to Supabase Storage.

## Overview

The test script is designed to validate the PiLab infrastructure with the local Docker Supabase environment. It demonstrates:

- ✅ Environment configuration and validation
- ✅ Configuration file management
- ✅ Supabase client integration
- ✅ Image capture simulation (placeholder for actual camera)
- ✅ Local file storage
- ✅ Supabase upload simulation
- ✅ Comprehensive logging and error handling

## Files Created

- `pilab_test_script.py` - Main test script
- `test_environment.py` - Environment validation script
- `pilab_test_script.log` - Execution logs
- `captures/` - Directory for captured images

## Configuration

### Environment Variables (.env.pi)
- `SUPABASE_URL` - Supabase project URL (http://localhost:54321 for local Docker)
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `CAPTURE_DIR` - Local directory for captures (/home/pi/pilab/captures)

### Configuration File (config.yaml)
```yaml
capture:
  interval_sec: 600          # 10 minutes
  resolution: "4056x3040"    # Camera resolution
  rotation: 180              # Image rotation

storage:
  local_dir: "${CAPTURE_DIR}"  # Uses environment variable
  bucket: "pilab-captures"      # Supabase bucket name
```

## Usage

### Environment Validation
```bash
python test_environment.py
```

### Single Capture Test
```bash
python pilab_test_script.py --single
```

### Continuous Capture (10-minute intervals)
```bash
python pilab_test_script.py
```

### Limited Captures
```bash
python pilab_test_script.py --max-captures 3
```

## Features

### ✅ Completed
- Environment setup and validation
- Configuration management
- Supabase client integration
- Image capture simulation
- Local file storage
- Comprehensive logging
- Error handling and recovery
- Cross-platform path handling

### 🔄 Next Steps
- Implement actual camera capture using PiCamera2
- Implement real Supabase upload functionality
- Add image quality metrics computation
- Integrate with existing PiLab capture pipeline
- Add database logging for captures

## Testing

The script has been tested on:
- ✅ Windows development environment
- ✅ Local file system operations
- ✅ Configuration parsing
- ✅ Environment variable expansion
- ✅ Logging and error handling

## Logs

All operations are logged to:
- Console output (with emojis for visual feedback)
- `pilab_test_script.log` file (UTF-8 encoded)

## Integration

This test script integrates with:
- Existing PiLab Supabase client (`src/supabase_client.py`)
- Local Docker Supabase environment
- PiLab configuration system
- Existing capture directory structure

## Deployment

For deployment on Raspberry Pi:
1. Copy the script to the Pi
2. Ensure `.env.pi` is configured with Pi-specific paths
3. Install required dependencies: `pip install supabase python-dotenv pyyaml`
4. Run environment validation: `python test_environment.py`
5. Test with single capture: `python pilab_test_script.py --single`
6. Deploy for continuous operation: `python pilab_test_script.py` 