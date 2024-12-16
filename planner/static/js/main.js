var activities = [];
var markers = [];
var timeWindows = [];
var waitTimes = [];
var selectedListItem = null; 

// Función para convertir horas a minutos
function convertToMinutes(time) {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
}
function minutesToTime(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

function addActivity(lat, lng) {
    const coords = lat + "," + lng;
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;
    const waitTime = document.getElementById('wait-time').value;

    if (!startTime || !endTime) {
        alert("Debes ingresar las ventanas de tiempo para la actividad.");
        return;
    }

    // Convertir horas (HH:MM) a minutos
    const startMinutes = convertToMinutes(startTime);
    const endMinutes = convertToMinutes(endTime);

    if (startMinutes >= endMinutes) {
        alert("La hora de inicio debe ser anterior a la hora de fin.");
        return;
    }


    // Agregar la actividad y la ventana de tiempo
    activities.push(coords);
    timeWindows.push(`${startMinutes},${endMinutes}`);
    waitTimes.push(waitTime);
    const activityIndex = activities.length;

    // Añadir marcador al mapa
    const marker = L.marker([lat, lng]).addTo(map).bindPopup(`Actividad ${activityIndex-1} Confirmada`).openPopup();
    markers.push(marker);

    // Añadir la actividad a la lista visual
    const activityList = document.getElementById('activity-list');
    const listItem = document.createElement('li');
    listItem.textContent = `Actividad ${activityIndex-1}: ${coords} (Ventana: ${startTime} - ${endTime}) espera de ${waitTime}`;
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
        removeActivity(coords, listItem, marker, activityIndex - 1);
    };

    listItem.appendChild(deleteButton);
    activityList.appendChild(listItem);
    console.log("Actividades: ",activities);
    console.log("timeWindows: ",timeWindows);
    console.log("selectedListItem", selectedListItem);
}

function removeActivity(coords, listItem, marker) {
    // Encontrar el índice de la actividad a eliminar
    const index = activities.indexOf(coords);

    if (index !== -1) {
        // Remover del array de actividades y ventanas de tiempo
        activities.splice(index, 1);
        timeWindows.splice(index, 1);
    }

    // Remover el marcador del mapa
    map.removeLayer(marker);

    // Remover la actividad de la lista visual
    listItem.remove();

    // Actualizar los índices visuales y datos
    updateActivityIndices();

    console.log("Actividades: ", activities);
    console.log("timeWindows: ", timeWindows);
    console.log("selectedListItem", selectedListItem);
}

function updateActivityIndices() {
    // Actualiza los índices de las actividades en la lista visual
    const activityListItems = document.querySelectorAll('#activity-list li');
    activityListItems.forEach((item, index) => {
        const coords = activities[index];
        const timeWindow = timeWindows[index].split(',').map(minutesToTime).join(' - ');

        if (coords && timeWindow) {
            item.firstChild.textContent = `Actividad ${index + 1}: ${coords} (Ventana: ${timeWindow})`;
        }
    });
}

function focusActivityOnMap(coords, lat, lng) {
    map.setView([lat, lng], 12);  // Centrar el mapa en la coordenada de la actividad
    showPlaceDetails(null, { lat, lng });  // Mostrar los detalles de la actividad
}


document.getElementById('get-location').addEventListener('click', function () {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                const userLat = position.coords.latitude;
                const userLng = position.coords.longitude;

                // Centrar el mapa en la ubicación del usuario
                map.setView([userLat, userLng], 13);
                L.marker([userLat, userLng]).addTo(map).bindPopup("Ubicación inicial").openPopup();

                // Guardar la ubicación como actividad inicial
                activities[0] = `${userLat},${userLng}`;
                timeWindows[0] = '540,540';
                waitTimes[0] = 10;
                alert("Ubicación inicial establecida.");
            },
            function (error) {
                alert("No se pudo obtener la ubicación. Por favor, ingresa una dirección manualmente.");
                console.error(error);
            }
        );
    } else {
        alert("La geolocalización no es soportada por este navegador.");
    }
});


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