import argparse
import concurrent.futures
import logging
import sys
import time
import signal
import os

from com.log_folder_manager.log_folder_manager import LogFolderManager
from com.signal_handler.signal_handler import SignalHandler
from com.url_handler.url_handler import UrlHandler
from com.database_handler.database_handler import DatabaseHandler

def parse_arguments():
    parser = argparse.ArgumentParser(description="Retrieve data from an API and save it to a file with digest authentication")
    parser.add_argument("database_host", type=str, help="MySQL database host")
    parser.add_argument("database_user", type=str, help="MySQL database username")
    parser.add_argument("database_password", type=str, help="MySQL database password")
    parser.add_argument("database_name", type=str, help="MySQL database name")
    parser.add_argument("table_name", type=str, help="Name of the database table to retrieve data from")
    parser.add_argument("--strength", type=str, default=30, help="Strength value to include in the URL")
    parser.add_argument("--query_type", type=str, choices=['ET', 'CT', 'MT', 'PT'], help="Type of SQL query to execute")

    args = parser.parse_args()

    return args

def main():
    signal.signal(signal.SIGINT, SignalHandler.signal_handler)  # Assign the signal handler
    args = parse_arguments()

    log_folder = LogFolderManager.create_log_folder(args.query_type)
    if not log_folder:
        logging.error("Failed to create log folder.")
        sys.exit(1)

    log_file = os.path.join(log_folder, "application.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    start_time = time.time()
    success_count = 0
    failure_count = 0

    rows = DatabaseHandler.get_data_from_database(args.database_host, args.database_user, args.database_password,
                                                  args.database_name, args.table_name, args.query_type)
    if not rows:
        logging.error("Failed to retrieve data from the database.")
        sys.exit(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for row in rows:
            future = executor.submit(UrlHandler.Zipstream, *row, args.strength)
            futures.append(future)

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                success_count += 1
            else:
                failure_count += 1

    LogFolderManager.log_summary(start_time, success_count, failure_count)
    LogFolderManager.delete_old_folders()

if __name__ == "__main__":
    main()
