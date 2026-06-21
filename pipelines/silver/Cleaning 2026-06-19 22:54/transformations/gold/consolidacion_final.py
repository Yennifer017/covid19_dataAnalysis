from pyspark import pipelines as dp
from pyspark.sql import functions as F

# =============================================================================
# FASE 3: CONSOLIDACIÓN FINAL (Diseño objetivo)
# =============================================================================
# Este archivo unifica todas las tablas parciales en la tabla maestra
# =============================================================================

@dp.materialized_view(
    comment="Tabla de hechos unificada: Mortalidad de todas las fuentes consolidadas"
)
def covid19_gold_fact_mortalidad_unificada():
    """
    Tabla de hechos maestra que consolida TODAS las fuentes de mortalidad.
    
    FUENTES UNIFICADAS:
    - fact_parcial_ine (Guatemala INE)
    - fact_parcial_oms (OMS datos globales)
    - fact_parcial_costa_rica (Costa Rica)
    
    ESTRUCTURA FINAL:
    - id_tiempo_mes: STRING formato "YYYY-MM"
    - id_geografia: STRING (ej: "GT-1", "CR-NA")
    - id_perfil: STRING formato "X-rango" (ej: "H-15-64", "M-65+")
    - id_causa: STRING (ej: "COVID", "RESP", "CARDIO")
    - cantidad_fallecidos: LONG
    - fuente: STRING (ej: "INE", "OMS", "CR")
    
    Este dataset permite analizar mortalidad desde múltiples ángulos:
    - Temporal: Filtrar por periodo Pre-COVID vs Pandemia
    - Geográfico: Comparar departamentos de Guatemala con Costa Rica
    - Demográfico: Analizar por sexo y rango de edad
    - Por causa: Identificar patrones de COVID vs otras causas
    - Por fuente: Validar consistencia entre fuentes
    """
    
    # Leer todas las tablas parciales (nombres totalmente calificados)
    df_ine = spark.read.table("covid19.gold.covid19_gold_fact_parcial_ine")
    df_oms = spark.read.table("covid19.gold.covid19_gold_fact_parcial_oms")
    df_costa_rica = spark.read.table("covid19.gold.covid19_gold_fact_parcial_costa_rica")
    
    # UNION ALL de todas las fuentes
    df_consolidado = df_ine.union(df_oms).union(df_costa_rica)
    
    # Validaciones de calidad
    # 1. Verificar que todos los registros tengan las claves foráneas válidas
    df_consolidado = df_consolidado.filter(
        F.col("id_tiempo_mes").isNotNull() &
        F.col("id_geografia").isNotNull() &
        F.col("id_perfil").isNotNull() &
        F.col("id_causa").isNotNull() &
        F.col("cantidad_fallecidos").isNotNull() &
        (F.col("cantidad_fallecidos") > 0)  # Solo registros con fallecidos
    )
    
    # 2. Agregar metadatos útiles
    df_consolidado = df_consolidado.withColumn(
        "fecha_actualizacion",
        F.current_timestamp()
    )
    
    return df_consolidado.select(
        "id_tiempo_mes",
        "id_geografia",
        "id_perfil",
        "id_causa",
        "cantidad_fallecidos",
        "fuente",
        "fecha_actualizacion"
    ).orderBy("id_tiempo_mes", "id_geografia", "fuente")


# =============================================================================
# QUERY DE EJEMPLO: Cómo usar la tabla consolidada con las dimensiones
# =============================================================================
"""
-- Total de fallecidos por COVID en Guatemala durante la pandemia
SELECT 
    t.periodo,
    g.nombre_departamento,
    p.sexo,
    p.rango_edad,
    SUM(f.cantidad_fallecidos) as total_fallecidos
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_tiempo t ON f.id_tiempo_mes = t.id_tiempo_mes
JOIN covid19.gold.covid19_gold_dim_geografia g ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_perfil p ON f.id_perfil = p.id_perfil
JOIN covid19.gold.covid19_gold_dim_causa_muerte c ON f.id_causa = c.id_causa
WHERE 
    c.es_covid = TRUE
    AND t.periodo = 'Pandemia'
    AND g.pais = 'Guatemala'
    AND f.fuente = 'INE'
GROUP BY t.periodo, g.nombre_departamento, p.sexo, p.rango_edad
ORDER BY total_fallecidos DESC;

-- Comparación de mortalidad COVID: Guatemala vs Costa Rica
SELECT 
    g.pais,
    t.anio,
    SUM(f.cantidad_fallecidos) as fallecidos_covid
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_geografia g ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_tiempo t ON f.id_tiempo_mes = t.id_tiempo_mes
JOIN covid19.gold.covid19_gold_dim_causa_muerte c ON f.id_causa = c.id_causa
WHERE c.es_covid = TRUE
GROUP BY g.pais, t.anio
ORDER BY g.pais, t.anio;
"""
