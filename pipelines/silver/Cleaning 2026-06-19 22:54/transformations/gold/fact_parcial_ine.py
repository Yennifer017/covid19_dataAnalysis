from pyspark import pipelines as dp
from pyspark.sql import functions as F

# =============================================================================
# FASE 2: TABLA DE HECHOS PARCIAL - INE (Mortalidad Guatemala)
# =============================================================================

@dp.materialized_view(
    comment="Hechos parciales de mortalidad desde INE (Guatemala)"
)
def covid19_gold_fact_parcial_ine():
    """
    Tabla de hechos parcial con mortalidad de INE.
    Mapea a las dimensiones maestras y cuenta fallecidos.
    Estructura: id_tiempo_mes, id_geografia, id_perfil, id_causa, cantidad_fallecidos, fuente
    """
    # Leer datos de INE ya limpiados (nombre totalmente calificado)
    df = spark.read.table("covid19.silver.silver_ine_deaths")
    
    # 1. MAPEO DE TIEMPO: anoreg + mesreg -> id_tiempo_mes
    df = df.withColumn(
        "id_tiempo_mes",
        F.concat(
            F.col("anoreg").cast("string"),
            F.lit("-"),
            F.lpad(F.col("mesreg").cast("string"), 2, "0")
        )
    )
    
    # 2. MAPEO DE GEOGRAFÍA: depocu -> id_geografia
    # Usar departamento de ocurrencia (depocu)
    df = df.withColumn(
        "id_geografia",
        F.concat(F.lit("GT-"), F.col("depocu").cast("string"))
    )
    
    # 3. MAPEO DE PERFIL: sexo + Edadif -> id_perfil
    # Clasificar edad en rangos
    df = df.withColumn(
        "rango_edad",
        F.when(F.col("Edadif") < 15, "0-14")
         .when((F.col("Edadif") >= 15) & (F.col("Edadif") < 65), "15-64")
         .when(F.col("Edadif") >= 65, "65+")
         .otherwise("Todas")  # Para datos sin edad
    )
    
    # Mapear sexo: 1=Hombre, 2=Mujer
    df = df.withColumn(
        "sexo_nombre",
        F.when(F.col("sexo") == 1, "Hombre")
         .when(F.col("sexo") == 2, "Mujer")
         .otherwise("Ambos")  # Para datos agregados sin sexo
    )
    
    # Construir id_perfil
    df = df.withColumn(
        "id_perfil",
        F.concat(
            F.when(F.col("sexo_nombre") == "Hombre", F.lit("H"))
             .when(F.col("sexo_nombre") == "Mujer", F.lit("M"))
             .otherwise(F.lit("A")),
            F.lit("-"),
            F.col("rango_edad")
        )
    )
    
    # 4. MAPEO DE CAUSA: Caudef -> id_causa
    # Clasificar causa según código/descripción (simplificado)
    df = df.withColumn(
        "id_causa",
        F.when(F.upper(F.col("Caudef")).contains("COVID") | 
               F.upper(F.col("Caudef")).contains("U07"), "COVID")
         .when(F.upper(F.col("Caudef")).contains("RESPIRAT") |
               F.upper(F.col("Caudef")).rlike("J[0-9]{2}"), "RESP")
         .when(F.upper(F.col("Caudef")).contains("CARDIO") |
               F.upper(F.col("Caudef")).rlike("I[0-9]{2}"), "CARDIO")
         .when(F.upper(F.col("Caudef")).contains("CANCER") |
               F.upper(F.col("Caudef")).contains("NEOPLAS") |
               F.upper(F.col("Caudef")).rlike("C[0-9]{2}"), "CANCER")
         .when(F.upper(F.col("Caudef")).contains("ACCIDENT") |
               F.upper(F.col("Caudef")).contains("VIOLENT") |
               F.upper(F.col("Caudef")).contains("HOMICID") |
               F.upper(F.col("Caudef")).rlike("V[0-9]{2}|X[0-9]{2}|Y[0-9]{2}"), "EXTERNA")
         .when((F.col("Caudef").isNull()) | (F.col("Caudef") == ""), "DESCONOCIDA")
         .otherwise("OTRA")
    )
    
    # 5. AGREGAR: Contar fallecidos por las dimensiones
    df = df.groupBy(
        "id_tiempo_mes",
        "id_geografia", 
        "id_perfil",
        "id_causa"
    ).agg(
        F.count("*").alias("cantidad_fallecidos")
    )
    
    # 6. Agregar columna de fuente
    df = df.withColumn("fuente", F.lit("INE"))
    
    # 7. Filtrar registros inválidos (sin tiempo o geografía)
    df = df.filter(
        F.col("id_tiempo_mes").isNotNull() &
        F.col("id_geografia").isNotNull()
    )
    
    return df.select(
        "id_tiempo_mes",
        "id_geografia",
        "id_perfil",
        "id_causa",
        "cantidad_fallecidos",
        "fuente"
    ).orderBy("id_tiempo_mes", "id_geografia", "id_perfil")
