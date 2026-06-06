"""
oscilaciones.py
===============
Cálculos de sistemas oscilatorios: muelle-masa, péndulo simple y doble,
amortiguación y frecuencias naturales. Sin Pymunk/Pygame.
"""

import math
from typing import Optional


class MuelleMasa:
    """
    Sistema masa-muelle con amortiguación viscosa.

    Ecuación de movimiento: m·x'' + b·x' + k·x = F_ext

    Convenciones
    ------------
    - masa  [kg]
    - k     [N/m]  rigidez (stiffness)
    - b     [N·s/m] amortiguamiento
    - t     [s]
    - x     [m]
    """

    def __init__(self, masa: float, k: float, b: float = 0.0):
        """
        Parámetros
        ----------
        masa : masa del objeto [kg]
        k    : constante del muelle [N/m]
        b    : coeficiente de amortiguamiento viscoso [N·s/m]
        """
        if masa <= 0 or k <= 0:
            raise ValueError("masa y k deben ser positivos.")
        self.masa = masa
        self.k    = k
        self.b    = b

    # ------------------------------------------------------------------ #
    #  Frecuencias y período                                              #
    # ------------------------------------------------------------------ #
    @property
    def omega_natural(self) -> float:
        """ω₀ = √(k/m)  [rad/s]"""
        return math.sqrt(self.k / self.masa)

    @property
    def frecuencia_natural(self) -> float:
        """f₀ = ω₀ / (2π)  [Hz]"""
        return self.omega_natural / (2.0 * math.pi)

    @property
    def periodo_natural(self) -> float:
        """T₀ = 2π / ω₀  [s]"""
        return 2.0 * math.pi / self.omega_natural

    @property
    def b_critico(self) -> float:
        """b_c = 2·√(k·m)  [N·s/m]"""
        return 2.0 * math.sqrt(self.k * self.masa)

    @property
    def factor_amortiguacion(self) -> float:
        """ζ = b / b_c  (adimensional)"""
        return self.b / self.b_critico

    @property
    def tipo_amortiguacion(self) -> str:
        """Clasifica el régimen de amortiguación."""
        z = self.factor_amortiguacion
        if z < 1.0:   return "Subamortiguado"
        if z == 1.0:  return "Críticamente amortiguado"
        return "Sobreamortiguado"

    @property
    def omega_amortiguada(self) -> Optional[float]:
        """
        ω_d = ω₀ · √(1 - ζ²)  [rad/s]
        None si el sistema está sobreamortiguado (ζ ≥ 1).
        """
        z = self.factor_amortiguacion
        if z >= 1.0:
            return None
        return self.omega_natural * math.sqrt(1.0 - z**2)

    # ------------------------------------------------------------------ #
    #  Posición en el tiempo (subamortiguado)                            #
    # ------------------------------------------------------------------ #
    def posicion(self, t: float, x0: float, v0: float) -> float:
        """
        Posición en el instante t para un sistema subamortiguado.

        x(t) = e^(-ζω₀t) · [x₀·cos(ω_d·t) + ((v₀+ζω₀x₀)/ω_d)·sin(ω_d·t)]

        Parámetros
        ----------
        t  : tiempo [s]
        x0 : posición inicial respecto al equilibrio [m]
        v0 : velocidad inicial [m/s]

        Retorna
        -------
        x  : posición en t [m]  (None si sobreamortiguado)
        """
        z   = self.factor_amortiguacion
        w0  = self.omega_natural
        wd  = self.omega_amortiguada

        if wd is None:
            return None  # no implementado para ζ ≥ 1

        decay = math.exp(-z * w0 * t)
        cos_t = math.cos(wd * t)
        sin_t = math.sin(wd * t)

        return decay * (x0 * cos_t + ((v0 + z * w0 * x0) / wd) * sin_t)

    # ------------------------------------------------------------------ #
    #  Energías                                                           #
    # ------------------------------------------------------------------ #
    @staticmethod
    def energia_elastica(k: float, x: float) -> float:
        """Ep = ½·k·x²  [J]"""
        return 0.5 * k * x**2

    @staticmethod
    def energia_cinetica(masa: float, v: float) -> float:
        """Ek = ½·m·v²  [J]"""
        return 0.5 * masa * v**2

    # ------------------------------------------------------------------ #
    #  Elongación de equilibrio                                          #
    # ------------------------------------------------------------------ #
    def elongacion_equilibrio(self, g: float = 9.81) -> float:
        """
        Elongación estática del muelle cuando cuelga una masa verticalmente.

        δ = m·g / k  [m]
        """
        return self.masa * g / self.k

    # ------------------------------------------------------------------ #
    #  Amortiguamiento crítico óptimo dado ζ objetivo                    #
    # ------------------------------------------------------------------ #
    def b_para_zeta(self, zeta: float) -> float:
        """
        Devuelve el coeficiente de amortiguamiento para un ζ dado.

        b = ζ · b_c
        """
        return zeta * self.b_critico

    # ------------------------------------------------------------------ #
    #  Resumen                                                            #
    # ------------------------------------------------------------------ #
    def resumen(self) -> str:
        lines = [
            f"Muelle-Masa: m={self.masa} kg, k={self.k} N/m, b={self.b} N·s/m",
            f"  ω₀   = {self.omega_natural:.4f} rad/s",
            f"  f₀   = {self.frecuencia_natural:.4f} Hz",
            f"  T₀   = {self.periodo_natural:.4f} s",
            f"  b_c  = {self.b_critico:.4f} N·s/m",
            f"  ζ    = {self.factor_amortiguacion:.4f}  → {self.tipo_amortiguacion}",
        ]
        wd = self.omega_amortiguada
        if wd:
            lines.append(f"  ω_d  = {wd:.4f} rad/s")
        return "\n".join(lines)


