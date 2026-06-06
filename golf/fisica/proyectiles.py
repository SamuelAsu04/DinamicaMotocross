"""
proyectiles.py
==============
Cálculos de tiro parabólico: con y sin resistencia del aire,
con viento y correcciones de altitud. Sin Pymunk/Pygame.
"""

import math
from typing import List, Tuple, Optional


class TiroParabolico:
    """
    Tiro parabólico sin resistencia del aire (solución analítica exacta).

    Convenciones
    ------------
    - Eje Y positivo hacia arriba.
    - Ángulo en grados (se convierte internamente a radianes).
    - g positivo (≈ 9.81 m/s²).
    """

    def __init__(self, v0: float, angulo_deg: float,
                 x0: float = 0.0, y0: float = 0.0,
                 g: float = 9.81):
        """
        Parámetros
        ----------
        v0         : velocidad inicial [m/s]
        angulo_deg : ángulo de lanzamiento respecto a la horizontal [°]
        x0, y0     : posición inicial [m]
        g          : aceleración gravitatoria (positiva) [m/s²]
        """
        self.v0  = v0
        self.ang = math.radians(angulo_deg)
        self.x0  = x0
        self.y0  = y0
        self.g   = g
        self.vx0 = v0 * math.cos(self.ang)
        self.vy0 = v0 * math.sin(self.ang)

    # ------------------------------------------------------------------ #
    #  Resultados analíticos                                              #
    # ------------------------------------------------------------------ #
    @property
    def tiempo_vuelo(self) -> float:
        """
        Tiempo hasta volver a la altura de lanzamiento (y = y0).

        t_v = 2·vy0 / g
        """
        return 2.0 * self.vy0 / self.g

    @property
    def alcance(self) -> float:
        """
        Alcance horizontal cuando el proyectil vuelve a y = y0.

        R = v0²·sin(2θ) / g
        """
        return self.v0**2 * math.sin(2.0 * self.ang) / self.g

    @property
    def altura_maxima(self) -> float:
        """
        Altura máxima sobre y0.

        H = vy0² / (2·g)
        """
        return self.vy0**2 / (2.0 * self.g)

    @property
    def tiempo_apogeo(self) -> float:
        """Tiempo hasta alcanzar la altura máxima."""
        return self.vy0 / self.g

    # ------------------------------------------------------------------ #
    #  Posición y velocidad en t                                         #
    # ------------------------------------------------------------------ #
    def posicion(self, t: float) -> Tuple[float, float]:
        """(x, y) en el instante t [m]."""
        x = self.x0 + self.vx0 * t
        y = self.y0 + self.vy0 * t - 0.5 * self.g * t**2
        return x, y

    def velocidad(self, t: float) -> Tuple[float, float]:
        """(vx, vy) en el instante t [m/s]."""
        return self.vx0, self.vy0 - self.g * t

    def rapidez(self, t: float) -> float:
        """Módulo de la velocidad en t [m/s]."""
        vx, vy = self.velocidad(t)
        return math.hypot(vx, vy)

    # ------------------------------------------------------------------ #
    #  Ángulo óptimo y alcance máximo                                    #
    # ------------------------------------------------------------------ #
    @classmethod
    def angulo_optimo(cls, v0: float, g: float = 9.81) -> float:
        """
        Ángulo que maximiza el alcance (45° en terreno llano).

        Retorna el ángulo en grados.
        """
        return 45.0  # siempre 45° cuando y_inicio = y_final

    @classmethod
    def alcance_maximo(cls, v0: float, g: float = 9.81) -> float:
        """Alcance máximo a 45°."""
        return v0**2 / g

    # ------------------------------------------------------------------ #
    #  Trayectoria discreta                                               #
    # ------------------------------------------------------------------ #
    def trayectoria(self, dt: float = 0.05,
                    suelo_y: float = 0.0) -> List[Tuple[float, float]]:
        """
        Lista de (x, y) desde el lanzamiento hasta que y ≤ suelo_y.

        Parámetros
        ----------
        dt      : paso de tiempo [s]
        suelo_y : altura del suelo [m]
        """
        puntos = []
        t = 0.0
        while True:
            x, y = self.posicion(t)
            puntos.append((x, y))
            if y < suelo_y and t > 0.0:
                break
            t += dt
        return puntos


