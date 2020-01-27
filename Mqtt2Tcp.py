#!/usr/bin/env python3

#To run after reboot add line here: sudo nano /etc/rc.local
#Run on backround: nohup python3 /home/pi/Mqtt2Tcp.py </dev/null &>/dev/null &

from __future__ import absolute_import, division, print_function, \
												   unicode_literals
import os
import time
import paho.mqtt.client as mqtt
import json
import socket
import logging
import logging.handlers
import yaml
from threading import Thread
import colorsys


conf_path = os.path.dirname(os.path.realpath(__file__))
with open(conf_path + r'/configuration.yaml') as stream:
	try:
		config = yaml.load(stream, Loader=yaml.FullLoader)
	except yaml.YAMLError as exc:
		print(exc)
		pass

logger = None

def create_logger():
	global logger
	logger = logging.getLogger(config['logger']['log_prefix'])
	level = logging.getLevelName(config['logger']['logging_level'])
	logger.setLevel(level)
	handler = logging.handlers.RotatingFileHandler(str(config['logger']['log_path']), maxBytes=config['logger']['log_max_size'], backupCount=config['logger']['log_backup_count'])
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

create_logger()


def process_tcp_message(config, tcp_valid_message):
	logger.info("Process TCP message::" + str(tcp_valid_message))

	for key,value in config['devices'].items():
		try:
			logger.debug("Device: " +  str(value['friendly_name']) + ". Show set_values:" + str(value['set_keys']) + ". Show json_format from yaml:" + str(value['json_format']))
			for k,v in value['set_keys'].items():
				logger.debug("Device: " +  str(value['friendly_name']) + ". Show action set_keys:" + str(k) + ", " + str(v) + ".")
				if (v != None):
					logger.debug("Device: " +  str(value['friendly_name']) + ". Show action set_keys:" + str(k) + ", " + str(v) + ".")
					device_id_from_conf = v.replace("GET ", "")
					logger.debug("Received TCP data:" + str(tcp_valid_message))
					values = tcp_valid_message.split(",")
					device_id = values[0]
					values.pop(1) # remove unused value
					values.pop(0) # remove unused value
					if device_id_from_conf == device_id:
						json_object = json.loads(value['json_format'])
						logger.debug("Read JSON Format:" + value['json_format'])
						logger.debug("Print JSON object:" + str(json_object))
						if len(values) == 1 and k == 'state': #boolean
							logger.debug("Size:" + str(len(values)) + ", Bool values:" + str(values))
							if float(values[0]) == 1:
								json_object[k] = 'ON'
							else:
								json_object[k] = 'OFF'

							logger.info("Send JSON BOOLEAN:" + str(json_object))
							json_data = json.dumps(json_object)
							client.publish("zigbee2mqtt/" + value['friendly_name'] + "/set", json_data);
						elif len(values) != 1 and k == 'hsv': #RGB
							logger.debug("Size:" + str(len(values)) + ", HSV values:" + str(values))
							r,g,b = colorsys.hsv_to_rgb(float(values[0])/360.0, float(values[1]), float(values[2]))
							logger.debug("Print R:" + str(r*255) + " G:" + str(g*255) + " B:" + str(b*255))
							json_object['color']['r'] = r*255
							json_object['color']['g'] = g*255
							json_object['color']['b'] = b*255
							if float(values[2]) > 0.05:
								json_object['brightness'] = float(values[2])*255
							else:
								json_object['brightness'] = 0

							#json_data = json.dumps({"brightness":json_object['brightness']})
							#client.publish("zigbee2mqtt/" + value['friendly_name'] + "/set", json_data);

							logger.info("Send JSON RGB/HSV:" + str(json_object))
							json_data = json.dumps(json_object)
							client.publish("zigbee2mqtt/" + value['friendly_name'] + "/set", json_data);

						else:
							logger.info("Size:" + str(len(values)) + ", value:" + str(values))

		except:
			logger.debug("No set_keys defined for device " + str(value['friendly_name']))
			pass


def tcp_connection_thread(config, ):
	global s
	global socket_connected
	global socket_need_reconnect
	logger.info("Starting TCP connection thread")
	while True:
		if (socket_connected != True):
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				s.settimeout(config['tcp']['timeout_on_recv'])

				s.connect((config['tcp']['ip'], config['tcp']['port']))
				logger.info("Opening TCP socket:" + str(config['tcp']['ip']) + ":" + str(config['tcp']['port']) + " successful.")
				s.send(str('PUSHALL ON\r\n').encode())
				socket_connected = True
				socket_need_reconnect = False
			except:
				logger.info("Opening TCP socket:" + str(config['tcp']['ip']) + ":" + str(config['tcp']['port']) + " failed!")
				s.close()
				s = None
				time.sleep(1)
				pass

		if (socket_need_reconnect == True) and (socket_connected == True):
				logger.info("Need reconnect.")
				s.close()
				time.sleep(1)
				socket_connected = False
				socket_need_reconnect = False
		time.sleep(10)

