import os
import sys
import certifi
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, CollectionInvalid
from datetime import datetime

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Завантаження змінних середовища
load_dotenv()

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance.client = None
            cls._instance.db = None
        return cls._instance

    def connect(self):
        if self.client is not None:
            return  # З'єднання вже встановлено

        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            logging.error("MONGO_URI не вказано в змінних середовища")
            sys.exit(1)

        try:
            self.client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
            self.client.admin.command('ping')  # Перевірка з'єднання
            self.db = self.client["message_database"]
        except ConnectionFailure as connection_failure_error:
            logging.error("Помилка підключення до бази даних: %s", connection_failure_error)
            sys.exit(1)

    def get_collection(self, collection_name):
        if self.db is None:
            self.connect()
        try:
            return self.db[collection_name]
        except CollectionInvalid as collection_invalid_error:
            sys.exit(1)

    def close_connection(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None

# Створення глобального екземпляра для використання в інших модулях
db_connection = DatabaseConnection()

class MessageOperations:
    def __init__(self):
        self.collection = db_connection.get_collection("messages")

    def save_message(self, username, message):
        try:
            document = {
                "date": datetime.now().isoformat(),
                "username": username,
                "message": message
            }
            result = self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Помилка при збереженні повідомлення: {e}")
            raise

    def get_all_messages(self):
        try:
            return list(self.collection.find({}, {"_id": 0}))
        except Exception as e:
            logging.error(f"Помилка при отриманні всіх повідомлень: {e}")
            raise

# Спроба підключення при імпорті модуля
try:
    db_connection.connect()
except Exception as e:
    logging.error("Не вдалося підключитися до бази даних: %s", e)
    sys.exit(1)

# Створення екземпляра MessageOperations
message_ops = MessageOperations()