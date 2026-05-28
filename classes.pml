@startuml
left to right direction
class Detector {
    Model
    VideoSource
start_tracking(callback: fn)
}
class Zone{
    coords: int[]
}
class DeviceManager{
    devices: Device[]
    set_zone_to_device()
    get_devices_by_zone(Zone)
}
class Device{
    on()
    off()
}
class VideoSource {
    name: str
    source_url: str
}
class VideoSourceManager {
    sources: VideoSource[]
    set_zone_to_source()
}
class SyncWSServe{
}
class ServerConfig{
}
class fn{}

fn -> SyncWSServer
Detector -> fn
Detector -> VideoSource
VideoSourceManager -> VideoSource
ServerConfig -> Detector
ServerConfig -> VideoSourceManager
DeviceManager -> Device
DeviceManager -> Zone
@enduml