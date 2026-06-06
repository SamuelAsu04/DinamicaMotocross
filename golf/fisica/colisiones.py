"""
colisiones.py
=============
Cálculos de colisiones en 1D y 2D: conservación del momento,
coeficiente de restitución, impulso y colisión con rotación.
Sin Pymunk/Pygame.
"""

import math
from typing import Tuple


class Colision:
    """
    Resuelve colisiones entre dos cuerpos.

    Convenciones
    ------------
    - Masas en kg, velocidades en m/s.
    - En 2D las velocidades son tuplas (vx, vy).
    - e = coeficiente de restitución (0 = perfectamente inelástica,
                                      1 = perfectamente elástica).
    """

    # ------------------------------------------------------------------ #
    #  Colisión 1D                                                        #
    # ------------------------------------------------------------------ #
    @staticmethod
    def colision_1D(m1: float, v1: float,
                    m2: float, v2: float,
                    e: float = 1.0) -> Tuple[float, float]:
        """
        Velocidades post-colisión en una dimensión.

        Parámetros
        ----------
        m1, m2 : masas [kg]
        v1, v2 : velocidades iniciales [m/s]
        e      : coeficiente de restitución [0,1]

        Retorna
        -------
        (v1f, v2f) : velocidades finales [m/s]
        """
        M = m1 + m2
        v1f = (m1 * v1 + m2 * v2 + m2 * e * (v2 - v1)) / M
        v2f = (m1 * v1 + m2 * v2 + m1 * e * (v1 - v2)) / M
        return v1f, v2f

    @staticmethod
    def colision_pared_1D(v: float, e: float = 1.0) -> float:
        """
        Velocidad post-colisión contra una pared fija.

        v_f = -e · v
        """
        return -e * v

    # ------------------------------------------------------------------ #
    #  Colisión 2D (línea de acción normal n̂)                           #
    # ------------------------------------------------------------------ #
    @staticmethod
    def colision_2D(m1: float, v1: Tuple[float, float],
                    m2: float, v2: Tuple[float, float],
                    n: Tuple[float, float],
                    e: float = 1.0) -> Tuple[Tuple[float, float],
                                              Tuple[float, float]]:
        """
        Colisión 2D entre dos esferas (sin rotación).

        El intercambio de momento sólo ocurre a lo largo de la línea de
        acción (vector normal al punto de contacto).

        Parámetros
        ----------
        m1, m2 : masas [kg]
        v1, v2 : velocidades (vx, vy) [m/s]
        n      : vector unitario de la línea de acción (de 2 a 1) [adim]
        e      : coeficiente de restitución

        Retorna
        -------
        (v1f, v2f) : tuplas (vx, vy) con las velocidades finales [m/s]
        """
        # Normalizar n
        n_mag = math.hypot(n[0], n[1])
        if n_mag < 1e-12:
            return v1, v2
        nx, ny = n[0] / n_mag, n[1] / n_mag

        # Proyección de velocidades relativas sobre n
        dv_x = v1[0] - v2[0]
        dv_y = v1[1] - v2[1]
        dv_n = dv_x * nx + dv_y * ny  # componente normal de la vel. relativa

        if dv_n <= 0:        # se alejan: no hay colisión real
            return v1, v2

        # Impulso escalar
        J = -(1.0 + e) * dv_n / (1.0 / m1 + 1.0 / m2)

        v1f = (v1[0] + J * nx / m1, v1[1] + J * ny / m1)
        v2f = (v2[0] - J * nx / m2, v2[1] - J * ny / m2)
        return v1f, v2f

    # ------------------------------------------------------------------ #
    #  Colisión con rotación (billar / taco)                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def colision_con_rotacion(m1: float, v1: Tuple[float, float],
                               I1: float, omega1: float,
                               m2: float, v2: Tuple[float, float],
                               I2: float, omega2: float,
                               n: Tuple[float, float],
                               r1: Tuple[float, float],
                               r2: Tuple[float, float],
                               e: float = 1.0,
                               mu_t: float = 0.0
                               ) -> Tuple[Tuple[float, float], float,
                                          Tuple[float, float], float]:
        """
        Colisión 2D con transferencia de momento lineal Y angular.

        Basado en el modelo de impulso generalizado usado en billar.py.

        Parámetros
        ----------
        m1, m2  : masas [kg]
        v1, v2  : velocidades (vx, vy) [m/s]
        I1, I2  : momentos de inercia [kg·m²]
        omega1/2: velocidades angulares [rad/s]
        n       : vector unitario normal al contacto (de 2 hacia 1)
        r1, r2  : vector del CM al punto de contacto para cada cuerpo [m]
        e       : coeficiente de restitución normal
        mu_t    : coeficiente de fricción tangencial (0 = sin fricción)

        Retorna
        -------
        (v1f, omega1f, v2f, omega2f)
        """
        # Normalizar n
        n_mag = math.hypot(n[0], n[1])
        if n_mag < 1e-12:
            return v1, omega1, v2, omega2
        nx, ny = n[0] / n_mag, n[1] / n_mag

        # Velocidad del punto de contacto de cada cuerpo
        #  v_contact = v_cm + ω × r   (en 2D: ω × r = (-ω·ry, ω·rx))
        vc1_x = v1[0] + (-omega1 * r1[1])
        vc1_y = v1[1] + ( omega1 * r1[0])
        vc2_x = v2[0] + (-omega2 * r2[1])
        vc2_y = v2[1] + ( omega2 * r2[0])

        # Velocidad relativa en el punto de contacto
        vrel_x = vc1_x - vc2_x
        vrel_y = vc1_y - vc2_y

        # Componente normal
        vrel_n = vrel_x * nx + vrel_y * ny

        # Denominador del impulso normal
        r1_x_n = r1[0] * ny - r1[1] * nx   # r1 × n (escalar z)
        r2_x_n = r2[0] * ny - r2[1] * nx   # r2 × n

        denom_n = (1.0/m1 + 1.0/m2
                   + r1_x_n**2 / I1 + r2_x_n**2 / I2)

        Jn = -(1.0 + e) * vrel_n / denom_n

        # Dirección tangencial
        tx, ty = -ny, nx   # perpendicular a n

        # Componente tangencial
        vrel_t = vrel_x * tx + vrel_y * ty

        r1_x_t = r1[0] * ty - r1[1] * tx
        r2_x_t = r2[0] * ty - r2[1] * tx
        denom_t = (1.0/m1 + 1.0/m2
                   + r1_x_t**2 / I1 + r2_x_t**2 / I2)

        Jt_max = -vrel_t / denom_t
        Jt     = max(-abs(mu_t * Jn), min(abs(mu_t * Jn), Jt_max))

        # Impulso total
        Jx = Jn * nx + Jt * tx
        Jy = Jn * ny + Jt * ty

        v1f    = (v1[0] + Jx / m1, v1[1] + Jy / m1)
        omega1f = omega1 + (r1[0] * Jy - r1[1] * Jx) / I1

        v2f    = (v2[0] - Jx / m2, v2[1] - Jy / m2)
        omega2f = omega2 - (r2[0] * Jy - r2[1] * Jx) / I2

        return v1f, omega1f, v2f, omega2f

    # ------------------------------------------------------------------ #
    #  Grandezas conservadas                                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def momento_lineal(masa: float, v: Tuple[float, float]) -> Tuple[float, float]:
        """p = m · v  [kg·m/s]"""
        return (masa * v[0], masa * v[1])

    @staticmethod
    def energia_cinetica(masa: float, v: Tuple[float, float],
                         I: float = 0.0, omega: float = 0.0) -> float:
        """Ek = ½ m v² + ½ I ω²  [J]"""
        v_mag2 = v[0]**2 + v[1]**2
        return 0.5 * masa * v_mag2 + 0.5 * I * omega**2

    @staticmethod
    def perdida_energia(Ek_antes: float, Ek_despues: float) -> float:
        """Energía disipada en la colisión [J]"""
        return Ek_antes - Ek_despues

    @staticmethod
    def coef_restitucion_medido(v1_rel_antes: float,
                                v1_rel_despues: float) -> float:
        """
        Calcula e experimentalmente.

        e = |v_rel_después| / |v_rel_antes|
        """
        if abs(v1_rel_antes) < 1e-12:
            return 0.0
        return abs(v1_rel_despues) / abs(v1_rel_antes)

    # ------------------------------------------------------------------ #
    #  Impulso en taco-bola (billar)                                     #
    # ------------------------------------------------------------------ #
    @staticmethod
    def impulso_taco_bola(v_taco: Tuple[float, float], m_taco: float,
                           v_bola: Tuple[float, float], m_bola: float,
                           I_bola: float, radio_bola: float,
                           n: Tuple[float, float],
                           r_contacto: Tuple[float, float],
                           e: float = 0.75) -> Tuple[float, float]:
        """
        Calcula el impulso lineal que el taco aplica a la bola en el
        punto de contacto, y el impulso angular derivado.

        Retorna
        -------
        (J_lineal, J_angular) en [N·s] y [N·m·s]
        """
        n_mag = math.hypot(n[0], n[1])
        if n_mag < 1e-12:
            return (0.0, 0.0)
        nx, ny = n[0]/n_mag, n[1]/n_mag

        dv_x = v_taco[0] - v_bola[0]
        dv_y = v_taco[1] - v_bola[1]
        dv_n = dv_x*nx + dv_y*ny

        if dv_n <= 0:
            return (0.0, 0.0)

        rx, ry = r_contacto
        r_cross_n = rx*ny - ry*nx

        denom = 1.0/m_taco + 1.0/m_bola + r_cross_n**2 / I_bola
        Jn    = -(1.0 + e) * dv_n / denom

        J_angular = (rx * Jn*ny - ry * Jn*nx)
        return (Jn, J_angular)


