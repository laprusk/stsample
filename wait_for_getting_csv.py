# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START drive_quickstart]
import os.path
import io
import json

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

import paho.mqtt.client as mqtt

protocol_version = "0.1.0"
download_dir = "./"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_credentials_from_service_account():
  credentials_info = os.getenv("GOOGLE_CREDENTIALS")
  if credentials_info is not None:
    credentials_dict = json.loads(credentials_info, strict=False)
    creds = Credentials.from_service_account_info(credentials_dict)
    return creds
  else:
    creds = Credentials.from_service_account_file("credentials.json")
    return creds


def _download_from_drive(file_id: str):
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
  creds = _get_credentials_from_service_account()
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  # if os.path.exists("token.json"):
  #   creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # # If there are no (valid) credentials available, let the user log in.
  # if not creds or not creds.valid:
  #   if creds and creds.expired and creds.refresh_token:
  #     creds.refresh(Request())
  #   else:
  #     flow = InstalledAppFlow.from_client_secrets_file(
  #         "credentials.json", SCOPES
  #     )
  #     creds = flow.run_local_server(port=0)
  #   # Save the credentials for the next run
  #   with open("token.json", "w") as token:
  #     token.write(creds.to_json())

  try:
    service = build("drive", "v3", credentials=creds)

    request = service.files().get_media(fileId=file_id)
    file_name = service.files().get(fileId=file_id).execute()["name"]

    # ダウンロードディレクトリが存在しない場合は作成
    if not os.path.exists(download_dir):
      os.makedirs(download_dir)

    # ファイルのダウンロード
    file = io.FileIO(f"{download_dir}/{file_name}", mode="wb")
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
      status, done = downloader.next_chunk()
      print(f"Download {int(status.progress() * 100)}.")
    print(f"ファイルのダウンロードが完了しました: {file_name}")

  except HttpError as error:
    # TODO(developer) - Handle errors from drive API.
    print(f"An error occurred: {error}")


def wait_for_getting_csv(topic: str):
  host = "broker.emqx.io"
  port = 1883

  def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
      print(f"接続失敗: {reason_code}")
    else:
      print(f"接続成功: {reason_code}")
      client.subscribe(topic)
  
  # メッセージ受信時のコールバック関数
  # メッセージを受信したらファイルをダウンロード
  # プロトコルバージョンが一致しない場合はエラーを出力
  def on_message(client, userdata, message):
    try:
      response = json.loads(message.payload)
    except json.JSONDecodeError as e:
      print(f"JSONとしてデコードできません: {e}")
      return
    print(f"メッセージを受信しました: {response}")
    if "protocol_version" not in response or "file_id_list" not in response:
      print("メッセージが不正です")
      return
    if response["protocol_version"] == protocol_version:
      file_id_list = response["file_id_list"]
      for file_id in file_id_list:
        _download_from_drive(file_id)
      client.disconnect()
    else:
      print("プロトコルバージョンが一致しません")
  
  client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
  client.on_connect = on_connect
  client.on_message = on_message
  client.connect(host, port)
  client.loop_forever()


if __name__ == "__main__":
  wait_for_getting_csv("nucit/project/gp4/exchange")
  print("終了")
