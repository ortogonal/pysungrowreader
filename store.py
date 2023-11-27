import json
import redis

def storeData(type: str, data: dict, delta: int):
    packet = { 'type': type, 'data': data, 'delta': delta}
    print(json.dumps(packet, indent=2))

    r = redis.Redis(host='192.168.1.15', port=6379, decode_responses=True)
    r.lpush('readings_queue', json.dumps(packet))
