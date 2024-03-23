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
import requests
from requests.auth import HTTPDigestAuth
from com.database.database import DatabaseManager
from com.utils.utils import retry
import botocore
import csv
from io import BytesIO
from botocore.exceptions import NoCredentialsError
from com.mail.mail import send_email_with_dynamic_csv
terminate_flag = False
retry_list = []
def signal_handler(sig, frame):
    global terminate_flag
    logging.info("Ctrl+C detected. Exiting gracefully...")
    terminate_flag = True
    sys.exit(0)

def create_log_folder(query_type, strength):
    current_date = datetime.now().strftime("%d%m%Y")
    folder_base_name = f"{query_type}.{strength}"
    folder_name = os.path.join("logs", current_date, folder_base_name)

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    return folder_name

def log_summary(start_time, success_count, failure_count):
    total_time = time.time() - start_time
    logging.info(f"Total Time: {total_time} seconds")
    logging.info(f"Total Success URLs: {success_count}")
    logging.info(f"Total Failed URLs: {failure_count}")

def log_to_csv(log_type, log_data, current_date, query_type, strength):
    base_folder = create_log_folder(query_type, strength)  # Get the base folder
    filename = os.path.join(base_folder, f"{current_date}.{query_type}.{log_type}.csv")  # CSV file path inside the base folder
    fieldnames = ['camera IP', 'Camera Port', 'UniqueCameraId', 'Status', 'Strength']  # Include 'Strength' in fieldnames

    # Write CSV file
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if the file is newly created
        if os.path.getsize(filename) == 0:
            writer.writeheader()

        # Write data
        writer.writerow({'camera IP': log_data[1], 'Camera Port': log_data[2], 'UniqueCameraId': log_data[3], 'Status': log_data[0], 'Strength': strength})  # Include strength in the row

@retry
def Zipstream(profitCameraIP, profitCameraPort, username, password, strength, uniqueCameraId, current_date, query_type):
    global terminate_flag
    if terminate_flag:
        return

    url = f"http://{profitCameraIP}:{profitCameraPort}/axis-cgi/zipstream/setstrength.cgi?schemaversion=1&strength={strength}&camera=1"

    try:
        response = requests.get(url, auth=HTTPDigestAuth(username, password))

        if response.status_code == 200:
            # logging.info(f"Request success :{profitCameraIP}:{profitCameraPort}")
            log_to_csv("success", ['Success', profitCameraIP, profitCameraPort, uniqueCameraId], current_date, query_type, strength)
            return True
        else:
            # logging.error(
            #     f"Request failed for {profitCameraIP}:{profitCameraPort} with status code: {response.status_code}")
            log_to_csv("failure", ['Failure', profitCameraIP, profitCameraPort, uniqueCameraId, response.status_code], current_date, query_type, strength)
            return False
    except Exception as e:
        # logging.error(f"Error in Zipstream: {e}")
        retry_list.append((profitCameraIP, profitCameraPort, username, password, strength))
        log_to_csv("failure", ['Failure', profitCameraIP, profitCameraPort, uniqueCameraId, str(e)], current_date, query_type, strength)
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
                        'ET', 'CT', 'MT', 'PT', 'ALL'], help="Type of SQL query to execute")
    parser.add_argument("--database_endpoint", type=str,
                        help="MySQL database endpoint")
    parser.add_argument("--database_port", type=int,
                        default=3306, help="MySQL database port")

    args = parser.parse_args()

    current_date = datetime.now().strftime("%d%m%Y")  # Get current date
    log_folder = create_log_folder(args.query_type, args.strength)
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

    logging.info("Fetching data from database...")
    rows = database_manager.fetch_data(args.query_type)
    if not rows:
        logging.error("Failed to retrieve data from the database.")
        sys.exit(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
        futures = []
        for row in rows:
            unique_camera_id = row[0]  # Assuming uniqueCameraId is the first element in row
            future = executor.submit(
                Zipstream, row[1], row[2], row[3], row[4], args.strength, unique_camera_id, current_date, args.query_type)  # Pass current_date and query_type
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                success_count += 1
            else:
                failure_count += 1
    if failure_count > 0:
        if failure_count > 0:
            if args.query_type in ['ET', 'CT', 'MT']:
                sleep_time = 2700  # 180 seconds
            elif args.query_type in ['ALL', 'PT']:
                sleep_time = 0  # No sleep
            else:
                logging.warning("Unknown query_type. Using default sleep time of 2700 seconds.")
                sleep_time = 2700

            logging.info(f"Waiting {sleep_time} seconds before retrying failed cameras...")
            time.sleep(sleep_time)

            for params in retry_list:
                Zipstream(*params)
            retry_list.clear()

    log_summary(start_time, success_count, failure_count)

    # Define sender details
    sender_email = 'ravi.choppara@pro-vigil.com'
    sender_password = 'saNvi@2016'

    # Define receiver details
    receiver_emails = ['ravi.choppara@pro-vigil.com', 'varaprasadu.palanki@pro-vigil.com']

    # Define email content
    subject = 'Zipstream automation success and failed cameras list'
    body = 'Please find the attached CSV files'
    # Define the signature
    signature = """
    With Best Regards

    Ravi Choppara

    Pro-Vigil Surveillance

    E-mail: ravi.choppara@pro-vigil.com

    Mobile: (91) 9966961022

    Website: pro-vigil.com
    """

    # Combine the body of the email with the signature
    body_with_signature = body + "\n\n" + signature

    # Send email if query_type is 'ALL'
    if args.query_type == 'ALL':
        for receiver_email in receiver_emails:
            send_email_with_dynamic_csv(sender_email, sender_password, receiver_email, subject, body)
        logging.info("Sent emails to recipients")

    # Upload log folders to S3
    s3_bucket = 'zipstreamlogs-test'
    s3_date_folder = current_date  # Date folder on S

    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=s3_bucket, Key=f"{s3_date_folder}/")
        logging.info(f"Connected to S3: s3://{s3_bucket}")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':
            logging.info(
                f"S3 folder {s3_date_folder} does not exist. Creating...")
            s3.put_object(Bucket=s3_bucket, Key=f"{s3_date_folder}/")
            logging.info(f"Created S3 folder: s3://{s3_bucket}/{s3_date_folder}")

    for root, dirs, files in os.walk(log_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            if os.path.isfile(file_path):
                if file_name.endswith('.csv'):
                    s3_key = os.path.join(s3_date_folder, args.query_type + '.' + args.strength, file_name)
                else:
                    s3_key = os.path.join(s3_date_folder, args.query_type + '.' + args.strength, file_name)
                s3_upload_object(s3_bucket, s3_key, file_path)

        # Remove the local log folder after successful upload
    shutil.rmtree(log_folder)


if __name__ == "__main__":
    main()
