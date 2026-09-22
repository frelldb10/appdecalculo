import streamlit as st
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad
import sympy as sp
from cvzone.HandTrackingModule import HandDetector
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
import av
import random
import math

# Configuración de página full-width
st.set_page_config(
    page_title="Cálculo Integral en Movimiento — Cyber Dashboard",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS para calcar el diseño de CustomTkinter
st.markdown("""
    <style>
    /* Ocultar barra superior y menús por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    
    /* Fondo principal y reset de márgenes */
    body, .stApp {
        background-color: #121318 !important;
        color: #ffffff;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Encabezado Neón */
    .header-bar {
        background-color: #1c1e26;
        padding: 10px 20px;
        border-radius: 12px;
        border: 1px solid #2e3240;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }

    /* Estilos de botones e inputs */
    .stButton>button {
        background-color: #252834;
        color: #ffffff;
        border: 1px solid #2e3240;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #00adb5;
        color: #121318;
    }

    /* Limitar tamaño del video WebRTC */
    div[data-testid="stWebrtc"] {
        max-width: 280px !important;
        margin: 0 auto;
    }
    div[data-testid="stWebrtc"] video {
        width: 280px !important;
        height: 210px !important;
        border-radius: 10px !important;
        border: 1px solid #00adb5 !important;
    }

    /* Ocultar etiquetas sobrantes */
    label { font-size: 0.82rem !important; color: #9094a6 !important; }
    </style>
""", unsafe_allow_html=True)

# Presets Industriales
CASOS_INDUSTRIALES = {
    "🛠️ Personalizado": {"func": "x**2", "a": "0.0", "b": "2.0", "desc": "Modo de libre edición matemática."},
    "🏭 Tasa de Producción (Piezas/Hora)": {"func": "100 + 15*x - 2*x**2", "a": "0.0", "b": "8.0", "desc": "Turno de 8h. 1 dedo calcula las piezas totales producidas."},
    "🛢️ Tanque / Silo Cilíndrico": {"func": "sqrt(4 - x)", "a": "0.0", "b": "4.0", "desc": "Perfil de depósito. 2 y 3 dedos calculan volumen en 3D."},
    "📦 Banda Transportadora Curva": {"func": "sin(x) + 2", "a": "0.0", "b": "6.28", "desc": "Ruta de faja de ensamble. 5 dedos calcula los metros de banda."}
}

CONEXIONES_MANO = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12), (5, 9),
    (13, 14), (14, 15), (15, 16), (9, 13),
    (17, 18), (18, 19), (19, 20), (13, 17), (0, 17)
]

detector = HandDetector(maxHands=1, detectionCon=0.7)

