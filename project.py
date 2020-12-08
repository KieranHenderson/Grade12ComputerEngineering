import time

import psutil

from gpiozero import Button
from subprocess import check_call
from signal import pause

from demo_opts import get_device
from luma.core.virtual import viewport, snapshot

from hotspot import memory, uptime, cpu_load, clock, network, disk

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixelPin = board.D18

# The number of NeoPixels
numPixels = 12

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixelPin, numPixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

shutdown_btn = Button(2, hold_time=2)

def wheel(pos):
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

def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

def position(max):
    forwards = range(0, max)
    backwards = range(max, 0, -1)
    while True:
        for x in forwards:
            yield x
        for x in backwards:
            yield x

def pause_every(interval, generator):
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

def intersect(a, b):
    return list(set(a) & set(b))

def first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default

def shutdown():
    pixels.show()
    check_call(['sudo', 'poweroff'])

def main():
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

        for x in pause_every(widget_width, position(widget_width * (len(widgets) - 2))):
            virtual.set_position((x, 0))

    else:
        virtual = viewport(device, width=widget_width, height=widget_height * len(widgets))
        for i, widget in enumerate(widgets):
            virtual.add_hotspot(widget, (0, i * widget_height))

        for y in pause_every(widget_height, position(widget_height * (len(widgets) - 2))):
            virtual.set_position((0, y))


if __name__ == "__main__":
    try:
        device = get_device()
        main()
    except KeyboardInterrupt:
        pass

#while True:
    # rainbow_cycle(0.001)  # rainbow cycle with 1ms delay per step
    # shutdown_btn.when_held = shutdown
    # if input() == "q":
    #     exit(0)