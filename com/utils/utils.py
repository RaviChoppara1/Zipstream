import logging
import time
from functools import lru_cache

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


@lru_cache(maxsize=None)
def get_data_from_database_cached(database_manager, query_type):
    cache = database_manager.load_cache()
    key = (database_manager.database_endpoint, database_manager.database_port, database_manager.database_user,
           database_manager.database_password, database_manager.database_name, database_manager.table_name, query_type)
    if key in cache:
        return cache[key]

    rows = database_manager.fetch_data(query_type)

    # Update cache
    cache[key] = rows
    database_manager.save_cache(cache)

    return rows
