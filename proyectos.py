import streamlit as st
import pandas as pd
import os
import plotly.express as px
from streamlit_cookies_controller import CookieController

# 1. Configuración de página unificada para todo el sitio
st.set_page_config(
    page_title="Dashboard OAC - CFG",
    page_icon="🇻🇪",
    layout="wide"
)

# 3. Función de carga de datos
@st.cache_data(show_spinner=False)
@st.cache_resource
def cargar_y_unificar_datos():
    try:
        # 3. Leemos los archivos usando las rutas absolutas corregidas
        df_antiguo = pd.read_excel("hasta2024.xls", engine="xlrd")
        df_2025 = pd.read_excel("2025.xls", engine="xlrd")
        df_2026 = pd.read_excel("2026.xls", engine="xlrd")
        
        df_total = pd.concat([df_antiguo, df_2025, df_2026], ignore_index=True)
        df_total["Monto del proyecto"] = pd.to_numeric(df_total["Monto del proyecto"], errors='coerce').fillna(0)
        df_total["Organización/Provincia/Nombre provincia"] = df_total["Organización/Provincia/Nombre provincia"].astype(str)
        df_total =  df_total.loc[~df_total["Organización/Provincia/Nombre provincia"].str.contains("False"), ]
        df_total["Organización/Nombre"] = df_total["Organización/Nombre"].astype(str)
        df_total =  df_total.loc[~df_total["Organización/Nombre"].str.contains("prueba"), ]
        df_total =  df_total.loc[~df_total["Organización/Nombre"].str.contains("False"), ]
        columnas_str = [
            "Estatus del proyecto", "Código del proyecto", "Código organización",
            "Organización/Provincia/Nombre provincia", "Organización/Municipio/Municipio", 
            "Organización/Parroquia/Parroquia"
        ]
        for col in columnas_str:
            if col in df_total.columns:
                df_total[col] = df_total[col].astype(str).str.strip()
                
        return df_total
        
    except Exception as e:
        st.error(f"🚨 Error al procesar los archivos Excel: {str(e)}")
        return pd.DataFrame()

df_completo = cargar_y_unificar_datos()

