from flask import Flask, render_template
from flask_mqtt import Mqtt
from gpiozero import LED
led = LED(21)

app = Flask(__name__)
app.config['SECRET'] = 'my secret key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MQTT_BROKER_URL'] = 'localhost'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False
app.config['MQTT_CLEAN_SESSION'] = True

mqtt = Mqtt(app)

toggle = False

def ledStatus():
    if led.is_lit:
        return("ON")
    else:
        return("OFF")
    
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('led/toggle')
    
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic = message.topic,
        payload=message.payload.decode().strip()
    )
    print(data['payload'])
    if data['payload'] == '1':
        led.on()
    elif data['payload'] == '0':
        led.off()
        
@app.route('/')
def index():
    return render_template('index.html', status=ledStatus())

@app.route('/led/toggle')
def ledOn():
    global toggle
    if toggle:
        led.on()
    else:
        led.off()
    toggle = not toggle
    return render_template('index.html', status=ledStatus())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug = True)