from objects.source import VideoSource
from mocks.source_mock import VideoSourceMock


class VideoSourceManager:
    sources: dict[str, VideoSource] = dict()
    id_counter = 1

    def _gen_id(self, suf="src_"):
        id = suf + str(self.id_counter)
        self.id_counter += 1
        return id

    def add_source(self, source: VideoSource):
        id = self._gen_id()
        source.id = id
        self.sources[id]=source
        return id

    def has_source(self, name: str) -> bool:
        return any(s.name == name for s in self.sources.values())

    def get_source_by_id(self, id: str):
        return self.sources.get(id)

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
        source = self.has_source(name)
        if (test is not None) and test:
            source = VideoSourceMock(name=name)
        if not source:
            url = value.get("url")
            source = VideoSource(url, name)
        value.pop("name")
        value.pop("url")
        return source, value

    def create_source_from_dict(self, value: dict)-> str:
        src, value = self.get_source_from_dict(value)
        id = self.add_source(src)
        for v in value:
            self.config_source(src,v,value[v])

        return id

    def config_source(self, source, key, value):
        match key:
            case "enable":
                self.toggle_source(source, value)
                
    def remove_source(self, source):
        self.sources.pop(source.id)

    def serialize_source(self, source: VideoSource) -> dict:
        """Serialize a VideoSource object to a dictionary."""
        return {
            "id": source.id,
            "name": source.name,
            "source_url": source.source_url,
            "enabled": source.enabled,
        }

    def serialize_sources(self) -> list[dict]:
        """Serialize all sources to a list of dictionaries."""
        return [self.serialize_source(source) for source in self.sources.values()]
