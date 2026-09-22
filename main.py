import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.integrate import quad
import sympy as sp
from cvzone.HandTrackingModule import HandDetector
import random
import math
import winsound
import pyttsx3
import threading

# Configuración Visual General
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLOR_BG = "#121318"          
COLOR_CARD = "#1c1e26"        
COLOR_ACCENT = "#00adb5"      
COLOR_GOLD = "#ffb703"        
COLOR_TEXT_DIM = "#9094a6"    


# ==========================================
# MÓDULO DE VOZ OFFLINE (SAPI5 WINDOWS)
# ==========================================
def hablar_en_segundo_plano(texto):
    """Ejecuta la voz en un hilo secundario para no congelar la interfaz."""
    def _hablar():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.setProperty('volume', 0.9)
            engine.say(texto)
            engine.runAndWait()
        except Exception:
            pass

    threading.Thread(target=_hablar, daemon=True).start()


# ==========================================
# SISTEMA DE PARTÍCULAS EN PYTHON (OPENCV)
# ==========================================
class SistemaParticulasCamara:
    def __init__(self, cantidad=35, ancho=280, alto=210):
        self.ancho = ancho
        self.alto = alto
        self.particulas = []
        for _ in range(cantidad):
            self.particulas.append([
                random.randint(0, ancho),
                random.randint(0, alto),
                random.uniform(-1.2, 1.2),
                random.uniform(-1.2, 1.2),
                random.randint(1, 2)
            ])

    def actualizar_y_dibujar(self, frame, yemas_dedos=None):
        # 1. Mover partículas y rebotar en bordes
        for p in self.particulas:
            p[0] += p[2]
            p[1] += p[3]

            if p[0] <= 0 or p[0] >= self.ancho: p[2] *= -1
            if p[1] <= 0 or p[1] >= self.alto: p[3] *= -1

            # Dibujar nodo de partícula (Cian)
            cv2.circle(frame, (int(p[0]), int(p[1])), p[4], (181, 173, 0), -1)

        # 2. Conectar partículas cercanas entre sí (Red / Constelación)
        num_p = len(self.particulas)
        for i in range(num_p):
            for j in range(i + 1, num_p):
                p1, p2 = self.particulas[i], self.particulas[j]
                dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                if dist < 45:
                    cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (100, 90, 0), 1)

        # 3. Conectar partículas a las yemas de los dedos cuando la mano esté presente
        if yemas_dedos:
            for yema in yemas_dedos:
                for p in self.particulas:
                    dist = math.hypot(yema[0] - p[0], yema[1] - p[1])
                    if dist < 50:
                        cv2.line(frame, (int(yema[0]), int(yema[1])), (int(p[0]), int(p[1])), (0, 255, 255), 1)


# 🏭 PRESETS DE APLICACIÓN A LA INGENIERÍA INDUSTRIAL
CASOS_INDUSTRIALES = {
    "🛠️ Personalizado": {
        "func": "x**2", "a": "0", "b": "2", 
        "desc": "Modo de libre edición matemática."
    },
    "🏭 Tasa de Producción (Piezas/Hora)": {
        "func": "100 + 15*x - 2*x**2", "a": "0", "b": "8", 
        "desc": "Turno de 8h. 1 dedo calcula las piezas totales producidas en planta."
    },
    "🛢️ Tanque / Silo Cilíndrico": {
        "func": "sqrt(4 - x)", "a": "0", "b": "4", 
        "desc": "Perfil de depósito. 2 y 3 dedos calculan volumen de capacidad en 3D."
    },
    "📦 Banda Transportadora Curva": {
        "func": "sin(x) + 2", "a": "0", "b": "6.28", 
        "desc": "Ruta de faja de ensamble. 5 dedos calcula los metros de banda requeridos."
    }
}

DESAFIOS_ARCADE = [
    {"pregunta": "¡Calcula el ÁREA BAJO LA CURVA (Producción)!", "dedos": 1},
    {"pregunta": "¡Genera el VOLUMEN en el EJE X (Discos)!", "dedos": 2},
    {"pregunta": "¡Genera el VOLUMEN en el EJE Y (Capas)!", "dedos": 3},
    {"pregunta": "¡Obtén el ÁREA SUPERFICIAL 3D (Recubrimiento)!", "dedos": 4},
    {"pregunta": "¡Mide la LONGITUD DE ARCO (Faja Transportadora)!", "dedos": 5}
]

