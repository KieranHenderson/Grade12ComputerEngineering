import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

operation = input("What operation would you like to do (read or write): ")

if(operation == "write"):
    try:
            text = input('New data:')
            print("Now place your tag to write")
            reader.write(text)
            print("Written")

    finally:
            GPIO.cleanup()
        
if(operation == "read"):
    try:
            id, text = reader.read()
            print(id)
            print(text)
    finally:
            GPIO.cleanup()