# --------------------------------------------------------------------------- #
#  Bloque de prueba rápida                                                     #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    c = Colision()

    print("=== COLISIÓN 1D ===")
    v1f, v2f = c.colision_1D(1.0, 4.0, 1.0, 0.0, e=1.0)
    print(f"Elástica (iguales): v1f={v1f:.2f}, v2f={v2f:.2f}  (esperado 0, 4)")

    v1f, v2f = c.colision_1D(2.0, 3.0, 1.0, 0.0, e=0.0)
    print(f"Perfectamente inelástica 2kg+1kg: v1f={v1f:.4f}, v2f={v2f:.4f}  (esperado 2, 2)")

    print("\n=== COLISIÓN 2D ===")
    v1f, v2f = c.colision_2D(1.0, (4.0, 0.0),
                              1.0, (0.0, 0.0),
                              n=(1.0, 0.0), e=1.0)
    print(f"Elástica frontal: v1f={v1f}, v2f={v2f}  (esperado (0,0),(4,0))")

    v1f, v2f = c.colision_2D(1.0, (4.0, 0.0),
                              1.0, (0.0, 0.0),
                              n=(0.707, 0.707), e=1.0)
    print(f"Elástica oblicua 45°: v1f=({v1f[0]:.3f},{v1f[1]:.3f})")

    print("\n=== ENERGÍA ===")
    Ek1 = c.energia_cinetica(1.0, (4.0, 0.0))
    Ek2 = c.energia_cinetica(1.0, (0.0, 0.0))
    print(f"Energía inicial: {Ek1+Ek2:.2f} J")
