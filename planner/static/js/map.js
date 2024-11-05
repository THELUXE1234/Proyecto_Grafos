var map = L.map('map').setView([-33.45, -70.65], 12); // Santiago
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

let selectedMarker = null;
let selectedCoords = null;

// Mostrar detalles del lugar seleccionado
function showPlaceDetails(feature, latlng) {
    const detailsContent = document.getElementById('details-content');
    const addRemoveButton = document.getElementById('add-remove-activity');
    const coords = latlng.lat + "," + latlng.lng;

    if (feature) {
        detalles = feature.properties;
        tipo ="Ninguno"
        if(detalles.amenity){
            tipo = "Iglesia"
        }else if(detalles.tourism){
            tipo = "Museo"
        }else if(detalles.leisure){
            tipo = "Parque"
        }
        detailsContent.innerHTML = `<p><b>Nombre:</b> ${detalles.name ? detalles.name:"No definido"}<p><b>Tipo:</b> ${tipo}</p></p><p><b>Coordenadas:</b> ${coords}</p>`;
    } else {
        detailsContent.innerHTML = `<p>Lugar encontrado sin información</p><p><b>Coordenadas:</b> ${coords}</p>`;
    }

    // Mostrar el botón de agregar/eliminar
    addRemoveButton.style.display = 'block';

    if (activities.includes(coords)) {
        addRemoveButton.textContent = 'Eliminar de Actividades';
    } else {
        addRemoveButton.textContent = 'Agregar a Actividades';
    }

    // Actualizar la selección de coordenadas
    selectedCoords = coords;

    // Cambiar el marcador seleccionado a rojo
    if (selectedMarker) {
        map.removeLayer(selectedMarker);
    }
    selectedMarker = L.circleMarker(latlng, {
        radius: 10,
        fillColor: "red",
        color: "#000",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map);
}

// Lógica para agregar o eliminar actividad desde los detalles
document.getElementById('add-remove-activity').addEventListener('click', function () {
    if (activities.includes(selectedCoords)) {
        // Eliminar actividad
        const index = activities.indexOf(selectedCoords);
        if (index > -1) {
            activities.splice(index, 1);
        }
        this.textContent = 'Agregar a Actividades';
    } else {
        // Agregar actividad
        addActivity(selectedMarker.getLatLng().lat, selectedMarker.getLatLng().lng);
        this.textContent = 'Eliminar de Actividades';
    }
});


// Al hacer clic en el mapa, permitir confirmar la actividad
map.on('click', (event) => {
    let lat = event.latlng.lat;
    let lng = event.latlng.lng;
    showPlaceDetails(null,{lat,lng})
});


// Inicializar capas para los lugares turísticos
var touristLayers = {
    museums: L.layerGroup(),
    churches: L.layerGroup(),
    parks: L.layerGroup()
};

// Función para definir el estilo de los lugares turísticos
function getColorForPlace(placeType) {
    switch (placeType) {
        case 'museum':
            return 'blue';
        case 'place_of_worship':
            return 'green';
        case 'park':
            return 'orange';
        default:
            return 'gray';
    }
}

// Función para cargar y agregar las capas de lugares turísticos
function loadTouristPlaces() {
    fetch('/static/geojson/lugares_turisticos.geojson')
        .then(response => response.json())
        .then(data => {
            // Recorrer los elementos del GeoJSON
            data.features.forEach(function (feature) {
                var placeType = feature.properties.tourism || feature.properties.amenity || feature.properties.leisure;
                var color = getColorForPlace(placeType);

                var layer = L.geoJSON(feature, {
                    pointToLayer: function (feature, latlng) {
                        return L.circleMarker(latlng, {
                            radius: 10,
                            fillColor: color,
                            color: "#000",
                            weight: 1,
                            opacity: 1,
                            fillOpacity: 0.8
                        });
                    },
                    onEachFeature: function (feature, layer) {
                        layer.bindPopup(`<b>${feature.properties.name || 'No definido'}</b>`);
                        // Permitir agregar el lugar a la lista de actividades
                        layer.on('click', function () {
                            showPlaceDetails(feature, layer.getLatLng())
                        });
                    }
                });

                // Añadir a la capa correspondiente
                if (placeType === 'museum') {
                    touristLayers.museums.addLayer(layer);
                } else if (placeType === 'place_of_worship') {
                    touristLayers.churches.addLayer(layer);
                } else if (placeType === 'park') {
                    touristLayers.parks.addLayer(layer);
                }
            });
        })
        .catch(error => console.error('Error al cargar el GeoJSON:', error));
}

// Cargar lugares turísticos solo si el checkbox está seleccionado
document.getElementById('show-tourist-places').addEventListener('change', function () {
    if (this.checked) {
        // Marcar el checkbox de "Mostrar lugares turísticos" y cargar todas las capas
        map.addLayer(touristLayers.museums);
        map.addLayer(touristLayers.churches);
        map.addLayer(touristLayers.parks);
        document.getElementById('filter-museums').checked = true;
        document.getElementById('filter-churches').checked = true;
        document.getElementById('filter-parks').checked = true;
    } else {
        // Eliminar todas las capas si se desmarca "Mostrar lugares turísticos"
        map.removeLayer(touristLayers.museums);
        map.removeLayer(touristLayers.churches);
        map.removeLayer(touristLayers.parks);
        document.getElementById('filter-museums').checked = false;
        document.getElementById('filter-churches').checked = false;
        document.getElementById('filter-parks').checked = false;
    }
});

// Funciones para filtrar los lugares turísticos
document.getElementById('filter-museums').addEventListener('change', function () {
    if (this.checked) {
        touristLayers.museums.addTo(map);
    } else {
        map.removeLayer(touristLayers.museums);
    }
    updateTouristPlacesCheckbox();
});

document.getElementById('filter-churches').addEventListener('change', function () {
    if (this.checked) {
        touristLayers.churches.addTo(map);
    } else {
        map.removeLayer(touristLayers.churches);
    }
    updateTouristPlacesCheckbox();
});

document.getElementById('filter-parks').addEventListener('change', function () {
    if (this.checked) {
        touristLayers.parks.addTo(map);
    } else {
        map.removeLayer(touristLayers.parks);
    }
    updateTouristPlacesCheckbox();
});

// Función para verificar el estado de los checkboxes de filtros
function updateTouristPlacesCheckbox() {
    const museumsChecked = document.getElementById('filter-museums').checked;
    const churchesChecked = document.getElementById('filter-churches').checked;
    const parksChecked = document.getElementById('filter-parks').checked;

    if (museumsChecked && churchesChecked && parksChecked) {
        // Si todos los checkboxes están marcados, marcar "Mostrar lugares turísticos"
        document.getElementById('show-tourist-places').checked = true;
    } else {
        // Si algún checkbox no está marcado, desmarcar "Mostrar lugares turísticos"
        document.getElementById('show-tourist-places').checked = false;
    }
}

// Cargar los datos GeoJSON al iniciar
loadTouristPlaces();