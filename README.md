# VisionGuard - Cow Repellent System

An intelligent video surveillance and detection system designed to automatically detect and repel animals (primarily cows) from restricted areas using YOLO-based object detection and IoT device control.

## Overview

VisionGuard is a multi-threaded Python application that combines real-time video processing with intelligent object detection to create an automated animal repellent system. The system monitors camera feeds, detects specified objects (cows, humans, vehicles), and automatically triggers repellent devices when targets enter designated zones.

## Architecture

### System Architecture

```
+-----------------------------------------------------------------+
|                    Application Manager                          |
|                    (Central Container)                          |
+-----------------------------------------------------------------+
|                                                                 |
|  +------------------+  +------------------+  +------------------+ |
|  | Video Source     |  | Detection        |  | Device           | |
|  | Manager          |  | Manager          |  | Manager          | |
|  |                  |  |                  |  |                  | |
|  | - Camera feeds   |  | - YOLO models    |  | - Repellents     | |
|  | - Frame capture  |  | - Object tracking|  | - On/Off control | |
|  | - Source config  |  | - Zone detection |  | - Status notify  | |
|  +------------------+  +------------------+  +------------------+ |
|                                                                 |
+-----------------------------------------------------------------+
|                    Communication Layer                          |
|  +------------------+  +------------------+  +------------------+ |
|  | WebSocket Server |  | REST API Server  |  | Config API       | |
|  | (Frame streaming)|  | (FastAPI)        |  | (Settings)       | |
|  +------------------+  +------------------+  +------------------+ |
|                                                                 |
+-----------------------------------------------------------------+
|                    Frontend Layer                               |
|  +------------------+  +------------------+  +------------------+ |
|  | Dashboard        |  | Device Manager   |  | Zone Editor      | |
|  | (Monitoring)     |  | (CRUD)           |  | (Drawing tool)   | |
|  +------------------+  +------------------+  +------------------+ |
+-----------------------------------------------------------------+
```

### Core Components

#### 1. Application Manager (`managers/application_manager.py`)
Central dependency container that orchestrates all system components.

- **Responsibilities**:
  - Initialize and manage all sub-managers
  - Provide unified state serialization
  - Track system uptime and status
  - Coordinate cross-manager operations

#### 2. Video Source Manager (`managers/source_manager.py`)
Manages camera feeds and video sources.

- **Features**:
  - Dynamic camera addition/removal
  - Support for RTSP, HTTP, and file sources
  - Thread-safe frame capture
  - Mock sources for testing
  - Auto-reconnection on failures

#### 3. Detection Manager (`managers/detection_manager.py`)
Core detection engine using YOLO models.

- **Capabilities**:
  - Multi-camera parallel detection
  - Configurable object classes (cows, humans, vehicles)
  - Zone-based detection logic
  - Real-time device triggering
  - Mock detection for testing

#### 4. Device Manager (`managers/device_manager.py`)
Controls IoT repellent devices.

- **Functions**:
  - Device registration and lifecycle
  - On/Off state management
  - Callback-based state notifications
  - Device-zone associations

### Domain Objects

#### VideoSource (`objects/source.py`)
Represents a camera or video feed source.

```python
class VideoSource:
    id: str              # Unique identifier (src_1, src_2, ...)
    name: str            # Human-readable name
    source_url: str      # Stream URL
    enabled: bool        # Active state
    _latest_frame: np.ndarray  # Current frame buffer
    ready: threading.Event     # Frame availability signal
```

#### Detector (`objects/detector.py`)
Handles YOLO model inference for a single video source.

```python
class Detector:
    model: YOLO          # YOLO model instance
    source: VideoSource  # Video feed
    callback: Callable   # Detection result handler
    allowed_classes: set # Classes to detect
    running: bool        # Thread control flag
    last_detections: list[Detected]  # Latest detections
```

#### Zone (`objects/zone.py`)
Defines detection zones on camera feeds.

```python
class Zone:
    coords: np.ndarray   # Polygon vertices (N x 2 array)
    active: bool         # Zone activation state
    id: str             # Unique identifier (zon_1, zon_2, ...)
    name: str           # Human-readable name
```

#### Device (`objects/device.py`)
Represents a controllable repellent device.

```python
class Device:
    id: uuid.UUID        # Unique identifier
    name: str            # Device name
    url: str             # Activation endpoint
    _active: bool        # Current state
    _callbacks: list     # State change listeners
```

## Design Patterns

### 1. Manager Pattern
Centralized management of related resources with uniform interfaces.

```python
class ApplicationManager:
    def __init__(self):
        self.video_source_manager = VideoSourceManager()
        self.detection_manager = DetectionManager()
        self.device_manager = DeviceManager()
```

### 2. Observer/Callback Pattern
Event-driven communication between components.

```python
class Device:
    def register_callback(self, callback):
        self._callbacks.append(callback)
    
    def on(self):
        self._active = True
        self._notify_callbacks()
```

### 3. Factory Pattern
Dynamic object creation based on configuration.

```python
class VideoSourceManager:
    def get_source_from_dict(self, value: dict):
        if value.get("test"):
            return VideoSourceMock(name=name)
        return VideoSource(url, name)
```

### 4. Strategy Pattern
Interchangeable detection callbacks.

```python
class ZoneCallback:
    def callback(self, detected, frame, source):
        # Zone-based detection logic
        
class DeviceCallback:
    def callback(self, detected, frame, source):
        # Device-based detection logic
```

### 5. Thread-per-Source Pattern
Parallel processing of multiple video streams.

```python
class Detector:
    def start_tracking(self):
        self.thread = threading.Thread(target=self._start_tracking)
        self.thread.start()
```