if not df_completo.empty:
    
    try:
        col_evento = df_completo.columns[15]
        df_completo[col_evento] = df_completo[col_evento].astype(str).str.strip()
    except IndexError:
        col_evento = "Evento excepcional"
        df_completo[col_evento] = "No registrado"

    # =========================================================================
    # 💥 DISTRIBUCIÓN EN COLUMNAS DE PÁGINA (20% Filtros | 80% Contenido)
    # =========================================================================
    st.title("📊 Dashboard Informativo CFG")
    
    col_filtros_izq, col_contenido_der = st.columns([1, 4])

    # -------------------------------------------------------------------------
    # COLUMNA IZQUIERDA (20%): Panel de Filtros Estático
    # -------------------------------------------------------------------------
    with col_filtros_izq:
        with st.expander("🛠️ Filtros de Control"):
            lista_estados = ["Todos"] + sorted(list(df_completo["Organización/Provincia/Nombre provincia"].unique()))
            estado_sel = st.selectbox("Estado:", lista_estados)

            if estado_sel != "Todos":
                df_mun = df_completo[df_completo["Organización/Provincia/Nombre provincia"] == estado_sel]
            else:
                df_mun = df_completo
            lista_municipios = ["Todos"] + sorted(list(df_mun["Organización/Municipio/Municipio"].unique()))
            municipio_sel = st.selectbox("Municipio:", lista_municipios)

            if municipio_sel != "Todos":
                df_parq = df_mun[df_mun["Organización/Municipio/Municipio"] == municipio_sel]
            else:
                df_parq = df_mun
            lista_parroquias = ["Todos"] + sorted(list(df_parq["Organización/Parroquia/Parroquia"].unique()))
            parroquia_sel = st.selectbox("Parroquia:", lista_parroquias)

            lista_estatus = ["Todos"] + sorted(list(df_completo["Estatus del proyecto"].unique()))
            estatus_sel = st.selectbox("Estatus del Proyecto:", lista_estatus)

            lista_eventos = ["Todos"] + sorted(list(df_completo[col_evento].unique()))
            evento_sel = st.selectbox("Plan de Financiamiento:", lista_eventos)

    # --- LÓGICA DE FILTRADO PANDAS (IGUAL DE POTENTE) ---
    df_filtrado = df_completo.copy()
    if estado_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Organización/Provincia/Nombre provincia"] == estado_sel]
    if municipio_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Organización/Municipio/Municipio"] == municipio_sel]
    if parroquia_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Organización/Parroquia/Parroquia"] == parroquia_sel]
    if estatus_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Estatus del proyecto"] == estatus_sel]
    if evento_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_evento] == evento_sel]

    # -------------------------------------------------------------------------
    # COLUMNA DERECHA (80%): Panel Principal de Trabajo
    # -------------------------------------------------------------------------
    with col_contenido_der:
        tab_estadisticas, tab_buscador = st.tabs(["📊 Análisis Estadístico", "🔍 Consulta de Proyectos", ])
        # PESTAÑA 1: EXPLORADOR Y DATAFRAME
        with tab_buscador:
            with st.container(height=500):
                col_titulo, col_txt = st.columns([0.5, 0.5])
                with col_txt:
                    codigo_buscar = st.text_input("🎯 Búsqueda directa por Código (Proyecto u Organización):").strip()

                if codigo_buscar:
                    resultado_especifico = df_filtrado[(df_filtrado["Código del proyecto"] == codigo_buscar) | (df_filtrado["Código organización"] == codigo_buscar)]

                    if not resultado_especifico.empty:
                        proyecto = resultado_especifico.iloc[0]
                        cod_org_actual = proyecto["Código organización"]

                        proyectos_organizacion = df_completo[df_completo["Código organización"] == cod_org_actual]
                        otros_proyectos = proyectos_organizacion[proyectos_organizacion["Código del proyecto"] != proyecto["Código del proyecto"]]

                        with st.container(border=True):
                            #st.subheader(f"🔍 Organización Vinculada: {proyecto['Organización/Nombre']}")
                            subtab_proyecto, subtab_organizacion = st.tabs(["📋 Proyecto Consultado", "🏢 Ficha de la Organización y Registro Histórico"])

                            with subtab_proyecto:
                                st.markdown(f"### {proyecto['Nombre del proyecto']}")
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.write(f"**Código del Proyecto:** {proyecto['Código del proyecto']}")
                                    st.write(f"**Descripción:** {proyecto['Descripcion of Proyecto'] if 'Descripcion of Proyecto' in df_completo.columns else proyecto.get('Descripcion de Proyecto', 'Sin descripción registrada')}")
                                    st.write(f"**Estatus Actual:** :blue[**{proyecto['Estatus del proyecto']}**]")
                                    st.write(f"**Registrado el:** {proyecto['Creado el']}")
                                with c2:
                                    st.metric(label="Monto Asignado", value=f"Bs{proyecto['Monto del proyecto']:,.2f}")
                                    st.write(f"**Ubicación:** {proyecto['Organización/Provincia/Nombre provincia']}, Mun. {proyecto['Organización/Municipio/Municipio']}, Parq. {proyecto['Organización/Parroquia/Parroquia']}")
                                    st.write(f"**Coordenadas:** Este: {proyecto['Coordenada UTM Este x-ea.']} | Norte: {proyecto['Coordenada UTM Norte y-no.']}")

                            with subtab_organizacion:
                                st.markdown("### Información de la Organización")
                                co1, co2 = st.columns(2)
                                with co1:
                                    st.write(f"**Nombre de la Organización:** {proyecto['Organización/Nombre']}")
                                    st.write(f"**Código de Organización:** {proyecto['Código organización']}")
                                    st.write(f"**NIF / Identificación:** {proyecto['Organización/NIF']}")
                                    st.write(f"**Registro de Organización:** {proyecto['Organización/Creado en']}")
                                with co2:
                                    total_proy_org = len(proyectos_organizacion)
                                    monto_total_org = proyectos_organizacion["Monto del proyecto"].sum()
                                    st.write(f"**Total Proyectos Históricos:** {total_proy_org}")
                                    st.write(f"**Inversión Total Asignada:** ${monto_total_org:,.2f}")

                                st.markdown("---")
                                st.markdown("#### 📂 Historial de Proyectos de esta Organización")

                                if not otros_proyectos.empty:
                                    st.info(f"Se encontraron otros {len(otros_proyectos)} proyectos registrados para esta misma organización:")
                                    st.dataframe(
                                        proyectos_organizacion,
                                        width='stretch',
                                        hide_index=True,
                                        column_order=["Código del proyecto", "Nombre del proyecto", "Monto del proyecto", "Estatus del proyecto", "Creado el"]
                                    )
                                else:
                                    st.write("ℹ️ Esta organización no tiene otros proyectos adicionales registrados.")
                    else:
                        st.warning(f"⚠️ No se encontró el código '{codigo_buscar}' bajo los filtros globales actuales.")
                else:
                    with col_titulo:
                        st.subheader(f"📋 Proyectos Registrados ({len(df_filtrado)})")
                    st.dataframe(
                        df_filtrado, 
                        width='stretch', 
                        hide_index=True,
                        column_order=["Código del proyecto", "Nombre del proyecto", "Organización/Nombre", "Organización/Provincia/Nombre provincia", "Organización/Municipio/Municipio", "Monto del proyecto", "Estatus del proyecto"]
                    )

        # PESTAÑA 2: ESTADÍSTICAS INTERACTIVAS
        with tab_estadisticas:
            with st.container(height=500):
                st.subheader("📉 Indicadores Dinámicos del Segmento")

                total_r = len(df_filtrado)
                monto_t = df_filtrado["Monto del proyecto"].sum()
                monto_p = df_filtrado["Monto del proyecto"].mean() if total_r > 0 else 0

                m1, m2, m3 = st.columns([0.2, 0.5, 0.3])
                with m1:
                    st.metric(label="Proyectos en el segmento", value=f"{total_r:,}")
                with m2:
                    st.metric(label="Inversión en el segmento", value=f"Bs.{monto_t:,.2f}")
                with m3:
                    st.metric(label="Monto Promedio", value=f"Bs.{monto_p:,.2f}")

                st.markdown("---")

                g1, g2 = st.columns(2)

                with g1:
                    st.markdown("#### 📌 Distribución por Estatus (Porcentaje)")
                    if total_r > 0:
                        df_estatus_graf = df_filtrado["Estatus del proyecto"].value_counts().reset_index()
                        df_estatus_graf.columns = ["Estatus", "Cantidad"]

                        fig1 = px.pie(
                            df_estatus_graf, names="Estatus", values="Cantidad",
                            hole=0.5, color_discrete_sequence=px.colors.qualitative.Prism
                        )
                        fig1.update_traces(textinfo="percent+label", textposition="inside")
                        fig1.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=350, showlegend=False)
                        st.plotly_chart(fig1, width='stretch')
                    else:
                        st.info("Sin datos suficientes.")

                with g2:
                    if estado_sel == "Todos":
                        st.markdown("#### 🗺️ Distribución por Estado (Top 10)")
                        if total_r > 0:
                            df_edo_graf = df_filtrado["Organización/Provincia/Nombre provincia"].value_counts().head(10).reset_index()
                            df_edo_graf.columns = ["Estado", "Cantidad"]

                            fig2 = px.bar(
                                df_edo_graf, x="Estado", y="Cantidad",
                                labels={"Cantidad": "N° de Proyectos"}, color_discrete_sequence=["#319795"]
                            )
                            fig2.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=350)
                            st.plotly_chart(fig2, width='stretch')
                    else:
                        st.markdown(f"#### 📍 Distribución por Municipios de: {estado_sel} (Top 10)")
                        if total_r > 0:
                            df_mun_graf = df_filtrado["Organización/Municipio/Municipio"].value_counts().head(10).reset_index()
                            df_mun_graf.columns = ["Municipio", "Cantidad"]

                            fig2 = px.bar(
                                df_mun_graf, x="Municipio", y="Cantidad",
                                labels={"Cantidad": "N° de Proyectos"}, color_discrete_sequence=["#dd6b20"]
                            )
                            fig2.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=350)
                            st.plotly_chart(fig2, width='stretch')

                # Fila de gráficos 2: Categorías y Eventos
                st.markdown("---")

                try:
                    col_categoria = df_completo.columns[14]
                    df_completo[col_categoria] = df_completo[col_categoria].astype(str).str.strip()
                except IndexError:
                    col_categoria = "Categoría del proyecto"

                if evento_sel == "Todos":
                    col_g3, col_g4 = st.columns(2)

                    with col_g3:
                        st.markdown(f"#### 🏷️ Distribución por Categorías (Top 10)")
                        if total_r > 0:
                            df_cat_graf = df_filtrado[col_categoria].value_counts().head(10).reset_index()
                            df_cat_graf.columns = [col_categoria, "Cantidad"]
                            df_cat_graf = df_cat_graf.sort_values(by="Cantidad", ascending=True)

                            fig3 = px.bar(
                                df_cat_graf, x="Cantidad", y=col_categoria, orientation='h',
                                labels={"Cantidad": "N° de Proyectos"}, color_discrete_sequence=["#2b6cb0"]
                            )
                            fig3.update_layout(margin=dict(l=180, r=20, t=10, b=20), height=380)
                            st.plotly_chart(fig3, width='stretch')
                        else:
                            st.info("Sin datos suficientes.")

                    with col_g4:
                        st.markdown(f"#### 🚩 Distribución por Plan de Financiamiento")
                        if total_r > 0:
                            conteo_eventos = df_filtrado[col_evento].value_counts()
                            df_evt_graf = conteo_eventos.sort_index(ascending=False).head(10).reset_index()
                            df_evt_graf.columns = [col_evento, "Cantidad"]

                            fig4 = px.bar(
                                df_evt_graf, x=col_evento, y="Cantidad",
                                labels={"Cantidad": "N° de Proyectos"}, color_discrete_sequence=["#ecc94b"]
                            )
                            fig4.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=380)
                            st.plotly_chart(fig4, width='stretch')
                        else:
                            st.info("Sin datos suficientes.")

                else:
                    st.markdown(f"#### 🏷️ Distribución por {col_categoria} (Filtro expandido - Top 15)")
                    if total_r > 0:
                        df_cat_graf = df_filtrado[col_categoria].value_counts().head(15).reset_index()
                        df_cat_graf.columns = [col_categoria, "Cantidad"]
                        df_cat_graf = df_cat_graf.sort_values(by="Cantidad", ascending=True)

                        fig3 = px.bar(
                            df_cat_graf, x="Cantidad", y=col_categoria, orientation='h',
                            labels={"Cantidad": "N° de Proyectos"}, color_discrete_sequence=["#2b6cb0"]
                        )
                        fig3.update_layout(margin=dict(l=200, r=20, t=10, b=20), height=450)
                        st.plotly_chart(fig3, width='stretch')
                    else:
                        st.info("Sin datos de categorías.")
else:
    st.warning("Estructura base vacía. Sube los archivos .xls históricos.")