from flask import Flask

app = Flask(__name__)

@app.route('/')
def mainWork():
    return "Integration Ran Successfull"
    
if __name__ == '__main__':
    app.run()
