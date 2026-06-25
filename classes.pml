@startuml VisionGuard

skinparam classAttributeIconSize 0
skinparam linetype ortho
skinparam nodesep 60
skinparam ranksep 40

title VisionGuard - Cow Repellent System\nClass Diagram

' ===== Domain Objects =====
package "objects" {
  class VideoSource {
    - id : str
    - source_url : str
    - name : str
    - _lock : threading.Lock
    - enabled : bool
    - _latest_frame : np.ndarray
    - _cap : cv2.VideoCapture
    - ready : threading.Event
    - _frame_timestamp : datetime
    + get_frame_with_timestamp() : tuple
    + get_frame() : np.ndarray
    + get_frame_timestamp() : datetime
    + start_reading()
    + stop_reading()
    + frame_generator() : Generator
    + get_resolution() : tuple
    + get_fps() : float
    + release()
  }

  class VideoSourceMock {
    + _start()
    + _get_cap()
  }

  class Detected {
    + box : numpy array
    + name : str
  }

  class Detector {
    - source : VideoSource
    - model : YOLO
    - callback : Callable
    - allowed_classes : set
    - running : bool
    - last_frame : np.ndarray
    - current_boxes : set
    - last_detections : list[Detected]
    - verbose : bool
    - thread : threading.Thread
    + track(frame) : results
    + start_tracking()
    + pause_tracking()
    - _start_tracking()
    - _handle_results(results)
  }

  class DetectorMock {
    + _start_tracking()
    - _generate_results(frame) : list[Detected]
  }

  class Zone {
    + coords : np.ndarray
    + active : bool
    + id : str
    + name : str
    + get_int_coords() : list
    + gen_square_zone(x1, y1, x2, y2) : Zone <<classmethod>>
    + gen_free_form_zone(dots) : Zone <<classmethod>>
    - _get_np_array(coords) : np.ndarray
  }

  class Device {
    + id : str
    + name : str
    + type : str
    - _active : bool
    - _callbacks : list
    + register_callback(callback)
    + on()
    + off()
    + is_active() : bool
    - _notify_callbacks()
  }

  class HttpDevice {
    + on_url : str
    + off_url : str
    + on()
    + off()
    - _send_request(url)
  }
}

' ===== Managers =====
package "managers" {
  class ApplicationManager {
    + video_source_manager : VideoSourceManager
    + detection_manager : DetectionManager
    + device_manager : DeviceManager
    + start_time : datetime
    + name : str
    + ui : bool
    + get_uptime() : str
    + get_status() : str
    + get_name() : str
    + serialize() : dict
    - _time_since() : str
  }

  class VideoSourceManager {
    - sources : dict[str, VideoSource]
    - id_counter : int
    + add_source(source) : str
    + has_source(name) : bool
    + get_source_by_id(id) : VideoSource
    + toggle_source(source, enable)
    + get_source_from_dict(value) : tuple
    + create_source_from_dict(value) : str
    + config_source(source, key, value)
    + remove_source(source)
    + serialize_source(source) : dict
    + serialize_sources() : list[dict]
    - _gen_id(suf) : str
  }

  class DetectionManager {
    - _detectors : dict[str, Detector]
    - enabled_detectors : set[Detector]
    - running : bool
    - model : YOLO
    - _devices : dict[str, Device]
    - mock : bool
    - mock_delay : int
    - _detector_callbacks : dict
    - _zones_source : dict[Zone, VideoSource]
    - _zones_devices : dict[Zone, Device]
    - model_verbose : bool
    + make_detection(source, callback)
    + set_model(model)
    + get_source_zones(source) : list[Zone]
    + enable_detection(source)
    + disable_detection(source)
    + start()
    + join_trackers()
    + add_zone_from_dict(data) : Zone
    + add_zone(zone, source)
    + remove_zone(zone_id) : Zone
    + update_zone(zone_id, data) : Zone
    + find_zone(zone_id) : Zone
    + remove_zones_for_source(source)
    + assign_device(device, zone)
    + serialize_detector(detector) : dict
    + serialize_detectors() : list[dict]
    + serialize_device_mapping() : dict
    + serialize_zone(zone) : dict
    + serialize_zones(zones) : list[dict]
    + get_last_detections(source) : list[Detected]
    + get_last_detected_frame(source) : np.ndarray
    - _gen_zone_id(suf) : str
    - _get_detection(source) : Detector
  }

  class DeviceManager {
    - devices : dict[str, Device]
    - enabled_devices : set[Device]
    - on_change : Callable
    + make_device(name, type, on_url, off_url) : Device
    + make_device_from_dict(data) : Device
    + get_devices() : dict
    + get_device_by_id(id) : Device
    + get_devices_by_id(ids) : list[Device]
    + enable_device(device)
    + disable_device(device)
    + switch_device(device, active)
    + toggle_device(device, enable)
    + delete_device(device)
    + serialize_device(device) : dict
    + serialize_devices() : list[dict]
    - _gen_dev_id(suf) : str
    - _on_device_active_change(device, state)
    - _notify_change(device, action)
  }

  class AppConfigManager {
    - _config : dict
    - _callbacks : dict
    + set_callback(name, callback)
    + set(name, val)
    + update_all(priorities)
    + get_callbacks(name) : list[Callable]
    + serialize_config() : dict
    + serialize_settings() : dict
    - _update(name)
  }

  class UIServer {
    - app : FastAPI
    - application_manager : ApplicationManager
    - ACTIVE_WEBSOCKETS : dict
    - ACTIVE_DEVICE_WEBSOCKETS : set
    - _loop : asyncio.AbstractEventLoop
    - _font_large : ImageFont
    - _font_small : ImageFont
    + run(host, port)
    - _setup_routes()
    - _setup_site_routes(app)
    - _setup_device_routes(app)
    - _setup_system_routes(app)
    - _setup_settings_routes(app)
    - _setup_source_routes(app)
    - _setup_zone_routes(app)
    - _setup_cors()
    - _setup_startup()
    - _generate_frame(camera_id)
    - _load_fonts()
    - _on_device_change(device, state, action)
    - _convert_frame(camera_id, frame)
    + broadcast_device_update(device_data, action)
  }
}

