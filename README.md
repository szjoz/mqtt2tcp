# Mqtt2Tcp Server

The primary purpose of the Mqtt2Tcp Server is to translate MQTT Messages to TCP/IP Connection. The Mqtt2Tcp Server performs Subscribing/Publishing MQTT messages (broker) based on keywords stored in configuration file and translating commands via TCP/IP. Mqtt2Tcp allows Zigbee devices (MQTT Subscribers/Publishers) to easily integrate with smart system, e.g. [taphome][tap-url]. Taphome system is able to integrate with other systems through simple ASCII integration protocol via TCP/IP. 

## Getting Started

These instructions explain how to run Mqtt2Tcp Server on single-board computers like Raspberry Pi, Orange Pi, etc. Allows to use with Zigbee2mqtt, It bridges events and allows you to control your Zigbee devices over MQTT service. In this way you can integrate your Zigbee devices with whatever smart home infrastructure you are using.
To run this bridge, you need the following hardware:
* Raspberry Pi board
* MicroSD card with installed [Rapbian][raspi-url]
* Power supply with at least 1A output
* CC2531 USB Dongle /*/
* [Supported Zigbee devices][devices-url]

/*/ Note: You need to flash CC2531 USB Dongle with CC Debugger or You can purchase with pre-programmed firmware. Instructions [here][cc-debugger-url].


At first you need to install Zigbee bridge Zigbee2Mqtt, follow these [instructions][instructions-url].

## 1. Download/Install Mqtt2Tcp

Clone mqtt2tcp repository
```
git clone https://github.com/szjoz/mqtt2tcp.git /opt/mqtt2tcp
```

## 2. Configuring Mqtt2Tcp

Edit config file

```
sudo nano /opt/mqtt2tcp/configuration.yaml
```

### 2.1. Logger settings

```
logger:
  log_prefix: Logger
  logging_level: DEBUG #DEBUG,INFO
  log_path: /var/log/Mqtt2Tcp.log
  log_max_size: 1000000
  log_backup_count: 20
```

Use Tail to View Your Log's

```
sudo tail -f /var/log/Mqtt2Tcp.log
```

### 2.2. MQTT Broker setup

```
mqtt:
  base_topic: zigbee2mqtt
  ip: localhost
  port: 1883
  keepalive: 60
```

### 2.3. TCP Connecton settings, fill in later

```
tcp:
  ip: 192.168.1.1
  port: 10003
  buffer_size: 1024
  timeout_on_recv: 5
```

### 2.4. Fill config file with paired Zigbee devices
e.g. [Xiaomi Smoke Detector][smoke-url], fill with "get_keys", in this example is only "smoke" get_keys used , more configurations [here][smoke-mqtt-url]

```
  '0x0000000000000000':
    friendly_name: smoke_detector
    get_keys:
        smoke:
            false : 'SET 12 0 0'
            true : 'SET 12 0 1' 
```

## 3. Integration into taphome
In Expose Devices add new TCP integration interface, set correct IP address and port number in the config file and same IP address (static, disable DHCP) and port set to the ControlUnit.
Create Virtual Device in App, e.g. VirtualSwitch or you can write Smoke detector state into Generic Variable. Add VirtualSwitch/Variable to Exposed Devices. Write correct ASCII command to set VirtualSwitch/Variable to the config file.


## 4. Run mqtt2tcp on Startup
### 4.1 Autostart mqtt2tcp with rc.local 
Edit file
```
sudo nano /etc/rc.local
```
and add this line before "exit 0"
```nohup python3 /opt/mqtt2tcp/Mqtt2Tcp.py </dev/null &>/dev/null &
```

### 4.2 Running as a daemon with systemctl
To run mqtt2tcp as daemon (in background) and start it automatically on boot we will run mqtt2tcp with systemctl. Create a systemctl configuration file for mqtt2tcp

```
sudo nano /etc/systemd/system/mqtt2tcp.service
```

Add the following to this file:

```
[Unit]

Description=mqtt2tcp
After=network.target

[Service]

ExecStart=/usr/bin/python3 /opt/mqtt2tcp/Mqtt2Tcp.py
StandardOutput=inherit
StandardError=inherit
Restart=always

[Install]
WantedBy=multi-user.target
```

Save the file and exit.
Verify that the configuration works:
##### Start mqtt2tcp
```
sudo systemctl start mqtt2tcp.service
```
##### Show status
```
systemctl status mqtt2tcp.service
```
##### To start mqtt2tcp automatically on boot
```
sudo systemctl enable mqtt2tcp.service
```


### Commands to start/stop service, view log
```
# Stopping mqtt2tcp
sudo systemctl stop mqtt2tcp

# Starting mqtt2tcp
sudo systemctl start mqtt2tcp

# View the log mqtt2tcp
sudo tail -f /var/log/Mqtt2Tcp.log
```

[raspi-url]: <https://www.raspberrypi.org/downloads/>
[cc-debugger-url]: <https://www.zigbee2mqtt.io/getting_started/flashing_the_cc2531.html>
[devices-url]: <https://www.zigbee2mqtt.io/information/supported_devices.html>
[instructions-url]: <https://www.zigbee2mqtt.io/getting_started/running_zigbee2mqtt.html>
[tap-url]: <https://taphome.com/en/support/171606078?e=t>
[smoke-url]: <https://xiaomi-mi.com/sockets-and-sensors/xiaomi-mijia-honeywell-smoke-detector-white/>
[smoke-mqtt-url]: <https://www.zigbee2mqtt.io/devices/JTYJ-GD-01LM_BW.html>
