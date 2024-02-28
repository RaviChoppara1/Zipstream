import logging
import signal
import sys
import os
import shutil
from datetime import datetime
import concurrent.futures
import argparse
import boto3
import time
from botocore.exceptions import NoCredentialsError
from io import BytesIO
import requests
from requests.auth import HTTPDigestAuth
from com.database.database import DatabaseManager
from com.utils.utils import retry, get_data_from_database_cached
import botocore
terminate_flag = False


def signal_handler(sig, frame):
    global terminate_flag
    logging.info("Ctrl+C detected. Exiting gracefully...")
    terminate_flag = True
    sys.exit(0)


def create_log_folder(query_type):
    current_date = datetime.now().strftime("%Y%m%d%H%M%S")
    folder_base_name = f"{current_date}"
    folder_name = os.path.join("logs", folder_base_name)

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    return folder_name


def log_summary(start_time, success_count, failure_count):
    total_time = time.time() - start_time
    logging.info(f"Total Time: {total_time} seconds")
    logging.info(f"Total Success URLs: {success_count}")
    logging.info(f"Total Failed URLs: {failure_count}")


@retry
def Zipstream(profitCameraIP, profitCameraPort, username, password, strength):
    global terminate_flag
    if terminate_flag:
        return

    url = f"http://{profitCameraIP}:{profitCameraPort}/axis-cgi/zipstream/setstrength.cgi?schemaversion=1&strength={strength}&camera=1"

    try:
        response = requests.get(url, auth=HTTPDigestAuth(username, password))

        if response.status_code == 200:
            logging.info(f"Request success :{url}")
            return True
        else:
            logging.error(
                f"Request failed for {url} with status code: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error in Zipstream: {e}")
        return False

def s3_upload_object(bucket, key, file_path):
    try:
        s3 = boto3.client('s3')
        with open(file_path, 'rb') as file:
            data = file.read()
            s3.upload_fileobj(BytesIO(data), bucket, key)
        logging.info(f"Uploaded to S3: s3://{bucket}/{key}")
        os.remove(file_path)
        logging.info(f"Deleted local file: {file_path}")
    except NoCredentialsError:
        logging.error("Credentials not available for S3 upload.")
        print("S3 upload failed: Credentials not available")
    except Exception as e:
        logging.error(f"Failed to upload to S3: s3://{bucket}/{key}")
        logging.error(f"Error: {e}")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(
        description="Retrieve data from an API and save it to a file with digest authentication")
    parser.add_argument("database_user", type=str,
                        help="MySQL database username")
    parser.add_argument("database_password", type=str,
                        help="MySQL database password")
    parser.add_argument("database_name", type=str,
                        help="MySQL database name")
    parser.add_argument("table_name", type=str,
                        help="Name of the database table to retrieve data from")
    parser.add_argument("--strength", type=str, default=30,
                        help="Strength value to include in the URL")
    parser.add_argument("--query_type", type=str, choices=[
                        'ET', 'CT', 'MT', 'PT'], help="Type of SQL query to execute")
    parser.add_argument("--database_endpoint", type=str,
                        help="MySQL database endpoint")
    parser.add_argument("--database_port", type=int,
                        default=3306, help="MySQL database port")

    args = parser.parse_args()

    log_folder = create_log_folder(args.query_type)
    if not log_folder:
        logging.error("Failed to create log folder.")
        sys.exit(1)

    log_file = os.path.join(log_folder, "application.log")
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    start_time = time.time()
    success_count = 0
    failure_count = 0

    database_manager = DatabaseManager(args.database_endpoint, args.database_port,
                                       args.database_user, args.database_password, args.database_name, args.table_name)

    cached_data = get_data_from_database_cached(
        database_manager, args.query_type)
    if cached_data:
        logging.info("Data retrieved from cache.")
        rows = cached_data
    else:
        logging.info("Fetching data from database...")
        rows = database_manager.fetch_data(args.query_type)
        if not rows:
            logging.error("Failed to retrieve data from the database.")
            sys.exit(1)
        get_data_from_database_cached.cache_clear()
        get_data_from_database_cached(database_manager, args.query_type)

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for row in rows:
            future = executor.submit(
                Zipstream, *row, args.strength)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                success_count += 1
            else:
                failure_count += 1
    log_summary(start_time, success_count, failure_count)

    # Upload log folders to S3
    current_date = datetime.now().strftime("%Y%m%d")
    s3_folder = f"{current_date}"
    s3_bucket = 'zipstreamlogs'

    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=s3_bucket, Key=f"{s3_folder}/")
        logging.info(f"Connected to S3: s3://{s3_bucket}")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            logging.info(
                f"S3 folder {s3_folder} does not exist. Creating...")
            s3.put_object(Bucket=s3_bucket, Key=f"{s3_folder}/")
            logging.info(f"Created S3 folder: s3://{s3_bucket}/{s3_folder}")

    for root, dirs, files in os.walk("logs"):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            key = f"{s3_folder}/{folder}"
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    s3_upload_object(s3_bucket, key, file_path)




if __name__ == "__main__":
    main()