' ===== Utility =====
package "util" {
  class ZoneCallback {
    - _devices : list[Device]
    - whitelist : list[str]
    - blocklist : list[str]
    - _zone_devices : dict[Zone, Device]
    + has_zone(zone) : bool
    + add_zone(zone)
    + remove_zone(zone)
    + add_device_to_zone(zone, device)
    + callback(detected, frame, source) : bool
    + turn_off_all()
  }

  class DeviceCallback {
    - _devices : list[Device]
    - whitelist : list[str]
    - blocklist : list[str]
    - _zone_devices : dict[Zone, Device]
    - _to_off : dict
    + callback(detected, frame, source) : bool
    + turn_off_all()
  }

  class CliCallback {
    - name : str
    + callback(detected, frame, source)
  }

  class SyncWSServer {
    - host : str
    - port : int
    - queue : queue.Queue
    - _loop : asyncio.AbstractEventLoop
    - _thread : threading.Thread
    - _ready : threading.Event
    + start()
    + send(image_bytes, boxes)
    + stop()
    - _run_async_server()
  }

  class WebConfigServer {
    - _app : FastAPI
    + start()
    + stop()
    - _setup_routes()
  }
}

' ===== Config Models =====
package "util/config" <<Rectangle>> {
  class Settings {
    + model : ModelConfig
    + application : ApplicationConfig
    + repellers : list[RepellerConfig]
    + cameras : list[CameraConfig]
    + zones : list[ZoneConfig]
  }

  class ModelConfig {
    + name : str
    + fuse : bool
    + test : bool
    + test_delay : int
    + verbose : bool
  }

  class ApplicationConfig {
    + enable_web_ui : bool
    + enable_config_api : bool
    + logging_level : str
    + name : str
  }

  class RepellerConfig {
    + name : str
    + type : str
    + camera : str
    + on_url : str
    + off_url : str
    + enabled : bool
  }

  class CameraConfig {
    + name : str
    + url : str
    + enable : bool
    + track : bool
    + test : bool
  }

  class ZoneConfig {
    + name : str
    + camera : str
    + active : bool
    + points : list[PointConfig]
    + linked_devices : list[str]
  }

  class PointConfig {
    + x : float
    + y : float
  }
}

' ===== Mock Classes =====
package "mocks" {
  class ModelMock {
    + track(frame, ...) : ResultMock
  }

  class ResultMock {
    + orig_img
  }
}

' ===== Pydantic API Models (UIServer) =====
package "managers/ui_server.py\n(Pydantic Models)" <<Rectangle>> {
  class DeviceCreate {
    + name : str
    + type : str
    + on_url : str
    + off_url : str
  }
  class DeviceUpdate {
    + name : str
    + type : str
    + on_url : str
    + off_url : str
  }
  class CameraCreate {
    + name : str
    + url : str
    + enable : bool
    + test : bool
  }
  class CameraUpdate {
    + name : str
    + url : str
    + enable : bool
  }
  class Point {
    + x : float
    + y : float
  }
  class ZoneCreate {
    + name : str
    + camera_id : str
    + active : bool
    + points : list[Point]
    + linked_devices : list[str]
  }
  class ZoneUpdate {
    + name : str
    + active : bool
    + points : list[Point]
    + linked_devices : list[str]
  }
  class SettingsUpdate {
    + model : dict
    + application : dict
  }
}

' ===== INHERITANCE =====
VideoSource <|-- VideoSourceMock
Detector <|-- DetectorMock
Device <|-- HttpDevice

' ===== COMPOSITION =====
ApplicationManager *-- VideoSourceManager
ApplicationManager *-- DetectionManager
ApplicationManager *-- DeviceManager

UIServer o-- ApplicationManager : reference

VideoSourceManager o-- "0..*" VideoSource : sources
DetectionManager o-- "0..*" Detector : _detectors
DetectionManager o-- "0..*" ZoneCallback : _detector_callbacks
DetectionManager o-- "0..*" Zone : _zones_source
DetectionManager o-- "0..*" Device : _zones_devices
DeviceManager o-- "0..*" Device : devices
DeviceManager o-- "0..*" Device : enabled_devices

' ===== ASSOCIATIONS =====
Detector o-- "1" VideoSource : source
Detector o-- "1" Detected : last_detections
ZoneCallback o-- "0..*" Zone : _zone_devices
ZoneCallback o-- "0..*" Device : _zone_devices
DeviceCallback o-- "0..*" Zone : _zone_devices
DeviceCallback o-- "0..*" Device : _devices

UIServer ..> CameraCreate
UIServer ..> CameraUpdate
UIServer ..> DeviceCreate
UIServer ..> DeviceUpdate
UIServer ..> ZoneCreate
UIServer ..> ZoneUpdate
UIServer ..> SettingsUpdate
UIServer ..> Point

' Config managers
AppConfigManager ..> Settings : reads
AppConfigManager ..> ModelConfig
AppConfigManager ..> ApplicationConfig
AppConfigManager ..> RepellerConfig
AppConfigManager ..> CameraConfig
AppConfigManager ..> ZoneConfig

' Mocks
ModelMock ..> ResultMock : returns

@enduml
