import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import time
import base64
import json

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
    .block-container { padding-top: 7rem !important; }
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

# =========================================================================
# FUNCIONES PARA MANEJO DE SESIÓN CON QUERY PARAMS
# =========================================================================

def guardar_sesion_en_url(usuario, nombre_completo):
    """Guarda los datos de sesión en la URL como parámetro codificado"""
    datos_sesion = {
        "usuario": usuario,
        "nombre": nombre_completo,
        "autenticado": True,
        "timestamp": time.time()
    }
    json_str = json.dumps(datos_sesion)
    encoded = base64.b64encode(json_str.encode()).decode()
    st.query_params['sesion'] = encoded

def cargar_sesion_desde_url():
    """Recupera los datos de sesión desde la URL"""
    if 'sesion' in st.query_params:
        try:
            encoded = st.query_params['sesion']
            json_str = base64.b64decode(encoded).decode()
            datos = json.loads(json_str)
            # Verificar que la sesión no sea demasiado antigua (opcional, 30 días por defecto)
            if time.time() - datos.get('timestamp', 0) < 2592000:  # 30 días
                return datos
        except Exception:
            return None
    return None

def limpiar_sesion_de_url():
    """Limpia la sesión de la URL"""
    st.query_params.clear()

# =========================================================================
# INICIALIZACIÓN DE SESIÓN
# =========================================================================

# Inicializar el session_state basado en los query params
if "autenticado" not in st.session_state:
    # Intentar cargar sesión desde la URL
    datos_sesion = cargar_sesion_desde_url()
    
    if datos_sesion and datos_sesion.get('autenticado', False):
        st.session_state["autenticado"] = True
        st.session_state["usuario_actual"] = datos_sesion.get('usuario', '')
        st.session_state["nombre_usuario"] = datos_sesion.get('nombre', '')
        # Opcional: Mostrar mensaje de bienvenida silencioso
        st.toast(f"¡Bienvenido de vuelta, {st.session_state['nombre_usuario']}! 👋", icon="🎉")
    else:
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = ""
        st.session_state["nombre_usuario"] = ""

# =========================================================================
# FUNCIÓN DE VALIDACIÓN DE CREDENCIALES
# =========================================================================

def verificar_credenciales(usuario_ingresado, clave_ingresada):
    try:
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
# PANTALLA DE LOGIN
# =========================================================================

def mostrar_pantalla_login():    
    # Maquetación de la pantalla informativa con Login lateral (Proporción 4 a 8)
    col_login_box, col_info_texto = st.columns([4, 8], gap="large")
    
    with col_login_box:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #1a365d; margin-bottom:20px;'>Login</h2>", unsafe_allow_html=True)
            
            txt_usuario = st.text_input("Usuario", placeholder="Ingrese su usuario")
            txt_clave = st.text_input("Contraseña", type="password", placeholder="********")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Ingresar", use_container_width=True, type="primary"):
                if txt_usuario and txt_clave:  # Validación básica
                    es_valido, nombre_completo = verificar_credenciales(txt_usuario.strip(), txt_clave)
                    
                    if es_valido:
                        # Guardar en session_state
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_actual"] = txt_usuario.strip()
                        st.session_state["nombre_usuario"] = nombre_completo
                        
                        # Guardar en la URL para persistencia
                        guardar_sesion_en_url(txt_usuario.strip(), nombre_completo)
                        
                        st.success(f"¡Bienvenido, {nombre_completo}!")
                        time.sleep(0.5)  # Pequeña pausa para mostrar el mensaje
                        st.rerun()
                    else:
                        st.error("❌ Usuario o Contraseña incorrectos")
                else:
                    st.warning("⚠️ Por favor ingrese usuario y contraseña")
                    
    with col_info_texto:
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

# =========================================================================
# FUNCIÓN DE CIERRE DE SESIÓN (Para usar desde cualquier página)
# =========================================================================

def cerrar_sesion():
    """Función global para cerrar sesión desde cualquier página"""
    # Limpiar session_state
    st.session_state["autenticado"] = False
    st.session_state["usuario_actual"] = ""
    st.session_state["nombre_usuario"] = ""
    
    # Limpiar la URL
    limpiar_sesion_de_url()
    
    # Mostrar mensaje y redirigir
    st.success("👋 Sesión cerrada correctamente")
    time.sleep(0.5)
    st.rerun()

# =========================================================================
# DECLARACIÓN DE PÁGINAS Y ENRUTADOR
# =========================================================================

# Declaramos la página del tablero de proyectos
# Nota: Necesitarás modificar proyectos.py para que tenga un botón de cerrar sesión
# que llame a la función cerrar_sesion()
page_proyectos = st.Page("proyectos.py", title="Tablero de Proyectos", icon="📋")

# DEFINICIÓN DEL ENRUTADOR DINÁMICO
if not st.session_state["autenticado"]:
    # Si no está autenticado, mostrar solo la pantalla de login
    page_login = st.Page(mostrar_pantalla_login, title="Iniciar Sesión", icon="🔒")
    pg = st.navigation([page_login], position="hidden")  # Ocultar barra lateral en login
else:
    # Si está autenticado, mostrar el dashboard
    pg = st.navigation([page_proyectos])

# Ejecutar el enrutador
pg.run()