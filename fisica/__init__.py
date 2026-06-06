"""
fisica/
=======
Módulo de cálculos físicos puros (sin Pymunk/Pygame).
Basado en los ejemplos de simulación del proyecto.

Clases disponibles
------------------
Aerodinamica      → Reynolds, Cd, densidad ISA, Mach, drag, Magnus
MomentoInercia    → I para disco, esfera, barra, rectángulo, polígono, Steiner
Rotacion          → energía rot., momento angular, rodadura, torques
Colision          → colisiones 1D/2D, con rotación, impulso taco-bola
MuelleMasa        → frecuencia, periodo, amortiguación, posición(t)
Pendulo           → periodo lineal/exacto, velocidad máxima, energía
OsciladorAmortiguado → parámetros generales de amortiguación
TiroParabolico    → solución analítica exacta
ProyectilConArrastre → integración RK4 con drag, viento y altitud

Uso rápido
----------
    from fisica import Aerodinamica, Colision, TiroParabolico
"""

from .aerodinamica  import Aerodinamica
from .rotacion      import MomentoInercia, Rotacion
from .colisiones    import Colision
from .oscilaciones  import MuelleMasa, Pendulo, OsciladorAmortiguado
from .proyectiles   import TiroParabolico, ProyectilConArrastre

__all__ = [
    "Aerodinamica",
    "MomentoInercia",
    "Rotacion",
    "Colision",
    "MuelleMasa",
    "Pendulo",
    "OsciladorAmortiguado",
    "TiroParabolico",
    "ProyectilConArrastre",
]
