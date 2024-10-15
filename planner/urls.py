from django.urls import path
from .views import home, calcular_tiempo_ruta_optima, buscar_direccion


urlpatterns = [
    path('home/', home, name='home'),
    path('calcular_tiempo_ruta_optima/', calcular_tiempo_ruta_optima, name='calcular_tiempo_ruta_optima'),
    path('buscar_direccion/', buscar_direccion, name='buscar_direccion'),
]