import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

# Define el alcance correcto
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

EMAIL = "guillotula@gmail.com"
CALENDAR_ID = "primary"  # O usa el email del calendario si no es el principal

def main():
    creds = None

    # Cargar credenciales si ya existen
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Si no hay credenciales o son inválidas, solicitar autenticación
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Guardar credenciales
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    # Llamar a la función para descargar eventos
    download_events(creds)


def download_events(creds):
    """Descarga eventos del Google Calendar"""
    url = f"https://www.googleapis.com/calendar/v3/calendars/{EMAIL}/events"

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }

    params = {
        "timeMin": "2025-02-18T00:00:00Z",
        "timeMax": "2025-02-20T00:00:00Z",
        "orderBy": "startTime",
        "singleEvents": "true"
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        eventos = response.json()
        print(json.dumps(eventos, indent=2))  # Imprimir eventos formateados
    else:
        print("Error:", response.status_code, response.text)



if __name__ == '__main__':
    main()
