from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return 'Welcome to Zoo Clicker!'
#weird

print('Good day')
dog = int(input())
if dog == (14):
    print('14 dogs!')
else:
    print('f')


