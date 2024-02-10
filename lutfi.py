import streamlit as st
import asyncio
import websockets
import requests
import uuid
from datetime import datetime, timezone, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

BASE_URL = "https://live.shopee.co.id"
API_URL = f"{BASE_URL}/api/v1/session/"
WEBSOCKET_URL = f"wss://live.shopee.co.id/im/v1/comet?version=v2"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CREDS_JSON = '''
{
  "type": "service_account",
  "project_id": "toolslivev1",
  "private_key_id": "590fe4b01badd10c7a1467b0762423fb34f81cc9",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCpAB4rkI4M+DoL\\nVb94zH9hCikL8D5rdpMBt+jqRSyfQ4QC4JMc/7krGsvH+Dsm4SNtKvr1elENTKSH\\nfHUxUxG/q4VUII+wri3bSsay9Rh4aecGx329NN1VC1pR+okKH5LHwhnbHuHeOYNB\\nG8j8xIMDNbGT5A9SH0vp1bidI+5cJn3Ohq57fdf3VoVzn9KaR6ltyaP0WrQgT7IF\\n39bMuuWGBhu8DGKv1bz0wKR0Yl3uqa5U3HG9ZW8602uFd011dpMFUKzYaqSQOJD2\\ndVUc6yrXrUhRHpzrB/SGeRHU/AeSCPzUczwk4Jq3ws4F+0indXzJOThLb7ZAo5hn\\nrzoZFZAXAgMBAAECggEAGGxC7+rJDIjG4qJ2tD9hXSW5vtbuPlt5bTMlvs1WYIHC\\nTyQjPnqaSOdrca+m5Lx+gSVH9TfDBNgBou7ShNlLZFamQv0dptvVFq7cvjn7WlN7\\nppgnzLMaFVM5r0U0jrj3XlTnpan13EaVeFBKoHTJtioJSqUXrbeGIfnX3yW1Ka3O\\nO6DV6Ac0ZoRIRbrheQlnRz7sfjWuQIyHlPyp8U0DYyrFvN2CoHaJTZ/U9aR232Tg\\nrwGoiQOVIicMS0ReY5b1ixcTNZkKp1E8YIcfic1Iesd9WpQRuZ5o3gnTPf9ijx4T\\nJpyJc7SF4s4oYQEzTu3C+5pKJt75Dy19tcE9NIwAMQKBgQDRuxGt/9ahzJlu/yqd\\nrzp1vAvYCR1/qWwgCuRICWSvQTnfa883FOdWJlI5SO+dVwvOmL94AyEdbkK6FBZp\\nYPznhN5Q/zz4hp6tcFKv+GZNn9/K0N4lcusvoCmC+pdFgMl0M8aspBbbYGydrqdb\\nUmtV3peR6SlsqLWJCEKdobM+7wKBgQDOSLsoMY+vGy2Qk1lOb8WJhg4+mmNU5OEi\\nTlYOPKXnjYfoGR5J9eHkoEmkZ/vVfXxM/iNQGNBwPexykBfyU2sfz1t01TK/MSYZ\\n3EQbNhDz0DKvv2jCkQ6sZgIcHbVD2e2LeWh4d5JR+CnNAH4BD31o6eTvFwUezRUz\\nzWkEbdZBWQKBgHm4Guuj5lni101u87muH7yClVEdASy9FA6Io7IXGYMI1OCQviMW\\nk6gQ93ldlgr3oNeXGNA66LYe7sT1sYgZDM4E882IREdsQZ0g6ixMenskhQo9LCAJ\\n0OrEBjOI4dApjUFOZ0h8tvM8w+zDl0dNzxN36vl4m1z/kNPlolu/o7qrAoGAQjWv\\n9J+ruY1km5HfyUAwzAo+CjPti/MGm8c+8cTfjymrJIDjauPDxGj6Gg3SE9z6B5BO\\nb0f3pv8JJGBBf2Ls8EHS3fYMGrfAve4n4gABgvAhRK2QB1sdtZHsPW//nS6WgvzN\\n3lSqnyqi6AyvZNG+8+yWsXLXDuLOWlkkyuoiKckCgYBdoLX1wB7ZNUFaHRyOBF0A\\nRoqibHuxEmBSiCLj4XmIhZxbipmoCpzJT6cywziujZom60+2QY1fgKPdHxCBzqXh\\npbxujmqcET2gfXqOXXbIV67VNtSCien8mCSSPGlKldxDAjCBiEt8a3MrFNc+egqc\\n4Fdh4ssGtTnJbKH2DbunCQ==\\n-----END PRIVATE KEY-----\\n",
  "client_email": "toolslivevi1@toolslivev1.iam.gserviceaccount.com",
  "client_id": "118264569871480891940",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/toolslivevi1%40toolslivev1.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
'''

