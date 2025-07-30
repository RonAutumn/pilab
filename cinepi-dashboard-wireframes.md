# CinePi Dashboard UI Wireframes & Feature Grid

## Overview
Based on analysis of MotionEye, PiKrellCam, OctoPrint, Home Assistant, and PiDash, this document outlines the UI wireframes and feature grid for the CinePi dashboard. The design prioritizes touch/tablet optimization, real-time feedback, and modular components.

## Design Principles
- **Touch-First**: Large tap targets (44px minimum), swipe gestures, minimal modals
- **Real-Time Feedback**: WebSocket updates for status, countdowns, and logs
- **Responsive Layout**: Adaptive grid system for different screen sizes
- **Modular Components**: Card-based layout for extensibility
- **Raspberry Pi Optimized**: Lightweight assets, efficient rendering

---

## Main Dashboard Layout

### Desktop/Tablet Layout (1024px+)
```
┌─────────────────────────────────────────────────────────────┐
│ Header Bar                                                  │
│ [CinePi] [Status: Active] [Session: 2h 15m] [Captures: 47] │
├─────────────────────────────────────────────────────────────┤
│ Live Preview Panel                    │ Control Panel       │
│ ┌─────────────────────────────────┐   │ ┌─────────────────┐ │
│ │                                 │   │ │ Start/Stop      │ │
│ │      MJPEG Stream Display       │   │ │ [●] [■]         │ │
│ │                                 │   │ │                 │ │
│ │  [Status Overlay] [Countdown]   │   │ │ Manual Capture  │ │
│ │                                 │   │ │ [📸]            │ │
│ └─────────────────────────────────┘   │ │                 │ │
│                                       │ │ Interval Slider │ │
│                                       │ │ [5s─────60m]    │ │
│                                       │ │ Current: 30s    │ │
│                                       │ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Camera Settings Panel                │ Session Feedback   │
│ ┌─────────────────────────────────┐   │ ┌─────────────────┐ │
│ │ Exposure: [Auto] [Manual]       │   │ │ Next Capture    │ │
│ │ ISO: [100─────800] Current: 400 │   │ │ 00:12           │ │
│ │ Resolution: [4056x3040 ▼]       │   │ │                 │ │
│ │ Gain: [1.0─────8.0] Current: 2.0│   │ │ Session Time    │ │
│ └─────────────────────────────────┘   │ │ 2h 15m 32s      │ │
│                                       │ │                 │ │
│                                       │ │ Total Captures  │ │
│                                       │ │ 47              │ │
│                                       │ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Timeline Browser                    │ Configuration       │
│ ┌─────────────────────────────────┐   │ ┌─────────────────┐ │
│ │ [📷] [📷] [📷] [📷] [📷] [📷]  │   │ │ YAML Editor     │ │
│ │ 14:32 14:33 14:34 14:35 14:36  │   │ │ ┌─────────────┐ │ │
│ │ [📷] [📷] [📷] [📷] [📷] [📷]  │   │ │ │             │ │ │
│ │ 14:37 14:38 14:39 14:40 14:41  │   │ │ │             │ │ │
│ │ [📷] [📷] [📷] [📷] [📷] [📷]  │   │ │ │             │ │ │
│ │ 14:42 14:43 14:44 14:45 14:46  │   │ │ └─────────────┘ │ │
│ └─────────────────────────────────┘   │ │ [Save] [Backup] │ │
│                                       │ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Live Logs Panel                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [2024-01-15 14:46:32] Capture #47 saved to /captures/  │ │
│ │ [2024-01-15 14:46:32] Next capture in 00:12            │ │
│ │ [2024-01-15 14:46:20] Manual capture triggered         │ │
│ │ [2024-01-15 14:46:15] Session started - 30s interval   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Layout (768px and below)
```
┌─────────────────────────────────────┐
│ Header                              │
│ [CinePi] [● Active] [47 captures]  │
├─────────────────────────────────────┤
│ Live Preview Panel                  │
│ ┌─────────────────────────────────┐ │
│ │                                 │ │
│ │      MJPEG Stream Display       │ │
│ │                                 │ │
│ │  [Status] [Next: 00:12]         │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ Control Panel                      │
│ [● Start] [■ Stop] [📸 Manual]     │
│ Interval: [5s─────60m] 30s         │
├─────────────────────────────────────┤
│ Camera Settings                    │
│ Exposure: [Auto] [Manual]          │
│ ISO: [100─────800] 400             │
│ Resolution: [4056x3040 ▼]          │
│ Gain: [1.0─────8.0] 2.0            │
├─────────────────────────────────────┤
│ Session Feedback                   │
│ Next: 00:12 | Session: 2h 15m      │
│ Total: 47 captures                 │
├─────────────────────────────────────┤
│ Timeline Browser                   │
│ [📷] [📷] [📷] [📷] [📷] [📷]     │
│ 14:32 14:33 14:34 14:35 14:36      │
│ [📷] [📷] [📷] [📷] [📷] [📷]     │
│ 14:37 14:38 14:39 14:40 14:41      │
├─────────────────────────────────────┤
│ Configuration                      │
│ [Edit Config] [Backup] [Restore]   │
├─────────────────────────────────────┤
│ Live Logs                          │
│ [2024-01-15 14:46:32] Capture #47  │
│ [2024-01-15 14:46:32] Next: 00:12  │
│ [2024-01-15 14:46:20] Manual cap   │
└─────────────────────────────────────┘
```

---

## Component Details

### 1. Live Preview Panel
**Purpose**: Real-time camera feed with status overlays
**Features**:
- MJPEG stream display (4056x3040 max resolution)
- Status indicator overlay (Active/Inactive)
- Countdown timer to next capture
- Fullscreen toggle button
- Snapshot button for manual captures

**Technical Requirements**:
- WebSocket updates for countdown timer
- Responsive image scaling
- Touch-friendly controls (44px minimum)

### 2. Control Panel
**Purpose**: Primary capture controls
**Features**:
- Start/Stop timelapse button (toggle state)
- Manual capture button
- Interval slider (5 seconds to 60 minutes)
- Current interval display
- Session status indicator

**Technical Requirements**:
- REST API calls for control actions
- Real-time status updates via WebSocket
- Slider with visual feedback
- Large touch targets for mobile

### 3. Camera Settings Panel
**Purpose**: Camera parameter configuration
**Features**:
- Exposure mode toggle (Auto/Manual)
- ISO slider (100-800)
- Resolution dropdown (4056x3040, 2028x1520, 1014x760)
- Gain slider (1.0-8.0)
- Real-time parameter display

**Technical Requirements**:
- REST API for parameter updates
- Live validation of settings
- Responsive form layout
- Visual feedback for changes

### 4. Session Feedback Panel
**Purpose**: Real-time session monitoring
**Features**:
- Countdown to next capture
- Session duration timer
- Total captures counter
- Session status (Active/Inactive/Paused)

**Technical Requirements**:
- WebSocket updates for real-time data
- Auto-refresh timers
- Visual indicators for status

### 5. Timeline Browser
**Purpose**: Browse and manage captured images
**Features**:
- Thumbnail grid of recent captures
- Timestamp display
- Download/delete actions
- Infinite scroll or pagination
- Search/filter by date

**Technical Requirements**:
- REST API for image metadata
- Thumbnail generation
- File download functionality
- Responsive grid layout

### 6. Configuration Panel
**Purpose**: YAML configuration editing
**Features**:
- Syntax-highlighted YAML editor
- Live validation
- Save/Backup/Restore buttons
- Validation feedback
- Auto-save functionality

**Technical Requirements**:
- Monaco Editor or CodeMirror integration
- YAML validation library
- File system integration
- Backup/restore functionality

### 7. Live Logs Panel
**Purpose**: Real-time log streaming
**Features**:
- Scrollable log output
- Timestamp formatting
- Log level indicators
- Auto-scroll toggle
- Clear logs button

**Technical Requirements**:
- WebSocket for real-time log streaming
- Log level filtering
- Timestamp parsing
- Responsive text display

---

## Feature Grid

| UI Section | Controls | Indicators | Data Sources | Real-Time Updates |
|------------|----------|------------|--------------|-------------------|
| **Live Preview** | Fullscreen, Snapshot | Status, Countdown | MJPEG Stream, WebSocket | Countdown timer, Status |
| **Control Panel** | Start/Stop, Manual, Interval Slider | Session Status | REST API, WebSocket | Button states, Interval value |
| **Camera Settings** | Exposure Toggle, ISO Slider, Resolution Dropdown, Gain Slider | Current Values | REST API | Parameter values |
| **Session Feedback** | None | Countdown, Session Time, Total Captures | WebSocket | All indicators |
| **Timeline Browser** | Download, Delete, Search | Thumbnails, Timestamps | REST API | New captures |
| **Configuration** | Save, Backup, Restore | Validation Status | File System, YAML Parser | Validation feedback |
| **Live Logs** | Clear, Auto-scroll Toggle | Log Entries | WebSocket | New log entries |

---

## Interaction Patterns

### Touch Gestures
- **Tap**: Primary actions (buttons, toggles)
- **Long Press**: Secondary actions (context menus)
- **Swipe**: Navigation between panels (mobile)
- **Pinch**: Zoom in/out on live preview
- **Double Tap**: Fullscreen toggle

### Keyboard Shortcuts
- **Space**: Start/Stop timelapse
- **C**: Manual capture
- **F**: Fullscreen toggle
- **S**: Save configuration
- **R**: Refresh page
- **Esc**: Close modals, exit fullscreen

### Responsive Breakpoints
- **Desktop** (1024px+): Full layout with side-by-side panels
- **Tablet** (768px-1023px): Stacked layout with larger touch targets
- **Mobile** (320px-767px): Single-column layout with collapsible sections

---

## Accessibility Features

### Visual
- High contrast mode toggle
- Large text option
- Color-blind friendly indicators
- Clear visual hierarchy

### Interaction
- Keyboard navigation support
- Screen reader compatibility
- Focus indicators
- ARIA labels and roles

### Performance
- Lazy loading for thumbnails
- Debounced slider updates
- Efficient WebSocket message handling
- Optimized image compression

---

## Technical Implementation Notes

### Backend Integration
- **REST API**: `/api/capture/start`, `/api/capture/stop`, `/api/camera/settings`
- **WebSocket**: Real-time updates for status, countdowns, logs
- **File System**: Image storage, configuration files, backups

### Frontend Framework
- **Flask + HTMX** for server-side rendering
- **Bootstrap 5** for responsive components
- **Alpine.js** for lightweight interactivity
- **Monaco Editor** for YAML editing

### Performance Considerations
- **MJPEG Streaming**: Native browser support, low latency
- **WebSocket Connection**: Persistent for real-time updates
- **Image Optimization**: Thumbnail generation, lazy loading
- **Caching**: Static assets, API responses

---

## Next Steps

1. **Wireframe Validation**: Review with stakeholders for feedback
2. **Component Development**: Implement individual UI components
3. **Integration Testing**: Test with actual camera hardware
4. **Performance Optimization**: Optimize for Raspberry Pi 5
5. **Accessibility Testing**: Ensure compliance with WCAG guidelines

This wireframe design provides a solid foundation for the CinePi dashboard, incorporating best practices from successful open-source projects while maintaining focus on time-lapse camera workflows and Raspberry Pi optimization. 