# Procesador de Video para generar el Lienzo Ciberespacio
class CyberVideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.num_dedos = 0
        self.particulas = [
            [random.randint(0, 280), random.randint(0, 210), random.uniform(-1.2, 1.2), random.uniform(-1.2, 1.2), random.randint(1, 2)]
            for _ in range(30)
        ]

    def recv(self, frame):
        raw_frame = frame.to_ndarray(format="bgr24")
        raw_frame = cv2.flip(raw_frame, 1)
        frame_resized = cv2.resize(raw_frame, (280, 210))

        # Canvas Oscuro
        canvas_cam = np.full((210, 280, 3), (24, 19, 18), dtype=np.uint8)

        hands, _ = detector.findHands(frame_resized, draw=False)
        yemas = []

        if hands:
            mano = hands[0]
            dedos = detector.fingersUp(mano)
            self.num_dedos = dedos.count(1)
            lmList = mano['lmList']
            yemas = [(lmList[i][0], lmList[i][1]) for i in [4, 8, 12, 16, 20]]

            # Esqueleto Ciberespacio
            for s, e in CONEXIONES_MANO:
                p1 = (lmList[s][0], lmList[s][1])
                p2 = (lmList[e][0], lmList[e][1])
                cv2.line(canvas_cam, p1, p2, (185, 173, 0), 2, cv2.LINE_AA)
                cv2.line(canvas_cam, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

            for idx, pt in enumerate(lmList):
                p = (pt[0], pt[1])
                if idx in [4, 8, 12, 16, 20]:
                    cv2.circle(canvas_cam, p, 5, (3, 183, 255), -1)
                else:
                    cv2.circle(canvas_cam, p, 3, (185, 173, 0), -1)
        else:
            self.num_dedos = 0

        # Mover Partículas
        for p in self.particulas:
            p[0] += p[2]
            p[1] += p[3]
            if p[0] <= 0 or p[0] >= 280: p[2] *= -1
            if p[1] <= 0 or p[1] >= 210: p[3] *= -1
            cv2.circle(canvas_cam, (int(p[0]), int(p[1])), p[4], (181, 173, 0), -1)

        return av.VideoFrame.from_ndarray(canvas_cam, format="bgr24")


# 1. HEADER SUPERIOR
h_col1, h_col2, h_col3 = st.columns([3, 1, 1])
with h_col1:
    st.markdown("<h3 style='margin:0; color:#ffffff;'>📐 CÁLCULO INTEGRAL EN MOVIMIENTO</h3>", unsafe_allow_html=True)
with h_col2:
    st.markdown("<p style='text-align:right; color:#ff5555; font-weight:bold; margin:0;'>🔥 RACHA: x0</p>", unsafe_allow_html=True)
with h_col3:
    st.markdown("<p style='text-align:right; color:#ffb703; font-weight:bold; margin:0;'>🏆 PUNTOS: 0</p>", unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid #2e3240; margin-top:5px; margin-bottom:15px;'>", unsafe_allow_html=True)

# 2. CUERPO EN DOS COLUMNAS
col_left, col_right = st.columns([1, 2.2])

with col_left:
    # CARD 1: Modalidad y Selector
    with st.container():
        st.markdown("<h5 style='color:#00adb5; margin-bottom:5px;'>🕹️ MODALIDAD Y CONTROL MANUAL</h5>", unsafe_allow_html=True)
        modo_manual = st.radio(
            "Selección manual:",
            [0, 1, 2, 3, 4, 5],
            format_func=lambda x: "Cámara" if x == 0 else f"{x}",
            horizontal=True,
            label_visibility="collapsed"
        )

    # CARD 2: Aplicación Industrial
    with st.container():
        st.markdown("<h5 style='color:#00adb5; margin-top:10px; margin-bottom:5px;'>⚙ APLICACIÓN INDUSTRIAL</h5>", unsafe_allow_html=True)
        preset_name = st.selectbox("Preset:", list(CASOS_INDUSTRIALES.keys()), label_visibility="collapsed")
        preset_data = CASOS_INDUSTRIALES[preset_name]

        func_input = st.text_input("Función f(x):", value=preset_data["func"])
        c_a, c_b = st.columns(2)
        a_val = c_a.text_input("a:", value=preset_data["a"])
        b_val = c_b.text_input("b:", value=preset_data["b"])
        st.button("Recalcular", use_container_width=True)

    # CARD 3: Recuadro Cámara
    with st.container():
        ctx = webrtc_streamer(
            key="gesture-cyber",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=CyberVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

        num_detectado = 0
        if ctx.video_processor:
            num_detectado = ctx.video_processor.num_dedos

        st.markdown(f"<p style='text-align:center; font-weight:bold; color:#ffffff; margin-top:5px;'>Detección en vivo: {num_detectado if modo_manual == 0 else modo_manual} Dedo(s)</p>", unsafe_allow_html=True)

# Determinar cuál dedo está activo
gesto_activo = modo_manual if modo_manual != 0 else (num_detectado if num_detectado in [1, 2, 3, 4, 5] else 2)

with col_right:
    # CARD HERO
    st.markdown("<h5 style='color:#00adb5; margin-bottom:2px;'>MODO LIBRE: MUESTRE DE 1 A 5 DEDOS</h5>", unsafe_allow_html=True)
    st.markdown("<div style='background-color:#ffb703; height:3px; width:100%; margin-bottom:10px;'></div>", unsafe_allow_html=True)

    # Motor Matemático
    try:
        a_f = float(a_val)
        b_f = float(b_val)
        x_sym = sp.Symbol('x')
        expr = sp.sympify(func_input)
        f_num = sp.lambdify(x_sym, expr, "numpy")
        df_expr = sp.diff(expr, x_sym)
        df_num = sp.lambdify(x_sym, df_expr, "numpy")

        if gesto_activo == 1:
            val, _ = quad(f_num, a_f, b_f)
            titulo, unidad = "Área Bajo la Curva", "unidades cuadradas"
        elif gesto_activo == 2:
            val, _ = quad(lambda x: np.pi * (f_num(x) ** 2), a_f, b_f)
            titulo, unidad = "Volumen Sólido Eje X", "unidades cúbicas"
        elif gesto_activo == 3:
            val, _ = quad(lambda x: 2 * np.pi * x * f_num(x), a_f, b_f)
            titulo, unidad = "Volumen Sólido Eje Y", "unidades cúbicas"
        elif gesto_activo == 4:
            val, _ = quad(lambda x: 2 * np.pi * np.abs(f_num(x)) * np.sqrt(1 + (df_num(x) ** 2)), a_f, b_f)
            titulo, unidad = "Área Superficial 3D", "unidades cuadradas"
        elif gesto_activo == 5:
            val, _ = quad(lambda x: np.sqrt(1 + (df_num(x) ** 2)), a_f, b_f)
            titulo, unidad = "Longitud de Arco", "unidades"

        st.markdown(f"<h3 style='color:#ffffff; margin:0;'>{titulo}: {val:.4f} {unidad}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#9094a6; font-size:0.85rem;'>{preset_data['desc']}</p>", unsafe_allow_html=True)

        # Gráfica Matplotlib 3D/2D
        fig = plt.figure(figsize=(7, 4.8), dpi=100)
        fig.patch.set_facecolor('#1c1e26')

        if gesto_activo in [1, 5]:
            ax = fig.add_subplot(111)
            ax.set_facecolor('#14151a')
            x = np.linspace(a_f - 0.5, b_f + 0.5, 200)
            ax.plot(x, f_num(x), color="#00adb5", linewidth=2.5)
            x_fill = np.linspace(a_f, b_f, 100)
            if gesto_activo == 1:
                ax.fill_between(x_fill, f_num(x_fill), color="#00adb5", alpha=0.4)
            else:
                ax.plot(x_fill, f_num(x_fill), color="#ff0055", linewidth=4)
            ax.grid(True, color='#222530', linestyle='--')
            ax.tick_params(colors='#9094a6', labelsize=8)

        elif gesto_activo in [2, 3, 4]:
            ax = fig.add_subplot(111, projection='3d')
            ax.set_facecolor('#14151a')
            x = np.linspace(a_f, b_f, 40)
            theta = np.linspace(0, 2 * np.pi, 40)
            X, Theta = np.meshgrid(x, theta)
            R = f_num(X)

            if gesto_activo in [2, 4]:
                Y, Z = R * np.cos(Theta), R * np.sin(Theta)
                ax.plot_surface(X, Y, Z, cmap="viridis" if gesto_activo == 2 else "magma", alpha=0.85)
            elif gesto_activo == 3:
                Y_mesh, X_mesh, Z_mesh = R, X * np.cos(Theta), X * np.sin(Theta)
                ax.plot_surface(X_mesh, Y_mesh, Z_mesh, cmap="plasma", alpha=0.85)

            ax.tick_params(colors='#9094a6', labelsize=8)

        fig.tight_layout()
        st.pyplot(fig)

    except Exception as e:
        st.error("Error en el cálculo numérico o parámetros.")