"""
aerodinamica.py
===============
Cálculos aerodinámicos puros (sin Pymunk/Pygame).
Basado en los módulos rozamiento_aire.py del proyecto.
"""

import math


class Aerodinamica:
    """
    Agrupa todos los cálculos aerodinámicos para una esfera en vuelo:
    número de Reynolds, coeficiente de arrastre (Cd), densidad del aire
    según altitud (modelo ISA), velocidad del sonido y corrección de Mach.
    """

    # ------------------------------------------------------------------ #
    #  Constantes por defecto (aire a nivel del mar, 15 °C)              #
    # ------------------------------------------------------------------ #
    MU_AIRE   = 1.85e-5   # Viscosidad dinámica [Pa·s]
    RHO0      = 1.225     # Densidad al nivel del mar [kg/m³]
    T0        = 288.15    # Temperatura ISA a nivel del mar [K]
    L         = 0.0065    # Gradiente térmico troposfera [K/m]
    G         = 9.80665   # Gravedad estándar [m/s²]
    M_AIRE    = 0.0289644 # Masa molar del aire [kg/mol]
    R_GAS     = 8.31446   # Constante universal de los gases [J/(mol·K)]
    V_SONIDO0 = 340.0     # Velocidad del sonido a 15 °C [m/s]

    # ------------------------------------------------------------------ #
    #  Número de Reynolds                                                 #
    # ------------------------------------------------------------------ #
    @staticmethod
    def reynolds(v: float, D: float,
                 mu: float = MU_AIRE, rho: float = RHO0) -> float:
        """
        Calcula el número de Reynolds.

        Parámetros
        ----------
        v   : módulo de la velocidad relativa [m/s]
        D   : longitud característica (diámetro para esferas) [m]
        mu  : viscosidad dinámica del fluido [Pa·s]
        rho : densidad del fluido [kg/m³]

        Retorna
        -------
        Re  : número de Reynolds (adimensional)
        """
        if mu <= 0:
            raise ValueError("La viscosidad dinámica debe ser positiva.")
        return rho * v * D / mu

    # ------------------------------------------------------------------ #
    #  Coeficiente de arrastre para esfera (Schiller-Naumann + crisis)   #
    # ------------------------------------------------------------------ #
    @classmethod
    def Cd_esfera(cls, Re: float, crisis: bool = False) -> float:
        """
        Coeficiente de arrastre (Cd) de una esfera en función de Re.

        Régimen      | Re           | Modelo
        -------------|--------------|---------------------------------------
        Stokes       | Re < 1       | 24/Re
        Intermedio   | Re < 1000    | Schiller-Naumann
        Newton       | Re ≤ 2e5     | Cd ≈ 0.44
        Crisis       | 2e5–3e5      | Interpolación log-log (si crisis=True)
        Recuperación | 3e5–2e6      | Interpolación log-log (si crisis=True)
        Turbulento   | Re > 2e6     | Cd ≈ 0.20

        Parámetros
        ----------
        Re     : número de Reynolds
        crisis : si True, modela la crisis de arrastre alrededor de Re≈2·10⁵
        """
        if Re <= 0:
            return 0.0

        if Re < 1000:
            return (24.0 / Re) * (1.0 + 0.15 * Re**0.687)

        if Re <= 2e5 or not crisis:
            return 0.44

        # Crisis de arrastre: 2e5 → 3e5 (0.44 → 0.10)
        if Re <= 3e5:
            return cls._log_interp(Re, 2e5, 0.44, 3e5, 0.10)

        # Recuperación: 3e5 → 2e6 (0.10 → 0.20)
        if Re <= 2e6:
            return cls._log_interp(Re, 3e5, 0.10, 2e6, 0.20)

        return 0.20

    @staticmethod
    def _log_interp(x, x1, y1, x2, y2) -> float:
        """Interpolación lineal en escala log-log."""
        lx  = math.log10(x)
        lx1 = math.log10(x1); ly1 = math.log10(y1)
        lx2 = math.log10(x2); ly2 = math.log10(y2)
        ly  = ly1 + (ly2 - ly1) * (lx - lx1) / (lx2 - lx1)
        return 10**ly

    # ------------------------------------------------------------------ #
    #  Propiedades del aire según altitud (modelo ISA)                   #
    # ------------------------------------------------------------------ #
    @classmethod
    def densidad(cls, alt_m: float) -> float:
        """
        Densidad del aire según el modelo ISA (troposfera hasta 11 000 m).

        Parámetros
        ----------
        alt_m : altitud [m]  (se limita al rango 0–11 000 m)

        Retorna
        -------
        rho   : densidad [kg/m³]
        """
        alt = max(0.0, min(alt_m, 11_000.0))
        T_local = cls.T0 - cls.L * alt
        exponent = (cls.G * cls.M_AIRE) / (cls.R_GAS * cls.L)
        return cls.RHO0 * (T_local / cls.T0) ** exponent

    @classmethod
    def vel_sonido_temp(cls, T_celsius: float) -> float:
        """
        Velocidad del sonido en función de la temperatura.

        Parámetros
        ----------
        T_celsius : temperatura [°C]

        Retorna
        -------
        v_s : velocidad del sonido [m/s]
        """
        T_K = T_celsius + 273.15
        gamma = 1.4
        return math.sqrt(gamma * cls.R_GAS / cls.M_AIRE * T_K)

    @classmethod
    def vel_sonido_altitud(cls, alt_m: float, T0_celsius: float = 15.0) -> float:
        """
        Velocidad del sonido según la altitud (modelo ISA).

        Parámetros
        ----------
        alt_m     : altitud [m]
        T0_celsius: temperatura al nivel del mar [°C]  (por defecto 15 °C)
        """
        T0_K    = T0_celsius + 273.15
        alt     = max(0.0, min(alt_m, 11_000.0))
        T_local = T0_K - cls.L * alt
        return cls.vel_sonido_temp(T_local - 273.15)

    # ------------------------------------------------------------------ #
    #  Corrección de Mach                                                 #
    # ------------------------------------------------------------------ #
    @classmethod
    def correccion_mach(cls, v: float, v_sonido: float = None) -> float:
        """
        Factor multiplicativo de corrección al Cd por compresibilidad (Mach).

        Parámetros
        ----------
        v        : velocidad relativa [m/s]
        v_sonido : velocidad del sonido local [m/s]  (por defecto 340 m/s)

        Retorna
        -------
        factor : Cd_corregido = Cd_reynolds * factor
        """
        if v_sonido is None:
            v_sonido = cls.V_SONIDO0
        Ma = v / v_sonido
        if Ma < 0.6:
            return 1.0
        if Ma < 1.0:
            return 1.0 + 4.5 * (Ma - 0.6)**2
        if Ma < 1.2:
            return 1.0 + 4.5 * (0.4**2) + 3.0 * (Ma - 1.0)
        return 1.0 + 4.5 * (0.4**2) + 3.0 * 0.2 + 0.5 * (Ma - 1.2)

    # ------------------------------------------------------------------ #
    #  Fuerza de arrastre de Newton (sin Pymunk)                         #
    # ------------------------------------------------------------------ #
    @classmethod
    def fuerza_drag(cls, v_vec: tuple, area: float,
                    Cd: float = 0.47, rho: float = RHO0,
                    v_viento: tuple = (0.0, 0.0)) -> tuple:
        """
        Fuerza de arrastre aerodinámica (modelo de Newton).

        F_drag = -0.5 · ρ · Cd · A · |v_rel| · v_rel

        Parámetros
        ----------
        v_vec   : velocidad del cuerpo (vx, vy) [m/s]
        area    : sección transversal [m²]
        Cd      : coeficiente de arrastre
        rho     : densidad del fluido [kg/m³]
        v_viento: velocidad del viento (vx, vy) [m/s]

        Retorna
        -------
        (Fx, Fy) : componentes de la fuerza de arrastre [N]
        """
        vrel_x = v_vec[0] - v_viento[0]
        vrel_y = v_vec[1] - v_viento[1]
        v_mag  = math.hypot(vrel_x, vrel_y)
        if v_mag < 1e-6:
            return (0.0, 0.0)
        factor = -0.5 * rho * Cd * area * v_mag
        return (factor * vrel_x, factor * vrel_y)

    # ------------------------------------------------------------------ #
    #  Efecto Magnus                                                      #
    # ------------------------------------------------------------------ #
    @classmethod
    def fuerza_magnus(cls, v_vec: tuple, omega: float, radio: float,
                      area: float, k: float = 0.5,
                      rho: float = RHO0,
                      v_viento: tuple = (0.0, 0.0)) -> tuple:
        """
        Fuerza de Magnus para una esfera en rotación.

        Parámetros
        ----------
        v_vec  : velocidad del cuerpo (vx, vy) [m/s]
        omega  : velocidad angular [rad/s]  (positivo = antihorario)
        radio  : radio de la esfera [m]
        area   : sección transversal [m²]
        k      : parámetro de deporte (≈0.5 genérico, 0.7 golf, etc.)
        rho    : densidad del aire [kg/m³]
        v_viento: velocidad del viento (vx, vy) [m/s]

        Retorna
        -------
        (Fx, Fy) : componentes de la fuerza de Magnus [N]
        """
        vrel_x = v_vec[0] - v_viento[0]
        vrel_y = v_vec[1] - v_viento[1]
        v_mag  = math.hypot(vrel_x, vrel_y)
        if v_mag < 0.1:
            return (0.0, 0.0)

        # Vector perpendicular a v_rel (rotado 90°)
        u_m_x = -vrel_y / v_mag
        u_m_y =  vrel_x / v_mag

        S  = radio * omega / v_mag
        Cm = k * S / (2.0 + abs(S))

        factor = 0.5 * rho * Cm * area * v_mag**2
        return (factor * u_m_x, factor * u_m_y)


# --------------------------------------------------------------------------- #
#  Bloque de prueba rápida                                                     #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    a = Aerodinamica()

    print("=== AERODINAMICA ===")
    Re = a.reynolds(30, 0.043)          # pelota de tenis a 30 m/s
    print(f"Reynolds (tenis 30 m/s): {Re:.0f}")
    print(f"Cd esfera (Re={Re:.0f}):  {a.Cd_esfera(Re):.4f}")
    print(f"Densidad a 3000 m:        {a.densidad(3000):.4f} kg/m³")
    print(f"Vel. sonido a 3000 m:     {a.vel_sonido_altitud(3000):.2f} m/s")
    print(f"Corrección Mach (Ma=0.8): {a.correccion_mach(0.8*340):.4f}")
    Fd = a.fuerza_drag((50, -20), area=math.pi*0.0215**2)
    print(f"Fuerza drag (50,-20 m/s): ({Fd[0]:.4f}, {Fd[1]:.4f}) N")
