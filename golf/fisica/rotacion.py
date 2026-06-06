"""
rotacion.py
===========
Cálculos de rotación: momentos de inercia, energía rotacional,
rodadura pura y torques disipativo. Sin Pymunk.
"""

import math
from typing import List, Tuple


class MomentoInercia:
    """
    Calcula el momento de inercia (I) para las formas más habituales.
    Todos los resultados son respecto al centro de masa (CM) salvo
    que se indique lo contrario.

    Unidades: kg, m  →  I en kg·m²
    """

    # ------------------------------------------------------------------ #
    #  Formas sólidas                                                     #
    # ------------------------------------------------------------------ #
    @staticmethod
    def disco_solido(masa: float, radio: float) -> float:
        """I = ½ m r²  (disco o cilindro sólido, eje central)"""
        return 0.5 * masa * radio**2

    @staticmethod
    def esfera_solida(masa: float, radio: float) -> float:
        """I = 2/5 m r²  (esfera maciza)"""
        return (2.0 / 5.0) * masa * radio**2

    @staticmethod
    def esfera_hueca(masa: float, radio: float) -> float:
        """I = 2/3 m r²  (esfera hueca de pared delgada)"""
        return (2.0 / 3.0) * masa * radio**2

    @staticmethod
    def anillo(masa: float, radio: float) -> float:
        """I = m r²  (aro o tubo fino, eje central)"""
        return masa * radio**2

    @staticmethod
    def rectangulo(masa: float, ancho: float, alto: float) -> float:
        """I = 1/12 m (w² + h²)  (placa rectangular, eje por el CM)"""
        return (masa / 12.0) * (ancho**2 + alto**2)

    @staticmethod
    def cuadrado(masa: float, lado: float) -> float:
        """I = 1/6 m L²  (cuadrado sólido, eje por el CM)"""
        return (masa / 6.0) * lado**2

    @staticmethod
    def barra_cm(masa: float, longitud: float) -> float:
        """I = 1/12 m L²  (barra delgada, eje por el CM)"""
        return (masa / 12.0) * longitud**2

    @staticmethod
    def barra_extremo(masa: float, longitud: float) -> float:
        """I = 1/3 m L²  (barra delgada, eje por un extremo)"""
        return (masa / 3.0) * longitud**2

    # ------------------------------------------------------------------ #
    #  Teorema de Steiner (traslación de ejes)                           #
    # ------------------------------------------------------------------ #
    @staticmethod
    def steiner(I_cm: float, masa: float, d: float) -> float:
        """
        Traslada el eje de rotación una distancia d desde el CM.

        I_eje = I_cm + m · d²

        Parámetros
        ----------
        I_cm : momento de inercia respecto al CM [kg·m²]
        masa : masa del cuerpo [kg]
        d    : distancia entre el CM y el nuevo eje [m]
        """
        return I_cm + masa * d**2

    # ------------------------------------------------------------------ #
    #  Polígono arbitrario (método de triángulos firmados)               #
    # ------------------------------------------------------------------ #
    @staticmethod
    def poligono(masa: float, vertices: List[Tuple[float, float]]) -> float:
        """
        Momento de inercia de un polígono convexo respecto al origen (0,0).

        Si los vértices están centrados en el CM el resultado es I_cm.
        Si no, aplica el Teorema de Steiner para corregir.

        Parámetros
        ----------
        masa     : masa total [kg]
        vertices : lista de (x, y) en orden (horario o antihorario)
        """
        n   = len(vertices)
        num = 0.0
        den = 0.0
        for i in range(n):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % n]
            cross   = abs(x1 * y2 - x2 * y1)
            num    += cross * (x1**2 + x1*x2 + x2**2 + y1**2 + y1*y2 + y2**2)
            den    += cross
        if den == 0:
            return 0.0
        return (masa / 6.0) * (num / den)

    # ------------------------------------------------------------------ #
    #  Centro de masa de un polígono                                     #
    # ------------------------------------------------------------------ #
    @staticmethod
    def centroide_poligono(vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Devuelve el centroide (cx, cy) de un polígono."""
        n    = len(vertices)
        area = 0.0
        cx   = 0.0
        cy   = 0.0
        for i in range(n):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % n]
            a  = x1 * y2 - x2 * y1
            area += a
            cx   += (x1 + x2) * a
            cy   += (y1 + y2) * a
        area *= 0.5
        if abs(area) < 1e-12:
            return (0.0, 0.0)
        cx /= (6.0 * area)
        cy /= (6.0 * area)
        return (cx, cy)


class Rotacion:
    """
    Cálculos sobre el movimiento rotacional:
    energía, momento angular, rodadura pura y torque de rozamiento.
    """

    # ------------------------------------------------------------------ #
    #  Energías                                                           #
    # ------------------------------------------------------------------ #
    @staticmethod
    def energia_cinetica_rot(I: float, omega: float) -> float:
        """Ek_rot = ½ I ω²  [J]"""
        return 0.5 * I * omega**2

    @staticmethod
    def energia_cinetica_total(masa: float, v: float,
                               I: float, omega: float) -> float:
        """Ek_total = ½ m v² + ½ I ω²  [J]"""
        return 0.5 * masa * v**2 + 0.5 * I * omega**2

    # ------------------------------------------------------------------ #
    #  Momento angular                                                    #
    # ------------------------------------------------------------------ #
    @staticmethod
    def momento_angular_spin(I: float, omega: float) -> float:
        """L_spin = I · ω  [kg·m²/s]"""
        return I * omega

    @staticmethod
    def momento_angular_orbital(pos: Tuple[float, float],
                                p: Tuple[float, float]) -> float:
        """
        L_orbital = r × p  (producto vectorial en 2D, componente z).

        Parámetros
        ----------
        pos : (x, y) posición respecto al punto de referencia [m]
        p   : (px, py) momento lineal [kg·m/s]
        """
        return pos[0] * p[1] - pos[1] * p[0]

    # ------------------------------------------------------------------ #
    #  Rodadura pura                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def velocidad_rodadura(omega: float, radio: float) -> float:
        """
        Velocidad lineal del CM en rodadura pura (sin deslizamiento).

        v_cm = ω · R   [m/s]
        """
        return omega * radio

    @staticmethod
    def omega_rodadura(v_cm: float, radio: float) -> float:
        """
        Velocidad angular en rodadura pura.

        ω = v_cm / R   [rad/s]
        """
        if radio <= 0:
            raise ValueError("El radio debe ser positivo.")
        return v_cm / radio

    @staticmethod
    def tiempo_hasta_rodadura_pura(v0: float, omega0: float,
                                   radio: float, mu_k: float,
                                   g: float = 9.81) -> float:
        """
        Tiempo hasta alcanzar la rodadura pura partiendo de v0 y omega0.
        Válido para una esfera sobre superficie horizontal.

        t = (v0 - R·ω0) / ((mu_k·g) · (1 + m·R²/I))

        Para esfera sólida (I = 2/5 m R²):
            t = 2(v0 - R·ω0) / (7·mu_k·g)

        Parámetros
        ----------
        v0    : velocidad lineal inicial [m/s]
        omega0: velocidad angular inicial [rad/s]
        radio : radio de la esfera [m]
        mu_k  : coeficiente de rozamiento cinético
        g     : aceleración gravitatoria [m/s²]
        """
        v_contact = v0 - radio * omega0
        if abs(v_contact) < 1e-9:
            return 0.0
        # Esfera sólida: factor = 7/2
        return 2.0 * abs(v_contact) / (7.0 * mu_k * g)

    # ------------------------------------------------------------------ #
    #  Torques disipativos                                                #
    # ------------------------------------------------------------------ #
    @staticmethod
    def torque_rodadura(F_normal: float, radio: float,
                        Crr: float = 0.02) -> float:
        """
        Torque de resistencia a la rodadura (máximo disponible).

        τ_rod = Crr · F_N · R   [N·m]

        Parámetros
        ----------
        F_normal : fuerza normal sobre la rueda [N]
        radio    : radio [m]
        Crr      : coeficiente de resistencia a la rodadura
        """
        return Crr * F_normal * radio

    @staticmethod
    def torque_frenado_rotacional(omega: float, radio: float,
                                  rho: float = 1.225,
                                  Cm: float = 0.02) -> float:
        """
        Torque de resistencia aerodinámica a la rotación (Spin Decay).

        τ = -½ · ρ · ω² · R⁵ · Cm   [N·m]

        Parámetros
        ----------
        omega : velocidad angular [rad/s]
        radio : radio de la esfera [m]
        rho   : densidad del aire [kg/m³]
        Cm    : coeficiente de momento aerodinámico (≈0.02 genérico, 0.07 golf)
        """
        if abs(omega) < 0.01:
            return 0.0
        magnitud = 0.5 * rho * omega**2 * radio**5 * Cm
        return -math.copysign(magnitud, omega)

    # ------------------------------------------------------------------ #
    #  Aceleración angular y velocidad final                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def alpha_desde_torque(torque: float, I: float) -> float:
        """α = τ / I  [rad/s²]"""
        if I <= 0:
            raise ValueError("El momento de inercia debe ser positivo.")
        return torque / I

    @staticmethod
    def omega_final(omega0: float, alpha: float, t: float) -> float:
        """ω = ω₀ + α·t  [rad/s]"""
        return omega0 + alpha * t

    @staticmethod
    def angulo_girado(omega0: float, alpha: float, t: float) -> float:
        """θ = ω₀·t + ½·α·t²  [rad]"""
        return omega0 * t + 0.5 * alpha * t**2


# --------------------------------------------------------------------------- #
#  Bloque de prueba rápida                                                     #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    mi = MomentoInercia()
    r  = Rotacion()

    m, R = 10.0, 0.045   # bola de bolos 10 kg, radio 4.5 cm

    I_esfera = mi.esfera_solida(m, R)
    I_disco  = mi.disco_solido(m, R)

    print("=== MOMENTO DE INERCIA ===")
    print(f"Esfera sólida ({m} kg, R={R} m): {I_esfera:.6f} kg·m²")
    print(f"Disco sólido  ({m} kg, R={R} m): {I_disco:.6f} kg·m²")

    barra_cm = mi.barra_cm(1.0, 1.5)
    barra_ex = mi.barra_extremo(1.0, 1.5)
    print(f"Barra 1 kg 1.5 m (CM):    {barra_cm:.6f} kg·m²")
    print(f"Barra 1 kg 1.5 m (extr.): {barra_ex:.6f} kg·m²")

    print("\n=== ROTACIÓN ===")
    v0, w0 = 5.0, 0.0   # bola lanzada sin spin
    t_rod = r.tiempo_hasta_rodadura_pura(v0, w0, R, mu_k=0.25)
    print(f"Tiempo hasta rodadura pura: {t_rod:.4f} s")
    print(f"ω en rodadura pura: {r.omega_rodadura(v0, R):.2f} rad/s")
    print(f"Energía cinética total (v={v0}, ω=10): "
          f"{r.energia_cinetica_total(m, v0, I_esfera, 10):.2f} J")
