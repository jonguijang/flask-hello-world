from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, DSC 한글입니다. !'
