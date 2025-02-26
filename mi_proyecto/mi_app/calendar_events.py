import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
import uuid
from googleapiclient.errors import HttpError
from mi_app.models import users
from django.db import IntegrityError
from mi_app.calendar_auth import get_credentials_from_bd

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_PATH = 'credentials.json'



def get_events(user, time_min, time_max):
    url = f"https://www.googleapis.com/calendar/v3/calendars/{user}/events"

    creds = get_credentials_from_bd(user)
    if not creds:
        print(f"⚠ No se encontraron credenciales para {user}")
        return []  # Evita que devuelva None

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

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # se lanza un error si falla la request
        events = response.json().get("items", [])

        if events is None:  # aseguramos que sea una lista
            return []
        print(events.__len__())
        return events

    except requests.RequestException as e:
        print(f"⚠ Error al obtener eventos: {e}")
        return []





def get_freetime(user, day):
    free_time = []
    day = day.split("T")[0]  # aseguramos que esté en formato YYYY-MM-DD

    # se define la zona horaria local (Montevideo, UTC-3)
    local_offset = timedelta(hours=-3)  
    local_tz = timezone(local_offset)

    # se crea las horas de trabajo en la zona horaria local 
    # (esto habría que cambiarlo porque cada usuario puede tener un horario de trabajo distinto)
    work_start = datetime.strptime(f"{day} 09:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=local_tz)
    work_end = datetime.strptime(f"{day} 18:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=local_tz)

    # se convierte a UTC
    work_start_utc = work_start.astimezone(timezone.utc)
    work_end_utc = work_end.astimezone(timezone.utc)

    # se convierte a string ISO 8601 para la API de Google Calendar
    work_start_iso = work_start_utc.isoformat()
    work_end_iso = work_end_utc.isoformat()

    events = get_events(user, work_start_iso, work_end_iso)

    work_start_minutes = 9 * 60  # 540 minutos (09:00 AM)
    work_end_minutes = 18 * 60  # 1080 minutos (18:00 PM)

    current_time = work_start_minutes  

    for event in events:
        print(current_time)
        event_start = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")).time()
        event_end = datetime.fromisoformat(event["end"]["dateTime"].replace("Z", "+00:00")).time()

        start_minutes = event_start.hour * 60 + event_start.minute
        end_minutes = event_end.hour * 60 + event_end.minute
        print("tiempo libre:", current_time, start_minutes)

        if current_time < start_minutes:
            print("tiempo libre:", current_time, start_minutes)
            free_time.append((current_time, start_minutes))

        current_time = end_minutes  # actualiza el tiempo actual al fin del evento

    # último bloque de tiempo libre después del último evento
    if current_time < work_end_minutes:
        free_time.append((current_time, work_end_minutes))

    return free_time





def new_event(user, summary, start, end):
    url = f"https://www.googleapis.com/calendar/v3/calendars/{user}/events"

    creds = get_credentials_from_bd(user)
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

    if response.status_code == 200:
        return response.json().get('items', [])  # lista los eventos
    else:
        return {"error": response.status_code, "message": response.text}
    


def new_event_meet(usersList, summary, start, end):
    if not usersList:
        return {"success": False, "error": "No hay usuarios en la lista."}

    attendees_list = [{"email": email} for email in usersList]  # asistentes

    event = {
        "summary": "Reunión de equipo",
        "location": "Google Meet",
        "description": summary,
        "start": {
            "dateTime": start,  
            "timeZone": "America/Montevideo",
        },
        "end": {
            "dateTime": end, 
            "timeZone": "America/Montevideo",
        },
        "attendees": attendees_list,  # lista de todos los usuarios como invitados
        "conferenceData": {
            "createRequest": {
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
                "requestId": str(uuid.uuid4())  # ID único para la reunión
            }
        }
    }

    meet_owner = usersList[0]  # el organizador es el primero en la lista
    creds = get_credentials_from_bd(meet_owner)
    service = build('calendar', 'v3', credentials=creds)

    try:
        service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1,  
            sendUpdates="all"
        ).execute()
        return {"success": True, "message": "Evento creado con éxito."}
    except HttpError as e:
        return {"success": False, "error": f"Error al crear evento: {e}"}



