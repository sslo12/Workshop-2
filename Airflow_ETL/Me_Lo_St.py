from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import logging
import pandas as pd
import json
import call_db

credentials_path = './Airflow_ETL/credentials_module.json'

# LOGIN SESSION
def login():
    GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = credentials_path
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(credentials_path)
    
    if gauth.credentials is None:
        logging.info("Initial authentication")
        gauth.LocalWebserverAuth(port_numbers=[8092])
    elif gauth.access_token_expired:
        logging.info("Refreshing authentication..")
        gauth.Refresh()
    else:
        logging.info("Authentication already exists")
        gauth.Authorize()
        
    gauth.SaveCredentialsFile(credentials_path)
    credenciales = GoogleDrive(gauth)
    return credenciales

# UPLOAD A FILE TO DRIVE
def upload_csv(file_path, id_folder):
    credentials = login()
    file_csv = credentials.CreateFile({'parents': [{"kind": "drive#fileLink",\
                                                    "id": id_folder}]})
    file_csv['title'] = file_path.split("/")[-1]
    file_csv.SetContentFile(file_path)
    file_csv.Upload()
    logging.info("Data Successfully Uploaded to Google Drive.")

def decade(year):
    return (year // 10) * 10

# COMBINATION OF CSV AND DB
def merge(**kwargs):
    ti = kwargs['ti']
    data = json.loads(ti.xcom_pull(task_ids="transform_db"))
    grammy_df = pd.json_normalize(data=data)

    data = json.loads(ti.xcom_pull(task_ids="transform_csv"))
    spotify_df = pd.json_normalize(data=data)
    logging.info("Data merging process started...")

    merged_data = pd.merge(grammy_df, spotify_df, left_on='artist', right_on='artists', how='inner')
    merged_data['decade'] = merged_data['year'].apply(decade)
    if 'grammy_id' in merged_data.columns:
        merged_data.drop_duplicates(subset='grammy_id', inplace=True)
    col_interest = ['year', 'category', 'nominee', 'artist', 'was_nominated', 
                           'track_id', 'artists', 'track_name', 'popularity', 'danceability', 
                           'energy', 'valence', 'album_name', 'explicit', 'decade']
    merged_data = merged_data[col_interest]
    logging.info("Data merging process successfully completed.")
    return merged_data.to_json(orient='records')


# LOAD MERGED CSV TO DB
def load(**kwargs):
    ti = kwargs["ti"]
    data = ti.xcom_pull(task_ids="merge")
    if data:
        data = pd.json_normalize(data)
        logging.info("Data normalized and DataFrame created.")
        
        try:
            call_db.insert_data(data)
            logging.info("Data has been successfully loaded into the database.")
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
    else:
        logging.error("No data available to load.")


# LOAD CSV MERGED TO DRIVE
def store(**kwargs):
    ti = kwargs["ti"]
    data = ti.xcom_pull(task_ids="merge")
    if data:
        data = pd.json_normalize(data)
        csv_path = './Datasets/awards.csv'
        data.to_csv(csv_path, index=False)
        upload_csv(csv_path, '1PnHh7eQz-aWPwuXALNQ2Hu7JaGIWaYUB')
        logging.info("File 'awards.csv' stored and uploaded to Google Drive.")