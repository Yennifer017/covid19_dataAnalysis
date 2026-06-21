from pyspark import pipelines as dp
from pyspark.sql import functions as F

# =============================================================================
# FASE 2: TABLA DE HECHOS PARCIAL - OMS (Mortalidad Global)
# =============================================================================
# RESPONSABLE: Yeni
# FUENTES: covid19.bronze.oms_* (tablas de OMS)
# =============================================================================

@dp.materialized_view(
    comment="Hechos parciales de mortalidad desde OMS (Datos globales)"
)
def covid19_gold_fact_parcial_oms():
    """
    PLANTILLA para Yeni - Tabla de hechos parcial con mortalidad de OMS.
    
    ESTRUCTURA OBLIGATORIA (debe coincidir exactamente):
    - id_tiempo_mes: STRING formato "YYYY-MM"
    - id_geografia: STRING (para países usar códigos ISO: "GT-NA", "CR-NA", etc.)
    - id_perfil: STRING formato "X-rango" donde X = H/M/A
    - id_causa: STRING (mapear a: "COVID", "RESP", "CARDIO", "CANCER", "EXTERNA", "OTRA", "DESCONOCIDA")
    - cantidad_fallecidos: LONG
    - fuente: STRING = "OMS"
    
    PASOS SUGERIDOS:
    1. Leer tus tablas bronze de OMS
    2. Mapear fechas a id_tiempo_mes (formato "YYYY-MM")
    3. Mapear países a id_geografia (ej: "GT-NA" para Guatemala nivel nacional)
    4. Mapear sexo y edad a id_perfil (ej: "H-15-64", "M-65+", "A-Todas")
    5. Mapear causas a id_causa (usa las categorías de dim_causa_muerte)
    6. Agrupar y contar fallecidos
    7. Agregar columna fuente = "OMS"
    
    EJEMPLO DE MAPEO:
    df = spark.read.table("covid19.bronze.oms_deaths")
    df = df.withColumn("id_tiempo_mes", F.date_format(F.col("fecha"), "yyyy-MM"))
    df = df.withColumn("id_geografia", F.concat(F.col("country_code"), F.lit("-NA")))
    ... (completar el resto)
    """
    
    # TODO: Implementar la lógica de transformación
    # Por ahora, retornar estructura vacía con el schema correcto
    
    from pyspark.sql.types import StructType, StructField, StringType, LongType
    
    schema = StructType([
        StructField("id_tiempo_mes", StringType(), False),
        StructField("id_geografia", StringType(), False),
        StructField("id_perfil", StringType(), False),
        StructField("id_causa", StringType(), False),
        StructField("cantidad_fallecidos", LongType(), False),
        StructField("fuente", StringType(), False)
    ])
    
    # DataFrame vacío hasta que Yeni implemente su lógica
    df = spark.createDataFrame([], schema)
    
    return df


# =============================================================================
# NOTAS PARA YENI:
# =============================================================================
# 1. Reemplaza el DataFrame vacío con tu lógica de transformación
# 2. Asegúrate que la estructura final coincida EXACTAMENTE con el schema
# 3. Valida que los id_geografia existan en dim_geografia
# 4. Valida que los id_perfil existan en dim_perfil  
# 5. Valida que los id_causa existan en dim_causa_muerte
# 6. Prueba tu código con un dry run antes de ejecutar
# =============================================================================
