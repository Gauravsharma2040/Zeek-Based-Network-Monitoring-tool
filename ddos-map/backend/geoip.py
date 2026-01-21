import geoip2.database
from pathlib import Path
_reader = None
def get_reader():
    global _reader
    if _reader is None:
        db_path = Path(__file__).parent / "GeoLite2-City.mmdb"
        _reader = geoip2.database.Reader(str(db_path))
    return _reader

def enrich(event: dict) -> dict:
    try:
        reader = get_reader()
        r = reader.city(event["src"])
        event["lat"] = r.location.latitude
        event["lon"] = r.location.longitude
    except Exception:
        event["lat"] = None
        event["lon"] = None
    return event
