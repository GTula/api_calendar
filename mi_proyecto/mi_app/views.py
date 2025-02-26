from django.http import JsonResponse
from mi_app.calendar_events import get_freetime
from mi_app.calendar_events import new_event_meet



EMAIL = "guillotula@gmail.com" # Email de ejemplo

def calendar_events(request):
    """Vista de Django para obtener eventos desde hoy en adelante."""
    from datetime import datetime, timedelta

    # Obtener fecha y hora actual en formato ISO 8601
    now = datetime.utcnow().isoformat() + "Z"

    eventos = get_freetime(EMAIL, now)
    
    return JsonResponse(eventos, safe=False)

def new_meet(request):
    """Vista de Django para crear un nuevo evento en el calendario."""

    event = {
        "list": ["guillotula@gmail.com", "dsuperate@gmail.com"],  # Ahora es una lista real
        "summary": "Reunión de trabajo",
        "start": "2025-02-26T11:00:00",
        "end": "2025-02-26T11:30:00"
    }


    response = new_event_meet(event["list"], event["summary"], event["start"], event["end"])

    return JsonResponse(response, safe=False)