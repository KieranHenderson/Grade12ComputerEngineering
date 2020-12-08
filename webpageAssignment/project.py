from flask import Flask, render_template, request
import requests
import RPi.GPIO as GPIO

## oled imports ##
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

app = Flask(__name__)

global pinState

#set up the gpio pins of my lights
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

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 12 to be an input pin and set 

#method for checking the pins of the raspberry pi and displaying them on the oled screen
@app.route('/check', methods = ['GET'])
def checkPins():
    pinNum = request.args.get('pin') #get the pin number of the desired pin
    pinNum = int(pinNum) #convert to an int just incase 
    print(pinNum)

    #if the pin is not a gpio pin return the home page
    if(pinNum!=2 and pinNum!=3 and pinNum!=4 and pinNum!=17 and pinNum!=27 and pinNum!=22 and pinNum!=10 and pinNum!=9 and pinNum!=11 and pinNum!=0 and pinNum!=5 and pinNum!=6 and pinNum!=13 and pinNum!=19 and pinNum!=26 and pinNum!=14 and pinNum!=15 and pinNum!=18 and pinNum!=23 and pinNum!=24 and pinNum!=25 and pinNum!=8 and pinNum!=7 and pinNum!=1 and pinNum!=12 and pinNum!=16 and pinNum!=20 and pinNum!=21):
        return render_template('projectHome.html')

    #check the input of the pin
    if (GPIO.input(pinNum)):
        pinState = "HIGH"
    else:
        pinState = "LOW"

    #oled
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

    #render the page to display the state as well
    return render_template('projectCheck.html', state = pinState) #send user to the check gpio port page

#method for the json part of the project 
@app.route('/json', methods=['POST']) #GET requests will be blocked
def json_example():
    req_data = request.get_json() #get the json data

    #get the data for each pin and assigen it to a variable 
    pin1 = req_data['pin1']
    pin2 = req_data['pin2']
    pin3 = req_data['pin3']
    pin4 = req_data['pin4']

    #turn the right leds on
    GPIO.output(26,int(pin1))
    GPIO.output(19,int(pin2))
    GPIO.output(13,int(pin3))
    GPIO.output(6,int(pin4))

    #render the json page
    return render_template('projectJson.html')

#method for the api part of the project
@app.route('/api', methods=['POST'])
def api():
    postal = request.form["postal code"] #get the postal code from the form
    if (GPIO.input(12) == 1): #if the button is pushed then go to the api and get the temperature
        r = requests.get('http://api.weatherapi.com/v1/current.json?key=e47465dbf69a4d02a83141754202010&q='+postal)
        json_object = r.json()
        tempC = float(json_object['current']['temp_c'])
        return render_template('projectApi.html', temp = tempC) #go to the api web page
    return render_template('projectHome.html')#if the button is not pushed reload the home page

#home page route
@app.route('/')
def index():
    return render_template('projectHome.html') #render the home page

if __name__ == '__main__':
    app.run(debug = True, port=5000, host='0.0.0.0') #set the host to be able to see the page on different computers
