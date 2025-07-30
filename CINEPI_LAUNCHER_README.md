# 🎬 CinePi Complete System Launcher

## Overview

The CinePi Complete System Launcher allows you to run both the **CinePi Dashboard** and the **Timelapse System** with just one click! This replaces the need to manually start separate scripts.

## 🚀 Quick Start

### Windows Users
```bash
# Double-click this file or run from command line:
run_cinepi.bat
```

### Linux/Mac Users
```bash
# Make executable and run:
chmod +x run_cinepi.sh
./run_cinepi.sh
```

### Python Users (All Platforms)
```bash
# Interactive mode (shows menu):
python run_cinepi_complete.py

# Direct mode (no menu):
python run_cinepi_complete.py both
```

## 📋 Available Modes

### 1. 🎯 Dashboard Only
- Runs only the web dashboard
- Access at: http://localhost:5000
- Perfect for testing the UI without camera operations

### 2. 📸 Timelapse Only  
- Runs only the camera timelapse system
- Command-line interface
- No web dashboard

### 3. 🚀 Complete System (Recommended)
- Runs both dashboard AND timelapse system
- Dashboard controls the timelapse system
- Full integration between web UI and camera operations

## 🎛️ Command Line Options

```bash
# Interactive menu
python run_cinepi_complete.py

# Dashboard only
python run_cinepi_complete.py dashboard
python run_cinepi_complete.py d
python run_cinepi_complete.py 1

# Timelapse only  
python run_cinepi_complete.py timelapse
python run_cinepi_complete.py t
python run_cinepi_complete.py 2

# Complete system
python run_cinepi_complete.py both
python run_cinepi_complete.py complete
python run_cinepi_complete.py c
python run_cinepi_complete.py 3

# Help
python run_cinepi_complete.py help
```

## 🌐 Dashboard Features

When you run the complete system, you get access to:

### 📱 Web Interface (http://localhost:5000)
- **Live Preview**: Real-time camera feed
- **Capture Control**: Start/stop timelapse, manual capture
- **Camera Settings**: Adjust exposure, ISO, resolution
- **Session Feedback**: Monitor progress, countdown, status
- **Timeline Browser**: View captured images
- **Configuration Editor**: Edit YAML config in browser
- **Live Logs**: Real-time system logs

### 🔧 Integration
- Dashboard controls the timelapse system
- Real-time status updates
- Live configuration changes
- Image preview and management

## 📊 Taskmaster Dashboard Progress

Based on your Taskmaster project, here's the current status:

### ✅ Completed (90.9% Complete)
- **Task 1**: Tech Stack Research (Flask + HTMX selected)
- **Task 2**: Open-source Dashboard Analysis  
- **Task 3**: UI Wireframes and Design
- **Task 4**: File Structure and Architecture
- **Task 5**: Core Flask Application
- **Task 6**: Capture Control Interface
- **Task 7**: Camera Settings Management
- **Task 8**: Real-time Feedback System
- **Task 9**: YAML Configuration Editor
- **Task 10**: Mobile-Responsive UI

### 🔄 In Progress (9.1% Remaining)
- **Task 11**: Testing and Documentation
  - Unit Testing Implementation
  - Integration Testing Setup
  - User Acceptance Testing
  - User Documentation
  - API Documentation
  - Deployment Guide

## 🛠️ System Requirements

- Python 3.8+
- All dependencies from `requirements.txt`
- Camera hardware (for timelapse functionality)
- Web browser (for dashboard access)

## 🔧 Troubleshooting

### Dashboard Won't Start
```bash
# Check if port 5000 is available
netstat -an | findstr :5000  # Windows
lsof -i :5000                # Linux/Mac

# Try different port
python run_cinepi_complete.py dashboard --port 5001
```

### Timelapse System Issues
```bash
# Check camera permissions
ls -la /dev/video*           # Linux
# Ensure camera is not in use by other applications
```

### Both Systems Won't Start
```bash
# Check Python dependencies
pip install -r requirements.txt

# Check configuration
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

## 📁 File Structure

```
cinepi/
├── run_cinepi_complete.py    # Main launcher script
├── run_cinepi.bat           # Windows batch file
├── run_cinepi.sh            # Linux/Mac shell script
├── run_dashboard.py         # Original dashboard launcher
├── run.py                   # Original timelapse launcher
├── dashboard/               # Dashboard application
├── src/                     # Timelapse system
└── config.yaml             # Configuration file
```

## 🎯 Next Steps

1. **Test the Complete System**: Run `python run_cinepi_complete.py both`
2. **Access Dashboard**: Open http://localhost:5000 in your browser
3. **Configure Camera**: Use the dashboard to adjust settings
4. **Start Timelapse**: Use the dashboard controls to begin capture
5. **Monitor Progress**: Watch real-time feedback and logs

## 📞 Support

If you encounter issues:
1. Check the logs in the dashboard
2. Verify your `config.yaml` settings
3. Ensure camera hardware is properly connected
4. Review the Taskmaster project for detailed implementation status

---

**🎉 Congratulations!** You now have a fully integrated CinePi system with a modern web dashboard and one-click launching capability! 