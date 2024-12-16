// Obtener el token requerido por Django para peticiones
const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;


//GET
/*
document.getElementById('search-address').addEventListener('click', function () {
    const address = document.getElementById('address-input').value;
    if (!address) {
        alert("Por favor ingresa una dirección.");
        return;
    }

    // Llamada a la vista de Django que hará la solicitud a la API de Google Geocoding
    fetch(`/buscar_direccion/?direccion=${encodeURIComponent(address)}`)
    .then(response => response.json())
    .then(data => {
        if (data.lat && data.lng) {
            const lat = data.lat;
            const lng = data.lng;

            // Agregar la dirección como actividad
            addActivity(lat, lng);
            L.marker([lat, lng]).addTo(map).bindPopup(`Dirección: ${data.direccion_formateada}`).openPopup();
            map.setView([lat, lng], 13); // Recentrar el mapa en la dirección encontrada
        } else {
            alert("No se pudo encontrar la dirección. Por favor intenta nuevamente.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
*/


// POST calcular tiempo ruta
document.getElementById('submit-activities').addEventListener('click', function () {
    if (activities.length < 2) {
        alert("Por favor selecciona al menos dos actividades.");
        return;
    }

    var formData = new FormData();
    activities.forEach(function(activity) {
        formData.append('activities[]', activity);
    });

    fetch('/calcular_tiempo_ruta_optima/', {
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        body: formData,
        mode: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.total_time) {
            alert(`Tiempo total estimado de viaje: ${data.total_time} minutos promedio`);
        } else {
            alert("Error al calcular la ruta");
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

//POST calcular VRPTW
document.getElementById('submit-cvrptw').addEventListener('click', function () {
    if (activities.length < 2 || timeWindows.length !== activities.length ||waitTimes.length !== activities.length) {
        alert("Por favor selecciona al menos dos actividades.");
        return;
    }

    var formData = new FormData();
    activities.forEach(function(activity) {
        formData.append('activities[]', activity);
    });
    timeWindows.forEach(function(timeWindow) {
        formData.append('time_windows[]', timeWindow);
    });
    waitTimes.forEach(waitTime => formData.append('wait_times[]', waitTime));
    fetch('/cvrptw/', {
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        body: formData,
        mode: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        console.log("Respuesta CVRPTW:", data);
        const { solution, geometries } = data;
        const vehiculesWeek = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes'];
        const routeColors = ['red', 'blue', 'green', 'orange', 'purple'];
        const routeLayers = {};
        const filterContainer = document.getElementById('route-filters');
        filterContainer.innerHTML = '';

        Object.values(routeLayers).forEach((layer) => {
            if (map.hasLayer(layer.group)) {
                map.removeLayer(layer.group);
            }
        });

        solution.forEach((route, vehicleId) => {
            const stops = route.stops;
            const color = routeColors[vehicleId % routeColors.length];
            const routeCoords = [];
            const routeNodes = [];
            const routeDetails = []; // Detalles de cada actividad (nodo y horarios)
        
            if (stops.length > 1) {
                for (let i = 0; i < stops.length - 1; i++) {
                    const fromNode = stops[i].node;
                    const toNode = stops[i + 1].node;
                    routeNodes.push(fromNode);
                    routeDetails.push({
                        node: fromNode,
                        arrival: stops[i].arrival_time,
                        departure: stops[i].departure_time
                    });
                    const segment = geometries[fromNode][toNode];
                    if (segment) {
                        routeCoords.push(...segment.coordinates);
                    }
                }
        
                // Última actividad al nodo inicial
                const lastNode = stops[stops.length - 1].node;
                routeNodes.push(lastNode, 0);
                if (lastNode !== 0) {
                    routeNodes.push(0); // Agregar el nodo inicial solo si no es ya el último nodo
                }
                routeDetails.push({
                    node: lastNode,
                    arrival: stops[stops.length - 1].arrival_time,
                    departure: stops[stops.length - 1].departure_time
                });
        
                // Agregar la vuelta al nodo inicial en los detalles
                // routeDetails.push({
                //     node: 0, // Nodo inicial
                //     arrival: stops[stops.length - 1].departure_time, // Tiempo de salida del último nodo
                //     departure: null, // Sin hora de salida, ya que es el final del recorrido
                // });
        
                const returnSegment = geometries[lastNode][0];
                if (returnSegment) {
                    routeCoords.push(...returnSegment.coordinates);
                }
            }
        
            const latLngCoords = routeCoords.map((coord) => [coord[1], coord[0]]);
            const routeLine = L.polyline(latLngCoords, { color: color, weight: 4 });
            const routeDecorator = L.polylineDecorator(routeLine, {
                patterns: [
                    {
                        offset: 25,
                        repeat: 50,
                        symbol: L.Symbol.arrowHead({
                            pixelSize: 12,
                            pathOptions: { fillOpacity: 1, weight: 0, color: color },
                        }),
                    },
                ],
            });
            const routeGroup = L.layerGroup([routeLine, routeDecorator]).addTo(map);
        
            stops.forEach((stop) => {
                const { node, arrival_time, departure_time } = stop;
                const [lat, lng] = activities[node].split(',');
                L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: 'stop-marker',
                        html: `<div style="background-color:${color}; border-radius:50%; width:20px; height:20px;"></div>`,
                    }),
                })
                    .bindPopup(
                        `Vehículo: ${vehicleId + 1}<br>Stop: ${node}<br>Arrival: ${arrival_time}<br>Departure: ${departure_time}`
                    )
                    .addTo(routeGroup);
            });
        
            routeLayers[`vehicle-${vehicleId}`] = { group: routeGroup };
        
            const filterButton = document.createElement('button');
            filterButton.textContent = `Ver ruta ${vehiculesWeek[vehicleId]} (vehículo ${vehicleId + 1})`;
            filterButton.style.backgroundColor = color;
            filterButton.style.color = 'white';
            filterButton.style.margin = '5px';
        
            const infoContainer = document.createElement('div');
            infoContainer.style.margin = '10px 0';
            infoContainer.style.padding = '5px';
            infoContainer.style.border = '1px solid #ccc';
            infoContainer.style.backgroundColor = '#f9f9f9';
        
            const routeTime = document.createElement('p');
            const routeActivities = document.createElement('p');
            const detailedSchedule = document.createElement('ul');
            routeTime.textContent = `Tiempo total: ${(route.total_time / 60).toFixed(2)} horas`;
            routeActivities.textContent = `Actividades: ${routeNodes.join(' -> ')}`;
        
            routeDetails.forEach((detail) => {
                console.log(detail);
                const scheduleItem = document.createElement('li');
                scheduleItem.textContent = `Nodo ${detail.node}: Llega a ${convertMinutesToTime(
                    detail.arrival
                )}${detail.departure ? ` - Sale a ${convertMinutesToTime(detail.departure)}` : ''}`;
                detailedSchedule.appendChild(scheduleItem);
            });
        
            infoContainer.appendChild(routeTime);
            infoContainer.appendChild(routeActivities);
            infoContainer.appendChild(detailedSchedule);
        
            filterButton.addEventListener('click', () => {
                if (map.hasLayer(routeGroup)) {
                    map.removeLayer(routeGroup);
                    filterButton.textContent = `Mostrar ruta vehículo ${vehicleId + 1}`;
                    infoContainer.style.display = 'none';
                } else {
                    routeGroup.addTo(map);
                    filterButton.textContent = `Ocultar ruta vehículo ${vehicleId + 1}`;
                    infoContainer.style.display = 'block';
                }
            });
        
            filterContainer.appendChild(filterButton);
            filterContainer.appendChild(infoContainer);
        });
        
    })
    .catch(error => {
        console.error('Error:', error);
    });
});


// Función para convertir minutos en formato "HH:MM"
function convertMinutesToTime(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}