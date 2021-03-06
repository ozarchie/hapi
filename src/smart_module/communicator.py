#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HAPI Master Controller v1.0
Release: March 2017 Alpha

Copyright 2016 Maya Culpa, LLC

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import print_function
import sys
import json
import datetime
import time
from log import Log
import paho.mqtt.client as mqtt
import notification
from alert import Alert

class Communicator(object):
    def __init__(self, sm):
        self.rtuid = ""
        self.name = ""
        self.broker_name = None
        self.broker_ip = None
        self.client = mqtt.Client(clean_session=True, userdata=None, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.smart_module = sm
        self.is_connected = False
        self.is_selected = False
        self.scheduler_found = False
        self.broker_connections = -1
        Log.info("Communicator initialized")

    def connect(self):
        """Connect to the broker."""
        try:
            Log.info("Connecting to %s at %s.", self.broker_name, self.broker_ip)
            self.client.connect(host=self.broker_ip, port=1883, keepalive=60)
            self.client.loop_start()
        except Exception as excpt:
            Log.exception("[Exiting] Error connecting to broker: %s", excpt)
            self.client.loop_stop()
            sys.exit(-1)

    def send(self, topic, message):
        try:
            if self.client:
                self.client.publish(topic, message)
        except Exception as excpt:
            Log.info("Error publishing message: %s.", excpt)

    def subscribe(self, topic):
        """Subscribe to a topic (QoS = 0)."""
        self.client.subscribe(topic, qos=0)

    def unsubscribe(self, topic):
        """Unsubscribe to a topic."""
        self.client.unsubscribe(topic)

# TODO check context as match from database
# -----------------------------------------
    def check_context(self, context):
        """Check context to see if required to respond to a topic"""
        if self.smart_module.asset.context == context:
            return True
        else:
            return False

# TODO check type as match from database
# --------------------------------------
    def check_type(self, stype):
        """Check context to see if required to respond to a topic"""
        if self.smart_module.asset.type == stype:
            return True
        else:
            return False

# TODO check asset as match from database
# --------------------------------------
    def check_asset(self, asset):
        """Check context to see if required to respond to a topic"""
        if self.smart_module.asset.id == asset:
            return True
        else:
            return False

    def check_selected(self, topic):
        """Check if required to respond to a topic"""
        level = topic.split("/")  # array of topic levels
        number_levels = len(topic.split("/"))  # number of levels

        # QUERY - Level1 - generic
        if  number_levels <= 2:  # Generic  query
            self.is_selected = True

        # QUERY - Level2 - NodeID
        elif  number_levels == 3:
            if level[2] == "#":  # Any NodeID
                self.is_selected = True
            elif level[2] == self.smart_module.id:
                self.is_selected = True

        # QUERY - Level3 - NodeID + context
        elif  number_levels == 4:
            if (
                level[2] == self.smart_module.id  # This smart module
                or level[2] == '+'  # Level expander
                ):
                if level[3] == "#":  # Any context
                    self.is_selected = True
                elif self.check_context(level[3]) is True:
                    self.is_selected = True

        # QUERY - Level4 - NodeID + context + type
        elif  number_levels == 5:
            if (
                topic.split("/")[2] == self.smart_module.id  # This smart module
                 or topic.split("/")[2] == '+'  # Level expander
                ):
                if (
                    self.check_context(level[3]) is True  # context match
                    or level[3] == '+'  # level expander
                    ):
                    if level[4] == "#":  # Any type
                        self.is_selected = True
                    elif self.check_type(level[4]) is True:  # type match
                        self.is_selected = True

        # QUERY - Level5 - NodeID + context + type + assetID
        elif  number_levels == 6:
            if (
                topic.split("/")[2] == self.smart_module.id  # This smart module
                 or topic.split("/")[2] == '+'  # Level expander
                ):
                if (
                    self.check_context(level[3]) is True  # context match
                    or level[3] == '+'  # level expander
                    ):
                    if (
                        self.check_type(level[4]) is True  # type match
                        or level[4] == '+'  # level expander
                        ):
                        if level[5] == "#":  # Any Asset
                            self.is_selected = True
                        elif self.check_asset(level[5]) is True:  # Asset match
                            self.is_selected = True

        # default is 'not selected'
        # -------------------------
        else:
            self.is_selected = False  # Set not-selected

    def on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        Log.info("[Exiting] Disconnected: %s", mqtt.error_string(rc))
        self.client.loop_stop()
        sys.exit(-1)

    # The callback for when the client receives a CONNACK response from the server.
    #@staticmethod
    def on_connect(self, client, userdata, flags, rc):
        Log.info("Connected with result code %s", rc)
        # Subscribing in on_connect() means if we lose connection and reconnect, subscriptions will
        # be renewed.
        #self.client.subscribe("SCHEDULER/LOCATE")
        self.is_connected = True
        self.subscribe("COMMAND" + "/#")
        self.subscribe("SCHEDULER/IDENT")
        self.subscribe("$SYS/broker/clients/total")
        self.subscribe("SYNCHRONIZE/DATA" + "/#")
        self.subscribe("SYNCHRONIZE/VERSION")
        self.subscribe("SYNCHRONIZE/CORE")
        self.subscribe("SYNCHRONIZE/GET")
        self.subscribe("ASSET/QUERY" + "/#")
        self.subscribe("STATUS/QUERY")
        self.subscribe("ENV/#")

    def on_message(self, client, userdata, msg):
        print(msg.topic)  # jma-debug
        print(msg.payload)  # jma-debug
        Log.info(msg.topic)
        if "ENV/QUERY" in msg.topic:
            self.smart_module.get_env()
        elif "ASSET/QUERY" in msg.topic:
            self.check_selected(msg.topic)
            if self.is_selected is True:  # Only send response if valid topic for the module
                asset_value = self.smart_module.get_asset_data()
                asset_unit = self.smart_module.get_asset_unit()
                json_data = (
                        {
                        "time": str(time.time()),
                        "value": str(asset_value).replace("u'", "'").replace("'", "\""),
                        "unit": str(asset_unit).replace("u'", "'").replace("'", "\"")
                        }
                        )
                json_asset = json.dumps(json_data)
                self.send(
                    "ASSET/RESPONSE/"
                    + self.smart_module.id + "/"
                    + self.smart_module.asset.context + "/"
                    + self.smart_module.asset.type + "/"
                    + self.smart_module.asset.id,
                    json_asset
                    )
        elif "ASSET/RESPONSE" in msg.topic:
            asset_id = (
                          msg.topic.split("/")[2] + "-"  # ID
                        + msg.topic.split("/")[3] + "-"  # Context
                        + msg.topic.split("/")[4] + "-"  # Type
                        + msg.topic.split("/")[5]        # ID (/Name)
                        )
            asset_info = json.loads(msg.payload)
            Log.info("AssetId = " + asset_id)
            self.smart_module.push_data(
                                        asset_id,  # assetID
                                        msg.topic.split("/")[3],  # Context
                                        asset_info["time"],
                                        asset_info["value"],
                                        asset_info["unit"]
                                        )
            alert = Alert()
            alert.update_alert(asset_id)
            if alert.check_alert(asset_info["value"]):
                json_alert = str(alert).replace("u'", "'").replace("'", "\"")
                self.send(
                        "ALERT/"
                        + msg.topic.split("/")[2] + "/"  # ID
                        + msg.topic.split("/")[3] + "/"  # Context
                        + msg.topic.split("/")[4] + "/"  # Type
                        + msg.topic.split("/")[5],       # Name
                        json_alert
                        )
        elif "STATUS/QUERY" in msg.topic:
            self.check_selected(msg.topic)
            if self.is_selected is True:  # Only send response if valid topic for the module
                self.smart_module.last_status = self.smart_module.get_status()
                json_payload = str(self.smart_module.last_status).replace("'", "\"")
                self.send(
                    "STATUS/RESPONSE/"
                    + self.smart_module.hostname
                    + "/System/",
                    json_payload
                    )
        elif "STATUS/RESPONSE" in msg.topic:
            status_payload = json.loads(msg.payload.replace("'", "\""))
            print(status_payload)  # jma debug
            self.smart_module.push_sysinfo("system", status_payload)

        elif "SCHEDULER/RESPONSE" in msg.topic:
            self.scheduler_found = True
            Log.info(msg.payload + " has identified itself as the Scheduler.")

        elif "SCHEDULER/QUERY" in msg.topic:
            self.check_selected(msg.topic)
            if self.is_selected is True:  # Only send response if valid topic for the module
                if self.smart_module.scheduler:
                    self.send("SCHEDULER/RESPONSE", self.smart_module.hostname)
                    Log.info("Sent SCHEDULER/RESPONSE")

        elif "SYNCHRONIZE/VERSION" in msg.topic:
            self.check_selected(msg.topic)
            if self.is_selected is True:  # Only send response if valid topic for the module
                self.send("SYNCHRONIZE/RESPONSE", self.smart_module.data_sync.read_db_version())

        elif "SYNCHRONIZE/GET" in msg.topic:
            self.check_selected(msg.topic)
            if self.is_selected is True:  # Only send response if valid topic for the module
                if msg.payload == self.smart_module.hostname:
                    self.smart_module.data_sync.publish_core_db(self)

        elif "SYNCHRONIZE/DATA" in msg.topic:
            self.check_selected(msg.topic)
            if self.is_selected is True:  # Only send response if valid topic for the module
                self.smart_module.data_sync.synchronize_core_db(msg.payload)

        elif "$SYS/broker/clients/total" in msg.topic:
            self.check_selected(msg.topic)
            if self.is_selected is True:  # Only send response if valid topic for the module
                if self.smart_module.scheduler:
                    self.broker_connections = int(msg.payload)

        elif "ALERT" in msg.topic:
            asset_payload = json.loads(msg.payload)
            if not asset_payload["notify_enabled"]:
                return
            asset_id = msg.topic.split("/")[1]
            site_name = self.smart_module.name
            time_now = datetime.datetime.now()
            value_now = asset_payload["value"]
            try:
                if "email" in asset_payload["response"]:
                    notify = notification.Email()
                    notify.send(
                        notify.subject.format(site=site_name, asset=asset_id),
                        notify.message.format(
                            time=time_now, site=site_name, asset=asset_id, value=value_now)
                    )
                if "sms" in asset_payload["response"]:
                    notify = notification.SMS()
                    notify.send(
                        "from",
                        "to",
                        notify.message.format(
                            time=time_now, site=site_name, asset=asset_id, value=value_now)
                    )
            except Exception as excpt:
                Log.exception("Trying to send notification: %s.", excpt)