class ProyectilConArrastre:
    """
    Tiro parabólico con resistencia del aire mediante integración numérica
    (método de Euler o RK4).

    Modelo de Newton: F_drag = -½·ρ·Cd·A·v²  (dirección opuesta a v)

    Combina los efectos de:
    - Arrastre aerodinámico (Cd, área, densidad)
    - Viento (velocidad vectorial constante)
    - Gradiente de densidad con la altitud (modelo ISA simplificado)
    """

    RHO0 = 1.225      # densidad al nivel del mar [kg/m³]
    L    = 0.0065     # gradiente ISA [K/m]
    T0   = 288.15     # temperatura ISA nivel del mar [K]
    G_E  = 9.80665
    M_A  = 0.0289644
    R_G  = 8.31446

    def __init__(self, masa: float, area: float, Cd: float,
                 v0: float, angulo_deg: float,
                 x0: float = 0.0, y0: float = 0.0,
                 g: float = 9.81,
                 v_viento: Tuple[float, float] = (0.0, 0.0),
                 corr_altitud: bool = False):
        """
        Parámetros
        ----------
        masa       : masa del proyectil [kg]
        area       : sección transversal [m²]
        Cd         : coeficiente de arrastre (constante o función de Re)
        v0         : velocidad inicial [m/s]
        angulo_deg : ángulo de lanzamiento [°]
        x0, y0     : posición inicial [m]
        g          : gravedad [m/s²]
        v_viento   : velocidad del viento (vx, vy) [m/s]
        corr_altitud: si True, ajusta ρ con la altitud (modelo ISA)
        """
        self.masa        = masa
        self.area        = area
        self.Cd          = Cd
        self.g           = g
        self.v_viento    = v_viento
        self.corr_alt    = corr_altitud

        ang   = math.radians(angulo_deg)
        self.estado0 = [x0, y0, v0 * math.cos(ang), v0 * math.sin(ang)]

    # ------------------------------------------------------------------ #
    #  Densidad según altitud                                             #
    # ------------------------------------------------------------------ #
    def _rho(self, y: float) -> float:
        if not self.corr_alt:
            return self.RHO0
        alt = max(0.0, min(y, 11_000.0))
        T_loc = self.T0 - self.L * alt
        exp   = (self.G_E * self.M_A) / (self.R_G * self.L)
        return self.RHO0 * (T_loc / self.T0)**exp

    # ------------------------------------------------------------------ #
    #  Derivadas del estado [x, y, vx, vy]                              #
    # ------------------------------------------------------------------ #
    def _derivadas(self, estado: List[float]) -> List[float]:
        _, y, vx, vy = estado
        rho   = self._rho(y)

        vrel_x = vx - self.v_viento[0]
        vrel_y = vy - self.v_viento[1]
        v_mag  = math.hypot(vrel_x, vrel_y)

        if v_mag < 1e-9:
            ax, ay = 0.0, -self.g
        else:
            factor = -0.5 * rho * self.Cd * self.area / self.masa
            ax = factor * v_mag * vrel_x
            ay = -self.g + factor * v_mag * vrel_y

        return [vx, vy, ax, ay]

    # ------------------------------------------------------------------ #
    #  Integración numérica (RK4)                                        #
    # ------------------------------------------------------------------ #
    def simular(self, dt: float = 0.01,
                suelo_y: float = 0.0,
                t_max: float = 300.0) -> List[Tuple[float, float, float]]:
        """
        Simula la trayectoria con RK4.

        Retorna
        -------
        Lista de (t, x, y) desde t=0 hasta impacto en suelo_y.
        """
        estado = list(self.estado0)
        t      = 0.0
        puntos = [(t, estado[0], estado[1])]

        while t < t_max:
            x, y = estado[0], estado[1]
            if y < suelo_y and t > 0:
                break

            k1 = self._derivadas(estado)
            k2 = self._derivadas([estado[i] + 0.5*dt*k1[i] for i in range(4)])
            k3 = self._derivadas([estado[i] + 0.5*dt*k2[i] for i in range(4)])
            k4 = self._derivadas([estado[i] +     dt*k3[i] for i in range(4)])

            estado = [estado[i] + (dt/6.0)*(k1[i]+2*k2[i]+2*k3[i]+k4[i])
                      for i in range(4)]
            t += dt
            puntos.append((t, estado[0], estado[1]))

        return puntos

    # ------------------------------------------------------------------ #
    #  Resumen del impacto                                               #
    # ------------------------------------------------------------------ #
    def impacto(self, dt: float = 0.01,
                suelo_y: float = 0.0) -> dict:
        """
        Calcula datos del punto de impacto con el suelo.

        Retorna un diccionario con: t, x, y, vx, vy, v_mod, angulo_impacto
        """
        tray = self.simular(dt, suelo_y)
        if not tray:
            return {}
        t, x, y = tray[-1]

        # Reconstruir velocidad final
        estado = list(self.estado0)
        for _ in range(int(t / dt)):
            k1 = self._derivadas(estado)
            k2 = self._derivadas([estado[i] + 0.5*dt*k1[i] for i in range(4)])
            k3 = self._derivadas([estado[i] + 0.5*dt*k2[i] for i in range(4)])
            k4 = self._derivadas([estado[i] +     dt*k3[i] for i in range(4)])
            estado = [estado[i] + (dt/6.0)*(k1[i]+2*k2[i]+2*k3[i]+k4[i])
                      for i in range(4)]

        vx, vy   = estado[2], estado[3]
        v_mod    = math.hypot(vx, vy)
        ang_imp  = math.degrees(math.atan2(abs(vy), vx))

        return {
            "t_impacto":     t,
            "x_impacto":     x,
            "y_impacto":     y,
            "vx":            vx,
            "vy":            vy,
            "v_modulo":      v_mod,
            "angulo_impacto": ang_imp
        }

    # ------------------------------------------------------------------ #
    #  Altura máxima                                                      #
    # ------------------------------------------------------------------ #
    def altura_maxima(self, dt: float = 0.01) -> Tuple[float, float, float]:
        """
        Retorna (t, x, y_max) del punto de apogeo.
        """
        tray = self.simular(dt)
        t_max_val, x_max, y_max = max(tray, key=lambda p: p[2])
        return t_max_val, x_max, y_max


