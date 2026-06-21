from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.functions import col, year, month, when, isnan

# =============================================================================
# FASE 2: TABLA DE HECHOS PARCIAL - OMS (Datos globales COVID-19)
# =============================================================================

@dp.materialized_view(
    comment="Hechos parciales de mortalidad COVID-19 desde OMS (Datos globales)"
)
def covid19_gold_fact_parcial_oms():
    """
    Tabla de hechos parcial con mortalidad COVID-19 de la OMS.
    
    FUENTE: covid19.bronze.who_covid_19_global_daily_data
    - Datos diarios de COVID-19 por país
    - Cobertura global desde enero 2020
    - Guatemala: datos desde marzo 2020
    
    TRANSFORMACIONES:
    - Conversión de datos diarios a agregación mensual
    - Mapeo a nivel nacional (sin desglose departamental)
    - Perfil agregado (sin desglose por sexo/edad en fuente OMS)
    - Causa: COVID-19 exclusivamente
    
    ESTRUCTURA DE SALIDA:
    - id_tiempo_mes: STRING formato "YYYY-MM"
    - id_geografia: STRING (ej: "GT-NA" para Guatemala nacional)
    - id_perfil: STRING = "A-Todas" (Ambos sexos, todas las edades)
    - id_causa: STRING = "COVID" (Causa COVID-19)
    - cantidad_fallecidos: LONG (muertes mensuales)
    - fuente: STRING = "OMS"
    """
    
    # Leer datos de OMS (nombre totalmente calificado)
    df = spark.read.table("covid19.bronze.who_covid_19_global_daily_data")
    
    # FILTRO 1: Solo Guatemala (para alinearse con INE)
    df = df.filter(F.col("country") == "Guatemala")
    
    # FILTRO 2: Solo datos desde 2020 en adelante (inicio de COVID)
    df = df.filter(F.col("date_reported") >= "2020-01-01")
    
    # LIMPIEZA: Convertir "NaN" a 0 en new_deaths
    # Los "NaN" en la fuente OMS representan días sin muertes reportadas
    df = df.withColumn(
        "new_deaths_clean",
        when(
            isnan(F.col("new_deaths")) | F.col("new_deaths").isNull(),
            F.lit(0)
        ).otherwise(F.col("new_deaths"))
    )
    
    # TRANSFORMACIÓN 1: Extraer año y mes de date_reported
    df = df.withColumn("date_parsed", F.to_date(F.col("date_reported"), "yyyy-MM-dd"))
    df = df.withColumn("anio", F.year(F.col("date_parsed")))
    df = df.withColumn("mes", F.month(F.col("date_parsed")))
    
    # MAPEO 1: Crear id_tiempo_mes en formato "YYYY-MM"
    df = df.withColumn(
        "id_tiempo_mes",
        F.concat(
            F.col("anio").cast("string"),
            F.lit("-"),
            F.lpad(F.col("mes").cast("string"), 2, "0")
        )
    )
    
    # MAPEO 2: id_geografia - Guatemala nivel nacional
    # OMS no tiene desglose departamental, todo es nivel país
    df = df.withColumn("id_geografia", F.lit("GT-NA"))
    
    # MAPEO 3: id_perfil - Ambos sexos, todas las edades
    # OMS no proporciona desglose por sexo ni edad en esta tabla
    df = df.withColumn("id_perfil", F.lit("A-Todas"))
    
    # MAPEO 4: id_causa - COVID-19
    # Esta fuente es exclusivamente de COVID-19
    df = df.withColumn("id_causa", F.lit("COVID"))
    
    # AGREGACIÓN: Sumar muertes diarias por mes
    df = df.groupBy(
        "id_tiempo_mes",
        "id_geografia",
        "id_perfil",
        "id_causa"
    ).agg(
        F.sum("new_deaths_clean").cast("long").alias("cantidad_fallecidos")
    )
    
    # VALIDACIÓN: Filtrar registros con cantidad > 0
    # Solo incluir meses donde hubo fallecidos
    df = df.filter(F.col("cantidad_fallecidos") > 0)
    
    # Agregar columna de fuente
    df = df.withColumn("fuente", F.lit("OMS"))
    
    # VALIDACIÓN FINAL: Verificar que no haya nulls en las claves
    df = df.filter(
        F.col("id_tiempo_mes").isNotNull() &
        F.col("id_geografia").isNotNull() &
        F.col("id_perfil").isNotNull() &
        F.col("id_causa").isNotNull()
    )
    
    return df.select(
        "id_tiempo_mes",
        "id_geografia",
        "id_perfil",
        "id_causa",
        "cantidad_fallecidos",
        "fuente"
    ).orderBy("id_tiempo_mes")


# =============================================================================
# NOTAS DE IMPLEMENTACIÓN PARA YENI
# =============================================================================
"""
Esta implementación usa SOLO datos de COVID-19 de Guatemala desde la OMS.

LIMITACIONES DE LOS DATOS OMS:
- No hay desglose por departamento (solo nacional: GT-NA)
- No hay desglose por sexo/edad (perfil agregado: A-Todas)
- Solo cubre mortalidad COVID-19 (causa: COVID)
- Los datos son reportes diarios agregados a nivel mensual

COMPATIBILIDAD CON EL MODELO ESTRELLA:
✅ id_tiempo_mes: Formato correcto "YYYY-MM"
✅ id_geografia: "GT-NA" existe en dim_geografia (Guatemala Nacional)
✅ id_perfil: "A-Todas" existe en dim_perfil (Ambos sexos, Todas las edades)
✅ id_causa: "COVID" existe en dim_causa_muerte
✅ cantidad_fallecidos: Agregación mensual de new_deaths
✅ fuente: "OMS"

POSIBLES MEJORAS FUTURAS (Opcionales para Yeni):
1. Agregar datos de otros países de who_covid_19_global_daily_data
   - Costa Rica: id_geografia = "CR-NA"
   - Otros países de interés
   
2. Usar who_mortality para causas no-COVID si se corrige el esquema
   - Requiere limpieza de la tabla (columnas desalineadas)
   - Permitiría análisis de otras causas de muerte

3. Agregar validación contra totales de INE
   - Comparar totales mensuales OMS vs INE
   - Detectar discrepancias entre fuentes

EJECUCIÓN:
Para probar solo esta tabla:
  startPipelineUpdate(
      fullRefresh=False,
      refreshSelectionByDataset=["covid19_gold_fact_parcial_oms"]
  )

Para incluirla en la consolidación final:
  - Simplemente completar esta tabla
  - consolidacion_final.py la incluirá automáticamente
"""
