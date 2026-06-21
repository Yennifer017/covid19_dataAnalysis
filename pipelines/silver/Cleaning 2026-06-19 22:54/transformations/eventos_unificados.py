from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import LongType

@dp.materialized_view(
    comment="Datos unificados de eventos por año (2015-2026) en formato normalizado"
)
def silver_eventos_unificados():
    """
    Unifica las tablas desagregados_por_evento de diferentes años,
    normalizando las diferencias de formato:
    - 2016: falta diciembre, usa total_general
    - 2026: solo hasta mayo, usa total
    - 2025: usa total
    - 2015: meses en double
    """
    
    # Lista de años y sus configuraciones
    years_config = {
        2015: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2016: {"has_diciembre": False, "total_col": "total_general", "complete": True},
        2017: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2018: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2019: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2020: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2021: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2022: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2023: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2024: {"has_diciembre": True, "total_col": "total_anual", "complete": True},
        2025: {"has_diciembre": True, "total_col": "total", "complete": True},
        2026: {"has_diciembre": False, "total_col": "total", "complete": False}
    }
    
    # Lista para almacenar los DataFrames transformados
    dfs = []
    
    for year, config in years_config.items():
        # Leer tabla del año
        df = spark.read.table(f"covid19.bronze.desagregados_por_evento_{year}")
        
        # Agregar columna de año
        df = df.withColumn("anio", F.lit(year))
        
        # Normalizar nombre de columna total
        df = df.withColumnRenamed(config["total_col"], "total_anual")
        
        # Convertir meses de double a bigint (para 2015)
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
                 "julio", "agosto", "septiembre", "octubre", "noviembre"]
        
        for mes in meses:
            if mes in df.columns:
                df = df.withColumn(mes, F.col(mes).cast(LongType()))
        
        # Agregar diciembre si no existe (caso 2016 y 2026)
        if not config["has_diciembre"]:
            df = df.withColumn("diciembre", F.lit(None).cast(LongType()))
        else:
            df = df.withColumn("diciembre", F.col("diciembre").cast(LongType()))
        
        # Agregar columnas faltantes para 2026 (junio-noviembre)
        if year == 2026:
            meses_faltantes = ["junio", "julio", "agosto", "septiembre", "octubre", "noviembre"]
            for mes in meses_faltantes:
                df = df.withColumn(mes, F.lit(None).cast(LongType()))
        
        # Seleccionar columnas en orden consistente
        df = df.select(
            "anio",
            "evento",
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
            "total_anual"
        )
        
        dfs.append(df)
    
    # Unir todos los DataFrames
    df_unificado = dfs[0]
    for df in dfs[1:]:
        df_unificado = df_unificado.union(df)
    
    return df_unificado


@dp.materialized_view(
    comment="Eventos desagregados en formato long (una fila por evento-año-mes)"
)
def silver_eventos_por_mes():
    """
    Transforma los datos de formato wide (una columna por mes) 
    a formato long (una fila por mes) usando UNPIVOT, facilitando análisis temporal.
    """
    df = spark.read.table("silver_eventos_unificados")
    
    # Definir columnas de meses para despivotar
    meses_cols = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    
    # UNPIVOT: convertir columnas de meses a filas
    df_unpivot = df.unpivot(
        ids=["anio", "evento", "total_anual"],
        values=meses_cols,
        variableColumnName="mes_nombre",
        valueColumnName="cantidad"
    )
    
    # Mapeo de nombre de mes a número
    mes_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
    # Crear expresión CASE para mapear mes_nombre a mes_numero
    mes_mapping = F.create_map([F.lit(x) for pair in mes_map.items() for x in pair])
    
    df_final = df_unpivot.withColumn(
        "mes_numero",
        mes_mapping[F.col("mes_nombre")]
    )
    
    # Crear columna de fecha (primer día del mes)
    df_final = df_final.withColumn(
        "fecha",
        F.to_date(F.concat_ws("-", F.col("anio"), F.col("mes_numero"), F.lit("01")))
    )
    
    # Filtrar valores NULL (meses sin datos)
    df_final = df_final.filter(F.col("cantidad").isNotNull())
    
    # Ordenar y seleccionar columnas finales
    return df_final.select(
        "fecha",
        "anio",
        "mes_numero",
        "mes_nombre",
        "evento",
        "cantidad"
    ).orderBy("fecha", "evento")
