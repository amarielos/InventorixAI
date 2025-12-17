import os, sys
import json
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.vision.detectar_producto import detectar_producto
from src.backend.registrar_movimiento import registrar_movimiento
from src.backend.obtener_historial import obtener_historial
from src.backend.graficas import generar_reportes, recalcular_figuras, recalcular_kpis

from src.analytics.anomalias import detectar_movimientos_extranos, resumen_anomalias

from src.frontend.styles import inject_corporate_css
from src.frontend.ui_components import (
    set_page, card, toast_ok, kpi_row, fmt_now
)

# -------------------------
# Configuración general
# -------------------------
st.set_page_config(page_title="Inventorix AI", page_icon="📦", layout="wide")
inject_corporate_css()

ANOM_PATH = Path("data/anomalias.json")


def guardar_anomalias_historico(registros_anomalias: list[dict]) -> int:
    """
    Guarda anomalías en data/anomalias.json evitando duplicados simples.
    """
    ANOM_PATH.parent.mkdir(parents=True, exist_ok=True)

    if ANOM_PATH.exists():
        try:
            prev = json.loads(ANOM_PATH.read_text(encoding="utf-8"))
            if not isinstance(prev, list):
                prev = []
        except Exception:
            prev = []
    else:
        prev = []

    seen = set()
    for x in prev:
        key = (x.get("product_id"), x.get("Fecha_Hora"), x.get("movement_type"), x.get("quantity"))
        seen.add(key)

    nuevos = []
    for r in registros_anomalias:
        key = (r.get("product_id"), r.get("Fecha_Hora"), r.get("movement_type"), r.get("quantity"))
        if key in seen:
            continue
        nuevos.append(r)

    merged = prev + nuevos
    ANOM_PATH.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(nuevos)


# -------------------- STATE --------------------
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "producto_detectado" not in st.session_state:
    st.session_state.producto_detectado = None

if "registro_en_progreso" not in st.session_state:
    st.session_state.registro_en_progreso = False

if "escaneo_en_progreso" not in st.session_state:
    st.session_state.escaneo_en_progreso = False

if "ultimo_registro" not in st.session_state:
    st.session_state.ultimo_registro = None

# --- Fix del diálogo de guardado (para que NO bloquee el guardado) ---
if "show_save_dialog" not in st.session_state:
    st.session_state.show_save_dialog = False

if "save_dialog_data" not in st.session_state:
    st.session_state.save_dialog_data = None

# --- Alertas IA cache ---
if "df_anom" not in st.session_state:
    st.session_state.df_anom = None

if "anom_last_contamination" not in st.session_state:
    st.session_state.anom_last_contamination = 0.15


# -------------------- DIÁLOGO GLOBAL: Registro guardado --------------------
# Nota: El registro YA fue guardado antes de abrir esto.
if st.session_state.show_save_dialog and st.session_state.save_dialog_data:
    data = st.session_state.save_dialog_data

    @st.dialog("✅ Registro guardado")
    def _saved_dialog():
        st.write("El movimiento se guardó correctamente.")
        st.write(f"**Producto:** {data.get('product_name')}")
        st.write(f"**Movimiento:** {data.get('movement_type')}")
        st.write(f"**Cantidad:** {data.get('quantity')}")
        st.write(f"**Stock después:** {data.get('stock_after')}")

        st.divider()
        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("✅ Confirmar / Cerrar", use_container_width=True):
                st.session_state.show_save_dialog = False
                st.session_state.save_dialog_data = None
                st.rerun()

        with c2:
            if st.button("📊 Ir a Reportes", use_container_width=True):
                st.session_state.show_save_dialog = False
                st.session_state.save_dialog_data = None
                st.session_state.page = "Reportes"
                st.rerun()

        with c3:
            if st.button("🤖 Ir a Alertas IA", use_container_width=True):
                st.session_state.show_save_dialog = False
                st.session_state.save_dialog_data = None
                st.session_state.page = "Alertas IA"
                st.rerun()

    _saved_dialog()


