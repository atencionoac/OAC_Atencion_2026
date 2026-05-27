import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_cookies_controller import CookieController

# 1. Configuración de página unificada para todo el sitio
st.set_page_config(
    page_title="Sistema Integral OAC - CFG",
    page_icon="🇻🇪",
    layout="wide"
)

# Estilos globales para la cabecera fija de la OAC
st.markdown(
    """
    <style>
    .block-container { padding-top: 3rem !important; }
    .oac-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #1a365d; color: white; padding: 15px 30px;
        z-index: 999999; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex; justify-content: space-between; align-items: center;
        font-family: 'Arial', sans-serif;
    }
    .oac-title { font-size: 18px; font-weight: bold; margin: 0; line-height: 1.2; }
    .oac-subtitle { font-size: 11px; color: #cbd5e0; margin: 0; letter-spacing: 1px; }
    .oac-right-text { font-size: 12px; text-align: right; border-left: 1px solid #cbd5e0; padding-left: 15px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="oac-header">
        <div>
            <div class="oac-title">Oficina de Atención Ciudadana</div>
            <div class="oac-subtitle">CONSEJO FEDERAL DE GOBIERNO</div>
        </div>
        <div class="oac-right-text">
            <strong>Dirección de Línea</strong><br>Atención Ciudadana
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 1. Inicializar el controlador de cookies
controller = CookieController()

# 2. Intentar leer cookies guardadas en el navegador del usuario
cookie_usuario = controller.get("oac_usuario_login")
cookie_nombre = controller.get("oac_usuario_nombre")

# 3. Inicializar el session_state basado en si existen las cookies o no
if "autenticado" not in st.session_state:
    if cookie_usuario and cookie_nombre:
        # Si las cookies existen, el usuario se mantiene conectado automáticamente
        st.session_state["autenticado"] = True
        st.session_state["usuario_actual"] = cookie_usuario
        st.session_state["nombre_usuario"] = cookie_nombre
    else:
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["nombre_usuario"] = ""

# Función para validar credenciales usando el conector nativo de Streamlit
def verificar_credenciales(usuario_ingresado, clave_ingresada):
    try:
        # Usamos la clase correspondiente a la importación de arriba
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_usuarios = conn.read(ttl="5m") 
        
        # Limpieza de textos
        df_usuarios["Usuario"] = df_usuarios["Usuario"].astype(str).str.strip()
        df_usuarios["Contraseña"] = df_usuarios["Contraseña"].astype(str).str.strip()
        
        # Búsqueda del usuario
        registro = df_usuarios[(df_usuarios["Usuario"] == usuario_ingresado) & (df_usuarios["Contraseña"] == clave_ingresada)]
        
        if not registro.empty:
            return True, registro.iloc[0]["Nombre Completo"]
        return False, ""
    except Exception as e:
        st.error(f"Error de conexión con el validador de usuarios: {e}")
        return False, ""
 
# =========================================================================
# LÓGICA DE RENDERIZADO
# =========================================================================
if not st.session_state["autenticado"]:
    
    # Maquetación de la pantalla informativa con Login lateral (Proporción 4 a 8)
    col_login_box, col_info_texto = st.columns([4, 8], gap="large")
    
    with col_login_box:
        # Contenedor visual del formulario de Login
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #1a365d; margin-bottom:20px;'>Login</h2>", unsafe_allow_html=True)
            
            txt_usuario = st.text_input("Usuario", placeholder="Ingrese su usuario").strip()
            txt_clave = st.text_input("Contraseña", type="password", placeholder="********")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Ingresar", width='stretch', type="primary"):
                es_valido, nombre_completo = verificar_credenciales(txt_usuario, txt_clave)
                if es_valido:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = txt_usuario
                    st.session_state["nombre_usuario"] = nombre_completo
                    # 💥 MÁGICA: Guardamos las cookies en el dispositivo físico (Duran 7 días)
                    controller.set("oac_usuario_login", txt_usuario)
                    controller.set("oac_usuario_nombre", nombre_completo)
                    st.success(f"¡Bienvenido, {nombre_completo}!")
                    st.rerun()
                else:
                    st.error("❌ Usuario o Contraseña incorrectos")
                    
    with col_info_texto:
        # Bloque de información institucional tal cual tu captura de pantalla
        st.markdown("<h2 style='color: #1a365d;'>¿Qué es la OAC FCI-CFG?</h2>", unsafe_allow_html=True)
        st.markdown(
            """
            En la **Oficina de Atención Ciudadana (OAC)**, del Fondo de Compensación Interterritorial (FCI) - 
            **Consejo Federal de Gobierno (CFG)**, se atiende a los voceros y voceras del Poder Popular 
            ya sea vía presencial o a través del Sistema de la Consulta Popular. Dicha atención se realiza de la siguiente forma:
            """
        )
        
        st.markdown("<h3 style='color: #2b6cb0;'>¿Cómo funciona la OAC FCI-CFG?</h3>", unsafe_allow_html=True)
        
        with st.expander("📍 Atención al Poder Popular de forma presencial", expanded=True):
            st.markdown(
                """
                * Atención en los espacios destinados para ello de los/las voceros(as) de las Organizaciones.
                * Verificación de su solicitud en la página de la Consulta Popular.
                * Registro de datos de atención y acuerdos con las personas que asistieron.
                * En caso de quedar algún trámite pendiente se procede a gestionar la solución y se responde a los datos aportados.
                """
            )
            
        with st.expander("💻 Atención al Poder Popular a través del módulo de comunicaciones"):
            st.markdown(
                """
                * Recepción y revisión de las solicitudes realizadas a través del módulo de comunicaciones.
                * Asignación a la dirección que le corresponda o al analista responsable de dar respuesta.
                * El analista asignado debe generar una respuesta para enviar a la organización.
                * El Responsable del caso debe aprobar la respuesta generada por el analista y enviar a la organización.
                """
            )
            
        st.info("📊 Recepción y revisión de solicitudes durante eventos externos.")
 
else:
    # =========================================================================
    # USUARIO AUTENTICADO: ENRUTADOR DE PÁGINAS DEL SISTEMA
    # =========================================================================
    
    # Botón de cierre de sesión en la parte inferior de la barra de navegación nativa
    # def logout():
    #     st.session_state["autenticado"] = False
    #     st.session_state["usuario_actual"] = ""
    #     st.session_state["nombre_usuario"] = ""
        
    #     # 💥 BORRAMOS LAS COOKIES del navegador para que pida login la próxima vez
    #     controller.remove("oac_usuario_login")
    #     controller.remove("oac_usuario_nombre")
    #     st.rerun()
        
    # col_menu, col_contenido = st.columns([4, 1])
    # with col_contenido:
    #     st.markdown(f"👤 **Usuario:** {st.session_state['nombre_usuario']}")
    #     if st.button("Cerrar Sesión", type="secondary"):
    #         logout()

    page_proyectos = st.Page("proyectos.py", title="Tablero de Proyectos", icon="📋")
    
    # Inicializamos el enrutador
    pg = st.navigation([page_proyectos])
    pg.run()