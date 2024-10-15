import os
import requests
from urllib.parse import quote
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from dotenv import load_dotenv

load_dotenv()

GOOGLE_GEOCODING_API_KEY = os.getenv("GOOGLE_GEOCODING_API_KEY")


# Create your views here.
def home(request):
    return render(request, 'index.html')

def calcular_tiempo_ruta_optima(request):
    if request.method == 'POST':
        activities = request.POST.getlist('activities[]')
        total_time = 0

        # Calcular rutas entre actividades utilizando OSRM
        for i in range(len(activities) - 1):
            coord1 = activities[i].split(',')
            coord2 = activities[i + 1].split(',')

            # Llamada a la API de OSRM para calcular el tiempo de viaje
            url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}?overview=false"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                print(data)
                travel_time = data['routes'][0]['duration'] / 60  # Convertir a minutos
                total_time += travel_time
            else:
                return JsonResponse({"error": "Error al calcular la ruta"}, status=500)

        return JsonResponse({"total_time": round(total_time,2)})

    return JsonResponse({"error": "Método no permitido"}, status=400)

def buscar_direccion(request):
    if request.method == 'GET':
        direccion = request.GET.get('direccion')
        if not direccion:
            return JsonResponse({"error": "Dirección no proporcionada."}, status=400)

        direccion_codificada = quote(direccion)
        print("Dirección codificada: ", direccion_codificada)

        # Hacer la solicitud a la API de Google Geocoding
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion_codificada}&key={GOOGLE_GEOCODING_API_KEY}"
        #print(url)
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("data: ",data)
            if data['status'] == 'OK':
                location = data['results'][0]['geometry']['location']
                return JsonResponse({
                    "lat": location['lat'],
                    "lng": location['lng'],
                    "direccion_formateada": data['results'][0]['formatted_address']
                })
            else:
                return JsonResponse({"error": "No se pudo encontrar la dirección."}, status=400)
        else:
            return JsonResponse({"error": "Error en la solicitud a la API de Google Geocoding."}, status=500)

    return JsonResponse({"error": "Método no permitido."}, status=400)