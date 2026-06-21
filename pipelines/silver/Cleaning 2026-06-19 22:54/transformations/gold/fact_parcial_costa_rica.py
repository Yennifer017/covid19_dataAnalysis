from pyspark import pipelines as dp
from pyspark.sql import functions as F

# =============================================================================
# FASE 2: TABLA DE HECHOS PARCIAL - COSTA RICA (Mortalidad Costa Rica)
# =============================================================================
# RESPONSABLE: Byron
# FUENTES: covid19.bronze.mortalidad_* (tablas de Costa Rica)
# NOTA: Las tablas desagregados_por_departamento NO se usarán (según instrucciones)
# =============================================================================

@dp.materialized_view(
    comment="Hechos parciales de mortalidad desde Costa Rica"
)
def covid19_gold_fact_parcial_costa_rica():
    """
    PLANTILLA para Byron - Tabla de hechos parcial con mortalidad de Costa Rica.
    
    ESTRUCTURA OBLIGATORIA (debe coincidir exactamente):
    - id_tiempo_mes: STRING formato "YYYY-MM"
    - id_geografia: STRING = "CR-NA" (Costa Rica nivel nacional)
    - id_perfil: STRING formato "X-rango" donde X = H/M/A
    - id_causa: STRING (mapear a: "COVID", "RESP", "CARDIO", "CANCER", "EXTERNA", "OTRA", "DESCONOCIDA")
    - cantidad_fallecidos: LONG
    - fuente: STRING = "CR"
    
    PASOS SUGERIDOS:
    1. Identificar qué tablas bronze de Costa Rica SÍ vas a usar 
       (NO usar: desagregados_por_departamento, mortalidad_indicadores_costa_rica,
                 mortalidad_por_edades_costa_rica, mortalidad_categorias_costa_rica_2020)
    2. Leer las tablas válidas de Costa Rica
    3. Mapear fechas a id_tiempo_mes (formato "YYYY-MM")
    4. Usar id_geografia = "CR-NA" (nivel nacional)
    5. Mapear sexo y edad a id_perfil (ej: "H-15-64", "M-65+", "A-Todas")
    6. Mapear causas a id_causa (usa las categorías de dim_causa_muerte)
    7. Agrupar y contar fallecidos
    8. Agregar columna fuente = "CR"
    
    EJEMPLO DE MAPEO:
    df = spark.read.table("covid19.bronze.tu_tabla_costa_rica")
    df = df.withColumn("id_tiempo_mes", F.date_format(F.col("fecha"), "yyyy-MM"))
    df = df.withColumn("id_geografia", F.lit("CR-NA"))
    df = df.withColumn("id_perfil", ...)  # Mapear sexo y edad
    df = df.withColumn("id_causa", ...)    # Mapear causa
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
    
    # DataFrame vacío hasta que Byron implemente su lógica
    df = spark.createDataFrame([], schema)
    
    return df


# =============================================================================
# NOTAS PARA BYRON:
# =============================================================================
# 1. Primero identifica qué tablas de Costa Rica están disponibles y son válidas
# 2. NO uses las tablas mencionadas en la lista de exclusión
# 3. Costa Rica solo tiene nivel nacional, usa siempre "CR-NA" como id_geografia
# 4. Reemplaza el DataFrame vacío con tu lógica de transformación
# 5. Asegúrate que la estructura final coincida EXACTAMENTE con el schema
# 6. Valida que los id_perfil existan en dim_perfil
# 7. Valida que los id_causa existan en dim_causa_muerte
# 8. Prueba tu código con un dry run antes de ejecutar
# =============================================================================
