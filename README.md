# Calculo Integral en Movimiento - Dashboard y Arcade

## Descripcion del Proyecto

Calculo Integral en Movimiento es una aplicacion interactiva de escritorio desarrollada en Python que combina vision por computador, modelado geometrico en 3D, asistente de voz en segundo plano y gamificacion para el calculo y visualizacion dinamica de integrales definidas y solidos de revolucion.

El sistema detecta en tiempo real el numero de dedos mostrados frente a la camara web (de 1 a 5) y ejecuta automaticamente el calculo simbolico y numerico correspondiente, generando las graficas en 2D y solidos tridimensionales en vivo.

---

## Explicacion de Funcionamiento y Gestos

El programa interpreta los gestos de la mano de 1 a 5 dedos para ejecutar diferentes conceptos geometricos de la integral definida:

1. Gesto 1 Dedo - Area Bajo la Curva (2D):
   Calcula el area plana encerrada entre la funcion f(x), el eje X y los limites a y b. Formula: A = integral(f(x) dx).
   Aplicacion Industrial: Produccion acumulada de piezas en un turno de trabajo o consumo energetico total.

2. Gesto 2 Dedos - Volumen Solido en Eje X (3D):
   Genera un solido de revolucion rotando la funcion alrededor del eje horizontal X mediante el metodo de discos. Formula: V = pi * integral([f(x)]^2 dx).
   Aplicacion Industrial: Calculo de capacidad volumetrica de depositos y tanques cilindricos horizontales.

3. Gesto 3 Dedos - Volumen Solido en Eje Y (3D):
   Genera un solido de revolucion rotando la funcion alrededor del eje vertical Y mediante el metodo de capas cilindricas. Formula: V = 2 * pi * integral(x * f(x) dx).
   Aplicacion Industrial: Capacidad de silos verticales, tolvas de alimentacion y embudos de planta.

4. Gesto 4 Dedos - Area Superficial 3D (3D):
   Calcula el area de la superficie exterior de la envoltura tridimensional generada por la rotacion. Formula: S = 2 * pi * integral(f(x) * sqrt(1 + [f'(x)]^2) dx).
   Aplicacion Industrial: Estimacion de insumos para recubrimiento, aislamiento o pintura industrial.

5. Gesto 5 Dedos - Longitud de Arco (2D):
   Mide la distancia lineal a lo largo de la trayectoria de la curva entre los limites a y b. Formula: L = integral(sqrt(1 + [f'(x)]^2) dx).
   Aplicacion Industrial: Metraje exacto de bandas transportadoras curvas y tuberias de proceso.

---

## Justificacion Geometrica: Graficas 2D vs 3D

1. Graficas en 2D: El Area (1 dedo) y la Longitud de Arco (5 dedos) son medidas contenidas en el plano bidimensional XY, por lo que no requieren una tercera dimension para su representacion.
2. Graficas en 3D: Los Solidos de Revolucion (2 y 3 dedos) y el Area Superficial (4 dedos) se generan al rotar la funcion 360 grados sobre un eje. Esta rotacion introduce la profundidad en el eje Z, requiriendo un espacio tridimensional XYZ para visualizar la forma geometrica completa.

---

## Arquitectura y Tecnologias Utilizadas

El software esta construido bajo una arquitectura modular en Python:

- Interfaz Grafica (GUI): CustomTkinter para el panel de control y Pillow (PIL) para el procesamiento de imagenes de camara.
- Vision por Computador: OpenCV y CVZone (HandTrackingModule) para la captura de video y deteccion de puntos de referencia de la mano.
- Motor Matematico: SymPy para derivacion simbolica y parseo de expresiones, SciPy (scipy.integrate.quad) para integracion numerica y NumPy para el manejo vectorial.
- Visualizacion Grafica: Matplotlib embebido mediante FigureCanvasTkAgg para renderizado en 2D y 3D.
- Audio y Voz: pyttsx3 para la sintesis de voz offline ejecutada en hilos secundarios (threading) y winsound para los efectos sonoros de la interfaz.

---

## Comandos de Instalacion de Librerias

Para instalar todas las dependencias requeridas en el entorno de Python, ejecute el siguiente comando exacto en la terminal:

pip install customtkinter opencv-python pillow numpy matplotlib scipy sympy cvzone pyttsx3

---

## Pasos para Abrir y Ejecutar el Programa

1. Abrir la terminal de comandos o la consola integrada en Visual Studio Code.

2. Navegar hasta la carpeta del proyecto (reemplace la ruta por la ubicacion de su carpeta si varia):

cd "C:\Users\frell\OneDrive - unicesar.edu.co\Escritorio\proyecto de calculo"

3. Ejecutar el archivo principal del sistema:

python main.py

4. Modo de uso en la interfaz:
   - Al iniciar se mostrara la pantalla de bienvenida con la guia de formulas.
   - Presione el boton "COMENZAR EXPERIENCIA" para habilitar la camara web y los graficos.
   - Muestre los gestos frente a la camara o utilice los botones del panel de control manual de respaldo.
   - Seleccione una opcion en el menu de Aplicacion Industrial para evaluar modelos reales de ingenieria.
   - Cambie a la pestaña "Arcade" para jugar al test de velocidad de calculo con racha y temporizador.