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
document.getElementById('submit-vrptw').addEventListener('click', function () {
    if (activities.length < 2) {
        alert("Por favor selecciona al menos dos actividades.");
        return;
    }

    var formData = new FormData();
    activities.forEach(function(activity) {
        formData.append('activities[]', activity);
    });

    fetch('/vrptw/', {
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        body: formData,
        mode: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        console.log("data:", data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
});