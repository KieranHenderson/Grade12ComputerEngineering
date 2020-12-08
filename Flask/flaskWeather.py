from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/temperature', methods = ['POST'])
def temperature():
    postal = request.form["postal code"]
    r = requests.get('http://api.weatherapi.com/v1/current.json?key=e47465dbf69a4d02a83141754202010&q='+postal)
    json_object = r.json()
    tempC = float(json_object['current']['temp_c'])
    print(tempC)
    return render_template('temperature.html', temp = tempC)

@app.route('/')
def index():
    return render_template('weatherIndex.html')

if __name__ == '__main__':
    app.run(debug = True)