creds_dict = json.loads(CREDS_JSON)
creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)


async def shopee_websocket(generated_uuid, waktu, sesi, usersig):
    uri = (f"{WEBSOCKET_URL}&conn_ts={waktu}"
           f"&device_id={generated_uuid}&session_id={sesi}"
           f"&usersig={usersig}&version=v2")

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as _:
            print(f"Connection closed on {generated_uuid}. Reconnecting...")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"An unexpected error occurred on {generated_uuid}: {e}")
            await asyncio.sleep(10)


def current_time_to_timestamp():
    current_time = datetime.now(timezone(timedelta(hours=7)))
    timestamp = int(current_time.timestamp() * 1000)
    return timestamp


def join_shopee_session(session_id, generated_uuid, usersig):
    url = f"{API_URL}{session_id}/join"
    data = {
        "uuid": generated_uuid,
        "ver": 1
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.193 Mobile Safari/537.36',
        'Referer': BASE_URL,
        'Authorization': f'Bearer {usersig}'
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        json_response = response.json()
        if 'data' in json_response and 'usersig' in json_response['data']:
            return json_response['data']['usersig']
        else:
            print(f"Error joining Shopee session {session_id}: Invalid response format")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error joining Shopee session {session_id}: {e}")
        return None


def shopee_streamlit_app():
    st.title("👁️View Mata Versi Premium👁️")

    # Input teks untuk login
    username = st.text_input("Enter your username:")
    key = st.text_input("Enter your key:", type="password")

    # Input teks untuk num_connections
    num_connections = st.slider("Select the number of view:", 1, 100, 1)

    # Input teks untuk session_ids
    session_ids = st.text_area("Enter session IDs (one per line):", "")
    session_ids = [line.strip() for line in session_ids.split("\n") if line.strip()]

    if st.button("Login and Start"):
        if not username or not key:
            st.error("Please enter both username and key.")
            return

        usersig = login(username, key)

        if usersig:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_shopee_websockets(num_connections, session_ids, usersig))


async def run_shopee_websockets(num_connections, session_ids, usersig):
    tasks = []

    for session_id in session_ids:
        for _ in range(num_connections):
            result_timestamp = current_time_to_timestamp()
            generated_uuid = str(uuid.uuid4())
            usersig = join_shopee_session(session_id, generated_uuid, usersig)
            if usersig:
                task = shopee_websocket(generated_uuid, result_timestamp, session_id, usersig)
                tasks.append(task)

    await asyncio.gather(*tasks)


def login(username, key):
    try:
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId="1peqn1uWgqVxvb9NDUxeA6YBtx3EdP_vE3fkPsM2w8LY", range="User!A:B")
            .execute()
        )

        values = result.get("values", [])

        if not values:
            print("No data found in the Google Sheet.")
            return None

        for row in values:
            if len(row) >= 2 and row[0] == username and row[1] == key:
                return row[1]  # Assuming the usersig is in the second column (index 1)

        print("Invalid username or key.")
        return None

    except HttpError as err:
        print(f"Error accessing Google Sheets API: {err}")
        return None


if __name__ == "__main__":
    shopee_streamlit_app()
