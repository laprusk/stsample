import streamlit as st
import time
import os
import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_credentials():
    """認証情報を取得する関数"""
    creds = None
    
    # セッションステートからトークンを取得
    if 'token' in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state['token'], SCOPES)
    
    # 認証情報が無効な場合の処理
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                st.error(f"Error refreshing credentials: {e}")
                creds = None
        
        # 新規認証が必要な場合
        if not creds:
            try:
                credentials_json = st.secrets["gdrive_credentials"]
                credentials_dict = json.loads(credentials_json)
                
                # 認証フローの作成
                flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
                
                # 認証URLの生成
                auth_url = flow.authorization_url()
                
                # 認証URLを表示
                st.write("Please visit this URL to authorize this application:")
                st.write(auth_url[0])
                
                # 認証コードの入力フィールド
                code = st.text_input('Enter the authorization code:')
                
                if code:
                    try:
                        # 認証コードを使用してクレデンシャルを取得
                        flow.fetch_token(code=code)
                        creds = flow.credentials
                        
                        # セッションステートにトークンを保存
                        st.session_state['token'] = json.loads(creds.to_json())
                        st.success("Successfully authenticated!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error during authentication: {e}")
                        return None
                else:
                    return None
                
            except Exception as e:
                st.error(f"Authentication error: {e}")
                return None
    
    return creds

def google_drive_api():
    """Google Drive APIを使用してファイル一覧を取得"""
    creds = get_credentials()
    
    if not creds:
        st.warning("Please complete the authentication process")
        return
    
    try:
        service = build("drive", "v3", credentials=creds)
        
        results = service.files().list(
            pageSize=10,
            fields="nextPageToken, files(id, name)"
        ).execute()
        
        items = results.get("files", [])
        
        if not items:
            st.write("No files found")
            return
            
        st.write("Files:")
        for item in items:
            st.write(f"{item['name']} ({item['id']})")
            
    except HttpError as error:
        st.error(f"An error occurred: {error}")

# UI部分
st.title("Google Drive File Viewer")

input_num = st.number_input('Input a number', value=0)
result = input_num ** 2
st.write('Result: ', result)

if st.button('Run'):
    google_drive_api()
    st.write('Done!')