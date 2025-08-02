# Update the markdown task list by replacing the bucket creation step
file_path = "/mnt/data/PiLab_Test_Script_Tasks.md"

updated_content = """# PiLab Test Script — 10-Minute Interval Capture & Supabase Sync

A concise, implementation-ready task list for our first **full official test script**: capture one image every **10 minutes**, save locally, then upload to Supabase Storage. No milestone tags. Hand this to Taskmaster/Cursor.

---

## 1. Prep Environment  
- [ ] **Create/verify `.env`** on the Pi with: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CAPTURE_DIR` (e.g., `/home/pi/pilab/captures`).  
- [ ] `pip install supabase~=2 picamera2 python-dotenv`.

## 2. Verify Supabase Bucket  
- [ ] Ensure bucket **`pilab-captures`** already exists and is **private** (`public = false`).  
- [ ] Confirm service key has permission to `list` / `upload` objects.

## 3. Build `supabase_client.py`  
- [ ] Wrap `create_client()` from `supabase_py` using env vars.  
- [ ] Implement `upload_file(local_path, remote_path)` with 3-retry exponential back-off.

## 4. Extend `config.yaml`  
```yaml
capture:
  interval_sec: 600          # 10 minutes
  resolution: "4056x3040"    # native HQ sensor res
  rotation: 180              # adjust for rig
storage:
  local_dir: "${CAPTURE_DIR}"
  bucket: "pilab-captures"
