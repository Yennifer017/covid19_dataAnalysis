import dlt
from pyspark.sql import functions as F
import pandas as pd
import requests
import io

def download_dropbox_csv(dropbox_url: str) -> pd.DataFrame:
    """
    Descarga CSV público desde Dropbox y lo convierte a DataFrame de pandas
    """
    # Convertir URL de Dropbox a formato de descarga directa
    if "&dl=0" in dropbox_url:
        download_url = dropbox_url.replace("&dl=0", "&dl=1")
    elif "?rlkey=" in dropbox_url and "&dl=" not in dropbox_url:
        download_url = dropbox_url + "&dl=1"
    else:
        download_url = dropbox_url
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }
    
    response = requests.get(download_url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    
    # Decodificar el contenido
    csv_content = response.content.decode('utf-8-sig', errors='ignore')
    file_stream = io.StringIO(csv_content)
    
    # Leer CSV con pandas
    pdf = pd.read_csv(file_stream, engine='python', encoding_errors='ignore')
    
    return pdf

# Tabla: códigos_cie10_enfermedades
@dlt.table(
    name="codigos_cie10_enfermedades",
    comment="Catálogo de códigos CIE-10 con descripciones en snake_case",
    table_properties={"quality": "bronze"}
)
def load_codigos_cie10():
    dropbox_url = "https://www.dropbox.com/scl/fi/fr8p3jvqj9xckisiru5ot/enfermedades.csv?rlkey=cphzsdsi7cc6ll15c1qjxfuxn&st=aow8stul&dl=0"
    
    pdf = download_dropbox_csv(dropbox_url)
    
    # Convertir a Spark DataFrame
    df = spark.createDataFrame(pdf)
    
    return df

# Tabla: códigos_cie10_enfermedades (versión Silver con snake_case)
@dlt.table(
    name="codigos_cie10_enfermedades_silver",
    comment="Catálogo de códigos CIE-10 con descripciones normalizadas a snake_case",
    table_properties={"quality": "silver"}
)
def transform_codigos_cie10_silver():
    # Leer desde la tabla bronze
    df_bronze = dlt.read("codigos_cie10_enfermedades")
    
    df_silver = (
        df_bronze
        # Renombrar columnas a snake_case si no lo están
        .withColumnRenamed("CAUSA", "causa")
        .withColumnRenamed("DESCRIP", "descripcion")
        # Convertir descripción a snake_case: reemplazar espacios y caracteres especiales
        .withColumn(
            "descripcion_snake_case",
            F.lower(
                F.regexp_replace(
                    F.regexp_replace(F.col("descripcion"), r"[^a-zA-Z0-9\s]", ""),  # Eliminar caracteres especiales
                    r"\s+", "_"  # Reemplazar espacios con guión bajo
                )
            )
        )
        # Estandarizar código a mayúsculas
        .withColumn("causa", F.upper(F.col("causa")))
        # Agregar metadatos
        .withColumn("pais_origen", F.lit("Guatemala/Centroamérica"))
        .withColumn("metadata_processed_at", F.current_timestamp())
        # Eliminar duplicados
        .dropDuplicates(["causa"])
    )
    
    return df_silver