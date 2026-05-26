import os
import base64
from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Evita errores de interfaz gráfica en servidores
import matplotlib.pyplot as plt

app = FastAPI()

# Permitir conexiones desde Google Apps Script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def concatenar_base_de_datos():
    # 1. Definir las rutas de tus 3 archivos segmentados
    file_antiguo = "hasta2024.xls"
    file_2025 = "2025.xls"
    file_2026 = "2026.xls"
    
    # Verificar que los tres archivos existan en el repositorio de GitHub
    archivos = [file_antiguo, file_2025, file_2026]
    for archivo in archivos:
        if not os.path.exists(archivo):
            raise HTTPException(
                status_code=500, 
                detail=f"Error interno: Falta el archivo '{archivo}' en el servidor."
            )
    
    try:
        # 2. Leer cada archivo usando el motor 'xlrd' para formato .xls
        df_antiguo = pd.read_excel(file_antiguo, engine='xlrd')
        df_2025 = pd.read_excel(file_2025, engine='xlrd')
        df_2026 = pd.read_excel(file_2026, engine='xlrd')
        
        # 3. Concatenar los 3 DataFrames en uno solo
        # Pandas los unirá en el orden en que los coloques en la lista
        df_unido = pd.concat([df_antiguo, df_2025, df_2026], ignore_index=True)
        
        # 4. Limpieza y formateo de datos (idéntico al anterior)
        df_unido["Monto del proyecto"] = pd.to_numeric(df_unido["Monto del proyecto"], errors='coerce').fillna(0)
        df_unido["Estatus del proyecto"] = df_unido["Estatus del proyecto"].astype(str).str.strip()
        
        return df_unido
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Fallo crítico al concatenar los segmentos .xls: {str(e)}"
        )

@app.get("/procesar")
def procesar_datos():
    # Llamamos a la función que unifica las dos partes
    df = concatenar_base_de_datos()
    
    # 1. Extracción de métricas clave basadas en tus campos
    total_proyectos = int(len(df))
    monto_total = float(df["Monto del proyecto"].sum())
    monto_promedio = float(df["Monto del proyecto"].mean())
    
    # Distribución de conteos según el campo "Estatus del proyecto"
    distribucion_estatus = df["Estatus del proyecto"].value_counts().to_dict()
    
    # 2. Generación de un gráfico con Matplotlib usando "Estatus del proyecto"
    plt.figure(figsize=(8, 4.5))
    df["Estatus del proyecto"].value_counts().plot(kind='bar', color='#2b6cb0', edgecolor='#1a365d')
    plt.title("Estatus Actual de los Proyectos Consolidados", fontsize=12, fontweight='bold')
    plt.xticks(rotation=35, ha='right')
    plt.tight_layout()
    
    # Convertir el gráfico en memoria a String Base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=120)
    buffer.seek(0)
    grafico_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    # Retornamos el JSON hacia Google Apps Script
    return {
        "status": "success",
        "total_registros": total_proyectos,
        "metricas": {
            "monto_total": monto_total,
            "monto_promedio": monto_promedio
        },
        "distribucion": distribucion_estatus,
        "grafico_base64": grafico_b64
    }