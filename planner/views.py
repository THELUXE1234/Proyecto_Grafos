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
    routes_geometry = []
    for i in range(len(activities)):
        matrix_row = []
        geometry_row = []
        for j in range(len(activities)):
            coord1 = activities[i].split(',')
            coord2 = activities[j].split(',')
            print("calculando tiempo ",f"actividad {i} ->",f"actividad {j}")
            url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}?geometries=geojson&overview=full"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                travel_time = data['routes'][0]['duration'] /60 
                geometry = data['routes'][0]['geometry']
                #print("tiempo:", travel_time)
                matrix_row.append(int(round(travel_time, 2)))
                geometry_row.append(geometry)
            else:
                print("Error al calcular el tiempo entre las actividades")
        matrix.append(matrix_row)
        routes_geometry.append(geometry_row)
    
    return matrix, routes_geometry


def CVRPTW(request):
    if request.method == 'POST':
        activities = request.POST.getlist('activities[]')
        time_windows_req = request.POST.getlist('time_windows[]')
        wait_times_req = request.POST.getlist('wait_times[]')
        print("Actividades recibidas:", activities)
        print("Ventanas de tiempo:", time_windows_req)
        print("Tiempos de espera actividades:", wait_times_req)

        # Creación de la matriz de distancia usando OSRM
        time_matrix, routes_geometry = create_matrix(activities)
        
        # Simulación de ventanas de tiempo (tiempos en minutos)
        #time_windows = generate_time_windows(len(activities))

        # Convertir ventanas de tiempo en formato (inicio, fin)
        time_windows = [tuple(map(int, tw.split(','))) for tw in time_windows_req]

        # Convertir tiempos de espera a enteros
        wait_times = list(map(int, wait_times_req))

        # Calcular demandas y capacidades
        demands = [1] * len(activities)
        demands[0] = 0
        # Ajustar capacidades dinámicamente
        total_activities = len(activities) - 1  # Excluyendo el depósito
        base_capacity = total_activities // 5
        extra_capacity = total_activities % 5

        vehicle_capacities = [base_capacity] * 5
        for i in range(extra_capacity):
            vehicle_capacities[i] += 1  # Distribuir actividades sobrantes

        print("Capacidades de los vehículos:", vehicle_capacities)

        # Definición del problema VRPTW con las ventanas de tiempo
        data = {
            "time_matrix": time_matrix,
            "time_windows": time_windows,
            "wait_times": wait_times,
            "num_vehicles": 5,
            "depot": 0,
            'vehicle_capacities': vehicle_capacities,
            'demands': demands,
        }

        # Llamar a la función para resolver VRPTW
        solution_output = solve_cvrptw(data)
        #solution_output = data

        print("Matriz de tiempos entre actividades:")
        for row in data["time_matrix"]:
            print(row)
        
        print("Ventanas de actividades:",data['time_windows'])
        
        return JsonResponse({
            "solution": solution_output, 
            "geometries": routes_geometry
        }, status=200)

    return JsonResponse({"error": "Método no permitido"}, status=400)


def solve_cvrptw(data):
    """Resuelve el problema CVRPTW utilizando OR-Tools."""
    manager = pywrapcp.RoutingIndexManager(
        len(data['time_matrix']), data['num_vehicles'], data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)

    # Definir la función de costo
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        travel_time = data['time_matrix'][from_node][to_node]
        wait_time = data['wait_times'][from_node]  # Añadir tiempo de espera del nodo actual
        return travel_time + wait_time

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Añadir restricciones de capacidad
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # No slack
        data['vehicle_capacities'],
        True,  # Cumul starts at zero
        'Capacity'
    )

    # Añadir restricciones de ventanas de tiempo
    time = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30,  # Tiempo de espera permitido
        1440,  # Tiempo máximo por vehículo (1 día)
        False,  # No forzar inicio en 0
        time
    )
    time_dimension = routing.GetDimensionOrDie(time)

    for location_idx, time_window in enumerate(data['time_windows']):
        if location_idx == 0:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    for vehicle_id in range(data['num_vehicles']):
        start_index = routing.Start(vehicle_id)
        time_dimension.CumulVar(start_index).SetRange(
            data['time_windows'][data['depot']][0], data['time_windows'][data['depot']][1]
        )

    # Minimizar tiempos de espera en nodos
    for i in range(len(data['time_matrix'])):
        wait_time = data['wait_times'][i]
        if wait_time > 0:
            index = manager.NodeToIndex(i)
            time_dimension.SlackVar(index).SetValue(wait_time)


     # Instantiate route start and end times to produce feasible times.
    for i in range(data['num_vehicles']):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i)))
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i)))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.time_limit.seconds = 10
    
    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)
        return extract_solution(data, manager, routing, solution)
    else:
        return {"Error", "No se encontro solución"}

def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    total_distance = 0
    total_load = 0
    time_dimension = routing.GetDimensionOrDie('Time')
    total_time = 0
    
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            route_load += data['demands'][node_index]
            plan_output += 'Place {0:>2} Arrive at {2:>2}min Depart at {3:>2}min (Load {1:>2})\n'.format(manager.IndexToNode(index), route_load, solution.Min(time_var), solution.Max(time_var))
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            
            
        time_var = time_dimension.CumulVar(index)
        total_time += solution.Min(time_var)
        plan_output +="Place {0:>2} Arrive at {2:>2}min \n\n".format(manager.IndexToNode(index), route_load, solution.Min(time_var), solution.Max(time_var))
        
        # route output
        plan_output += 'Load of the route: {}\n'.format(route_load)
        plan_output += 'Time of the route: {}min\n'.format(solution.Min(time_var))
        plan_output += "--------------------"
        
        print(plan_output)
        total_load += route_load

    print('Total load of all routes: {}'.format(total_load))
    print('Total time of all routes: {}min'.format(total_time))


def extract_solution(data, manager, routing, solution):
    """Transforma la solución en un formato serializable."""
    routes = []
    time_dimension = routing.GetDimensionOrDie('Time')

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route = {
            "vehicle_id": vehicle_id,
            "stops": [],
            "total_time": 0
        }

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            arrival_time = solution.Min(time_var)
            departure_time = arrival_time + data['wait_times'][node_index]
            route["stops"].append({
                "node": node_index,
                "arrival_time": arrival_time,
                "departure_time": departure_time,
            })
            index = solution.Value(routing.NextVar(index))

        # Añadir la llegada desde el último nodo hacia el nodo inicial
        if route["stops"][-1]["node"] != data["depot"]:
            last_node = route["stops"][-1]["node"]
            depot_index = data["depot"]
            return_time = data["time_matrix"][last_node][depot_index]
            return_arrival_time = route["stops"][-1]["departure_time"] + return_time
            route["stops"].append({
                "node": depot_index,
                "arrival_time": return_arrival_time,
                "departure_time": None,  # Sin hora de salida
            })

        # Calcular el tiempo total de la ruta
        route["total_time"] = route["stops"][-1]["arrival_time"]
        routes.append(route)

    return routes