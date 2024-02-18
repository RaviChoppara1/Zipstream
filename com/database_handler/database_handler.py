import mysql.connector
import logging

class DatabaseHandler:
    @staticmethod
    def get_data_from_database(database_host, database_user, database_password, database_name, table_name, query_type):
        try:
            if not database_host:
                logging.error("Database host is not provided.")
                return []
            if not database_user or not database_password:
                logging.error("Database username or password is missing.")
                return []
            if not database_name:
                logging.error("Database name is not provided.")
                return []

            conn = mysql.connector.connect(
                host=database_host,
                user=database_user,
                password=database_password,
                database=database_name
            )

            if not conn.is_connected():
                logging.error("Failed to connect to the database.")
                return []

            cursor = conn.cursor()

            if query_type == 'ET':
                cursor.execute(f'SELECT profitCameraIp, profitCameraPort, username, password FROM {table_name} where TimeZone like "E%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            elif query_type == 'CT':
                cursor.execute(f'SELECT profitCameraIp, profitCameraPort, username, password FROM {table_name} where TimeZone like "C%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            elif query_type == 'MT':
                cursor.execute(f'SELECT profitCameraIp, profitCameraPort, username, password FROM {table_name} where TimeZone like "M%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            elif query_type == 'PT':
                cursor.execute(f'SELECT profitCameraIp, profitCameraPort, username, password FROM {table_name} where TimeZone like "P%" and ProdFullName = "AXIS M2025-LE Bullet Camera"')
            else:
                logging.error("Invalid query type.")
                return []

            if not cursor:
                logging.error("Failed to execute SQL query.")
                conn.close()
                return []

            rows = cursor.fetchall()

            conn.close()

            return rows
        except mysql.connector.Error as err:
            logging.error(f"Database connection error: {err}")
            return []
