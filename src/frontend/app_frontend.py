import streamlit as st
import pandas as pd
from datetime import datetime

import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)



from src.vision.detectar_producto import detectar_producto
from src.backend.registrar_movimiento import registrar_movimiento
from src.backend.obtener_historial import obtener_historial
from src.backend.graficas import generar_reportes



st.set_page_config(page_title="Inventorix AI", page_icon="📦", layout="wide")

if "producto_detectado" not in st.session_state:
    st.session_state.producto_detectado = None 

if "registro_en_progreso" not in st.session_state:
    st.session_state.registro_en_progreso = False

if "escaneo_en_progreso" not in st.session_state:
    st.session_state.escaneo_en_progreso = False

if "ultimo_registro" not in st.session_state:
    st.session_state.ultimo_registro = None


# -------------------- HEADER --------------------
st.title("📦 Inventorix AI")
st.write("Gestión inteligente de inventario con visión artificial (YOLO) y analítica.")

tab_escaneo, tab_analisis, tab_reportes = st.tabs(["Escaneo y registro", "Análisis", "Reportes"])


# =========================================================
# TAB 1: ESCANEO Y REGISTRO
# =========================================================
with tab_escaneo:
    st.subheader("👋 Bienvenido")

    st.info(
        "1) Presiona **Iniciar escaneo (YOLO)**\n"
        "2) Se abrirá una **ventana nueva** con la cámara (OpenCV)\n"
        "3) Cuando detecte un producto del inventario, se cerrará y volverá aquí\n"
        "4) Registras cantidad y entrada/salida\n"
    )

    # Si no hay registro en progreso, se permiteReconnecta escaneo
    colA, colB = st.columns([1, 1])

    with colA:
        iniciar = st.button("▶️ Iniciar escaneo (YOLO)", disabled=st.session_state.registro_en_progreso)

    with colB:
        cancelar = st.button("❌ Cancelar registro", disabled=not st.session_state.registro_en_progreso)

    if cancelar:
        st.session_state.producto_detectado = None
        st.session_state.registro_en_progreso = False
        st.session_state.escaneo_en_progreso = False
        st.session_state.ultimo_registro = None
        st.success("Registro cancelado.")
        st.rerun()

    # ---------- BOTÓN ESCANEO ----------
    if iniciar:
        st.session_state.escaneo_en_progreso = True
        st.warning("Se abrirá una ventana de cámara. Para salir manualmente, presiona 'q' en la ventana.")

        # Llama a la función que abre cámara + YOLO + ventana
        producto = detectar_producto()  # retorna dict de inventario.json o None

        st.session_state.escaneo_en_progreso = False

        if producto is None:
            st.error("No se detectó ningún producto válido del inventario.")
        else:
            st.session_state.producto_detectado = producto
            st.session_state.registro_en_progreso = True
            st.success(f"Producto detectado: {producto.get('name')}")

        st.rerun()

    # ---------- FORMULARIO REGISTRO ----------
    if st.session_state.registro_en_progreso and st.session_state.producto_detectado is not None:
        prod = st.session_state.producto_detectado

        st.markdown("### 🧾 Producto detectado")
        st.write(f"**ID:** {prod.get('product_id')}")
        st.write(f"**Nombre:** {prod.get('name')}")
        st.write(f"**Categoría:** {prod.get('category')}")
        st.write(f"**Precio Unitario:** {prod.get('price')}")
        st.write(f"**Stock actual:** {prod.get('stock')}")
        st.write(f"**Stock mínimo:** {prod.get('minimum_stock')}")

        st.markdown("---")
        st.markdown("### ✏️ Registrar movimiento")

        tipo = st.radio("Tipo de movimiento", ["Entrada", "Salida"], horizontal=True)
        cantidad = st.number_input("Cantidad", min_value=1, step=1, value=1)

        if st.button("💾 Guardar registro"):
            # Llama al backend
            resp = registrar_movimiento(
                product_id=int(prod["product_id"]),
                cantidad=int(cantidad),
                tipo_movimiento=tipo.lower()  # "entrada" o "salida"
            )

            if isinstance(resp, dict) and resp.get("error"):
                st.error(resp["error"])
            else:
                st.session_state.ultimo_registro = resp
                st.session_state.producto_detectado = None
                st.session_state.registro_en_progreso = False
                st.success("Registro guardado correctamente.")
                st.rerun()

    # ---------- ÚLTIMO REGISTRO ----------
    if st.session_state.ultimo_registro is not None:
        st.markdown("---")
        st.markdown("### ✅ Último registro guardado")
        st.json(st.session_state.ultimo_registro)


