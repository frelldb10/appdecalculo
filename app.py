import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad
import sympy as sp

# Configuración de página
st.set_page_config(page_title="Cálculo Integral en Movimiento", page_icon="📐", layout="wide")

# Estilos Neón / Dark Mode
st.markdown("""
    <style>
    .stApp { background-color: #121318; color: #ffffff; }
    h1, h2, h3 { color: #00adb5 !important; }
    .stButton>button { background-color: #00adb5; color: #121318; font-weight: bold; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Presets de Ingeniería Industrial
CASOS_INDUSTRIALES = {
    "🛠️ Personalizado": {"func": "x**2", "a": "0.0", "b": "2.0", "desc": "Modo de libre edición matemática."},
    "🏭 Tasa de Producción (Piezas/Hora)": {"func": "100 + 15*x - 2*x**2", "a": "0.0", "b": "8.0", "desc": "Turno de 8h. 1 dedo calcula las piezas totales producidas."},
    "🛢️ Tanque / Silo Cilíndrico": {"func": "sqrt(4 - x)", "a": "0.0", "b": "4.0", "desc": "Perfil de depósito. 2 y 3 dedos calculan volumen de capacidad en 3D."},
    "📦 Banda Transportadora Curva": {"func": "sin(x) + 2", "a": "0.0", "b": "6.28", "desc": "Ruta de faja de ensamble. 5 dedos calcula los metros de banda requeridos."}
}

# Sidebar / Panel Izquierdo
st.sidebar.title("⚙️ Control del Modelo")

preset_name = st.sidebar.selectbox("Aplicación Industrial (Preset):", list(CASOS_INDUSTRIALES.keys()))
preset_data = CASOS_INDUSTRIALES[preset_name]

func_input = st.sidebar.text_input("Función f(x):", value=preset_data["func"])
col1, col2 = st.sidebar.columns(2)
a_val = col1.number_input("Límite a:", value=float(preset_data["a"]))
b_val = col2.number_input("Límite b:", value=float(preset_data["b"]))

modo_gesto = st.sidebar.radio(
    "Seleccionar Gesto (Cálculo):",
    [
        "☝️ 1 Dedo — Área Bajo la Curva (2D)",
        "✌️ 2 Dedos — Volumen Eje X (3D Discos)",
        "🤟 3 Dedos — Volumen Eje Y (3D Capas)",
        "🖖 4 Dedos — Área Superficial (3D)",
        "🖐️ 5 Dedos — Longitud de Arco (2D)"
    ]
)

gesto_num = int(modo_gesto[0]) if modo_gesto[0].isdigit() else 1

# Motor Matemático
x_sym = sp.Symbol('x')
try:
    expr = sp.sympify(func_input)
    f_num = sp.lambdify(x_sym, expr, "numpy")
    df_expr = sp.diff(expr, x_sym)
    df_num = sp.lambdify(x_sym, df_expr, "numpy")
    valida = True
except Exception as e:
    st.error(f"Error en la fórmula ingresada: {e}")
    valida = False

# Panel Principal
st.title("📐 CÁLCULO INTEGRAL EN MOVIMIENTO")
st.caption(f"Contexto Industrial: {preset_data['desc']}")

if valida:
    if gesto_num == 1:
        val, _ = quad(f_num, a_val, b_val)
        st.subheader("Área Bajo la Curva")
        st.metric("Resultado", f"{val:.4f} u²")
        st.latex(r"A = \int_{a}^{b} f(x) \, dx")

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#1c1e26')
        ax.set_facecolor('#14151a')
        
        x = np.linspace(a_val - 0.5, b_val + 0.5, 200)
        ax.plot(x, f_num(x), color="#00adb5", linewidth=2.5)
        x_fill = np.linspace(a_val, b_val, 100)
        ax.fill_between(x_fill, f_num(x_fill), color="#00adb5", alpha=0.4)
        ax.tick_params(colors='#9094a6')
        ax.grid(True, color='#222530', linestyle='--')
        st.pyplot(fig)

    elif gesto_num in [2, 3, 4]:
        fig = plt.figure(figsize=(8, 5))
        fig.patch.set_facecolor('#1c1e26')
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('#14151a')

        x = np.linspace(a_val, b_val, 40)
        theta = np.linspace(0, 2 * np.pi, 40)
        X, Theta = np.meshgrid(x, theta)
        R = f_num(X)

        if gesto_num == 2: # Volumen X
            f_vol = lambda x_val: np.pi * (f_num(x_val) ** 2)
            val, _ = quad(f_vol, a_val, b_val)
            st.subheader("Volumen Sólido de Revolución (Eje X)")
            st.metric("Resultado", f"{val:.4f} u³")
            st.latex(r"V = \pi \int_{a}^{b} [f(x)]^2 \, dx")

            Y, Z = R * np.cos(Theta), R * np.sin(Theta)
            ax.plot_surface(X, Y, Z, cmap="viridis", alpha=0.85)

        elif gesto_num == 3: # Volumen Y
            f_vol_y = lambda x_val: 2 * np.pi * x_val * f_num(x_val)
            val, _ = quad(f_vol_y, a_val, b_val)
            st.subheader("Volumen Sólido de Revolución (Eje Y)")
            st.metric("Resultado", f"{val:.4f} u³")
            st.latex(r"V = 2\pi \int_{a}^{b} x \cdot f(x) \, dx")

            Y_mesh, X_mesh, Z_mesh = R, X * np.cos(Theta), X * np.sin(Theta)
            ax.plot_surface(X_mesh, Y_mesh, Z_mesh, cmap="plasma", alpha=0.85)

        elif gesto_num == 4: # Área Superficial
            f_surf = lambda x_val: 2 * np.pi * np.abs(f_num(x_val)) * np.sqrt(1 + (df_num(x_val) ** 2))
            val, _ = quad(f_surf, a_val, b_val)
            st.subheader("Área de la Superficie 3D")
            st.metric("Resultado", f"{val:.4f} u²")
            st.latex(r"S = 2\pi \int_{a}^{b} f(x) \sqrt{1 + [f'(x)]^2} \, dx")

            Y, Z = R * np.cos(Theta), R * np.sin(Theta)
            ax.plot_surface(X, Y, Z, cmap="magma", alpha=0.85)

        ax.tick_params(colors='#9094a6', labelsize=8)
        st.pyplot(fig)

    elif gesto_num == 5:
        f_arc = lambda x_val: np.sqrt(1 + (df_num(x_val) ** 2))
        val, _ = quad(f_arc, a_val, b_val)
        st.subheader("Longitud de Arco")
        st.metric("Resultado", f"{val:.4f} u")
        st.latex(r"L = \int_{a}^{b} \sqrt{1 + [f'(x)]^2} \, dx")

        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#1c1e26')
        ax.set_facecolor('#14151a')
        
        x = np.linspace(a_val - 0.5, b_val + 0.5, 200)
        ax.plot(x, f_num(x), color="#00adb5", linewidth=2)
        x_arc = np.linspace(a_val, b_val, 100)
        ax.plot(x_arc, f_num(x_arc), color="#ff0055", linewidth=4, label="Longitud de Arco")
        ax.legend(facecolor='#1c1e26', edgecolor='#2e3240', labelcolor='#ffffff')
        ax.tick_params(colors='#9094a6')
        ax.grid(True, color='#222530', linestyle='--')
        st.pyplot(fig)