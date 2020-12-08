#imports for flask and socketio(websocket)
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit

import requests
import RPi.GPIO as GPIO

import json

#import for threads
from threading import Lock

## oled imports ##
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

async_mode = None

#initializing the flask app and websocket
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

#initialization for second thread
thread = None
thread_lock = Lock()
#global veriable that determines when the thread should be running
loop = True

#globals for api info
global postal
global r
global json_object
global tempC

global pinState

#initialization the gpio pins of my lights
GPIO.setup(26, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(6, GPIO.OUT)

# Define the Reset Pin for the oled
oled_reset = digitalio.DigitalInOut(board.D4)
 
#size of oled display
WIDTH = 128
HEIGHT = 64
BORDER = 5
 
# Use for I2C.
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=oled_reset)

#initialization for buttons
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 12 to be an input pin and set 

#thread that runs in the background during the api page so that the info in continuously updated 
def background_thread():
    global loop
    while loop:
        socketio.sleep(1)
        updateAPI() #function that updates the api
            
#this function updates the api information 
def updateAPI():
    #use the global veraibles 
    global r 
    global json_object
    global tempC
    #update the api link in case the user changed it 
    r = requests.get('http://api.weatherapi.com/v1/current.json?key=e47465dbf69a4d02a83141754202010&q='+postal)
    json_object = r.json() #set the json object 
    tempC = float(json_object['current']['temp_c']) #get the temperature from the json object
    if (GPIO.input(12) == 1): #if the button is pushed then update the info on screen
        with app.test_request_context('/api'):
            emit('my_response', {'data': tempC}, namespace = "/test", broadcast = True)

### Flash Routes ###
#method for directing the user to the check pin screen
@app.route('/check', methods = ['GET'])
def checkPins():
    return render_template('projectCheck.html') #send user to the check gpio port page

#method for the json part of the project 
@app.route('/json', methods=['GET'])
def json_example():
    #render the json page
    return render_template('projectJson.html', async_mode=socketio.async_mode)

#method for the api part of the project
@app.route('/api', methods=['GET'])
def api():
    global loop 
    loop = True #allows the loop to start
    return render_template('projectApiWS.html') #go to the api web page

#home page route
@app.route('/')
def index():
    return render_template('projectHome.html') #render the home page

### Web Sockets ###
#JSON websocket
@socketio.on('json', namespace='/test')
def jsonMessage(message):
    req_data = json.loads(json.dumps(message['data'], indent=4)).strip(' {').strip('}').replace('"',"").replace(" ","").replace("ON", "1").replace("OFF", "0").split(",") #get the json data and format it to usable data
    dataArray = [] #array for the data
    for x in req_data: #split the data into the array
        dataArray += x.split(":")
    print(dataArray)

    #get the data for each pin and assigen it to a variable 
    pin1 = dataArray[1]
    pin2 = dataArray[3]
    pin3 = dataArray[5]
    pin4 = dataArray[7]

    #turn the right leds on or off
    GPIO.output(26,int(pin1))
    GPIO.output(19,int(pin2))
    GPIO.output(13,int(pin3))
    GPIO.output(6,int(pin4))
    
    #emit (javascript function, message, callbacK?)
    emit('my_response', {'data': message['data']}, broadcast=True) #send the message to the collector 

#API websocket
@socketio.on('api', namespace='/test')
def apiMessage(message):
    global postal #use the global postal varriable 
    postal = json.loads(json.dumps(message['data'], indent=4)) #update the postal code from the form

    with thread_lock:
        global thread
        if thread is None: #start the background loop if the thread is none 
            thread = socketio.start_background_task(background_thread)

#back button websocket for the api page
@socketio.on('back', namespace='/test')
def back():
    global loop #sets the global loop veriable to false to stop the backgroud thread from running while the api page is not open
    loop = False

#Check pin websocket 
@socketio.on('check', namespace='/test')
def check(message):
    global pinState
    #get the pin number form the page
    pinNum = int(message['data'])

    #if the pin is not a gpio pin then emit that a gpio pin is required and return
    if(pinNum!=2 and pinNum!=3 and pinNum!=17 and pinNum!=27 and pinNum!=22 and pinNum!=10 and pinNum!=9 and pinNum!=11 and pinNum!=0 and pinNum!=5 and pinNum!=6 and pinNum!=13 and pinNum!=19 and pinNum!=14 and pinNum!=15 and pinNum!=18 and pinNum!=23 and pinNum!=24 and pinNum!=25 and pinNum!=8 and pinNum!=7 and pinNum!=1 and pinNum!=16 and pinNum!=20 and pinNum!=21 and pinNum!=26):
        emit('bad', {'data': "Please enter a GPIO pin"}, broadcast=True)
        return
    
    GPIO.setup(pinNum, GPIO.OUT) #set up the pin as output so I can read the value 

    #check the state of the pin
    if (GPIO.input(pinNum)):
        pinState = "HIGH"
    else:
        pinState = "LOW"

    ### oled ###
    oled.fill(0)
    oled.show()
    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new("1", (oled.width, oled.height))
    
    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)
    
    # Draw a white background
    draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=255)
    
    # Draw a smaller inner rectangle
    draw.rectangle(
        (BORDER, BORDER, oled.width - BORDER - 1, oled.height - BORDER - 1),
        outline=0,
        fill=0,
    )
    
    # Load default font.
    font = ImageFont.load_default()
    
    # Draw pin state
    text = pinState

    (font_width, font_height) = font.getsize(text)
    draw.text(
        (oled.width // 2 - font_width // 2, oled.height // 2 - font_height // 2),
        text,
        font=font,
        fill=255,
    )
    
    # Display pin state
    oled.image(image)
    oled.show()

    #emit (javascript function, message, callbacK?)
    #emit the pin number and the pin state to the reciver to be updated on the website
    emit('my_response', {'data': pinState, 'num' : pinNum}, broadcast=True)

#run the websocket app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
