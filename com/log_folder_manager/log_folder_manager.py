import os
import shutil
from datetime import datetime, timedelta
import logging
import time

class LogFolderManager:
    LOG_FOLDER = "logs"

    @staticmethod
    def create_log_folder(query_type):
        current_date = datetime.now().strftime("%Y%m%d")
        folder_base_name = f"{current_date}_{query_type}"
        folder_name = os.path.join(LogFolderManager.LOG_FOLDER, folder_base_name)

        if os.path.exists(folder_name):
            suffix = 2
            while True:
                new_folder_name = f"{folder_base_name}{suffix}"
                new_folder_path = os.path.join(LogFolderManager.LOG_FOLDER, new_folder_name)
                if not os.path.exists(new_folder_path):
                    os.makedirs(new_folder_path)
                    return new_folder_path
                suffix += 1
        else:
            os.makedirs(folder_name)
            return folder_name

    @staticmethod
    def delete_old_folders():
        for folder in os.listdir(LogFolderManager.LOG_FOLDER):
            folder_path = os.path.join(LogFolderManager.LOG_FOLDER, folder)
            if os.path.isdir(folder_path):
                folder_date = datetime.strptime(folder.split("_")[0], "%Y%m%d")
                if datetime.now() - folder_date > timedelta(days=30):
                    shutil.rmtree(folder_path)


    def log_summary(start_time, success_count, failure_count):
        total_time = time.time() - start_time
        logging.info(f"Total Time: {total_time} seconds")
        logging.info(f"Total Success URLs: {success_count}")
        logging.info(f"Total Failed URLs: {failure_count}")