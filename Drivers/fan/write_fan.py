#!/usr/bin/env python3
import gatt
import sys
import struct
from mqtt_client import MQTTClient
import os
import time

# This module was developed for testing purposes and is not required in the final product
# It sends a single command to the fan taken from the command line.

# Instead, you want to use publish_fan.py and fan.py together which achieve the same result
# while also being able to be called multiple times to change the fan speed
# and reporting back the current value (roughly every second)

# Subclass gatt.DeviceManager to allow discovery only of HEADWIND devices
# When the alias begins with the required prefix, connect to the device
class AnyDeviceManager(gatt.DeviceManager):
	def device_discovered(self, device):
		alias = device.alias()
		if alias is not None and self.prefix is not None and len(alias) >= len(self.prefix) and alias[0:len(self.prefix)] == self.prefix:
			#print("[%s] Discovered, alias = %s" % (device.mac_address, device.alias()))
			device = AnyDevice(mac_address=device.mac_address, manager=self)
			device.speed = self.speed
			device.state = 0
			device.connect()


# Send a given value to the fan through Bluetooth
class AnyDevice(gatt.Device):
	# When the program exits, stop measurements and discovery services
	def __del__(self):
		self.stop_measurements()
		self.manager.stop_discovery()

	# Called when the connection succeeds
	def connect_succeeded(self):
		super().connect_succeeded()
		#print("[%s] Connected" % (self.mac_address))


	# Called when the connection fails
	# Display an error message on the console
	def connect_failed(self, error):
		super().connect_failed(error)
		print("[%s] Connection failed: %s" % (self.mac_address, str(error)))


	# Called with disconnection succeeds
	def disconnect_succeeded(self):
		super().disconnect_succeeded()
		#print("[%s] Disconnected" % (self.mac_address))


	def services_resolved(self):
		super().services_resolved()
		print("Services resolved")
		self.manager.stop_discovery()

		self.enable_service = next(
			s for s in self.services
			if s.uuid[4:8] == 'ee01')

		self.enable_characteristic = next(
			c for c in self.enable_service.characteristics
			if c.uuid[4:8] == 'e002')

		self.fan_service = next(
			s for s in self.services
			if s.uuid[4:8] == 'ee0c')

		self.fan_characteristic = next(
			c for c in self.fan_service.characteristics
			if c.uuid[4:8] == 'e038')

		self.enable_characteristic.enable_notifications()
		self.fan_characteristic.enable_notifications()

		# Enable write permission
		value = bytes([0x20, 0xee, 0xfc])
		self.enable_characteristic.write_value(value)
		print(f"Enable write permission {self.state}")

	def stop_measurements(self):
		self.enable_characteristic.enable_notifications(False)
		self.fan_characteristic.enable_notifications(False)

	def characteristic_write_value_succeeded(self, characteristic):
		if characteristic == self.enable_characteristic:
			print(f"Communication enabled")
			if self.state < 3:
				print(f"Enable write permission {self.state}")
				value = bytes([0x20, 0xee, 0xfc])
				self.enable_characteristic.write_value(value)
			else:
				print(f"Turn on {self.state}")
				value = bytes([0x04, 0x04])
				self.fan_characteristic.write_value(value)
			self.state = self.state + 1
		if characteristic == self.fan_characteristic:
			if self.state < 6:
				print(f"Turn on {self.state}")
				value = bytes([0x04, 0x04])
				self.fan_characteristic.write_value(value)
				self.state = self.state + 1
			elif self.state < 9:
				value = bytes([0x02, self.speed])
				self.fan_characteristic.write_value(value)
				print(f"Speed set to {self.speed}")
				self.state = self.state + 1


	def characteristic_write_value_failed(self, error):
		print("Write failed")

	def characteristic_enable_notifications_succeeded(self, characteristic):
		print("Notifications enabled")

	def characteristic_enable_notifications_failed(self, characteristic, error):
		print("Notifications failed")

	def characteristic_value_updated(self, characteristic, value):
		if characteristic == self.enable_characteristic:
			print(f"Updated Enable: {value}")
		if characteristic == self.fan_characteristic:
			print(f"Updated Fan: {value}")

def main():
	try:
		if len(sys.argv) != 2:
			print(f"Usage: {sys.argv[0]} speed")
			print("Where speed is in range 0 to 100")
			exit(1)

		speed = int(sys.argv[1])
		if speed < 0 or speed > 100:
			print(f"Usage: {sys.argv[0]} speed")
			print("Where speed is in range 0 to 100")
			exit(1)

		adapter_name=os.getenv('FAN_ADAPTER_NAME')
		alias_prefix=os.getenv('FAN_ALIAS_PREFIX')

		global mqtt_client
		global deviceId
		mqtt_client = MQTTClient(os.getenv('MQTT_HOSTNAME'), \
			os.getenv('MQTT_USERNAME'), os.getenv('MQTT_PASSWORD'))
		mqtt_client.setup_mqtt_client()
		deviceId = os.getenv('DEVICE_ID')

		manager = AnyDeviceManager(adapter_name=adapter_name)
		manager.prefix=alias_prefix
		manager.speed = speed
		manager.start_discovery()
		manager.run()
	except KeyboardInterrupt:
		pass


if __name__=="__main__":
    main()
