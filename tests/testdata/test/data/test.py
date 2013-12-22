import json
import time

result = {
    "user" : "hefangshi",
    "time" : time.time(),
    "2333" : 233
}

handler.set_header('Content-Type','application/json')
handler.write(json.dumps(result))