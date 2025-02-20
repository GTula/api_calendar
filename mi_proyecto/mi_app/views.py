from django.http import JsonResponse
from mi_app.services import get_freetime

def calendar_events(request):
    """Vista de Django para obtener eventos desde hoy en adelante."""
    from datetime import datetime, timedelta

    # Obtener fecha y hora actual en formato ISO 8601
    now = datetime.utcnow().isoformat() + "Z"
    end = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"  # Ejemplo: próximos 7 días

    eventos = get_freetime(now, end)
    
    return JsonResponse(eventos, safe=False)
