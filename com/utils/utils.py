import logging
import time

LOG_FOLDER = "logs"

def retry(func):
    def wrapper(*args, **kwargs):
        retries = 2
        while retries > 0:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error: {e}. Retrying...")
                retries -= 1
                time.sleep(1)  # Add a delay before retrying
        logging.error(f"Failed after retrying.")
        return None
    return wrapper

# def get_data_from_database(database_manager, query_type):
#     return database_manager.fetch_data(query_type)

