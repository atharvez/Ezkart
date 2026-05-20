import os
from motor.motor_asyncio import AsyncIOMotorClient

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    def connect(cls):
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client.auto_cart_db
        print("Connected to MongoDB.")

    @classmethod
    def get_db(cls):
        if cls.db is None:
            cls.connect()
        return cls.db

db = Database()