class Pendulo:
    """
    Péndulo simple (hilo inextensible, masa puntual).
    Válido para ángulos pequeños (< ~15°) en la aproximación lineal.
    Para ángulos grandes usa el método numérico `periodo_exacto`.

    Convenciones
    ------------
    - longitud L [m]
    - ángulo en radianes
    - g [m/s²]
    """

    def __init__(self, longitud: float, masa: float = 1.0,
                 g: float = 9.81, b: float = 0.0):
        """
        Parámetros
        ----------
        longitud : longitud del hilo [m]
        masa     : masa de la esfera [kg]
        g        : aceleración gravitatoria [m/s²]
        b        : coeficiente de amortiguamiento [N·s/m] (0 = sin amortiguar)
        """
        if longitud <= 0:
            raise ValueError("La longitud debe ser positiva.")
        self.L    = longitud
        self.masa = masa
        self.g    = g
        self.b    = b

    @property
    def omega0(self) -> float:
        """ω₀ = √(g/L)  [rad/s]"""
        return math.sqrt(self.g / self.L)

    @property
    def periodo_lineal(self) -> float:
        """T ≈ 2π·√(L/g)  [s]  (aproximación ángulos pequeños)"""
        return 2.0 * math.pi * math.sqrt(self.L / self.g)

    @property
    def frecuencia_lineal(self) -> float:
        """f ≈ 1/T  [Hz]"""
        return 1.0 / self.periodo_lineal

    def periodo_exacto(self, theta0_rad: float, n_terminos: int = 5) -> float:
        """
        Periodo exacto para amplitud θ₀ usando la serie de Legendre.

        T = T_lineal · Σ [(2n)! / (2^n · n!)²]² · sin²ⁿ(θ₀/2)

        Parámetros
        ----------
        theta0_rad : ángulo de amplitud [rad]
        n_terminos : términos de la serie (≥ 2 para resultados precisos)
        """
        T0 = self.periodo_lineal
        k  = math.sin(theta0_rad / 2.0)
        suma = 1.0
        factor = 1.0
        k2n = 1.0
        for n in range(1, n_terminos + 1):
            factor *= ((2*n - 1) / (2*n))**2
            k2n    *= k**2
            suma   += factor * k2n
        return T0 * suma

    def coef_amort_critico(self) -> float:
        """b_c = 2·m·ω₀  [N·s/m]"""
        return 2.0 * self.masa * self.omega0

    def factor_amortiguacion(self) -> float:
        """ζ = b / b_c"""
        return self.b / self.coef_amort_critico()

    def energia_potencial(self, theta: float) -> float:
        """
        Energía potencial gravitatoria relativa al punto más bajo.

        Ep = m·g·L·(1 - cos θ)  [J]
        """
        return self.masa * self.g * self.L * (1.0 - math.cos(theta))

    def energia_cinetica(self, omega: float) -> float:
        """
        Energía cinética del péndulo.

        Ek = ½·m·(L·ω)²  [J]
        """
        return 0.5 * self.masa * (self.L * omega)**2

    def velocidad_max(self, theta0: float) -> float:
        """
        Velocidad máxima en el punto más bajo (conservación de energía).

        v_max = √(2·g·L·(1 - cos θ₀))  [m/s]
        """
        return math.sqrt(2.0 * self.g * self.L * (1.0 - math.cos(theta0)))

    def resumen(self) -> str:
        lines = [
            f"Péndulo: L={self.L} m, m={self.masa} kg, g={self.g} m/s², b={self.b}",
            f"  ω₀             = {self.omega0:.4f} rad/s",
            f"  T (lineal)     = {self.periodo_lineal:.4f} s",
            f"  f (lineal)     = {self.frecuencia_lineal:.4f} Hz",
            f"  T (exacto 30°) = {self.periodo_exacto(math.radians(30)):.4f} s",
            f"  T (exacto 70°) = {self.periodo_exacto(math.radians(70)):.4f} s",
        ]
        return "\n".join(lines)


