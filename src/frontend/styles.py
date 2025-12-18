import streamlit as st

def inject_corporate_css():
    st.markdown(
        """
        <style>
        /* ---- Base ---- */
        .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
        h1, h2, h3 { letter-spacing: -0.2px; }

        /* ---- New palette ---- */
        :root{
          --c1:#17153B; /* darkest */
          --c2:#2E236C; /* primary */
          --c3:#433D8B; /* secondary */
          --c4:#C8ACD6; /* light accent */

          /* Derived */
          --bg-soft: rgba(200,172,214,0.18);
          --border-soft: rgba(200,172,214,0.45);
          --shadow: rgba(23,21,59,0.10);

          --text-dark: #17153B;
          --text-mid: rgba(23,21,59,0.78);
          --text-light: rgba(255,255,255,0.92);
          --white: #ffffff;
        }

        /* Page background */
        [data-testid="stAppViewContainer"]{
          background: linear-gradient(180deg, var(--bg-soft) 0%, #ffffff 60%);
        }

        /* ---- Cards ---- */
        .card{
          background: var(--white);
          border: 1px solid var(--border-soft);
          border-radius: 16px;
          padding: 16px 18px;
          box-shadow: 0 10px 22px var(--shadow);
        }
        .card-title{
          font-weight: 750;
          color: var(--text-dark);
          margin-bottom: 6px;
        }
        .muted{
          color: var(--text-mid);
          font-size: 0.96rem;
          line-height: 1.35rem;
        }

        /* ---- Buttons (alignment + slightly smaller icons) ---- */
        div[data-testid="stButton"] > button{
          border-radius: 12px;
          padding: 0.70rem 1rem;
          font-weight: 700;
          font-size: 0.95rem;          /* baja un poco iconos/emojis */
          min-height: 46px;            /* alinea alturas */
          width: 100%;
          display: flex;               /* centra el contenido */
          align-items: center;
          justify-content: center;
          gap: 0.45rem;
          border: 1px solid rgba(23,21,59,0.14);
          background: #ffffff;
          color: var(--text-dark);
        }
        div[data-testid="stButton"] > button:hover{
          border-color: rgba(67,61,139,0.35);
          background: rgba(200,172,214,0.12);
        }

        /* Primary button wrapper */
        .btn-primary button{
          background: var(--c2) !important;
          color: var(--text-light) !important;
          border: 1px solid rgba(0,0,0,0) !important;
        }
        .btn-primary button:hover{
          background: var(--c3) !important;
          filter: none;
        }

        /* Secondary button wrapper */
        .btn-secondary button{
          background: var(--c3) !important;
          color: var(--text-light) !important;
          border: 1px solid rgba(0,0,0,0) !important;
        }
        .btn-secondary button:hover{
          background: var(--c2) !important;
        }

        /* Success-style wrapper (reuse for "Guardar") */
        .btn-success button{
          background: var(--c2) !important;
          color: var(--text-light) !important;
          border: 1px solid rgba(0,0,0,0) !important;
        }
        .btn-success button:hover{
          background: var(--c3) !important;
        }

        /* ---- Sidebar ---- */
        [data-testid="stSidebar"]{
          background: var(--c1);
          border-right: 1px solid rgba(200,172,214,0.25);
        }
        [data-testid="stSidebar"] *{
          color: var(--text-light) !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"]{
          background: rgba(255,255,255,0.06);
          border: 1px solid rgba(200,172,214,0.20);
          border-radius: 14px;
          padding: 10px 10px;
        }

        /* Keep main content text readable */
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] label{
          color: var(--text-dark);
        }

        </style>
        """,
        unsafe_allow_html=True
    )
