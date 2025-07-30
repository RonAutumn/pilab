CinePi Tier 1 — Error Log & Fix Report
Date: 2025-07-29

1. Executive Summary
During the first full-system launch we uncovered several blocking and non-blocking issues. Key pain points included invalid camera-control IDs, CSV metadata mis-alignment, missing OpenCV, and camera resource contention between the preview server and timelapse loop. This report logs each error, its root cause, and the repo changes required for Tier 1 stability.

2. Detailed Errors & Fixes
2.1 Invalid Camera Control (Auto)
Log snippet	'libcamera._libcamera.ControlId' object has no attribute 'Auto'
Root cause	capture_utils.py tries to set controls['Auto']; Picamera2 uses AeEnable, AwbEnable, etc.
Fix actions	- Replace invalid key with valid controls (AeEnable, AwbEnable, ExposureTime, …).
- Update default config.yaml accordingly.
Files to modify	src/capture_utils.py, config.yaml.example

2.2 CSV Logging Field Mismatch
Log snippet	ValueError: dict contains fields not in fieldnames: 'filepath', 'capture_number', 'interval_seconds'
Root cause	metrics.log_capture_event() writes extra keys not declared in fieldnames.
Fix actions	- Extend fieldnames list in src/metrics.py to include filepath, capture_number, interval_seconds.
- Add regression test tests/test_metrics_csv.py.
Files to modify	src/metrics.py, tests/

2.3 OpenCV Not Available for Metrics
Log snippet	WARNING:metrics:OpenCV not available for sharpness calculation
Root cause	opencv-python missing from environment and requirements.txt.
Fix actions	- Add opencv-python to requirements.txt.
- Document sudo apt install python3-opencv for system installs.
- Add graceful fallback when cv2 is absent.
Files to modify	requirements.txt, README.md

2.4 Camera Resource Busy (Preview vs Main)
Log snippet	RuntimeError: Failed to acquire camera: Device or resource busy
Root cause	preview.py and main.py both try to open the camera simultaneously.
Fix actions	- Create mutually-exclusive launch scripts (run_capture.sh, run_preview.sh).
- Long-term: design shared-frame pipeline or use a second camera.
Files to modify	run_capture.sh new, run_preview.sh new

2.5 Path / nohup Mis-launch
Log snippet	python3: can't open file '/home/richdollaz/src/main.py'
Root cause	nohup was executed from ~/ instead of ~/pilab; relative path failed.
Fix actions	- Add run_all.sh wrapper that cd $(dirname "$0") before launching.
- Update README quick-start section.
Files to modify	run_all.sh new, README.md

2.6 Timing-Controller Clock Drift Warnings
Log snippet	WARNING:timing_controller:System clock adjustment detected: 1.00s jump
Root cause	NTP or kernel slewing introduces 1 s corrections; benign but noisy.
Fix actions	- Downgrade to INFO after first few occurrences or add --suppress-drift flag.
- Document expected behavior.
Files to modify	src/timing_controller.py

3. Scaffolding & Repo Updates
Create logs/ during install (install.sh).

Add run_capture.sh, run_preview.sh, run_all.sh launchers with timestamped logging.

Update requirements.txt (add opencv-python) and pin picamera2 version.

Add tests for CSV logging and camera-control validation.

Extend README with install notes, single-camera limitations, log handling, and venv vs system picamera2 guidance.

Consider migrating to pyproject.toml (PEP 517) for modern packaging.

4. Immediate Next Steps
Patch camera-control keys and verify single capture success.

Fix CSV header, confirm log contains new fields.

Install OpenCV and re-enable sharpness/brightness metrics.

Commit launch scripts and update README.

Tag as v0.1.1-hotfix in Git.

End of report — ready for PRs and hot-fix branches.