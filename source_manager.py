from source import VideoSource
from source_mock import VideoSourceMock


class VideoSourceManager:
    sources = []

    def add_source(self, source: VideoSource):
        self.sources.append(source)
        return self.sources.index(source)

    def has_source(self, name: str) -> bool:
        return any(s.name == name for s in self.sources)

    def get_source(self, name: str):
        try:
            i = self.sources.index(name)
        except ValueError:
            i = -1
        if i >= 0:
            return self.sources[i]
        else:
            return None

    def toggle_source(self, source: VideoSource, enable=None):
        if enable is None:
            source.enabled = not source.enabled
        else:
            source.enabled = enable
        if source.enabled:
            source.start_reading()

    def get_source_from_dict(self, value: dict):
        test = value.get("test")
        name = value.get("name")
        source = self.get_source(name)
        if test:
            source = VideoSourceMock(name=name)
        if not source:
            url = value.get("url")
            source = VideoSource(url, name)
        value.pop("name")
        value.pop("url")
        return source, value

    def config_source(self, source, key, value):
        match key:
            case "enable":
                self.toggle_source(source, value)

    def serialize_source(self, source: VideoSource) -> dict:
        """Serialize a VideoSource object to a dictionary."""
        return {
            "name": source.name,
            "source_url": source.source_url,
            "enabled": source.enabled,
        }

    def serialize_sources(self) -> list[dict]:
        """Serialize all sources to a list of dictionaries."""
        return [self.serialize_source(source) for source in self.sources]
