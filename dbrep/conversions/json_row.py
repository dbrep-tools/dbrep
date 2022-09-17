from .base import BaseFormat
from . import add_conversion
import json

class JSONRowFormat(BaseFormat):
    id = 'JSONRow'

    def __init__(self, config):
        super().__init__(config)

    def from_bytes(self, bytes):
        return json.loads(bytes.decode('utf-8'))
    
    def to_bytes(self, object):
        return json.dumps(object).encode('utf-8')

add_conversion(JSONRowFormat)