import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from mi_app.models import users

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_PATH = 'credentials.json'

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