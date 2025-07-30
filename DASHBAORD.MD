# CinePi Dashboard Research & Implementation Planning

**Tier:** 1  
**Goal:** Replace all CLI usage with a lightweight, interactive dashboard to manage camera and capture settings during testing.

---

## 🎯 Objective

Design and implement a **web-based dashboard** to control and monitor CinePi. The dashboard will:

- Eliminate need to edit Python files or use terminal for basic tasks
- Enable dynamic camera settings and timelapse control
- Simplify testing by providing visual and interactive feedback

---

## 🧩 Phase 1 — Research

### ✅ 1. Tech Stack Evaluation

Research and compare 2–3 web-based dashboard stacks that meet the following criteria:

| Requirement           | Description |
|-----------------------|-------------|
| ✅ Lightweight         | Minimal overhead for Raspberry Pi 5 |
| ✅ Python Compatible   | Must easily integrate with CinePi's Python scripts |
| ✅ Real-time Capable   | Must support MJPEG preview stream and live UI updates |
| ✅ Simple UI Hooks     | Should support interactive forms, sliders, and buttons |

**Stack Candidates to Evaluate:**
- Flask + Jinja2 (HTML templates)
- Flask + HTMX (lightweight interactivity)
- Flask + React (full SPA)
- Streamlit (Python-native dashboard)
- FastAPI + Vue (optional if needed later)

---

### ✅ 2. Existing OSS Projects to Analyze

Identify 3–5 existing open-source dashboards with relevant architecture or UI design. Focus on:

- Time-lapse camera systems (MotionEye, PiKrellCam)
- OctoPrint UI (Raspberry Pi 3D printing interface)
- Home automation dashboards (e.g. Home Assistant, PiDash)

Summarize:
- Architecture choices
- Key dashboard UI components
- Relevant features or layouts to adapt

---

## 🛠 Phase 2 — Implementation Planning

### 📦 Target v0.1 Dashboard Features (Tier 1 only)

| Category | Feature |
|----------|---------|
| Capture Control | Start / stop timelapse |
| Capture Control | Set interval dynamically (5s–60min slider) |
| Capture Control | Manual "Capture Now" button |
| Camera Settings | Exposure toggle (Auto/Manual) |
| Camera Settings | ISO / Gain slider |
| Camera Settings | Resolution dropdown (4056x3040, 2028x1520, etc.) |
| Feedback | View last captured image |
| Feedback | Countdown to next capture |
| Feedback | Status: active/inactive |
| Feedback | Session time + total captures |
| Logs | Stream recent logs in textarea or table |
| Config | Edit and reload `config.yaml` in-browser |
| UI Design | Responsive layout for touch or tablet use |

---

## 🧠 Optional Stretch Goals (Tier 1.5+ Prep)

- Async image preview thumbnails
- Auto-refresh logs without reloading page
- Camera lock warning banner
- Reboot/shutdown Pi from UI

---

## 🧪 Deliverables for Taskmaster

- 📄 Research Summary (tech stack + OSS comparisons)
- 📐 UI Wireframe or Feature Grid
- 📁 Suggested file structure for new dashboard app
- 🏗 Initial scaffolding plan (e.g. `dashboard/`, entry point, routes)