def tcp_receive_thread():
	global s
	global socket_connected
	logger.info("Starting TCP Receive thread:")		

	#for key,value in config['devices'].items():
	#	try:
	#		client.publish("zigbee2mqtt/" + str(value['friendly_name']) + "/get");
	#		logger.info("Get last state of device:" + str(value['friendly_name']))
	#	except:
	#		logger.info("Get last state exception:" + str(value['friendly_name']))
	#		pass
	
	#data = {"state":"ON","brightness":25,"hue": 360,"saturation":100,"transition":3}#     "hue": 360,"saturation":100
	#data = {"state":"ON","brightness":255,"color":{"r":255,"g":200,"b":100},"transition":1}
	#data = {"state":"ON","brightness":255,"color":{"x":0.19,"y":0.2038},"transition":1}
	#data = {"state":"ON","brightness":10,"color_mode":3,"color":{"hue": 300,"saturation":99},"transition":1}
	#json_data = json.dumps(data)
	#client.publish("zigbee2mqtt/tradfri_rgb/set", json_data);
	#logger.info("Create JSON. On init." + str(data))

	last_message = None
	while True:
		#time.sleep(1)
		if socket_connected == True:
			try:
				data = s.recv(config['tcp']['buffer_size']).decode('UTF-8')
				logger.debug("Receive all:" + str(data))
				if data != '':
					temp_data_list = data.split('\r\n')
					logger.debug("Received msg:" + str(temp_data_list) + ", Size of list:" + str(len(temp_data_list)))
					for message in temp_data_list:
						if message and last_message != message:
							logger.debug("Valid received message:" + str(message))
							last_message = message
							process_tcp_message(config, message)
			except socket.timeout as e:
				err = e.args[0]
				if err == 'timed out':
					#time.sleep(1)
					#logger.info("Recv timed out:" + str(err))
					continue
				else:
					logger.info("Recv Except timeout:" + str(err))
					pass
			except socket.error as e:
				logger.info("Recv Except Error:" + str(e))
				time.sleep(5)
				pass



def on_connect(client, userdata, flags, rc):
	if rc==0:
		logger.info("MQTT: Connected OK Returned code=" + str(rc))
		client.subscribe(config['mqtt']['base_topic'] + "/#")
	else:
		logger.info("MQTT: Bad connection Returned code=" + str(rc))

def on_message(client, userdata, msg):
	global socket_need_reconnect
	m_decode=str(msg.payload.decode("utf-8","ignore"))
	m_in=json.loads(m_decode) #decode json data
	logger.info("MQTT: Message received. Topic:" + str(msg.topic) + ", Message:" + str(m_decode))
	if msg.topic.startswith(config['mqtt']['base_topic']):
		for key,value in config['devices'].items():
			logger.debug("Key:" + str(key) + ", Value:" + str(value['friendly_name']))
			if str(msg.topic) == (str(config['mqtt']['base_topic'] + "/" + value['friendly_name'])):
				try:
					logger.debug("Device: " +  str(value['friendly_name']) + ". Show values:" + str(value['get_keys']))
					for k,v in value['get_keys'].items():
						logger.debug("Device: " +  str(value['friendly_name']) + ". Show action get_keys:" + str(k) + ", " + str(v) + ".")
						for mqtt_value,tcp_str in value['get_keys'][k].items():
							logger.debug("Device: " +  str(value['friendly_name']) + ". Show get_states:" + str(mqtt_value) + ", " + str(tcp_str) +".")
							#if (str(message).find(k) != -1) and (str(message).find(mqtt_value) != -1):
							if (m_in[k] == mqtt_value):

								try:
									s.send(str(tcp_str + '\r\n').encode())
									logger.info("Sending TCP message successful:" + str(tcp_str) + ", friendly_name:" + str(value['friendly_name']) + ", Action get_key:" + str(k) + ", State:" + str(mqtt_value) + ".")
								except:
									logger.info("Failed to send TCP message:" + str(tcp_str) + ", friendly_name:" + str(value['friendly_name']) + ", Action get_key:" + str(k) + ", State:" + str(mqtt_value) + ".")
									logger.info("Trying to reconnect:" + str(config['tcp']['ip']) + ":" + str(config['tcp']['port']) + ".")
									socket_need_reconnect = True
									time.sleep(5)
									pass
							elif (mqtt_value == "int_val"):
								try:
									logger.info("Parse integer value, Action key:" + str(k) + ", Value:" + str(m_in[k]) + ".")
									tcp_mes = str(tcp_str) + ' ' + str(m_in[k]) + '\r\n'
									s.send(tcp_mes.encode())
									logger.info("Sending TCP message successful:" + str(tcp_str) + ' ' + str(m_in[k]) + ", friendly_name:" + str(value['friendly_name']) + ", Action key:" + str(k) + ", State:" + str(mqtt_value) + ".")
								except:
									logger.info("Failed to send TCP  message:" + str(tcp_str) + ' ' + str(m_in[k])  + ", friendly_name:" + str(value['friendly_name']) + ", Action key:" + str(k) + ", State:" + str(mqtt_value) + ".")
									logger.info("Trying to reconnect:" + str(config['tcp']['ip']) + ":" + str(config['tcp']['port']) + ".")
									socket_need_reconnect = True
									time.sleep(5)
									pass
							else:
								logger.debug("Unknown action key! Do nothing.  Message:" + str(m_decode) + ".")
				except:
					logger.debug("No get_keys defined for device " + str(value['friendly_name']))
					pass

	else:
		logger.info("Unknown topic! " + str(msg.topic))

	if str(m_decode) == "test":
		logger.debug("Test message. Client:" + str(client) + ", User data:" + str(userdata) + ", Message:" + str(m_decode))

# Connect to the broker/server
client = mqtt.Client()
client.connect(config['mqtt']['ip'],config['mqtt']['port'],config['mqtt']['keepalive'])

client.on_connect = on_connect
client.on_message = on_message

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.settimeout(config['tcp']['timeout_on_recv'])
socket_connected = False
socket_need_reconnect = False

t = Thread(target=tcp_connection_thread, args=(config , ))
t.start()

u = Thread(target=tcp_receive_thread, args=())
u.start()

client.loop_forever()

