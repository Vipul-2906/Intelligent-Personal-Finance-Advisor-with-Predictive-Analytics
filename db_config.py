# db_config.py
from flask_mysqldb import MySQL

def init_db(app):
    # Update these values to match your local MySQL config
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'VIKASSAINI#&7345'
    app.config['MYSQL_DB'] = 'finance_advisor'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
    return MySQL(app)
