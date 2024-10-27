import streamlit as st
import os
import json
import glob
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]

file_name = None

def get_credentials():
    credentials_json = os.getenv("GOOGLE_CREDENTIALS")
    if credentials_json is not None:
        # 内容をJSONファイルとして保存
        with open("credentials.json", "w") as f:
            f.write(credentials_json)
        return Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    elif os.path.exists("credentials.json"):
        return Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    

def download_file(file_id):
    creds = get_credentials()
    if creds is None:
        st.error("GOOGLE_CREDENTIALS environment variable not set.")
        return
    
    try:
        service = build('drive', 'v3', credentials=creds)
        file_name = service.files().get(fileId=file_id).execute()["name"]
        request = service.files().get_media(fileId=file_id)
        fh = open(file_name, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            st.write(f"Download {int(status.progress() * 100)}%.")
        st.success("Download complete.")
    except HttpError as e:
        st.error(f"An error occurred: {e}")


st.title("Google Drive Downloader")
if os.getenv("GOOGLE_CREDENTIALS") is None:
    st.write("GOOGLE_CREDENTIALS environment variable not set.")
else:
    st.write("GOOGLE_CREDENTIALS environment variable set.")
file_id = st.text_input("Enter the file ID:")
if st.button("Download"):
    download_file(file_id)
    st.write("Download complete.")
    files = glob.glob("./*")
    for f in files:
        st.write(f)
# st.download_button("Download the downloaded file", file_name)

