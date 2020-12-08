import paho.mqtt.client as mqtt
from time import sleep
from gpiozero import LED

client = mqtt.Client("mypi")

client.connect('broker.mqttdashboard.com')

client.publish('test/message12345678999', payload = 'hola', qos = 0, retain=False)
sleep(5)