CONEXIONES_MANO = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Pulgar
    (0, 5), (5, 6), (6, 7), (7, 8),        # Índice
    (9, 10), (10, 11), (11, 12), (5, 9),   # Medio
    (13, 14), (14, 15), (15, 16), (9, 13), # Anular
    (17, 18), (18, 19), (19, 20), (13, 17), (0, 17) # Meñique / Palma
]


# ==========================================
# 1. MOTOR MATEMÁTICO
# ==========================================
class MotorCalculo:
    def __init__(self, expresion_str="x**2", a_str="0", b_str="2"):
        self.x_sym = sp.Symbol('x')
        self.a = float(a_str)
        self.b = float(b_str)
        self.expr_sym = sp.sympify(expresion_str)
        
        self.f = sp.lambdify(self.x_sym, self.expr_sym, "numpy")
        self.df_sym = sp.diff(self.expr_sym, self.x_sym)
        self.df = sp.lambdify(self.x_sym, self.df_sym, "numpy")

    def ejecutar_calculo(self, num_dedos):
        if num_dedos == 1:
            val, _ = quad(self.f, self.a, self.b)
            return "Área Bajo la Curva", val, "unidades cuadradas", "A = ∫ [a, b] f(x) dx"
        elif num_dedos == 2:
            f_vol = lambda x: np.pi * (self.f(x) ** 2)
            val, _ = quad(f_vol, self.a, self.b)
            return "Volumen Sólido Eje X", val, "unidades cúbicas", "V = π ∫ [a, b] [f(x)]² dx"
        elif num_dedos == 3:
            f_vol_y = lambda x: 2 * np.pi * x * self.f(x)
            val, _ = quad(f_vol_y, self.a, self.b)
            return "Volumen Sólido Eje Y", val, "unidades cúbicas", "V = 2π ∫ [a, b] x · f(x) dx"
        elif num_dedos == 4:
            f_surf = lambda x: 2 * np.pi * np.abs(self.f(x)) * np.sqrt(1 + (self.df(x) ** 2))
            val, _ = quad(f_surf, self.a, self.b)
            return "Área Superficial 3D", val, "unidades cuadradas", "S = 2π ∫ [a, b] f(x) √(1 + [f']²) dx"
        elif num_dedos == 5:
            f_arc = lambda x: np.sqrt(1 + (self.df(x) ** 2))
            val, _ = quad(f_arc, self.a, self.b)
            return "Longitud de Arco", val, "unidades", "L = ∫ [a, b] √(1 + [f']²) dx"

        return "Modo Standby", 0.0, "", "Muestre de 1 a 5 dedos frente a la cámara"