## Data Flow

### Detection Pipeline

```
+-------------+    +-------------+    +-------------+    +-------------+
| VideoSource |--- |  Detector   |--- |  Callback   |--- |   Device    |
| (Frame Gen) |    | (YOLO Track)|    | (Zone Check)|    | (Trigger)   |
+-------------+    +-------------+    +-------------+    +-------------+
       |                  |                  |                  |
       |                  |                  |                  |
       v                  v                  v                  v
   Raw Frames      Detections         Zone Status         Device On/Off
```

### Configuration Flow

```
+-------------+    +-------------+    +-------------+    +-------------+
| config.toml |--- |   Settings  |--- |  Config     |--- |  Handlers   |
| (TOML)      |    |  (Pydantic) |    |  Manager    |    | (Callbacks) |
+-------------+    +-------------+    +-------------+    +-------------+
```

### Real-time Communication

```
+-------------+    +-------------+    +-------------+
|  Detection  |--- |  WebSocket  |--- |   Browser   |
|  Manager    |    |   Server    |    |   Client    |
+-------------+    +-------------+    +-------------+
       |                                      |
       |                                      |
       v                                      v
   Frame + Detections                   Live Video Feed
```

## API Endpoints

### System
- `GET /api/system/status` - System status and uptime

### Cameras
- `GET /api/camera/{id}` - Get camera details
- `GET /api/camera/{id}/info` - Get camera info (resolution, FPS)
- `POST /api/camera` - Create new camera
- `PUT /api/camera/{id}` - Update camera
- `DELETE /api/camera/{id}` - Delete camera
- `GET /api/camera/{id}/last-frame` - Get latest frame

### Devices
- `GET /api/devices` - List all devices
- `POST /api/devices` - Create new device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device

### Zones
- `GET /api/camera/{id}/zones` - List zones for camera
- `POST /api/camera/{id}/zone` - Create zone
- `PUT /api/zone/{id}` - Update zone
- `DELETE /api/zone/{id}` - Delete zone

### Settings
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Update settings

### WebSocket
- `ws://localhost:8000/ws/{camera_id}` - Camera frame stream
- `ws://localhost:8000/ws/devices` - Device status updates

## Configuration

### config.toml Structure

```toml
[model]
name = "yolo26s"           # YOLO model variant
fuse = true                # Enable model fusion
test = false               # Enable mock detection
test_delay = 1             # Mock detection delay (sec)
verbose = false            # Verbose logging

[application]
enable_web_ui = true       # Enable web interface
enable_config_api = false  # Enable config API
logging_level = "info"     # Log level
name = "Cow Repellent System"

[[camera]]
name = "Main Camera"
url = "rtsp://192.168.1.100/stream"
enable = true
track = true
test = false

[[repeller]]
name = "Left Repellent"
type = "test"
camera = "cam1"
enabled = true
```

### Pydantic Models

```python
class ModelConfig(BaseModel):
    name: str = "yolo26m"
    fuse: bool = True
    test: bool = False
    test_delay: int = 1
    verbose: bool = False

class ApplicationConfig(BaseModel):
    enable_web_ui: bool = False
    enable_config_api: bool = False
    logging_level: str = "info"
    name: str = "Cow Repellent System"
```

## Frontend

### Pages
- **Dashboard** (`front/index.html`) - Main monitoring view with camera grid
- **Devices** (`front/devices.html`) - Device management interface
- **Zones** (`front/zones.html`) - Interactive zone drawing tool
- **Settings** (`front/settings.html`) - System configuration

### Features
- Real-time camera streams via WebSocket
- Interactive zone drawing with polygon tools
- Device status monitoring with live updates
- Dark theme UI with responsive design

## Testing

### Mock Objects
- `VideoSourceMock` - Simulates video feed from file
- `DetectorMock` - Generates random detections
- `ModelMock` - Mocks YOLO model responses

### Test Mode
Enable in config.toml:
```toml
[model]
test = true
test_delay = 1  # Seconds between mock detections
```

## Dependencies

### Core
- Python 3.10+
- OpenCV (cv2)
- Ultralytics YOLO
- FastAPI + Uvicorn
- Pydantic + Pydantic Settings
- NumPy

### Frontend
- Vanilla JavaScript (no framework)
- SVG for zone visualization
- WebSocket API

## Development

### Project Structure
```
mid/
+-- main.py                 # Application entry point
+-- config.toml             # Configuration file
+-- managers/               # Core managers
|   +-- application_manager.py
|   +-- config_manager.py
|   +-- detection_manager.py
|   +-- device_manager.py
|   +-- source_manager.py
|   +-- ui_server.py
+-- objects/                # Domain objects
|   +-- detector.py
|   +-- device.py
|   +-- source.py
|   +-- zone.py
+-- util/                   # Utilities
|   +-- callbacks.py
|   +-- config.py
|   +-- config_api.py
|   +-- config_handlers.py
|   +-- frame_sender.py
|   +-- logger.py
+-- mocks/                  # Test mocks
|   +-- detector_mock.py
|   +-- model_mock.py
|   +-- source_mock.py
+-- front/                  # Web UI
    +-- index.html
    +-- devices.html
    +-- zones.html
    +-- settings.html
    +-- server.py
```

### Running the Application

```bash
# Install dependencies
pip install ultralytics fastapi uvicorn pydantic pydantic-settings opencv-python numpy websockets

# Run the application
python main.py

# Access web UI
open http://localhost:8000
```

### Environment Variables
- `CONFIG_FILE` - Path to configuration file (default: `config.toml`)
