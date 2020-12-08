## A small program that uses an oLed, RFID, led ring, and a button to simulate a small dance party or give system informations using a raspberry pi ##
## Kieran Henderson ##
## 10/15/20 ##

import time
import board
import neopixel
import psutil
import os.path

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

from subprocess import check_call
from signal import pause

from demo_opts import get_device # import for the oled screen
from PIL import Image, ImageSequence # import for the dancing oled screen
from luma.core.virtual import viewport, snapshot # import for the system oled screen
from luma.core.sprite_system import framerate_regulator #import for the dancing oled screen

from hotspot import memory, uptime, cpu_load, clock, network, disk # import for the system oled screen

pixelPin = board.D18 # led ring is connected to port d18

# The number of NeoPixels
numPixels = 12

# The order of the pixel colors (constant)
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel( # initialize the pixels object 
    pixelPin, numPixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

reader = SimpleMFRC522() # initializing the rfi scanner 

## button setup ##
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 10 to be an input pin and set initial value to be pulled low (off)

#### Both of the led ring functions were taken from https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage ###
def wheel(pos): #Wheel function that is used by the rainbow cycle function to determine the correct color
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0

        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (r, g, b) if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)

def rainbowCycle(wait): #funtion used to flash a rainbow in a circle 
    for j in range(255):
        for i in range(numPixels):
            pixelIndex = (i * 256 // numPixels) + j
            pixels[i] = wheel(pixelIndex & 255)
        pixels.show()
        time.sleep(wait)

### All the OLED functions were acuired from various different projects here: https://github.com/rm-hull/luma.oled ###
def position(max): #function that the system oled display uses to move the screen from side to side (changed, added rainbow if wanted and the shutdown)
    forwards = range(0, max)
    backwards = range(max, 0, -1)
    while True:
        for x in forwards:
            if GPIO.input(15) == GPIO.HIGH: #if the button on pin 15 is pushed then shutdown everything 
                shutdown()
            ##rainbowCycle(0.001)  # rainbow cycle with 1ms delay per step
            yield x
        for x in backwards:
            if GPIO.input(15) == GPIO.HIGH: #if the button on pin 15 is pushed then shutdown everything 
                shutdown()
            ##rainbowCycle(0.001)  # rainbow cycle with 1ms delay per step
            yield x

def pauseEvery(interval, generator): #function that the system oled display uses to pause the screen
    try:
        while True:
            x = next(generator)
            if x % interval == 0:
                for _ in range(20):
                    yield x
            else:
                yield x
    except StopIteration:
        pass

def intersect(a, b): #function that the system oled display uses to display the different text and widgets on the oled 
    return list(set(a) & set(b))

def first(iterable, default=None):#function that the system oled display uses to display the network properties
    if iterable:
        for item in iterable:
            return item
    return default

def mainSys():#main function that the system oled display uses to manage all of the different widgets and everything that is happening 
    pixels.fill((0,0,0))
    pixels.show()
    if device.rotate in (0, 2):
        # Horizontal
        widget_width = device.width // 2
        widget_height = device.height
    else:
        # Vertical
        widget_width = device.width
        widget_height = device.height // 2

    # Either function or subclass
    #  cpuload = hotspot(widget_width, widget_height, cpu_load.render)
    #  cpuload = cpu_load.CPU_Load(widget_width, widget_height, interval=1.0)
    utime = snapshot(widget_width, widget_height, uptime.render, interval=1.0)
    mem = snapshot(widget_width, widget_height, memory.render, interval=2.0)
    dsk = snapshot(widget_width, widget_height, disk.render, interval=2.0)
    cpuload = snapshot(widget_width, widget_height, cpu_load.render, interval=0.5)
    clk = snapshot(widget_width, widget_height, clock.render, interval=1.0)

    network_ifs = psutil.net_if_stats().keys()
    wlan = first(intersect(network_ifs, ["wlan0", "wl0"]), "wlan0")
    eth = first(intersect(network_ifs, ["eth0", "en0"]), "eth0")
    lo = first(intersect(network_ifs, ["lo", "lo0"]), "lo")

    net_wlan = snapshot(widget_width, widget_height, network.stats(wlan), interval=2.0)
    net_eth = snapshot(widget_width, widget_height, network.stats(eth), interval=2.0)
    net_lo = snapshot(widget_width, widget_height, network.stats(lo), interval=2.0)

    widgets = [cpuload, utime, clk, net_wlan, net_eth, net_lo, mem, dsk]

    if device.rotate in (0, 2):
        virtual = viewport(device, width=widget_width * len(widgets), height=widget_height)
        for i, widget in enumerate(widgets):
            virtual.add_hotspot(widget, (i * widget_width, 0))

        for x in pauseEvery(widget_width, position(widget_width * (len(widgets) - 2))):
            virtual.set_position((x, 0))

    else:
        virtual = viewport(device, width=widget_width, height=widget_height * len(widgets))
        for i, widget in enumerate(widgets):
            virtual.add_hotspot(widget, (0, i * widget_height))

        for y in pauseEvery(widget_height, position(widget_height * (len(widgets) - 2))):
            virtual.set_position((0, y))

def mainDance():#main function of the that the oled screen uses when displaying the dance mode (changed, added led ring color and shutdown)
    regulator = framerate_regulator(fps=10)
    img_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
        'images', 'banana.gif'))
    banana = Image.open(img_path)
    size = [min(*device.size)] * 2
    posn = ((device.width - size[0]) // 2, device.height - size[1])

    while True:
        for frame in ImageSequence.Iterator(banana):
            rainbowCycle(0.001) #call the rainbow cycle for the led ring 
            if GPIO.input(15) == GPIO.HIGH: #if the button on pin 15 is pushed then shutdown everything 
                shutdown()
            with regulator:
                background = Image.new("RGB", device.size, "white")
                background.paste(frame.resize(size, resample=Image.LANCZOS), posn)
                device.display(background.convert(device.mode))

def shutdown():#shutdown function that gets called upon a button push that will turn off the pi
    device.clear() #clear the oled display
    pixels.fill((0,0,0)) #clear the led ring
    pixels.show() #update teh led ring
    check_call(['sudo', 'poweroff']) #shut the pi down

id, text = reader.read() #read the text from the rfid reader
i = text.strip() #strip the text of trailing and leading spaces 

if i == "system": #if the text value is system engage system mode 
    try:
        device = get_device() #gets the oled device
        mainSys() #call the mainsys oled function that manages the system oled screen
    except KeyboardInterrupt:
        pass   

if i == "dance":#if the text value is system engage dance mode 
    try:
        device = get_device() #gets the oled device
        mainDance() #call the maindance oled function that manages the dance oled screen
    except KeyboardInterrupt:
        pass   