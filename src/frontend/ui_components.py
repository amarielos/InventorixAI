import streamlit as st
from datetime import datetime

def set_page(page: str):
    st.session_state.page = page
    st.rerun()

def card(title: str, body: str):
    st.markdown(
        f"""
        <div class="card">
          <div class="card-title">{title}</div>
          <div class="muted">{body}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def toast_ok(msg: str):
    # Streamlit moderno tiene st.toast; si no, caemos a st.success
    if hasattr(st, "toast"):
        st.toast(msg, icon="✅")
    else:
        st.success(msg)

def show_dialog_success(title: str, lines: list[str]):
    """
    Muestra un “cuadro de diálogo” si existe st.dialog.
    Si no existe, muestra un bloque tipo modal (st.success + card).
    """
    if hasattr(st, "dialog"):
        @st.dialog(title)
        def _dlg():
            for ln in lines:
                st.write("•", ln)
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.button("Ir a Reportes", on_click=set_page, args=("Reportes",))
            with c2:
                st.button("Ir a Alertas IA", on_click=set_page, args=("Alertas IA",))
        _dlg()
    else:
        st.success(title)
        for ln in lines:
            st.write("•", ln)
        c1, c2 = st.columns(2)
        with c1:
            st.button("Ir a Reportes", on_click=set_page, args=("Reportes",))
        with c2:
            st.button("Ir a Alertas IA", on_click=set_page, args=("Alertas IA",))

def kpi_row(kpis: list[tuple[str, str]]):
    cols = st.columns(len(kpis))
    for i, (label, value) in enumerate(kpis):
        cols[i].metric(label, value)

def fmt_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")
