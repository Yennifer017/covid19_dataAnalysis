from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.functions import col, year, month, when, isnan

# =============================================================================
# FASE 2: TABLA DE HECHOS PARCIAL - COSTA RICA (Datos OMS)
# =============================================================================

@dp.materialized_view(
    comment="Hechos parciales de mortalidad COVID-19 desde Costa Rica (OMS)"
)
def covid19_gold_fact_parcial_costa_rica():
    """
    Tabla de hechos parcial con mortalidad COVID-19 de Costa Rica.
    
    FUENTE: covid19.bronze.who_covid_19_global_daily_data
    - Datos diarios de COVID-19 por país (OMS)
    - Costa Rica: datos desde marzo 2020
    - Cobertura global, filtrando solo Costa Rica
    
    TRANSFORMACIONES:
    - Conversión de datos diarios a agregación mensual
    - Mapeo a nivel nacional (sin desglose provincial/cantonal)
    - Perfil agregado (sin desglose por sexo/edad en fuente OMS)
    - Causa: COVID-19 exclusivamente
    
    ESTRUCTURA DE SALIDA:
    - id_tiempo_mes: STRING formato "YYYY-MM"
    - id_geografia: STRING = "CR-NA" (Costa Rica nacional)
    - id_perfil: STRING = "A-Todas" (Ambos sexos, todas las edades)
    - id_causa: STRING = "COVID" (Causa COVID-19)
    - cantidad_fallecidos: LONG (muertes mensuales)
    - fuente: STRING = "CR"
    
    NOTA IMPORTANTE:
    Según instrucciones del equipo, NO se usan las siguientes tablas bronze:
    - mortalidad_categorias_costa_rica_2020/2021/2022
    - mortalidad_indicadores_costa_rica
    - mortalidad_por_edades_costa_rica
    - desagregados_por_departamento_20xx
    
    En su lugar, se usa la fuente OMS (who_covid_19_global_daily_data)
    que es consistente con la fuente usada para Guatemala (Yeni).
    """
    
    # Leer datos de OMS (nombre totalmente calificado)
    df = spark.read.table("covid19.bronze.who_covid_19_global_daily_data")
    
    # FILTRO 1: Solo Costa Rica
    df = df.filter(F.col("country") == "Costa Rica")
    
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
    
    # MAPEO 2: id_geografia - Costa Rica nivel nacional
    # OMS no tiene desglose provincial/cantonal, todo es nivel país
    df = df.withColumn("id_geografia", F.lit("CR-NA"))
    
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
    df = df.withColumn("fuente", F.lit("CR"))
    
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
# NOTAS DE IMPLEMENTACIÓN PARA BYRON
# =============================================================================
"""
Esta implementación usa datos de COVID-19 de Costa Rica desde la OMS.

FUENTE DE DATOS:
- covid19.bronze.who_covid_19_global_daily_data (misma fuente que Guatemala-OMS)
- Datos diarios reportados por Costa Rica a la OMS
- Período: marzo 2020 - mayo 2026
- 734 días con muertes reportadas

LIMITACIONES DE LOS DATOS OMS:
- No hay desglose provincial/cantonal (solo nacional: CR-NA)
- No hay desglose por sexo/edad (perfil agregado: A-Todas)
- Solo cubre mortalidad COVID-19 (causa: COVID)
- Los datos son reportes diarios agregados a nivel mensual

COMPATIBILIDAD CON EL MODELO ESTRELLA:
✅ id_tiempo_mes: Formato correcto "YYYY-MM"
✅ id_geografia: "CR-NA" existe en dim_geografia (Costa Rica Nacional)
✅ id_perfil: "A-Todas" existe en dim_perfil (Ambos sexos, Todas las edades)
✅ id_causa: "COVID" existe en dim_causa_muerte
✅ cantidad_fallecidos: Agregación mensual de new_deaths
✅ fuente: "CR"

CONSISTENCIA CON OTRAS FUENTES:
- Misma estructura que fact_parcial_oms (Guatemala OMS)
- Misma fuente de datos (who_covid_19_global_daily_data)
- Permite comparación directa Guatemala vs Costa Rica
- Ambos países a nivel nacional sin desglose

TABLAS EXCLUIDAS (Según instrucciones del equipo):
❌ covid19.bronze.mortalidad_categorias_costa_rica_2020
❌ covid19.bronze.mortalidad_categorias_costa_rica_2021
❌ covid19.bronze.mortalidad_categorias_costa_rica_2022
❌ covid19.bronze.mortalidad_indicadores_costa_rica
❌ covid19.bronze.mortalidad_por_edades_costa_rica
❌ covid19.bronze.desagregados_por_departamento_20xx

POSIBLES MEJORAS FUTURAS (Opcionales para Byron):
1. Si se obtienen datos nacionales de Costa Rica con desglose:
   - Agregar sexo/edad (requeriría fuente diferente)
   - Agregar nivel provincial (requeriría actualizar dim_geografia)
   - Agregar otras causas de muerte (requeriría fuente diferente)

2. Agregar validación cruzada:
   - Comparar totales OMS vs fuentes nacionales de Costa Rica
   - Detectar discrepancias entre reportes

3. Análisis comparativo:
   - Tasas de mortalidad per cápita Guatemala vs Costa Rica
   - Curvas epidemiológicas comparadas
   - Efectividad de respuestas de salud pública

EJECUCIÓN:
Para probar solo esta tabla:
  startPipelineUpdate(
      fullRefresh=False,
      refreshSelectionByDataset=["covid19_gold_fact_parcial_costa_rica"]
  )

Para incluirla en la consolidación final:
  - Simplemente completar esta tabla
  - consolidacion_final.py la incluirá automáticamente
  - Permitirá análisis comparativo Guatemala vs Costa Rica
"""
