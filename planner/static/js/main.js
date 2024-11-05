var activities = [];
var markers = [];
var selectedListItem = null; 

function addActivity(lat, lng) {
    const coords = lat + "," + lng;

    // Agregar la actividad al array
    activities.push(coords);
    const activityIndex = activities.length;
    // Añadir marcador al mapa
    const marker = L.marker([lat, lng]).addTo(map).bindPopup("Actividad confirmada").openPopup();
    markers.push(marker);

    // Añadir la actividad a la lista visual
    const activityList = document.getElementById('activity-list');
    const listItem = document.createElement('li');
    listItem.textContent = `Actividad ${activityIndex}: ${coords}`;
    listItem.setAttribute('data-coords', coords);


    // Añadir evento al hacer clic en el elemento de la lista
    listItem.addEventListener('click', function () {
        focusActivityOnMap(coords, lat, lng);
        selectListItem(listItem);
    });

    // Añadir botón para eliminar la actividad
    const deleteButton = document.createElement('button');
    deleteButton.textContent = 'Eliminar';
    deleteButton.style.marginLeft = '10px';
    deleteButton.onclick = () => {
        removeActivity(coords, listItem, marker);
    };

    listItem.appendChild(deleteButton);
    activityList.appendChild(listItem);
}

function removeActivity(coords, listItem, marker) {
    // Remover del array de actividades
    activities = activities.filter(activity => activity !== coords);

    // Remover el marcador del mapa
    map.removeLayer(marker);

    // Remover la actividad de la lista visual
    listItem.remove();
    updateActivityIndices();
}

function updateActivityIndices() {
    // Actualiza los índices de las actividades en la lista visual
    const activityListItems = document.querySelectorAll('#activity-list li');
    activityListItems.forEach((item, index) => {
        const coords = item.getAttribute('data-coords');
        item.firstChild.textContent = `Actividad ${index + 1}: ${coords}`;
    });
}

function focusActivityOnMap(coords, lat, lng) {
    map.setView([lat, lng], 12);  // Centrar el mapa en la coordenada de la actividad
    showPlaceDetails(null, { lat, lng });  // Mostrar los detalles de la actividad
}


// Función para resaltar la actividad seleccionada
function selectListItem(listItem) {
    // Si ya hay una actividad seleccionada, remover la clase 'selected'
    if (selectedListItem) {
        selectedListItem.classList.remove('selected');
    }
    console.log(selectedListItem);
    // Añadir la clase 'selected' al nuevo elemento seleccionado
    listItem.classList.add('selected');
    selectedListItem = listItem;  // Actualizar la referencia al nuevo elemento seleccionado
}