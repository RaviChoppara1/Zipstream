import mysql.connector
import logging

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
                    f"SELECT uniqueCameraId, profitCameraIp, profitCameraPort, username, password FROM {self.table_name} WHERE TimeZone LIKE 'E%'")
            elif query_type == 'CT':
                cursor.execute(
                    f"SELECT uniqueCameraId, profitCameraIp, profitCameraPort, username, password FROM {self.table_name} WHERE TimeZone LIKE 'C%'")

            elif query_type == 'MT':
                cursor.execute(
                    f"SELECT uniqueCameraId, profitCameraIp, profitCameraPort, username, password FROM {self.table_name} WHERE TimeZone LIKE 'M%'")
            elif query_type == 'PT':
                cursor.execute(
                    f"SELECT uniqueCameraId, profitCameraIp, profitCameraPort, username, password FROM {self.table_name} WHERE TimeZone LIKE 'P%'")
            elif query_type == 'ALL':
                cursor.execute(
                    f"SELECT uniqueCameraId, profitCameraIp, profitCameraPort, username, password FROM {self.table_name}")

            else:
                logging.error("Invalid query type.")
                return []

            rows = cursor.fetchall()
            conn.close()

            return rows
        except Exception as e:
            logging.error(f"Error fetching data from database: {e}")
            return []

