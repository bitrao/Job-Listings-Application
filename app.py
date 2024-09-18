from flask import Flask
from routes import bp

app = Flask(__name__)
app.secret_key = 'secret_key'

# Register the Blueprint
app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=True)
