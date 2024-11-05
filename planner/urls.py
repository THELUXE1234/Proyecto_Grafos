from django.urls import path
from .views import home, calcular_tiempo_ruta_optima, buscar_direccion, obtener_lugares_turisticos,VRPTW


urlpatterns = [
    path('home/', home, name='home'),
    path('calcular_tiempo_ruta_optima/', calcular_tiempo_ruta_optima, name='calcular_tiempo_ruta_optima'),
    path('buscar_direccion/', buscar_direccion, name='buscar_direccion'),
    path('obtener_lugares_turisticos/',obtener_lugares_turisticos, name='obtener_lugares_turisticos'),
    path('vrptw/',VRPTW, name='vrptw'),
]