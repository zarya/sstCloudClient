from __future__ import print_function
import requests
import json
import time
import codecs
import sys
import datetime

name = "sstCloudClient"

# stole this from requests libary. To determine whether we are dealing
# with Python 2 or 3
_ver = sys.version_info

#: Python 2.x?
is_py2=(_ver[0]==2)
#: Python 3.x?
is_py3=(_ver[0]==3)

class SstCloudClient:
    def __init__(self, username, password):
        self.email = username
        self.username = username
        self.password = password
        self.user_data = None
        self.full_data = None 
        self.homes_data = None 
        self.reader = codecs.getdecoder("utf-8")
        self.lastRefresh = datetime.datetime.now() 
    
    def _convert(self, object):
        return json.loads(self.reader(object)[0])

    def _populate_full_data(self, force_refresh=False):
        if self.full_data is None or force_refresh:
            self._populate_user_info()
            self._populate_homes_info()

            for house in self.homes_data:
                full_data = dict()
                full_data[house['id']] = dict() 
                full_data[house['id']]['House'] = house
                full_data[house['id']]['wired_sensor'] = list()
                full_data[house['id']]['water_counter'] = list()
                url = 'https://api.sst-cloud.com/houses/%s/devices/' % (house['id'])
                response = requests.get(url, headers=self.headers, cookies=self.user_data)
                full_data[house['id']]['Devices'] = list()
                if response.status_code != 200:
                    return False
                json_response = response.json()
                for device in response.json():
                    device['parsed_configuration'] = json.loads(device['parsed_configuration'])
                    full_data[house['id']]['Devices'].append(device)
                    _device = device['parsed_configuration']['settings']['lines_in']
                    for sensor, sensorType in _device.items():
                        if sensorType == "wired_sensor":
                            _sensor = {
                                    'name': sensor,
                                    'deviceid': device['id'],
                                    'homeid' : house['id'],
                                    'value' : device['parsed_configuration']['lines_status'][sensor]
                                    }
                            full_data[house['id']]['wired_sensor'].append(_sensor)
                    full_data[house['id']]['water_counter'] = self._get_home_dev_counters(house['id'],device['id'])
            self.full_data = full_data
            self.lastRefresh = datetime.datetime.now()

    def _get_home_dev_counters(self, homeid, deviceid):
        url = "https://api.sst-cloud.com/houses/%s/devices/%s/counters" % (homeid,deviceid)
        response = requests.get(url, headers=self.headers, cookies=self.user_data)
        return response.json()

    def _populate_homes_info(self):
        if self.homes_data is None:
            url = 'https://api.sst-cloud.com/houses/'
            response = requests.get(url, headers = self.headers, cookies = self.user_data)
            self.homes_data = response.json()
            if len(self.homes_data) > 1:
                raise Exception("More than one home available")

    def _populate_user_info(self):
        if self.user_data is None:
            url = 'https://api.sst-cloud.com/auth/login/'
            self.postdata = {'username':self.username,'password':self.password,'email':self.email,'language':'ru'}
            self.headers = {'content-type':'application/json', 'Accept': 'application/json'}

            response = requests.post(url, json=self.postdata, headers=self.headers)
            self.user_data = response.cookies
            self.headers['X-CSRFToken'] = response.cookies['csrftoken']
        return self.user_data

    def test(self):
        self._populate_full_data()
        print(json.dumps(self.homes_data,sort_keys=True,indent=4))
        print(json.dumps(self.full_data,sort_keys=True,indent=4))

    def waterCounters(self, houseid, force_refresh=False):
        self._populate_full_data(force_refresh)
        house = self.full_data[houseid]
        for sensor in house['water_counter']:
            sensor['deviceid'] = sensor['device']
            del sensor['device']
            sensor['homeid'] = houseid 
            yield sensor 

    def wiredSensors(self, homeid, force_refresh=False):
        self._populate_full_data(force_refresh)
        house = self.full_data[homeid]
        for sensor in house['wired_sensor']:
            yield sensor 

    def status(self, homeid, force_refresh=False):
        self._populate_full_data(force_refresh)
        house = self.full_data[homeid]
        status = list()
        for device in house['Devices']:
            status.append({
                'name':device['name'],
                'homeid':device['house'],
                'deviceid':device['id'],
                'close_valve_flag':device['parsed_configuration']['settings']['close_valve_flag'],
                'dry_flag':device['parsed_configuration']['settings']['dry_flag'],
                'valve_settings':device['parsed_configuration']['settings']['valve_settings'],
                'signal_level':device['parsed_configuration']['signal_level'],
                'alert':device['parsed_configuration']['settings']['status']['alert'],
                'dry_flag':device['parsed_configuration']['settings']['status']['dry_flag'],
                'sensors_lost':device['parsed_configuration']['settings']['status']['sensors_lost']
                })
        return status

    def setValve(self, homeid, deviceid, value=False):
        url = 'https://api.sst-cloud.com/houses/%s/devices/%s/valve_settings/' % (homeid, deviceid)
        data = {
                'valve_settings':'opened' if value else 'closed'
                }
        response = requests.post(url, json=data, headers = self.headers, cookies = self.user_data)
        self._populate_full_data(True)

    def setValveOpen(self, homeid, deviceid):
        self.setValve(homeid,deviceid,True)

    def setValveClosed(self, homeid, deviceid):
        self.setValve(homeid,deviceid,False)

    def getValve(self, homeid, deviceid):
        self._populate_full_data()
        house = self.full_data[homeid]
        for device in house['Devices']:
            if device['id'] == deviceid:
                return device['parsed_configuration']['settings']['valve_settings']
        return None

    def setDryFlag(self, homeid, deviceid, value=False):
        url = 'https://api.sst-cloud.com/houses/%s/devices/%s/dry_flag/' % (homeid, deviceid)
        data = {
                'dry_flag' : 'on' if value else 'off'
                }
        response = requests.post(url, json=data, headers = self.headers, cookies = self.user_data)
        self._populate_full_data(True)

    def setDryOn(self, homeid, deviceid):
        self.setDryFlag(homeid, deviceid, True)

    def setDryOff(self, homeid, deviceid):
        self.setDryFlag(homeid, deviceid, False)
