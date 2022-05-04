from flask_pymongo import PyMongo
import os

class MongoConnect:
    def __init__(self,app):
        self.mongo = PyMongo(app,uri=os.getenv('MONGO_URI'))