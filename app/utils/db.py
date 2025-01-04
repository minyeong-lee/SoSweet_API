from flask_pymongo import PyMongo

mongo = PyMongo()

def get_db(app):
    mongo.init_app(app)
    return mongo.db

