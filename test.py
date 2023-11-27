#!/usr/local/bin/python3
import asyncio
import dataclasses
import json
import threading
import store

from datetime import datetime
from sungrowinverter import SungrowInverter

@dataclasses.dataclass
class PacketData:
    id: str = ''
    timestamp: int = 0
    loadPower: int = 0
    exportPower: int = 0
    batteryPower: int = 0
    batteryLevel: int = 0

    def __add__(self, other):
        sum = PacketData()
        sum.id = other.id
        sum.timestamp = max(self.timestamp, other.timestamp)
        sum.loadPower = self.loadPower + other.loadPower
        sum.exportPower = self.exportPower + other.exportPower
        sum.batteryPower = self.batteryPower + other.batteryPower
        sum.batteryLevel = self.batteryLevel + other.batteryLevel
        return sum

    def __itruediv__(self, divisor):
        ret = PacketData()
        ret.id = self.id
        ret.timestamp = self.timestamp
        ret.loadPower = self.loadPower / divisor
        ret.exportPower = self.exportPower / divisor
        ret.batteryPower = self.batteryPower / divisor
        ret.batteryLevel = self.batteryLevel / divisor
        return ret

client = SungrowInverter("192.168.1.3", timeout=5)
readings = []

def toEpoch(timestamp: str):
    p = '%Y/%m/%d %H:%M:%S'
    epoch = datetime(1970, 1, 1)
    return (datetime.strptime(timestamp, p) - epoch).total_seconds()

def storeValues(data: PacketData):
    #print(json.dumps(dataclasses.asdict(data)))
    print(f'Data: {data.timestamp} ES: {data.exportPower} LP: {data.loadPower} BP: {data.batteryPower} ({data.batteryLevel})')
    readings.append(data)
    if data.timestamp % 10 == 0:
        dataAvg = PacketData()
        for d in readings:
            dataAvg += d

        dataAvg /= len(readings)
        store.storeData('sungrow', dataclasses.asdict(dataAvg), 10)
        readings.clear()

def readValues():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(client.async_update())

    #Get a list data returned from the inverter.
    if result:
        data = PacketData()
        data.id = client.data['serial_number']
        data.timestamp = int(toEpoch(str(client.data['timestamp'])))
        data.batteryLevel = client.data['battery_level']
        data.batteryPower = client.data['battery_power']
        data.exportPower = client.data['export_power']
        data.loadPower = client.data['load_power']

        storeValues(data)
    else:
        print("Could not connect to inverter")

def timerFunc():
    t = threading.Timer(0.1, timerFunc).start()
    startTime = datetime.now()
    if (startTime.second % 2) == 0 and startTime.microsecond < 100000:
        readValues()
        #diff = datetime.now() - startTime

def main():
    timerFunc()


if __name__ == '__main__':
    main()