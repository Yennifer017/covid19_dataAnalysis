from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import *

# =============================================================================
# FASE 1: DIMENSIONES MAESTRAS (Base compartida para todo el equipo)
# =============================================================================

@dp.materialized_view(
    comment="Dimensión de tiempo a nivel mes (2015-2026)"
)
def covid19_gold_dim_tiempo():
    """
    Dimensión temporal con periodos Pre-COVID y Pandemia.
    Cobertura: 2015-01 a 2026-12
    """
    # Generar fechas desde 2015 hasta 2026
    df = spark.range(2015, 2027).withColumnRenamed("id", "anio")
    
    # Expandir a 12 meses por año
    meses = spark.range(1, 13).withColumnRenamed("id", "mes")
    df = df.crossJoin(meses)
    
    # Crear id_tiempo_mes en formato "YYYY-MM"
    df = df.withColumn(
        "id_tiempo_mes",
        F.concat(
            F.col("anio").cast("string"),
            F.lit("-"),
            F.lpad(F.col("mes").cast("string"), 2, "0")
        )
    )
    
    # Clasificar periodo: Pre-COVID (antes de marzo 2020) vs Pandemia (marzo 2020 en adelante)
    df = df.withColumn(
        "periodo",
        F.when((F.col("anio") < 2020) | 
               ((F.col("anio") == 2020) & (F.col("mes") < 3)), "Pre-COVID")
         .otherwise("Pandemia")
    )
    
    # Nombre del mes en español
    mes_nombres = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    mes_mapping = F.create_map([F.lit(x) for pair in mes_nombres.items() for x in pair])
    df = df.withColumn("nombre_mes", mes_mapping[F.col("mes")])
    
    return df.select(
        "id_tiempo_mes",
        "anio",
        "mes",
        "nombre_mes",
        "periodo"
    ).orderBy("id_tiempo_mes")


@dp.materialized_view(
    comment="Dimensión de geografía (Guatemala y Costa Rica)"
)
def covid19_gold_dim_geografia():
    """
    Dimensión geográfica con departamentos de Guatemala y Costa Rica.
    Incluye mapeos desde códigos INE/INACIF.
    """
    # Cargar departamentos de Guatemala desde INACIF
    gt_dept = spark.read.table("covid19.bronze.inacif_departamentos") \
        .withColumn("pais", F.lit("Guatemala")) \
        .withColumn("id_geografia", F.concat(F.lit("GT-"), F.col("id").cast("string"))) \
        .select(
            F.col("id_geografia"),
            F.col("pais"),
            F.col("id").alias("id_departamento"),
            F.col("nombre").alias("nombre_departamento")
        )
    
    # Agregar Costa Rica (nivel país, sin subdivisión por ahora)
    cr_row = spark.createDataFrame([
        ("CR-NA", "Costa Rica", 0, "Nacional")
    ], ["id_geografia", "pais", "id_departamento", "nombre_departamento"])
    
    # Unir ambos
    df = gt_dept.union(cr_row)
    
    return df.orderBy("pais", "id_departamento")


@dp.materialized_view(
    comment="Dimensión de perfil demográfico (sexo y rango de edad)"
)
def covid19_gold_dim_perfil():
    """
    Dimensión de perfil demográfico combinando sexo y rango de edad.
    Incluye categorías agregadas (Ambos sexos, Todas las edades).
    """
    # Definir combinaciones de sexo y rango de edad
    perfiles = [
        # Hombres por rango
        ("H-0-14", "Hombre", "0-14"),
        ("H-15-64", "Hombre", "15-64"),
        ("H-65+", "Hombre", "65+"),
        ("H-Todas", "Hombre", "Todas"),
        
        # Mujeres por rango
        ("M-0-14", "Mujer", "0-14"),
        ("M-15-64", "Mujer", "15-64"),
        ("M-65+", "Mujer", "65+"),
        ("M-Todas", "Mujer", "Todas"),
        
        # Ambos sexos por rango
        ("A-0-14", "Ambos", "0-14"),
        ("A-15-64", "Ambos", "15-64"),
        ("A-65+", "Ambos", "65+"),
        ("A-Todas", "Ambos", "Todas"),
    ]
    
    schema = StructType([
        StructField("id_perfil", StringType(), False),
        StructField("sexo", StringType(), False),
        StructField("rango_edad", StringType(), False)
    ])
    
    df = spark.createDataFrame(perfiles, schema)
    
    return df.orderBy("sexo", "rango_edad")


@dp.materialized_view(
    comment="Dimensión de causa de muerte (clasificación general + flag COVID)"
)
def covid19_gold_dim_causa_muerte():
    """
    Dimensión de causas de muerte con categorías generales.
    Incluye clasificación de COVID-19 y otras enfermedades respiratorias.
    """
    # Base: causas desde INACIF
    inacif_causas = spark.read.table("covid19.bronze.inacif_causas_muerte") \
        .select(
            F.concat(F.lit("INACIF-"), F.col("id").cast("string")).alias("id_causa"),
            F.col("nombre").alias("nombre_causa")
        )
    
    # Clasificar en categorías generales y detectar COVID
    inacif_causas = inacif_causas.withColumn(
        "categoria_general",
        F.when(F.lower(F.col("nombre_causa")).contains("covid"), "COVID-19")
         .when(F.lower(F.col("nombre_causa")).contains("respirat"), "Enfermedad Respiratoria")
         .when(F.lower(F.col("nombre_causa")).contains("cardio"), "Enfermedad Cardiovascular")
         .when(F.lower(F.col("nombre_causa")).contains("violent") | 
               F.lower(F.col("nombre_causa")).contains("accident") |
               F.lower(F.col("nombre_causa")).contains("homicid"), "Causa Externa")
         .otherwise("Otra")
    ).withColumn(
        "es_covid",
        F.lower(F.col("nombre_causa")).contains("covid")
    )
    
    # Agregar causas sintéticas para mapeos de INE (CIE-10 resumidos)
    causas_sinteticas = [
        ("RESP", "Enfermedad Respiratoria", "Enfermedades del sistema respiratorio", False),
        ("COVID", "COVID-19", "COVID-19 (U07.1 o U07.2)", True),
        ("CARDIO", "Enfermedad Cardiovascular", "Enfermedades del sistema circulatorio", False),
        ("CANCER", "Cáncer", "Tumores (neoplasias)", False),
        ("EXTERNA", "Causa Externa", "Causas externas de mortalidad", False),
        ("OTRA", "Otra", "Otras causas de muerte", False),
        ("DESCONOCIDA", "Desconocida", "Causa no especificada", False)
    ]
    
    schema = StructType([
        StructField("id_causa", StringType(), False),
        StructField("categoria_general", StringType(), False),
        StructField("nombre_causa", StringType(), False),
        StructField("es_covid", BooleanType(), False)
    ])
    
    df_sinteticas = spark.createDataFrame(causas_sinteticas, schema)
    
    # Unir ambas fuentes
    inacif_causas = inacif_causas.select("id_causa", "categoria_general", "nombre_causa", "es_covid")
    df = inacif_causas.union(df_sinteticas)
    
    return df.orderBy("categoria_general", "id_causa")
