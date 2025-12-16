import streamlit as st

def inject_corporate_css():
    st.markdown(
        """
        <style>
        /* ---- Base ---- */
        .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
        h1, h2, h3 { letter-spacing: -0.2px; }

        /* ---- Corporate palette ---- */
        :root{
          --brand-navy:#0B1F3A;
          --brand-blue:#1C64F2;
          --brand-teal:#0E9F6E;
          --brand-gray:#F5F7FB;
          --brand-border:#E6EAF2;
        }

        /* Page background "corporativo" */
        [data-testid="stAppViewContainer"]{
          background: linear-gradient(180deg, var(--brand-gray) 0%, #ffffff 55%);
        }

        /* ---- Cards ---- */
        .card{
          background: #fff;
          border: 1px solid var(--brand-border);
          border-radius: 16px;
          padding: 16px 18px;
          box-shadow: 0 6px 18px rgba(11,31,58,0.06);
        }
        .card-title{
          font-weight: 700;
          color: var(--brand-navy);
          margin-bottom: 6px;
        }
        .muted{
          color: rgba(11,31,58,0.70);
          font-size: 0.95rem;
        }

        /* ---- Big buttons ---- */
        div[data-testid="stButton"] > button{
          border-radius: 12px;
          padding: 0.65rem 1rem;
          font-weight: 650;
        }

        /* Primary button effect (aplica al primer botón en una columna usualmente) */
        .btn-primary button{
          background: var(--brand-blue) !important;
          color: white !important;
          border: 1px solid rgba(0,0,0,0) !important;
        }
        .btn-primary button:hover{
          filter: brightness(0.95);
        }

        /* Success button */
        .btn-success button{
          background: var(--brand-teal) !important;
          color: white !important;
          border: 1px solid rgba(0,0,0,0) !important;
        }

        /* Sidebar look */
        [data-testid="stSidebar"]{
          border-right: 1px solid var(--brand-border);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
