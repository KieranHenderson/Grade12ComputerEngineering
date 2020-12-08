from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit, disconnect

async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

@app.route('/')
def index():
    return render_template('projectSocket.html', async_mode=socketio.async_mode)

# @socketio.on('my_event', namespace='/test')
# def test_message(message):
#     print("yay")
#     emit('my_response', 'hello!')

@socketio.on('my_broadcast_event', namespace='/test')
def test_broadcast_message(message):
    print(1)
    print(message)
    
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)

@socketio.on('connect', namespace='/test')
def test_connect():
    print('connected')
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)