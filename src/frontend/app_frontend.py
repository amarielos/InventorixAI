
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Inventorix AI",
    page_icon="📦",
    layout="wide"
)


if "scanning_active" not in st.session_state:
    st.session_state.scanning_active = False

if "producto_detectado" not in st.session_state:
    st.session_state.producto_detectado = None  
if "registro_en_progreso" not in st.session_state:
    st.session_state.registro_en_progreso = False

if "movimientos" not in st.session_state:
    # Lista de dicts con los movimientos registrados
    st.session_state.movimientos = []

#funcion IA
def detectar_producto_con_ia_simulado():

    return {
        "Producto": "Leche Entera 1L",
        "Categoria": "Lácteos",
        "Precio_Unitario": 10.50
    }


st.markdown(
    "<h1 style='margin-bottom:0;'>📦 Inventorix AI</h1>",
    unsafe_allow_html=True
)
st.write("Gestión inteligente de inventario con visión artificial y analítica de datos.")

st.markdown("---")

tab_escaneo, tab_analisis = st.tabs(["Escaneo y registro", "Análisis gráfico"])


with tab_escaneo:
    st.markdown("### 👋 Bienvenido")

    # CASO 1: No hay escaneo activo ni producto detectado
    if (not st.session_state.scanning_active) and (st.session_state.producto_detectado is None):
        st.write(
            "En esta sección puedes iniciar el escaneo con IA para detectar un producto, "
            "registrar una entrada o salida, y luego pasar al análisis gráfico."
        )

        st.info(
            "Cuando presiones **Iniciar escaneo con IA**, se activará el modelo para detectar el producto. "
            "Una vez detectado, podrás ingresar la cantidad y el tipo de movimiento."
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("▶️ Iniciar escaneo con IA"):
               
                st.session_state.scanning_active = True

               
                producto = detectar_producto_con_ia_simulado()

               
                st.session_state.producto_detectado = producto
                st.session_state.registro_en_progreso = True
                st.session_state.scanning_active = False  # La IA se detiene tras detectar

                st.success("Producto detectado correctamente. Continúa con el registro más abajo.")
                st.experimental_rerun()

        with col2:
            st.caption("También podrás ir al análisis gráfico cuando tengas movimientos registrados.")

  
    if st.session_state.producto_detectado is not None and st.session_state.registro_en_progreso:
        st.markdown("### 📄 Registro del movimiento")

        prod = st.session_state.producto_detectado

        with st.container():
            st.markdown("#### 🧾 Producto detectado")
            st.write(f"**Producto:** {prod.get('Producto', 'N/D')}")
            st.write(f"**Categoría:** {prod.get('Categoria', 'N/D')}")
            st.write(f"**Precio sugerido:** Q {prod.get('Precio_Unitario', 0):.2f}")

        st.markdown("---")

        col_form1, col_form2 = st.columns([2, 1])

        with col_form1:
            st.markdown("#### ✏️ Datos del movimiento")

            tipo_mov = st.radio(
                "Tipo de movimiento",
                options=["Entrada", "Salida"],
                horizontal=True
            )

            cantidad = st.number_input(
                "Cantidad",
                min_value=1,
                step=1,
                value=1
            )

            precio_unit = st.number_input(
                "Precio unitario (puedes ajustarlo si es necesario)",
                min_value=0.0,
                step=0.01,
                value=float(prod.get("Precio_Unitario", 0.0))
            )

        with col_form2:
            st.markdown("#### 📅 Fecha y hora")
            fecha_hora = datetime.now()
            st.write(fecha_hora.strftime("%Y-%m-%d %H:%M:%S"))

        col_botones = st.columns([1, 1, 2])

        with col_botones[0]:
            if st.button("💾 Guardar registro"):
                movimiento = {
                    "Fecha_Hora": fecha_hora,
                    "Producto": prod.get("Producto"),
                    "Categoria": prod.get("Categoria"),
                    "Tipo_Movimiento": tipo_mov.lower(),  # "entrada" o "salida"
                    "Cantidad": cantidad,
                    "Precio_Unitario": precio_unit,
                }

                st.session_state.movimientos.append(movimiento)

               
                st.session_state.registro_en_progreso = False
                st.session_state.producto_detectado = None

                st.success("Registro guardado correctamente. ¡Ya puedes ir al análisis gráfico!")

        with col_botones[1]:
            if st.button("❌ Cancelar registro"):
                st.session_state.registro_en_progreso = False
                st.session_state.producto_detectado = None
                st.info("Registro cancelado. Puedes iniciar un nuevo escaneo cuando lo desees.")
                st.experimental_rerun()

        # Si ya hay movimientos registrados, mostramos un aviso para ir al análisis
        if len(st.session_state.movimientos) > 0:
            st.markdown("---")
            st.info(
                "Tienes movimientos registrados. Cambia a la pestaña **“Análisis gráfico”** "
                "para ver las gráficas del producto."
            )

   
    elif (st.session_state.producto_detectado is None 
          and not st.session_state.registro_en_progreso 
          and len(st.session_state.movimientos) > 0):

        st.markdown("### ✅ Movimientos registrados")
        df_movs = pd.DataFrame(st.session_state.movimientos)
        st.dataframe(df_movs, use_container_width=True)

        st.info(
            "Puedes iniciar un nuevo escaneo o ir a la pestaña **“Análisis gráfico”** "
            "para visualizar las estadísticas."
        )


# =========================================================
# TAB 2: ANÁLISIS GRÁFICO
# =========================================================
with tab_analisis:
    st.markdown("### 📈 Análisis gráfico del inventario")

    # REGLA: el usuario puede entrar a esta pestaña en cualquier momento,
    # pero si hay escaneo/registro en curso, no puede hacer análisis.
    if st.session_state.scanning_active or st.session_state.registro_en_progreso:
        st.warning(
            "El análisis gráfico está deshabilitado mientras haya un escaneo o un registro en curso.\n\n"
            "Por favor, termina o cancela el registro en la pestaña **“Escaneo y registro”**."
        )
    else:
        if len(st.session_state.movimientos) == 0:
            st.info(
                "Aún no hay movimientos registrados. "
                "Regresa a la pestaña **“Escaneo y registro”** para escanear un producto y guardar al menos un movimiento."
            )
        else:
            df_movs = pd.DataFrame(st.session_state.movimientos)

            # ------------------- ANÁLISIS GENERAL -------------------
            st.markdown("#### 🧾 Tabla de movimientos registrados")
            st.dataframe(df_movs, use_container_width=True)

            st.markdown("#### 🔍 Cantidad total movida por producto")
            df_resumen = (
                df_movs.groupby(["Producto", "Tipo_Movimiento"])["Cantidad"]
                .sum()
                .reset_index()
            )

            st.bar_chart(
                df_resumen,
                x="Producto",
                y="Cantidad",
                color="Tipo_Movimiento",  # En versiones antiguas de Streamlit, no uses 'color'
            )

            st.markdown("---")

            # ------------------- ANÁLISIS POR PRODUCTO -------------------
            st.markdown("### 📊 Análisis detallado por producto")

            # Lista de productos únicos
            productos_disponibles = df_movs["Producto"].dropna().unique().tolist()

            producto_seleccionado = st.selectbox(
                "Selecciona el producto a analizar:",
                options=productos_disponibles,
                index=0 if len(productos_disponibles) > 0 else None
            )

            # Filtramos el DataFrame por el producto elegido
            df_prod = df_movs[df_movs["Producto"] == producto_seleccionado].copy()

            # Aseguramos que Fecha_Hora sea datetime
            if not pd.api.types.is_datetime64_any_dtype(df_prod["Fecha_Hora"]):
                df_prod["Fecha_Hora"] = pd.to_datetime(df_prod["Fecha_Hora"])

            # Ordenamos por fecha
            df_prod = df_prod.sort_values("Fecha_Hora")

            # Mostramos tabla específica
            st.markdown(f"#### 🧾 Movimientos del producto: **{producto_seleccionado}**")
            st.dataframe(df_prod, use_container_width=True)

            # ---------- Tendencia en el tiempo (por movimiento) ----------
            st.markdown("#### 📉 Tendencia de movimientos en el tiempo")

            # Agrupamos por fecha y tipo de movimiento
            df_tendencia = (
                df_prod.groupby(["Fecha_Hora", "Tipo_Movimiento"])["Cantidad"]
                .sum()
                .reset_index()
            )

            if len(df_tendencia) > 0:
                # Gráfica de líneas de tendencia por tipo de movimiento
                st.line_chart(
                    df_tendencia,
                    x="Fecha_Hora",
                    y="Cantidad",
                    color="Tipo_Movimiento"
                )
            else:
                st.info("Aún no hay suficientes datos para mostrar la tendencia de este producto.")

            # ---------- Tendencia acumulada (stock estimado simple) ----------
            st.markdown("#### 📈 Tendencia acumulada (estimación simple de stock)")

            # Convertimos entrada/salida a signo para una curva acumulada
            df_prod["Delta"] = df_prod.apply(
                lambda row: row["Cantidad"] if row["Tipo_Movimiento"] == "entrada" else -row["Cantidad"],
                axis=1
            )

            df_cumul = df_prod[["Fecha_Hora", "Delta"]].copy()
            df_cumul = df_cumul.sort_values("Fecha_Hora")
            df_cumul["Stock_Aproximado"] = df_cumul["Delta"].cumsum()

            if len(df_cumul) > 0:
                st.line_chart(
                    df_cumul,
                    x="Fecha_Hora",
                    y="Stock_Aproximado"
                )
                st.caption(
                    "Nota: Este stock es una estimación acumulada basada solo en los movimientos registrados "
                    "en la aplicación (no considera un stock inicial real)."
                )
            else:
                st.info("No se pudo calcular una tendencia acumulada para este producto.")
