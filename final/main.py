#imports for flask and socketio(websocket)
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import requests

import json #import for communicating with the api better

import time #import time to use for threading on the home page 

from threading import Thread #import thread from threading so I can use multiple threads 

from mfrc522 import SimpleMFRC522 #rfid import

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

# Define the Reset Pin for the oled
oled_reset = digitalio.DigitalInOut(board.D4)
 
#size of oled display
WIDTH = 128
HEIGHT = 64
BORDER = 5

# Use for I2C.
i2c = board.I2C()
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=oled_reset)

reader = SimpleMFRC522() # initializing the rfid scanner 

#initialize amount of coins player has
coins = 0

#home page route
@app.route('/', methods = ['GET','POST'])
def home():
    balThread = Thread(target=checkBal,args=[]) #initialize the bal thread with the function check bal
    balThread.start() #start the bal thread
    return render_template('home.html') #render the home page

def checkBal():
    global coins #use global variable coins 
    time.sleep(1) #sleep, VERY IMPORTANT, ensures the webpage can render 
    cost = 50 #sets cost of the game to 50
    while True:
        text = reader.read()[1] #read the text from the rfid reader
        coins = int(text.strip()) #strip the text of trailing and leading spaces 
        if coins >= cost: #if the text value is system engage system mode 
            reader.write(str(coins-cost))#write updated balance to the card
            try:

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
                
                text = "You have " + str(coins-cost) + " credits" #text is how many coins you have after paying 

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
                
                socketio.emit('play', {"admit": "True", "cd": "3"}) #send the message to the collector
                print(3)
                time.sleep(1) #sleep so the page counts down seconds 
                socketio.emit('play', {"admit": "True", "cd": "2"}) #send the message to the collector
                print(2)
                time.sleep(1)#sleep so the page counts down seconds 
                socketio.emit('play', {"admit": "True", "cd": "1"}) #send the message to the collector
                print(1)
                time.sleep(1)#sleep so the page counts down seconds 

                #render the home page 
                ## render_template doesnt work because I am in a sepearte thread
                #emit instead and change the page in the javascript 
                socketio.emit('start', {"start":"True"})
                return #exit the thread
            except KeyboardInterrupt:
                pass   

        else:
            try:
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
                
                text = "Not enough credits" #display not enough credits 

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

                socketio.emit('play', {"admit": "False"}) #send the message to the collector that the user doesnt have enough coins 
                time.sleep(3) #sleep for three seconds before refreshing the page 
                socketio.emit('start', {"start":"False"}) #send the message to the collector to refresh the page 
                return #exit thread
            except KeyboardInterrupt:
                pass

#game route 
@app.route('/game', methods = ['GET','POST'])
def game():
    return render_template('game.html') #render the game page

#update websocket for the game page
@socketio.on('update', namespace='/test')
def update(state):
    #initialize variables 
    board = ""
    temp = []
    dictList = []
    url = "https://stujo-tic-tac-toe-stujo-v1.p.rapidapi.com/"
    winner = ""

    #get data being passed to the socket and convert it into a list 
    for key, value in state.items():
        temp = [key,value]
        dictList.append(temp)

    print("_____________")
    print(dictList)
    print("_____________")

    #using the dictList generate a string in the correct format for the api to read it based off the data recieved from the socket
    for x in dictList:
        if(x[1] == ""):
            board+="-"
        else:
            board+=(x[1])
    
    #if the game is not over 
    if("-" in board and winner == ""):
        #set the url of the api
        url+=(board+"/"+"O")
        
        #initialize api headers 
        headers = {
            'x-rapidapi-host': "stujo-tic-tac-toe-stujo-v1.p.rapidapi.com",
            'x-rapidapi-key': "76a6145710mshd7a7df48d8f7f94p11ea33jsn6f1660e68af3"
            }

        #get the optimal move for the ai from the api
        response = requests.request("GET", url, headers=headers)
        aiTurn = response.json()["recommendation"]+1
        board = board[:aiTurn-1] + "O" + board[aiTurn:]
        emit('aiTurn', aiTurn, broadcast=True) #send the message to the collector with the best move 


    #check horizontal win 
    for x in range (0, 3):
        if(x==0):
            tile = x
        else:
            tile = int(x+(x*((3/x)-x)))

        if(board[tile]==board[tile+1] and board[tile]==board[tile+2] and board[tile]!="-"):
            highlightWinner(tile,tile+1,tile+2,board[tile])
            winner = board[tile]
            print("hor")

    #check vertical win
    for x in range (0, 3):
        if(board[x]==board[x+3] and board[x]==board[x+6] and board[x]!="-"):
            highlightWinner(x,x+3,x+6,board[x])
            winner=board[x]
            print("vert")

    #check top left to bottom right diagonal win
    if(board[0]==board[4] and board[0]==board[8] and board[0]!="-"):
            highlightWinner(0,4,8,board[0])
            winner=board[0]
            print("left to right")
    
    #check top right to bottom left diagonal win 
    if(board[2]==board[4] and board[x]==board[6] and board[2]!="-"):
            highlightWinner(2,4,6,board[2])
            winner=board[2]
            print("right to left")

    #check tie 
    if("-" not in board and winner == ""):
        print("tie")
        winner = "t"
        highlightWinner(None,None,None,winner)
        emit('tie', broadcast=True) #send the message to the collector 



def highlightWinner(b1,b2,b3,winner):

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
    
    #display the correct winner 
    if(winner == "O" or winner == "X"):
        text = "THE WINNER IS " + winner + "'S"
    else:
        text = "IT WAS A TIE!"

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

    if(winner != "t"): #if its not a tie 
        emit('endGame', {"winner": winner, "b1": b1,"b2": b2, "b3": b3}, broadcast=True) #send the message to the collector with the correct buttons which need to be highlighted 


#run the websocket app 
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)