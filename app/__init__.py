from flask import Flask
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os

load_dotenv()

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

    # MySQL Config
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
    #app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))
    #app.config['MYSQL_UNIX_SOCKET'] = os.getenv('MYSQL_UNIX_SOCKET', None)

    mysql.init_app(app)

    from .routes import main
    app.register_blueprint(main)
    
    return app
