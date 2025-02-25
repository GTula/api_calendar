import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account
import uuid
from googleapiclient.errors import HttpError
from mi_app.models import users
from django.db import IntegrityError

SCOPES = ['https://www.googleapis.com/auth/calendar']
EMAIL = "guillotula@gmail.com" # Email de ejemplo
TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'
url = f"https://www.googleapis.com/calendar/v3/calendars/{EMAIL}/events"


#funcion para obtener valores de las credenciales de oauth
def load_credentials():
    """Carga client_id y client_secret desde el archivo credentials.json."""
    with open('credentials.json', 'r') as file:
        creds_data = json.load(file)

    client_id = creds_data['installed']['client_id']
    client_secret = creds_data['installed']['client_secret']
    
    return client_id, client_secret


#función para autenticar al usuario si no se encuentra registrado en la bd
def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', ['https://www.googleapis.com/auth/calendar']
    )
    creds = flow.run_local_server(port=0)  # abre una ventana para autenticación
    
    return creds

#función para obtener el token de un usuario en específico
def obtener_refresh_token_bd(email):
    try:
        user = users.objects.get(email=email)
        return user.refresh_token
    except users.DoesNotExist:
        return None

#función para guardar el token en la bd
def guardar_refresh_token_bd(email, refresh_token):
    try:
        user = users.objects.get(email=email)
        user.refresh_token = refresh_token
        user.save()
    except users.DoesNotExist:
        user = users(email=email, refresh_token=refresh_token)
        user.save()

#función para obtener las credenciales del usuario
def get_credentials_from_bd(email):
    stored_data = obtener_refresh_token_bd(email)  # obtiene el refresh_token de la BD

    (client_id, client_secret) = load_credentials()

    if stored_data:
        creds = Credentials(
            token=None,  # se regenerará con refresh
            refresh_token=stored_data,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )

        # si las credenciales son válidas o se pueden refrescar, usarlas
        if creds and creds.refresh_token:
            creds.refresh(Request())  # se renueva el token de acceso
            guardar_refresh_token_bd(email, creds.refresh_token)
            return creds
    
    # si no hay refresh_token en la BD, obtiene nuevas credenciales
    creds = get_credentials()
    guardar_refresh_token_bd(email, creds.refresh_token)  # guarda el nuevo refresh_token
    return creds



def get_events(user, time_min, time_max):
    url = f"https://www.googleapis.com/calendar/v3/calendars/{user}/events"


    """Obtiene eventos de Google Calendar entre fechas específicas."""
    creds = creds = get_credentials_from_bd(user)
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




def get_freetime(user, day):
    free_time = []

    # asegura que day solo tenga el formato YYYY-MM-DD
    day = day.split("T")[0]  # eliminamos cualquier hora/zona horaria si la tiene

    now = f"{day}T09:00:00Z"  # inicio de jornada laboral
    end = f"{day}T18:00:00Z"  # fin de jornada laboral
    
    events = get_events(user, now, end)  # obtener los eventos del usuario en ese día

    work_start = datetime.strptime("09:00", "%H:%M").time()
    work_end = datetime.strptime("18:00", "%H:%M").time()
    
    current_time = work_start

    for event in events:
        event_start = datetime.fromisoformat(event["start"]["dateTime"].replace("Z", "+00:00")).time()
        event_end = datetime.fromisoformat(event["end"]["dateTime"].replace("Z", "+00:00")).time()

        start_minutes = current_time.hour * 60 + current_time.minute
        end_minutes = event_start.hour * 60 + event_start.minute

        if start_minutes < end_minutes:  # Hay un espacio libre antes del evento
            free_time.append((start_minutes, end_minutes))

        current_time = event_end  # actualiza la hora actual al fin del evento

    # último bloque de tiempo disponible después del último evento
    start_minutes = current_time.hour * 60 + current_time.minute
    end_minutes = work_end.hour * 60 + work_end.minute

    if start_minutes < end_minutes:
        free_time.append((start_minutes, end_minutes))

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
    


# def new_event_meet(usersList, summary, start, end):
#     attendees_list = [{"email": email} for email in usersList]

#     service = build('calendar', 'v3', credentials=get_credentials())

#     event = {
#         "summary": "Reunión de equipo",
#         "location": "Google Meet",
#         "description": summary,
#         "start": {
#             "dateTime": start,  # hay que verificar de que esté en formato correcto: "YYYY-MM-DDTHH:MM:SS-03:00"
#             "timeZone": "America/Montevideo",
#         },
#         "end": {
#             "dateTime": end,  # hay que verificar de que esté en formato correcto: "YYYY-MM-DDTHH:MM:SS-03:00"
#             "timeZone": "America/Montevideo",
#         },
#         "attendees": attendees_list,  
#         "conferenceData": {
#             "createRequest": {
#                 "conferenceSolutionKey": {"type": "hangoutsMeet"},
#                 "requestId": str(uuid.uuid4())  # Genera un ID único para la reunión
#             }
#         }
#     }

#     # crea el evento en el calendario principal del usuario autenticado
#     try:
#         event_response = service.events().insert(
#             calendarId="primary",  # Usa 'primary' para el calendario del usuario autenticado
#             body=event,
#             conferenceDataVersion=1  # Necesario para crear reuniones de Google Meet
#         ).execute()

#         return {
#             "success": True,
#             "eventLink": event_response.get("htmlLink"),  # Enlace al evento en Google Calendar
#             "meetLink": event_response.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri")  # Link de Google Meet
#         }

#     except HttpError as error:
#         return {
#             "success": False,
#             "error": error.resp.status,
#             "message": error._get_reason()
#         }

