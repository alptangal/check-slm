from flask import Flask
from threading import Thread
import asyncio

app = Flask('')

@app.route('/')
def main():
    return 'Bot ready!'

def run():
    app.run(host='0.0.0.0', port=8888)

def b():
    server =  Thread(target=run)
    server.start()
    
