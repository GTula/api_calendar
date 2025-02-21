import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from datetime import datetime, timezone

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
EMAIL = "guillotula@gmail.com" # Email de ejemplo
TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'
url = f"https://www.googleapis.com/calendar/v3/calendars/{EMAIL}/events"


def get_credentials():
    """Autentica con Google y devuelve credenciales válidas."""
    creds = None

    # Cargar credenciales si ya existen
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # realiza autenticación si no hay credenciales 
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # guarda las credenciales
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds


def get_events(time_min, time_max):
    """Obtiene eventos de Google Calendar entre fechas específicas."""
    creds = get_credentials()
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }

    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "orderBy": "startTime",
        "singleEvents": "true"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json().get('items', [])  # lista los eventos
    else:
        return {"error": response.status_code, "message": response.text}




def get_freetime(now, end):
    free_time = []
    events = get_events(now, end)

    event_day = datetime.fromisoformat(now.replace("Z", "+00:00")).date()  # Extraer solo la fecha

    work_start = datetime.combine(event_day, datetime.strptime("09:00", "%H:%M").time(), tzinfo=timezone.utc)
    work_end = datetime.combine(event_day, datetime.strptime("18:00", "%H:%M").time(), tzinfo=timezone.utc)
    current_time = work_start
    
    for event in events:
        event_start = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00"))
        event_end = datetime.fromisoformat(event["end"]["dateTime"].replace("Z", "+00:00"))

        start = current_time.hour * 60 + current_time.minute
        end = event_start.hour * 60 + event_start.minute

        if current_time.strftime("%H:%M") < event_start.strftime("%H:%M"):  
            free_time.append({
                "day": datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")).date().strftime("%Y-%m-%d"),
                "start": start,
                "end": end
            })
        current_time = event_end  

    start = current_time.hour * 60 + current_time.minute
    end = work_end.hour * 60 + work_end.minute

    if current_time.strftime("%H:%M") < work_end.strftime("%H:%M"):
        free_time.append({
            "day": datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")).date().strftime("%Y-%m-%d"),
            "start": start,
            "end": end
        })

    return free_time


def new_event(summary, start, end):

    creds = get_credentials()
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }

    event_data = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": "UTC"},
        "end": {"dateTime": end, "timeZone": "UTC"}
    }
    response = requests.post(url, headers=headers, data=json.dumps(event_data))