# -------------------- SIDEBAR NAV --------------------
with st.sidebar:
    st.markdown("## 📦 Inventorix AI")
    st.caption("Inventario con visión artificial + analítica")
    st.divider()

    page = st.radio(
        "Navegación",
        ["Dashboard", "Escaneo", "Reportes", "Alertas IA"],
        index=["Dashboard", "Escaneo", "Reportes", "Alertas IA"].index(st.session_state.page),
    )
    if page != st.session_state.page:
        st.session_state.page = page

    st.divider()
    st.caption("Estado")
    st.write("Escaneo:", "🟢" if st.session_state.escaneo_en_progreso else "⚪")
    st.write("Registro:", "🟢" if st.session_state.registro_en_progreso else "⚪")


# -------------------- HEADER --------------------
st.markdown("# 📦 Inventorix AI")
st.caption("Interfaz corporativa • Flujo guiado • Acciones rápidas")


# =========================================================
# PAGE: DASHBOARD
# =========================================================
if st.session_state.page == "Dashboard":
    col1, col2 = st.columns([1.2, 1])

    with col1:
        card(
            "Resumen",
            "Identifique productos con cámara (YOLO), registre entradas/salidas y obtenga reportes y alertas para decisiones."
        )
        st.write("")
        kpi_row([
            ("Fecha/Hora", fmt_now()),
            ("Modo", "Local (OpenCV)"),
            ("Estado", "Listo ✅" if not st.session_state.registro_en_progreso else "En registro…"),
        ])

        st.write("")
        st.markdown("### Acciones rápidas")
        a, b, c = st.columns(3)
        with a:
            st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
            st.button("▶️ Ir a Escaneo", on_click=set_page, args=("Escaneo",), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with b:
            st.button("📊 Ver Reportes", on_click=set_page, args=("Reportes",), use_container_width=True)
        with c:
            st.button("🤖 Ver Alertas IA", on_click=set_page, args=("Alertas IA",), use_container_width=True)

    with col2:
        st.markdown("### Último registro")
        if st.session_state.ultimo_registro:
            r = st.session_state.ultimo_registro
            card(
                "Registro guardado",
                f"Producto: {r.get('product_name')} • Movimiento: {r.get('movement_type')} • Cantidad: {r.get('quantity')} • Stock después: {r.get('stock_after')}"
            )
        else:
            card("Sin registros aún", "Realiza un escaneo y guarda un movimiento para ver actividad aquí.")


# =========================================================
# PAGE: ESCANEO (YOLO + Registro)
# =========================================================
elif st.session_state.page == "Escaneo":
    st.markdown("## 🎥 Escaneo y registro")
    st.info(
        "1) Presiona **Iniciar escaneo (YOLO)**\n"
        "2) Se abrirá una **ventana nueva** con la cámara\n"
        "3) Selecciona **Entrada / Salida** en la ventana\n"
        "4) El registro se guardará automáticamente\n"
    )

    st.write("")
    topA, topB, topC = st.columns([1.1, 1.1, 1])

    with topA:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        iniciar = st.button(
            "▶️ Iniciar escaneo (YOLO)",
            disabled=st.session_state.escaneo_en_progreso,
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with topB:
        cancelar = st.button(
            "⛔ Cancelar",
            disabled=not st.session_state.escaneo_en_progreso,
            use_container_width=True
        )

    with topC:
        st.button(
            "📊 Ir a Reportes",
            on_click=set_page,
            args=("Reportes",),
            use_container_width=True
        )

    # -------------------- CANCELAR --------------------
    if cancelar:
        st.session_state.escaneo_en_progreso = False
        st.session_state.ultimo_registro = None
        toast_ok("Escaneo cancelado.")
        st.rerun()

    # -------------------- INICIAR ESCANEO --------------------
    if iniciar:
        st.session_state.escaneo_en_progreso = True
        st.info(
            "Se abrirá una ventana nueva.\n"
            "Usa **Entrada / Salida** o teclas **E / S**.\n"
            "Presiona **Q** para cancelar."
        )

        resultado = detectar_producto()

        st.session_state.escaneo_en_progreso = False

        if resultado is None:
            st.warning("Escaneo cancelado o sin detección válida.")
        else:
            prod = resultado["producto"]
            cantidad = resultado["cantidad"]
            tipo = resultado["tipo"]

            resp = registrar_movimiento(
                product_id=int(prod["product_id"]),
                cantidad=int(cantidad),
                tipo_movimiento=tipo
            )

            if isinstance(resp, dict) and resp.get("error"):
                st.error(resp["error"])
            else:
                st.session_state.ultimo_registro = resp
                toast_ok("Registro guardado correctamente")

        st.rerun()

    # =====================================================
    # CONFIRMACIÓN VISUAL – TARJETA DE REGISTRO GUARDADO
    # =====================================================
    if st.session_state.ultimo_registro:
        r = st.session_state.ultimo_registro

        st.write("")
        st.markdown("### ✅ Último registro guardado")

        card(
            "Movimiento registrado",
            f"""
            <ul style="list-style: none; padding-left: 0; margin: 0;">
            <li><strong>Producto:</strong> {r.get('product_name')}</li>
            <li><strong>Movimiento:</strong> {r.get('movement_type')}</li>
            <li><strong>Cantidad:</strong> {r.get('quantity')}</li>
            <li><strong>Stock anterior:</strong> {r.get('stock_before')}</li>
            <li><strong>Stock después:</strong> {r.get('stock_after')}</li>
            <li><strong>Fecha / Hora:</strong> {r.get('datetime')}</li>
            </ul>
            """
        )


# =========================================================
# PAGE: REPORTES (Dashboard BI)
# =========================================================

elif st.session_state.page == "Reportes":
    st.markdown("## 📊 Reportes")
    st.caption("Dashboard analítico para apoyo a la toma de decisiones")

    # ---------- ESTADO ----------
    if "df_reportes" not in st.session_state:
        st.session_state.df_reportes = None
        st.session_state.figs = None
        st.session_state.kpis = None

    if st.session_state.escaneo_en_progreso or st.session_state.registro_en_progreso:
        st.warning("Termina o cancela el escaneo/registro para habilitar reportes.")
        st.button("Volver a Escaneo", on_click=set_page, args=("Escaneo",))
    else:
        # ===============================
        # BOTONES SUPERIORES
        # ===============================
        top = st.columns([1, 1, 1])
        with top[0]:
            generar = st.button("📌 Generar reportes", use_container_width=True)
        with top[1]:
            st.button("🏠 Volver al Dashboard", on_click=set_page, args=("Dashboard",), use_container_width=True)
        with top[2]:
            st.button("🤖 Ir a Alertas IA", on_click=set_page, args=("Alertas IA",), use_container_width=True)

        # ---------- GENERAR REPORTE UNA SOLA VEZ ----------
        if generar or st.session_state.df_reportes is None:
            if generar:
                df_rep, figs, kpis = generar_reportes()
                st.session_state.df_reportes = df_rep
                st.session_state.figs = figs
                st.session_state.kpis = kpis

        # ---------- SI YA HAY DATOS ----------
        if st.session_state.df_reportes is not None:
            df_rep = st.session_state.df_reportes.copy()
            figs = st.session_state.figs
            kpis = st.session_state.kpis

            # ===============================
            # KPIs
            # ===============================
            st.markdown("### 📌 Indicadores Clave")

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("💰 Ventas totales", f"${kpis['ventas_totales']:,.2f}")
            with k2:
                st.metric("📦 Productos", kpis["productos_distintos"])
            with k3:
                st.metric("⚠️ Bajo stock mínimo", kpis["productos_bajo_minimo"])
            with k4:
                st.metric("📉 Riesgo inventario", f"{kpis['riesgo_pct']:.1f}%")

            # ===============================
            # FILTROS
            # ===============================
            st.markdown("### 🎛️ Filtros")

            f1, f2, f3 = st.columns(3)
            with f1:
                categoria = st.multiselect(
                    "Categoría",
                    sorted(df_rep["Categoria_Tienda"].unique())
                )
            with f2:
                producto = st.multiselect(
                    "Producto",
                    sorted(df_rep["Producto_Tienda"].unique())
                )
            with f3:
                tipo = st.multiselect(
                    "Movimiento",
                    sorted(df_rep["Tipo_de_Movimiento"].unique())
                )

            # ---------- APLICAR FILTROS ----------
            df_filtrado = df_rep.copy()

            if categoria:
                df_filtrado = df_filtrado[df_filtrado["Categoria_Tienda"].isin(categoria)]
            if producto:
                df_filtrado = df_filtrado[df_filtrado["Producto_Tienda"].isin(producto)]
            if tipo:
                df_filtrado = df_filtrado[df_filtrado["Tipo_de_Movimiento"].isin(tipo)]

            # ---------- DATASET VACÍO ----------
            if df_filtrado.empty:
                st.warning("⚠️ No hay datos para los filtros seleccionados.")
                st.stop()

            # ===============================
            # ANALISIS PRINCIPAL
            # ===============================
            st.markdown("### 📈 Análisis Principal")

            figs_filtradas = recalcular_figuras(df_filtrado)

            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(figs_filtradas["fig1_ranking_ventas"], use_container_width=True)
            with c2:
                st.plotly_chart(figs_filtradas["fig2_alerta_stock"], use_container_width=True)

            c3, c4 = st.columns(2)
            with c3:
                st.plotly_chart(figs_filtradas["fig6_pareto"], use_container_width=True)
            with c4:
                st.plotly_chart(figs_filtradas["fig7_riesgo"], use_container_width=True)

            # ===============================
            # ANALISIS OPERACIONAL
            # ===============================
            st.markdown("### 🔍 Operación y Comportamiento")

            c5, c6 = st.columns(2)
            with c5:
                st.plotly_chart(figs_filtradas["fig3_heatmap"], use_container_width=True)
            with c6:
                st.plotly_chart(figs_filtradas["fig4_cuadrante"], use_container_width=True)

            st.plotly_chart(figs_filtradas["fig5_sunburst"], use_container_width=True)

            # ===============================
            # ALERTAS ANALITICAS
            # ===============================
            kpis_filtrados = recalcular_kpis(df_filtrado)

            if kpis_filtrados["productos_criticos"] > 0:
                st.warning(
                    f"⚠️ {kpis_filtrados['productos_criticos']} productos con menos de 3 días de cobertura estimada."
                )

            # ===============================
            # DATASET
            # ===============================
            with st.expander("📄 Ver dataset completo"):
                st.dataframe(df_filtrado, use_container_width=True)

# =========================================================
# PAGE: ALERTAS IA
# =========================================================
elif st.session_state.page == "Alertas IA":
    st.subheader("🤖 Alertas IA – Detección de movimientos extraños")
    st.caption("Modelo de IA (Isolation Forest) para identificar patrones inusuales")

    with st.expander("¿Qué es una anomalía en este sistema?"):
        st.write(
            "Una **anomalía** es un movimiento que el modelo considera **inusual** comparado con el patrón histórico. "
            "No significa automáticamente que esté mal, sino que **vale la pena revisarlo**."
        )
        st.write("Ejemplos típicos:")
        st.write("• Cantidades mucho más altas o bajas de lo habitual.")
        st.write("• Salidas atípicas que pueden indicar error de registro, merma o venta inusual.")
        st.write("• Patrones raros por horario/día (si hay suficientes datos).")

    # Bloqueo si hay procesos activos
    if st.session_state.escaneo_en_progreso or st.session_state.registro_en_progreso:
        st.warning("Finaliza o cancela el escaneo/registro para analizar alertas.")
        c1, c2 = st.columns(2)
        with c1:
            st.button("⏪ Volver a Escaneo", on_click=set_page, args=("Escaneo",), use_container_width=True)
        with c2:
            st.button("🏠 Ir al Dashboard", on_click=set_page, args=("Dashboard",), use_container_width=True)

    else:
        top = st.columns([1.2, 1, 1])
        with top[0]:
            st.markdown("### ⚙️ Configuración del análisis")
            contamination = st.slider(
                "Sensibilidad del modelo",
                min_value=0.05,
                max_value=0.40,
                value=float(st.session_state.anom_last_contamination),
                step=0.01,
                help="Más alto = detecta más anomalías. Recomendado 0.10–0.20"
            )

        with top[1]:
            st.write("")
            st.write("")
            ejecutar = st.button(
                "🔍 Ejecutar detección IA",
                type="primary",
                use_container_width=True
            )

        with top[2]:
            st.write("")
            st.write("")
            st.button(
                "📊 Ir a Reportes",
                on_click=set_page,
                args=("Reportes",),
                use_container_width=True
            )

        st.divider()

        if ejecutar:
            df_hist = obtener_historial()

            if df_hist is None or len(df_hist) == 0:
                st.info("No existe historial suficiente para analizar.")
            else:
                st.session_state.anom_last_contamination = contamination

                df_anom = detectar_movimientos_extranos(
                    df_historial=df_hist,
                    contamination=contamination
                )
                st.session_state.df_anom = df_anom

        # Mostrar resultados si existen
        if st.session_state.df_anom is not None and len(st.session_state.df_anom) > 0:
            df_anom = st.session_state.df_anom
            kpi = resumen_anomalias(df_anom)

            k1, k2, k3 = st.columns(3)
            k1.metric("Registros analizados", kpi["total"])
            k2.metric("Anomalías detectadas", kpi["anomalias"])
            k3.metric("% Anomalías", f"{kpi['porcentaje']:.1f}%")

            st.divider()

            # -------------------------
            # Gráfica temporal
            # -------------------------
            st.markdown("### 📈 Gráfica temporal (anomalías resaltadas)")
            df_plot = df_anom.copy()
            df_plot["Etiqueta"] = df_plot["anomaly"].map({1: "Anomalía", 0: "Normal"})

            fig_t = px.scatter(
                df_plot,
                x="Fecha_Hora",
                y="quantity",
                color="Etiqueta",
                hover_data=["product_name", "movement_type", "stock_after", "motivo"],
                title="Movimientos en el tiempo (cantidad)"
            )
            st.plotly_chart(fig_t, use_container_width=True)

            st.divider()

            # -------------------------
            # Tabla anómalos + interpretación
            # -------------------------
            st.markdown("### 🚨 Movimientos marcados como anómalos (con interpretación)")
            anomalos = df_anom[df_anom["anomaly"] == 1].copy()

            if anomalos.empty:
                st.success("✅ No se detectaron movimientos extraños con esta configuración.")
            else:
                cols = [
                    "Fecha_Hora",
                    "product_name",
                    "movement_type",
                    "quantity",
                    "stock_after",
                    "motivo",
                    "interpretacion",
                    "accion_sugerida",
                ]
                cols = [c for c in cols if c in anomalos.columns]

                st.dataframe(
                    anomalos[cols].sort_values("Fecha_Hora", ascending=False),
                    use_container_width=True
                )

                # -------------------------
                # Guardar histórico
                # -------------------------
                st.markdown("### 💾 Guardar alertas IA en histórico")
                registros = anomalos.copy()

                # Normalizar para JSON
                if "Fecha_Hora" in registros.columns:
                    registros["Fecha_Hora"] = registros["Fecha_Hora"].astype(str)

                campos = [
                    "id", "Fecha_Hora", "product_id", "product_name",
                    "movement_type", "quantity", "stock_after",
                    "anomaly_score", "motivo", "interpretacion", "accion_sugerida"
                ]
                campos = [c for c in campos if c in registros.columns]
                payload = registros[campos].to_dict(orient="records")

                if st.button("Guardar anomalías detectadas en data/anomalias.json"):
                    n = guardar_anomalias_historico(payload)
                    st.success(f"Se guardaron {n} anomalías nuevas en el histórico.")

                if ANOM_PATH.exists():
                    with st.expander("Ver histórico guardado (data/anomalias.json)"):
                        try:
                            hist = json.loads(ANOM_PATH.read_text(encoding="utf-8"))
                            st.dataframe(pd.DataFrame(hist), use_container_width=True)
                        except Exception:
                            st.error("No se pudo leer el histórico de anomalías.")

            # -------------------------
            # Historial completo
            # -------------------------
            with st.expander("📄 Ver historial completo con clasificación IA"):
                cols_full = [
                    "Fecha_Hora",
                    "product_name",
                    "movement_type",
                    "quantity",
                    "stock_after",
                    "anomaly",
                    "anomaly_score",
                    "motivo",
                ]
                cols_full = [c for c in cols_full if c in df_anom.columns]

                st.dataframe(
                    df_anom[cols_full].sort_values("Fecha_Hora", ascending=False),
                    use_container_width=True
                )

            st.divider()
            b1, b2, b3 = st.columns(3)
            with b1:
                st.button("🏠 Dashboard", on_click=set_page, args=("Dashboard",), use_container_width=True)
            with b2:
                st.button("📊 Reportes", on_click=set_page, args=("Reportes",), use_container_width=True)
            with b3:
                st.button("🎥 Escaneo", on_click=set_page, args=("Escaneo",), use_container_width=True)
        else:
            st.info("Ejecuta la detección IA para ver resultados.")
