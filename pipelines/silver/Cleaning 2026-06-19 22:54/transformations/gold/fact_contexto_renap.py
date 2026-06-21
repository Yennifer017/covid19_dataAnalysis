from pyspark import pipelines as dp
from pyspark.sql import functions as F

# =============================================================================
# FASE 2: TABLA DE HECHOS - CONTEXTO RENAP (Eventos civiles)
# =============================================================================

@dp.materialized_view(
    comment="Hechos de contexto: Eventos civiles de RENAP (Nacimientos, Matrimonios, etc.)"
)
def covid19_gold_fact_contexto_renap():
    """
    Tabla de hechos satélite con eventos civiles del RENAP.
    Estructura: id_tiempo_mes, tipo_evento, cantidad
    
    NO incluye dimensiones de geografía/perfil/causa porque estos eventos 
    no son de mortalidad, son contexto poblacional.
    """
    # Leer datos de RENAP ya normalizados (nombre totalmente calificado)
    df = spark.read.table("covid19.silver.silver_eventos_por_mes")
    
    # Filtrar eventos técnicos/totales que no son eventos reales
    eventos_excluir = [
        "TOTAL GENERAL", 
        "Total", 
        "AJUSTE (FILAS FALTANTES EN IMAGEN)",
        "Otros"
    ]
    
    df = df.filter(~F.col("evento").isin(eventos_excluir))
    
    # Normalizar nombres de eventos (estandarizar capitalización)
    df = df.withColumn(
        "tipo_evento",
        F.when(F.upper(F.col("evento")).contains("NACIMIENTO"), "Nacimientos")
         .when(F.upper(F.col("evento")).contains("DEFUNCI"), "Defunciones")
         .when(F.upper(F.col("evento")).contains("MATRIMONIO"), "Matrimonios")
         .when(F.upper(F.col("evento")).contains("DIVORCIO"), "Divorcios")
         .when(F.upper(F.col("evento")).contains("RECONOCIMIENTO"), "Reconocimientos")
         .when(F.upper(F.col("evento")).contains("IDENTIFICACION"), "Identificación de Persona")
         .when(F.upper(F.col("evento")).contains("ADOPCION"), "Adopciones")
         .when(F.upper(F.col("evento")).contains("CAMBIO DE NOMBRE"), "Cambio de Nombre")
         .when(F.upper(F.col("evento")).contains("UNION DE HECHO"), "Unión de Hecho")
         .when(F.upper(F.col("evento")).contains("GUATEMALTECO"), "Naturalizaciones")
         .when(F.upper(F.col("evento")).contains("EXTRANJERO"), "Extranjeros Domiciliados")
         .otherwise(F.col("evento"))
    )
    
    # Crear id_tiempo_mes en formato "YYYY-MM"
    df = df.withColumn(
        "id_tiempo_mes",
        F.date_format(F.col("fecha"), "yyyy-MM")
    )
    
    # Agregar por mes y tipo de evento (para consolidar variantes del mismo evento)
    df = df.groupBy("id_tiempo_mes", "tipo_evento").agg(
        F.sum("cantidad").alias("cantidad")
    )
    
    # Agregar columna de fuente
    df = df.withColumn("fuente", F.lit("RENAP"))
    
    return df.select(
        "id_tiempo_mes",
        "tipo_evento",
        "cantidad",
        "fuente"
    ).orderBy("id_tiempo_mes", "tipo_evento")
