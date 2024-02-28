import mysql.connector
import logging
import os
import pickle
import time
import boto3
import botocore

CACHE_FILE = "cache.pickle"
CACHE_EXPIRY_SECONDS = 7 * 24 * 60 * 60  # 7 days in seconds

class DatabaseManager:
    def __init__(self, database_endpoint, database_port, database_user, database_password, database_name, table_name):
        self.database_endpoint = database_endpoint
        self.database_port = database_port
        self.database_user = database_user
        self.database_password = database_password
        self.database_name = database_name
        self.table_name = table_name

    def connect(self):
        try:
            conn = mysql.connector.connect(
                host=self.database_endpoint,
                port=self.database_port,
                user=self.database_user,
                password=self.database_password,
                database=self.database_name
            )
            return conn
        except mysql.connector.Error as err:
            logging.error(f"Database connection error: {err}")
            return None

    def fetch_data(self, query_type):
        try:
            conn = self.connect()
            if not conn.is_connected():
                logging.error("Failed to connect to the database.")
                return []

            cursor = conn.cursor()

            if query_type == 'ET':
                cursor.execute(
                    f'SELECT profitCameraIp, profitCameraPort, username, password FROM {self.table_name} where TimeZone like "E%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            elif query_type == 'CT':
                cursor.execute(
                    f'SELECT profitCameraIp, profitCameraPort, username, password FROM {self.table_name} where TimeZone like "C%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            elif query_type == 'MT':
                cursor.execute(
                    f'SELECT profitCameraIp, profitCameraPort, username, password FROM {self.table_name} where TimeZone like "M%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            elif query_type == 'PT':
                cursor.execute(
                    f'SELECT profitCameraIp, profitCameraPort, username, password FROM {self.table_name} where TimeZone like "P%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            else:
                logging.error("Invalid query type.")
                return []

            rows = cursor.fetchall()
            conn.close()

            return rows
        except Exception as e:
            logging.error(f"Error fetching data from database: {e}")
            return []

    @staticmethod
    def load_cache():
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "rb") as f:
                cache = pickle.load(f)
                current_time = time.time()
                for key, value in list(cache.items()):
                    if isinstance(value, dict) and 'timestamp' in value:
                        if current_time - value['timestamp'] > CACHE_EXPIRY_SECONDS:
                            del cache[key]  # Remove expired cache entry
                    else:
                        #logging.warning("Invalid cache format found. Skipping.")
                        del cache[key]  # Remove invalid cache entry
                return cache
        else:
            return {}

    def save_cache(self, cache):
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(cache, f)
        except Exception as e:
            logging.error(f"Error saving cache: {e}")