# =========================================================
# TAB 2: ANÁLISIS GRÁFICO
# =========================================================
with tab_analisis:
    st.subheader("📈 Análisis gráfico")

    # Bloqueo según tu regla: si hay escaneo o registro activo, no permitir análisis
    if st.session_state.escaneo_en_progreso or st.session_state.registro_en_progreso:
        st.warning(
            "El análisis está deshabilitado mientras haya un escaneo o un registro en curso.\n\n"
            "Termina o cancela el registro en la pestaña **Escaneo y registro**."
        )
    else:
        # Cargar historial desde backend
        df_hist = obtener_historial()

        if df_hist is None or len(df_hist) == 0:
            st.info("No hay historial aún.")
        else:
            st.markdown("#### 🧾 Historial (JSON → DataFrame)")
            st.dataframe(df_hist, use_container_width=True)

            # Selector de producto
            if "product_name" in df_hist.columns:
                productos = sorted(df_hist["product_name"].dropna().unique().tolist())
                prod_sel = st.selectbox("Selecciona producto a analizar:", productos)
                df_prod = df_hist[df_hist["product_name"] == prod_sel].copy()
            else:
                st.info("No existe la columna 'product_name' en el historial.")
                df_prod = df_hist.copy()

            # Tendencia (date+time)
            if "date" in df_prod.columns and "time" in df_prod.columns:
                df_prod["Fecha_Hora"] = pd.to_datetime(df_prod["date"] + " " + df_prod["time"], errors="coerce")
                df_prod = df_prod.dropna(subset=["Fecha_Hora"]).sort_values("Fecha_Hora")
                st.markdown("#### 📉 Tendencia (Cantidad vs Fecha/Hora)")
                st.line_chart(df_prod, x="Fecha_Hora", y="quantity")
            else:
                st.info("No existen columnas 'date' y 'time' para construir tendencia.")

            # Top ventas simple (suma de quantity)
            if "product_name" in df_hist.columns and "quantity" in df_hist.columns:
                st.markdown("#### 🏆 Productos con más movimiento (cantidad total)")
                top = df_hist.groupby("product_name")["quantity"].sum().sort_values(ascending=False).reset_index()
                st.bar_chart(top, x="product_name", y="quantity")


with tab_reportes:
    st.subheader("📊 Reportes (Plotly)")

    # Regla: no permitir reportes si hay escaneo o registro activo
    if st.session_state.escaneo_en_progreso or st.session_state.registro_en_progreso:
        st.warning("Termina o cancela el escaneo/registro para habilitar los reportes.")
    else:
        if st.button("📌 Generar reportes"):
            df_rep, figs = generar_reportes()

            st.markdown("### 🧾 DataFrame estandarizado")
            st.dataframe(df_rep, use_container_width=True)

            st.markdown("### 📈 Gráficas")
            st.plotly_chart(figs["fig1_ranking_ventas"], use_container_width=True)
            st.plotly_chart(figs["fig2_alerta_stock"], use_container_width=True)
            st.plotly_chart(figs["fig3_heatmap"], use_container_width=True)
            st.plotly_chart(figs["fig4_cuadrante"], use_container_width=True)
            st.plotly_chart(figs["fig5_sunburst"], use_container_width=True)
            st.plotly_chart(figs["fig6_pareto"], use_container_width=True)
            st.plotly_chart(figs["fig7_riesgo"], use_container_width=True)
