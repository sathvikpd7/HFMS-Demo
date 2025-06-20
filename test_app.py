from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World! If you can see this, the application is running correctly."

if __name__ == '__main__':
    print("Starting test application...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 