# --------------------------------------------------------------------------- #
#  Bloque de prueba rápida                                                     #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("=== TIRO PARABÓLICO (sin arrastre) ===")
    t = TiroParabolico(v0=50.0, angulo_deg=45.0)
    print(f"Alcance:          {t.alcance:.2f} m")
    print(f"Altura máxima:    {t.altura_maxima:.2f} m")
    print(f"Tiempo de vuelo:  {t.tiempo_vuelo:.2f} s")
    print(f"Posición en t=2s: {t.posicion(2.0)}")

    print("\n=== CON ARRASTRE (bomba B52) ===")
    # Bomba típica: 200 kg, área ≈ 0.04 m², Cd=0.5
    p = ProyectilConArrastre(
        masa=200.0, area=0.04, Cd=0.5,
        v0=150.0, angulo_deg=0.0,   # lanzada horizontalmente
        y0=3000.0,                   # desde 3000 m de altitud
        corr_altitud=True
    )
    tray = p.simular(dt=0.5, suelo_y=0.0)
    t_f, x_f, _ = tray[-1]
    print(f"Alcance horizontal: {x_f:.1f} m  en  t={t_f:.1f} s")

    print("\n=== PELOTA DE TENIS CON VIENTO ===")
    radio = 0.032
    area  = math.pi * radio**2
    pt    = ProyectilConArrastre(
        masa=0.058, area=area, Cd=0.55,
        v0=60.0, angulo_deg=5.0,
        v_viento=(-5.0, 0.0)   # viento de cara -5 m/s
    )
    datos = pt.impacto(dt=0.005)
    print(f"Alcance:     {datos['x_impacto']:.2f} m")
    print(f"Tiempo:      {datos['t_impacto']:.3f} s")
    print(f"Vel. impacto:{datos['v_modulo']:.2f} m/s")
