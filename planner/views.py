import os
import json
import random
import requests
from urllib.parse import quote
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from dotenv import load_dotenv
from ortools.constraint_solver import pywrapcp, routing_enums_pb2 

load_dotenv()

GOOGLE_GEOCODING_API_KEY = os.getenv("GOOGLE_GEOCODING_API_KEY")


# Create your views here.
def home(request):
    return render(request, 'index.html')

#Calculo ruta optima con OSRM
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
                #print(data)
                travel_time = data['routes'][0]['duration'] / 60  # Convertir a minutos
                total_time += travel_time
            else:
                return JsonResponse({"error": "Error al calcular la ruta"}, status=500)

        return JsonResponse({"total_time": round(total_time,2)})

    return JsonResponse({"error": "Método no permitido"}, status=400)

#Buscar direccion con GEOXCODING DE GOOGLE
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

#Obtencion de lugares turisticos
def obtener_lugares_turisticos(request):
    if request.method == 'GET':
        # Definir la consulta Overpass para obtener iglesias, parques, museos en la Región Metropolitana
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = """
        [out:json];
        area[name="Región Metropolitana de Santiago"]->.searchArea;
        (
        node["tourism"="museum"](area.searchArea);
        node["amenity"="place_of_worship"](area.searchArea);
        node["leisure"="park"](area.searchArea);
        );
        out center;
        """
        
        response = requests.get(overpass_url, params={'data': overpass_query})
        
        if response.status_code == 200:
            data = response.json()
            
            # Convertir los datos a GeoJSON
            geojson_data = convert_to_geojson(data)

            # Crear la carpeta 'geojson' si no existe
            geojson_dir = os.path.join(settings.BASE_DIR, 'planner/static', 'geojson')
            if not os.path.exists(geojson_dir):
                os.makedirs(geojson_dir)

            # Guardar el archivo GeoJSON
            geojson_path = os.path.join(geojson_dir, 'lugares_turisticos.geojson')
            with open(geojson_path, 'w', encoding='utf-8') as geojson_file:
                json.dump(geojson_data, geojson_file, ensure_ascii=False, indent=4)
            
            return JsonResponse({"status": "success", "message": "Lugares turísticos obtenidos y guardados exitosamente."})
        
        return JsonResponse({"status": "error", "message": "Error al obtener los lugares turísticos."})
    
    return JsonResponse({"status": "error", "message": "Método no permitido."})

#FUNCION QUE CONVIERTE LOS DATOS A GEOJSON
def convert_to_geojson(overpass_data):
    """
    Convierte los datos obtenidos de la API Overpass al formato GeoJSON.

    Args:
        overpass_data (dict): Datos JSON devueltos por la Overpass API.
    
    Returns:
        dict: Un diccionario en formato GeoJSON.
    """
    features = []
    
    # Recorrer los elementos y convertir a Feature
    for element in overpass_data.get('elements', []):
        if 'lat' in element and 'lon' in element:  # Si es un nodo con coordenadas
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [element['lon'], element['lat']]
                },
                "properties": element.get('tags', {})  # Las propiedades provienen de los "tags"
            }
            features.append(feature)
    
    # Estructura GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    return geojson



#FUNCIONES PARA PODER CALCULAR CON GOOGLE OR TOOLS(Las mejores rutas VRPTW)
def generate_time_windows(num_activities):
    time_windows = []
    for i in range(num_activities):
        start_time = random.randint(540, 660)  # Entre 5:00 AM y 10:00 AM
        end_time = random.randint(900, 1020)  # Entre 5:00 PM y 1020 PM
        time_windows.append((start_time, end_time))
    return time_windows

def create_matrix(activities):
    matrix = []

    for i in range(len(activities)):
        matrix_row = []
        for j in range(len(activities)):
            coord1 = activities[i].split(',')
            coord2 = activities[j].split(',')
            print("calculando tiempo ",f"actividad {i} ->",f"actividad {j}")
            url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}?overview=false"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                travel_time = data['routes'][0]['duration'] /60  
                #print("tiempo:", travel_time)
                matrix_row.append(int(round(travel_time, 2)))
            else:
                print("Error al calcular el tiempo entre las actividades")
        matrix.append(matrix_row)
    
    return matrix


def VRPTW(request):
    if request.method == 'POST':
        activities = request.POST.getlist('activities[]')
        print("Actividades recibidas:", activities)

        # Creación de la matriz de distancia usando OSRM
        time_matrix = create_matrix(activities)
        
        # Simulación de ventanas de tiempo (tiempos en minutos)
        time_windows = generate_time_windows(len(activities))

        # Definición del problema VRPTW con las ventanas de tiempo
        data = {
            "time_matrix": time_matrix,
            "num_vehicles": 4,
            "depot": 0,
            "time_windows": time_windows  
        }

        # Llamar a la función para resolver VRPTW
        #solution_output = solve_vrptw(data)
        solution_output = []

        print("Matriz de tiempos entre actividades:")
        for row in data["time_matrix"]:
            print(row)
        
        print("Ventanas de actividades:",data['time_windows'])
        
        return JsonResponse({"solution": solution_output}, status=200)

    return JsonResponse({"error": "Método no permitido"}, status=400)


def solve_vrptw(data):
    """Resuelve el problema de VRPTW utilizando OR-Tools."""
    manager = pywrapcp.RoutingIndexManager(
        len(data['time_matrix']), data['num_vehicles'], data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        """Retorna la distancia entre dos nodos."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Añadir restricciones de tiempo (ventanas de tiempo)
    time = "Time"
    routing.AddDimension(
        transit_callback_index,
        20,  # Permitir tiempo de espera (30 minutos)
        1000,  # Tiempo máximo para las rutas (5 horas)
        False,  # No permitir tiempos negativos
        time,
    )
    time_dimension = routing.GetDimensionOrDie(time)
    

    for location_idx, time_window in enumerate(data['time_windows']):
        if location_idx == data["depot"]:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    #Add time window constraints for each vehicle start node.
    depot_idx = data["depot"]
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            data["time_windows"][depot_idx][0], data["time_windows"][depot_idx][1]
        )

    for i in range(data["num_vehicles"]):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i))
        )
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(i)))


    # Solucionar el problema
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        return print_solution(data, manager, routing, solution)
    else:
        return "No se encontró solución."

def print_solution(data, manager, routing, solution):
    solution_output = []

    """Imprimir y devolver la solución."""
    print(f'Objective: {solution.ObjectiveValue()}')
    time_dimension = routing.GetDimensionOrDie("Time")
    total_time = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = f"Ruta para vehiculo {vehicle_id}:\n"
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += (
                f"{manager.IndexToNode(index)}"
                f" Time({solution.Min(time_var)},{solution.Max(time_var)})"
                " -> "
            )
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += (
            f"{manager.IndexToNode(index)}"
            f" Time({solution.Min(time_var)},{solution.Max(time_var)})\n"
        )
        plan_output += f"Time of the route: {solution.Min(time_var)}min\n"
        print(plan_output)
        total_time += solution.Min(time_var)
    print(f"Total time of all routes: {total_time}min")
    return solution_output