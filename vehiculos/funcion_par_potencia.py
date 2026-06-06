import numpy as np
from scipy.interpolate import interp1d

def par_potencia_ferrari_f430(rpm_consulta):
	"""
	Calcula el par motor (Nm) y la potencia (CV) del Ferrari F430 para unas RPM dadas.
	Utiliza interpolación de spline cúbica basada en datos técnicos reales.
	"""
	# Datos maestros del Ferrari F430 V8
	rpm_datos = np.array([1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5250, 5500, 6000, 6500, 7000, 7500, 8000, 8500])
	par_datos = np.array([320, 345, 370, 400, 415, 430, 445, 455, 465, 465, 460, 455, 450, 440, 430, 415, 390])

	# Creamos la función de interpolación (spline cúbica)
	# Esto permite que la curva sea suave: T = f(RPM)
	interp_par = interp1d(rpm_datos, par_datos, kind='cubic', fill_value="extrapolate")

	# 1. Calculamos el Par (T) para la consulta
	par = float(interp_par(rpm_consulta))

	# 2. Calculamos la Potencia (P) en CV
	# Aplicamos la relación física: P = (T * omega) / 735.5
	# Donde omega = (RPM * 2 * pi) / 60
	# Simplificando: P(CV) \simeq \dfrac{T \cdot RPM}{7023}
	potencia = (par * rpm_consulta * 2 * np.pi) / (60 * 735.5)

	return par, potencia

# Ejemplo de uso:
if __name__ == "__main__":
	revs = 5250
	t, p = par_potencia_ferrari_f430(revs)
	print(f"A {revs} RPM:")
	print(f"\tPar Motor: {t:.2f} Nm")
	print(f"\tPotencia: {p:.2f} CV")