class OsciladorAmortiguado:
    """
    Calcula parámetros de amortiguamiento óptimo para
    cualquier oscilador (no solo muelle o péndulo).
    """

    @staticmethod
    def b_critico_general(masa: float, omega0: float) -> float:
        """b_c = 2·m·ω₀"""
        return 2.0 * masa * omega0

    @staticmethod
    def tiempo_decaimiento(zeta: float, omega0: float) -> float:
        """
        Tiempo característico de decaimiento de amplitud.

        τ = 1 / (ζ·ω₀)  [s]
        """
        if zeta * omega0 < 1e-12:
            return float('inf')
        return 1.0 / (zeta * omega0)

    @staticmethod
    def ciclos_hasta_mitad_amplitud(zeta: float) -> float:
        """
        Número de ciclos completos hasta que la amplitud cae a la mitad.

        N = ln(2) / (2π·ζ)
        """
        if zeta <= 0:
            return float('inf')
        return math.log(2) / (2.0 * math.pi * zeta)

    @staticmethod
    def amplitud_en_t(A0: float, zeta: float, omega0: float, t: float) -> float:
        """
        Amplitud envolvente en el instante t.

        A(t) = A₀ · e^(-ζ·ω₀·t)
        """
        return A0 * math.exp(-zeta * omega0 * t)


# --------------------------------------------------------------------------- #
#  Bloque de prueba rápida                                                     #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    print("=== MUELLE-MASA ===")
    sys = MuelleMasa(masa=8.0, k=150.0, b=0.7)
    print(sys.resumen())
    print(f"  x(t=1s) desde x0=0.25m: {sys.posicion(1.0, 0.25, 0.0):.4f} m")

    print("\n=== PÉNDULO ===")
    p = Pendulo(longitud=1.5, masa=0.3, g=9.81)
    print(p.resumen())
    print(f"  v_max (θ=45°): {p.velocidad_max(math.radians(45)):.4f} m/s")

    print("\n=== AMORTIGUAMIENTO ===")
    oa = OsciladorAmortiguado()
    omega0 = math.sqrt(150/8)
    zeta   = 0.05
    print(f"  Ciclos hasta mitad de amplitud (ζ=0.05): "
          f"{oa.ciclos_hasta_mitad_amplitud(zeta):.1f}")
    print(f"  A(t=3s) con A0=1, ζ=0.05: "
          f"{oa.amplitud_en_t(1.0, zeta, omega0, 3.0):.4f}")