# ==========================================
# 2. INTERFAZ GRÁFICA FUTURISTA CON CIBER-ESQUELETO
# ==========================================
class AppCalculoIntegral(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cálculo Integral en Movimiento — Cyber Dashboard")
        self.geometry("1280x760")
        self.configure(fg_color=COLOR_BG)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.puntos = 0
        self.racha = 0
        self.modo_juego = "Exploración"
        self.desafio_actual = None
        self.tiempo_restante = 5.0
        self.dedos_previos = -1
        self.juego_activo = False

        # Sistema de partículas para el recuadro de la cámara (280x210 px)
        self.sistema_particulas = SistemaParticulasCamara(cantidad=35, ancho=280, alto=210)

        # HEADER SUPERIOR
        self.header_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12, height=60)
        self.header_frame.grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="ew")

        self.lbl_title = ctk.CTkLabel(
            self.header_frame, 
            text=" 📐 CÁLCULO INTEGRAL EN MOVIMIENTO", 
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff"
        )
        self.lbl_title.pack(side="left", padx=15, pady=10)

        self.btn_guia = ctk.CTkButton(
            self.header_frame,
            text="📖 Ver Fórmulas",
            font=("Segoe UI", 11, "bold"),
            fg_color="#252834",
            hover_color="#323646",
            width=110,
            command=self.mostrar_guia_bienvenida
        )
        self.btn_guia.pack(side="left", padx=5)

        self.lbl_score = ctk.CTkLabel(self.header_frame, text="🏆 PUNTOS: 0", font=("Segoe UI", 13, "bold"), text_color=COLOR_GOLD)
        self.lbl_score.pack(side="right", padx=15)

        self.lbl_streak = ctk.CTkLabel(self.header_frame, text="🔥 RACHA: x0", font=("Segoe UI", 12, "bold"), text_color="#ff5555")
        self.lbl_streak.pack(side="right", padx=5)

        # PANEL IZQUIERDO
        self.panel_izq = ctk.CTkFrame(self, fg_color="transparent", width=380)
        self.panel_izq.grid(row=1, column=0, padx=(15, 10), pady=(0, 15), sticky="nsew")

        # CARD 1: Modalidad y Selector Manual
        self.card_modo = ctk.CTkFrame(self.panel_izq, fg_color=COLOR_CARD, corner_radius=12)
        self.card_modo.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(self.card_modo, text="🕹️ MODALIDAD Y CONTROL MANUAL", font=("Segoe UI", 11, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=15, pady=(6, 2))

        self.btn_modo = ctk.CTkSegmentedButton(
            self.card_modo,
            values=["Exploración", "Arcade ⚡"],
            selected_color=COLOR_ACCENT,
            font=("Segoe UI", 11, "bold"),
            command=self.cambiar_modalidad
        )
        self.btn_modo.set("Exploración")
        self.btn_modo.pack(pady=(2, 6), padx=15, fill="x")

        ctk.CTkLabel(self.card_modo, text="Control por Botones (Respaldo):", font=("Segoe UI", 10), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=15)
        self.selector_manual = ctk.CTkSegmentedButton(
            self.card_modo,
            values=["Cámara", "1", "2", "3", "4", "5"],
            selected_color="#2b82c5",
            font=("Segoe UI", 10, "bold"),
            command=self.cambio_modo_manual
        )
        self.selector_manual.set("Cámara")
        self.selector_manual.pack(pady=(2, 8), padx=15, fill="x")

        # CARD 2: Presets Industriales
        self.card_params = ctk.CTkFrame(self.panel_izq, fg_color=COLOR_CARD, corner_radius=12)
        self.card_params.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(self.card_params, text="⚙ APLICACIÓN INDUSTRIAL", font=("Segoe UI", 11, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=15, pady=(8, 2))

        self.opt_preset = ctk.CTkOptionMenu(
            self.card_params,
            values=list(CASOS_INDUSTRIALES.keys()),
            fg_color="#121318",
            button_color="#2e3240",
            button_hover_color="#3c4254",
            font=("Segoe UI", 11),
            command=self.seleccionar_preset
        )
        self.opt_preset.pack(pady=(0, 6), fill="x", padx=15)

        ctk.CTkLabel(self.card_params, text="Función f(x):", font=("Segoe UI", 10), text_color=COLOR_TEXT_DIM).pack(anchor="w", padx=15)
        self.entry_func = ctk.CTkEntry(self.card_params, fg_color="#121318", border_color="#2e3240", font=("Consolas", 12))
        self.entry_func.insert(0, "x**2")
        self.entry_func.pack(pady=2, fill="x", padx=15)

        self.frame_lims = ctk.CTkFrame(self.card_params, fg_color="transparent")
        self.frame_lims.pack(pady=2, fill="x", padx=15)

        ctk.CTkLabel(self.frame_lims, text="a:", font=("Segoe UI", 10), text_color=COLOR_TEXT_DIM).pack(side="left")
        self.entry_a = ctk.CTkEntry(self.frame_lims, width=50, fg_color="#121318", border_color="#2e3240")
        self.entry_a.insert(0, "0")
        self.entry_a.pack(side="left", padx=(5, 10))

        ctk.CTkLabel(self.frame_lims, text="b:", font=("Segoe UI", 10), text_color=COLOR_TEXT_DIM).pack(side="left")
        self.entry_b = ctk.CTkEntry(self.frame_lims, width=50, fg_color="#121318", border_color="#2e3240")
        self.entry_b.insert(0, "2")
        self.entry_b.pack(side="left", padx=5)

        self.btn_recalc = ctk.CTkButton(
            self.card_params, text="Recalcular", fg_color="#252834", hover_color="#323646", height=24, command=self.forzar_recalculo
        )
        self.btn_recalc.pack(pady=6, padx=15, fill="x")

        # CARD 3: Cámara Web
        self.card_cam = ctk.CTkFrame(self.panel_izq, fg_color=COLOR_CARD, corner_radius=12)
        self.card_cam.pack(fill="both", expand=True)

        self.label_camara = ctk.CTkLabel(self.card_cam, text="")
        self.label_camara.pack(pady=6, padx=10)

        self.label_gesto = ctk.CTkLabel(self.card_cam, text="Modo Cámara Activo", font=("Segoe UI", 11, "bold"), text_color="#ffffff")
        self.label_gesto.pack(pady=(0, 6))

        # PANEL DERECHO
        self.panel_der = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_der.grid(row=1, column=1, padx=(0, 15), pady=(0, 15), sticky="nsew")

        # CARD HERO
        self.card_hero = ctk.CTkFrame(self.panel_der, fg_color=COLOR_CARD, corner_radius=12)
        self.card_hero.pack(fill="x", pady=(0, 8))

        self.lbl_concepto = ctk.CTkLabel(self.card_hero, text="MODO LIBRE: MUESTRE DE 1 A 5 DEDOS", font=("Segoe UI", 13, "bold"), text_color=COLOR_ACCENT)
        self.lbl_concepto.pack(anchor="w", padx=20, pady=(8, 2))

        self.progress_timer = ctk.CTkProgressBar(self.card_hero, fg_color="#121318", progress_color=COLOR_GOLD, height=6)
        self.progress_timer.set(1.0)
        self.progress_timer.pack(fill="x", padx=20, pady=3)

        self.lbl_resultado_val = ctk.CTkLabel(self.card_hero, text="---", font=("Segoe UI", 22, "bold"), text_color="#ffffff")
        self.lbl_resultado_val.pack(anchor="w", padx=20, pady=(0, 2))

        self.lbl_contexto_ind = ctk.CTkLabel(self.card_hero, text="Contexto Industrial: Selecciona un caso de aplicación.", font=("Segoe UI", 10), text_color=COLOR_TEXT_DIM)
        self.lbl_contexto_ind.pack(anchor="w", padx=20, pady=(0, 8))

        # CARD GRAFICA
        self.card_grafica = ctk.CTkFrame(self.panel_der, fg_color=COLOR_CARD, corner_radius=12)
        self.card_grafica.pack(fill="both", expand=True)

        self.fig = plt.Figure(figsize=(6, 4.5), dpi=100, facecolor='#1c1e26')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.card_grafica)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        self.detector = HandDetector(maxHands=1, detectionCon=0.7)
        self.cap = cv2.VideoCapture(0)

        # OVERLAY DE BIENVENIDA
        self.overlay_guia = ctk.CTkFrame(self, fg_color="#0e0f14", corner_radius=15)
        self.construir_pantalla_bienvenida()
        self.mostrar_guia_bienvenida()

        hablar_en_segundo_plano("Bienvenido al sistema Cálculo Integral en Movimiento")

        self.actualizar_video()

    def construir_pantalla_bienvenida(self):
        lbl_intro_title = ctk.CTkLabel(
            self.overlay_guia, 
            text="📐 PROYECTO DE AULA: CÁLCULO INTEGRAL EN MOVIMIENTO", 
            font=("Segoe UI", 17, "bold"), 
            text_color=COLOR_ACCENT
        )
        lbl_intro_title.pack(pady=(15, 2))

        lbl_intro_sub = ctk.CTkLabel(
            self.overlay_guia, 
            text="Guía de Gestos, Fórmulas y Modelado Geométrica 3D Aplicado a la Ingeniería", 
            font=("Segoe UI", 11), 
            text_color=COLOR_TEXT_DIM
        )
        lbl_intro_sub.pack(pady=(0, 10))

        gestos_frame = ctk.CTkFrame(self.overlay_guia, fg_color=COLOR_CARD, corner_radius=10)
        gestos_frame.pack(fill="both", expand=True, padx=20, pady=5)

        lista_gestos = [
            ("☝️ 1 DEDO", "Área Bajo la Curva", "A = ∫ [a, b] f(x) dx", "Producción acumulada (piezas totales) o energía consumida."),
            ("✌️ 2 DEDOS", "Volumen Sólido (Eje X)", "V = π ∫ [a, b] [f(x)]² dx", "Diseño volumétrico de tanques y depósitos por método de discos."),
            ("🤟 3 DEDOS", "Volumen Sólido (Eje Y)", "V = 2π ∫ [a, b] x · f(x) dx", "Capacidad volumétrica de silos y tolvas mediante capas cilíndricas."),
            ("🖖 4 DEDOS", "Área Superficial 3D", "S = 2π ∫ [a, b] f(x) √(1 + [f']²) dx", "Estimación de recubrimientos, aislamiento y pintura industrial."),
            ("🖐️ 5 DEDOS", "Longitud de Arco", "L = ∫ [a, b] √(1 + [f']²) dx", "Metraje exacto de bandas transportadoras y tuberías en planta.")
        ]

        for gesto, concepto, formula, desc in lista_gestos:
            card_item = ctk.CTkFrame(gestos_frame, fg_color="#14151a", corner_radius=8)
            card_item.pack(fill="x", padx=12, pady=4)

            lbl_gesto_name = ctk.CTkLabel(card_item, text=f"{gesto} — {concepto}", font=("Segoe UI", 12, "bold"), text_color="#ffffff")
            lbl_gesto_name.pack(anchor="w", padx=12, pady=(4, 1))

            lbl_formula_text = ctk.CTkLabel(card_item, text=f"Fórmula: {formula}", font=("Consolas", 11, "bold"), text_color=COLOR_GOLD)
            lbl_formula_text.pack(anchor="w", padx=12)

            lbl_desc_text = ctk.CTkLabel(card_item, text=f"Aplicación Industrial: {desc}", font=("Segoe UI", 10), text_color=COLOR_TEXT_DIM)
            lbl_desc_text.pack(anchor="w", padx=12, pady=(0, 4))

        btn_start = ctk.CTkButton(
            self.overlay_guia, 
            text="🚀 COMENZAR EXPERIENCIA", 
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_ACCENT,
            hover_color="#008b91",
            height=40,
            command=self.ocultar_guia_bienvenida
        )
        btn_start.pack(pady=12, padx=40, fill="x")

    def mostrar_guia_bienvenida(self):
        self.overlay_guia.place(relx=0.02, rely=0.08, relwidth=0.96, relheight=0.90)

    def ocultar_guia_bienvenida(self):
        self.overlay_guia.place_forget()
        hablar_en_segundo_plano("Cámara activa. Muestre un gesto frente al sensor.")

    def cambio_modo_manual(self, seleccion):
        if seleccion != "Cámara":
            num_dedos = int(seleccion)
            self.label_gesto.configure(text=f"Modo Manual: {num_dedos} Dedo(s)")
            hablar_en_segundo_plano(f"Seleccionado manualmente gesto {num_dedos}")
            if self.modo_juego == "Exploración":
                self.renderizar_grafica(num_dedos)
            elif self.modo_juego == "Arcade" and self.juego_activo:
                self.evaluar_respuesta_arcade(num_dedos)
        else:
            self.label_gesto.configure(text="Modo Cámara Activo")
            self.dedos_previos = -1
            hablar_en_segundo_plano("Modo cámara activado")

    def seleccionar_preset(self, eleccion):
        datos = CASOS_INDUSTRIALES[eleccion]
        self.entry_func.delete(0, "end")
        self.entry_func.insert(0, datos["func"])
        self.entry_a.delete(0, "end")
        self.entry_a.insert(0, datos["a"])
        self.entry_b.delete(0, "end")
        self.entry_b.insert(0, datos["b"])

        self.lbl_contexto_ind.configure(text=f"Caso Activo: {datos['desc']}")
        hablar_en_segundo_plano(f"Cargado caso industrial {eleccion}")
        self.forzar_recalculo()

    def forzar_recalculo(self):
        modo_man = self.selector_manual.get()
        if modo_man != "Cámara":
            self.renderizar_grafica(int(modo_man))
        elif self.dedos_previos in [1, 2, 3, 4, 5]:
            self.renderizar_grafica(self.dedos_previos)

    def cambiar_modalidad(self, seleccion):
        self.modo_juego = "Arcade" if "Arcade" in seleccion else "Exploración"
        if self.modo_juego == "Arcade":
            self.puntos = 0
            self.racha = 0
            self.lbl_score.configure(text="🏆 PUNTOS: 0")
            self.lbl_streak.configure(text="🔥 RACHA: x0")
            hablar_en_segundo_plano("Modo Arcade activado. ¡Responde rápido!")
            self.nuevo_desafio_arcade()
        else:
            self.juego_activo = False
            self.lbl_concepto.configure(text="MODO LIBRE: MUESTRE DE 1 A 5 DEDOS", text_color=COLOR_ACCENT)
            self.progress_timer.set(1.0)
            hablar_en_segundo_plano("Modo exploración activado.")

    def nuevo_desafio_arcade(self):
        self.desafio_actual = random.choice(DESAFIOS_ARCADE)
        self.lbl_concepto.configure(text=f"🎯 {self.desafio_actual['pregunta']}", text_color=COLOR_GOLD)
        self.tiempo_restante = 5.0
        self.juego_activo = True
        self.dedos_previos = -1
        winsound.Beep(800, 150)
        self.bucle_temporizador_arcade()

    def bucle_temporizador_arcade(self):
        if not self.juego_activo or self.modo_juego != "Arcade":
            return

        self.tiempo_restante -= 0.1
        progreso = max(0.0, self.tiempo_restante / 5.0)
        self.progress_timer.set(progreso)

        if self.tiempo_restante <= 0:
            self.juego_activo = False
            self.racha = 0
            self.lbl_streak.configure(text="🔥 RACHA: x0")
            self.lbl_concepto.configure(text="❌ ¡TIEMPO AGOTADO! Inténtalo de nuevo", text_color="#ff5555")
            winsound.Beep(300, 400)
            hablar_en_segundo_plano("Tiempo agotado")
            self.after(2000, self.nuevo_desafio_arcade)
        else:
            self.after(100, self.bucle_temporizador_arcade)

    def evaluar_respuesta_arcade(self, num_dedos):
        if not self.juego_activo or self.desafio_actual is None:
            return

        if num_dedos == self.desafio_actual["dedos"]:
            self.juego_activo = False
            self.racha += 1
            puntos_ganados = 100 * self.racha
            self.puntos += puntos_ganados

            self.lbl_score.configure(text=f"🏆 PUNTOS: {self.puntos}")
            self.lbl_streak.configure(text=f"🔥 RACHA: x{self.racha}")
            self.lbl_concepto.configure(text=f"🎉 ¡CORRECTO! +{puntos_ganados} PTS", text_color="#00ff88")

            winsound.Beep(1200, 100)
            winsound.Beep(1600, 200)

            hablar_en_segundo_plano(f"¡Correcto! Más {puntos_ganados} puntos.")

            self.renderizar_grafica(num_dedos)
            self.after(2000, self.nuevo_desafio_arcade)

    def renderizar_grafica(self, num_dedos):
        try:
            expr = self.entry_func.get().strip()
            a_str = self.entry_a.get().strip()
            b_str = self.entry_b.get().strip()

            motor = MotorCalculo(expr, a_str, b_str)
            titulo, valor, unidad, formula = motor.ejecutar_calculo(num_dedos)

            self.lbl_resultado_val.configure(text=f"{titulo}: {valor:.4f} {unidad}")

            if self.modo_juego == "Exploración":
                hablar_en_segundo_plano(f"{titulo}. {valor:.2f} {unidad}")

            self.fig.clear()

            if num_dedos in [1, 5]:
                ax = self.fig.add_subplot(111)
                ax.set_facecolor('#14151a')
                x = np.linspace(motor.a - 0.5, motor.b + 0.5, 200)
                y = motor.f(x)
                ax.plot(x, y, color="#00adb5", linewidth=2.5)

                x_fill = np.linspace(motor.a, motor.b, 100)
                y_fill = motor.f(x_fill)

                if num_dedos == 1:
                    ax.fill_between(x_fill, y_fill, color="#00adb5", alpha=0.4)
                elif num_dedos == 5:
                    ax.plot(x_fill, y_fill, color="#ff0055", linewidth=4)

                ax.grid(True, color='#222530', linestyle='--')
                ax.tick_params(colors='#9094a6', labelsize=8)

            elif num_dedos in [2, 3, 4]:
                ax = self.fig.add_subplot(111, projection='3d')
                ax.set_facecolor('#14151a')
                x = np.linspace(motor.a, motor.b, 40)
                theta = np.linspace(0, 2 * np.pi, 40)
                X, Theta = np.meshgrid(x, theta)
                R = motor.f(X)

                if num_dedos in [2, 4]:
                    Y = R * np.cos(Theta)
                    Z = R * np.sin(Theta)
                    ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.85)
                elif num_dedos == 3:
                    Y_mesh = R
                    X_mesh = X * np.cos(Theta)
                    Z_mesh = X * np.sin(Theta)
                    ax.plot_surface(X_mesh, Y_mesh, Z_mesh, cmap="plasma", alpha=0.85)

                ax.tick_params(colors='#9094a6', labelsize=8)

            self.fig.tight_layout()
            self.canvas.draw()

        except Exception:
            self.lbl_resultado_val.configure(text="Error de parámetros")

    def actualizar_video(self):
        ret, raw_frame = self.cap.read()
        modo_man = self.selector_manual.get()

        if ret:
            raw_frame = cv2.flip(raw_frame, 1)

            # 1. Crear Lienzo Ciberespacio Oscuro (280x210 px)
            canvas_cam = np.full((210, 280, 3), (24, 19, 18), dtype=np.uint8)

            if modo_man == "Cámara":
                frame_resized = cv2.resize(raw_frame, (280, 210))
                
                # Desempaquetado correcto de la tupla de cvzone: (manos, imagen)
                hands, _ = self.detector.findHands(frame_resized, draw=False)
                num_dedos = 0
                yemas = []

                if hands:
                    mano = hands[0]
                    dedos = self.detector.fingersUp(mano)
                    num_dedos = dedos.count(1)

                    lmList = mano['lmList']  # Puntos 3D/2D de la mano
                    yemas_indices = [4, 8, 12, 16, 20]
                    yemas = [(lmList[i][0], lmList[i][1]) for i in yemas_indices]

                    # 2. Dibujar Conexiones Neón del Ciber-Esqueleto
                    for start_idx, end_idx in CONEXIONES_MANO:
                        p1 = (lmList[start_idx][0], lmList[start_idx][1])
                        p2 = (lmList[end_idx][0], lmList[end_idx][1])
                        # Línea exterior resplandeciente
                        cv2.line(canvas_cam, p1, p2, (185, 173, 0), 3, cv2.LINE_AA)
                        # Núcleo brillante
                        cv2.line(canvas_cam, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

                    # 3. Dibujar Puntos/Nodos de Articulaciones
                    for idx, point in enumerate(lmList):
                        p = (point[0], point[1])
                        if idx in yemas_indices:
                            # Nodos de las yemas (Brillo dorado/amarillo)
                            cv2.circle(canvas_cam, p, 6, (3, 183, 255), -1, cv2.LINE_AA)
                            cv2.circle(canvas_cam, p, 3, (255, 255, 255), -1, cv2.LINE_AA)
                        else:
                            # Nodos articulares (Cian)
                            cv2.circle(canvas_cam, p, 4, (185, 173, 0), -1, cv2.LINE_AA)
                            cv2.circle(canvas_cam, p, 2, (255, 255, 255), -1, cv2.LINE_AA)

                # 4. Actualizar partículas de fondo y conectar con yemas
                self.sistema_particulas.actualizar_y_dibujar(canvas_cam, yemas)

                self.label_gesto.configure(text=f"Detección en vivo: {num_dedos} Dedo(s)")

                if num_dedos in [1, 2, 3, 4, 5]:
                    if self.modo_juego == "Exploración":
                        if num_dedos != self.dedos_previos:
                            self.dedos_previos = num_dedos
                            self.renderizar_grafica(num_dedos)
                    elif self.modo_juego == "Arcade" and self.juego_activo:
                        self.evaluar_respuesta_arcade(num_dedos)
            else:
                self.sistema_particulas.actualizar_y_dibujar(canvas_cam)

            img_pil = Image.fromarray(cv2.cvtColor(canvas_cam, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(280, 210))
            self.label_camara.configure(image=ctk_img)
            self.label_camara.image = ctk_img

        self.after(15, self.actualizar_video)

    def on_closing(self):
        self.cap.release()
        self.destroy()


if __name__ == "__main__":
    app = AppCalculoIntegral()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()