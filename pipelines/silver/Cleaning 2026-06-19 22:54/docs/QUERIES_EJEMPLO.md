# 📝 Queries de Ejemplo - Modelo Estrella COVID-19

**Proyecto:** Análisis comparativo de mortalidad COVID-19  
**Última actualización:** 21 de junio de 2026

Este documento contiene queries SQL listas para ejecutar que demuestran diferentes casos de uso del modelo estrella.

---

## Índice de Queries

1. [Comparación Guatemala vs Costa Rica (COVID-19 por año)](#query-1-comparación-guatemala-vs-costa-rica-covid-19-por-año)
2. [Comparación de fuentes (INE vs OMS) para Guatemala](#query-2-comparación-de-fuentes-ine-vs-oms-para-guatemala)
3. [Mortalidad COVID en Guatemala durante pandemia (INE departamental)](#query-3-mortalidad-covid-en-guatemala-durante-pandemia-ine-departamental)
4. [Análisis por grupo etario (solo INE con desglose)](#query-4-análisis-por-grupo-etario-solo-ine-con-desglose)
5. [Eventos civiles vs mortalidad (contexto)](#query-5-eventos-civiles-vs-mortalidad-contexto)
6. [Top departamentos con mayor mortalidad COVID](#query-6-top-departamentos-con-mayor-mortalidad-covid)
7. [Mortalidad por sexo y edad (análisis demográfico)](#query-7-mortalidad-por-sexo-y-edad-análisis-demográfico)
8. [Tendencia mensual COVID-19 (ambos países)](#query-8-tendencia-mensual-covid-19-ambos-países)
9. [Comparación Pre-COVID vs Pandemia](#query-9-comparación-pre-covid-vs-pandemia)
10. [Causas de muerte más frecuentes](#query-10-causas-de-muerte-más-frecuentes)

---

## Query 1: Comparación Guatemala vs Costa Rica (COVID-19 por año)

**Objetivo:** Comparar la mortalidad por COVID-19 entre Guatemala y Costa Rica usando datos de la OMS.

```sql
SELECT 
    g.pais,
    CAST(SUBSTRING(f.id_tiempo_mes, 1, 4) AS INT) as anio,
    COUNT(DISTINCT f.id_tiempo_mes) as meses_con_datos,
    SUM(f.cantidad_fallecidos) as total_fallecidos_covid
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_geografia g 
    ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
WHERE c.es_covid = TRUE
  AND f.fuente IN ('OMS', 'CR')
GROUP BY g.pais, SUBSTRING(f.id_tiempo_mes, 1, 4)
ORDER BY anio, g.pais;
```

**Resultados esperados:**
```
+-------------+------+-----------------+-------------------------+
| pais        | anio | meses_con_datos | total_fallecidos_covid  |
+-------------+------+-----------------+-------------------------+
| Costa Rica  | 2020 |       10        |         2,156           |
| Guatemala   | 2020 |       10        |         4,803           |
| Costa Rica  | 2021 |       12        |         5,198           |
| Guatemala   | 2021 |       12        |        11,299           |
| Costa Rica  | 2022 |       12        |         1,731           |
| Guatemala   | 2022 |       12        |         3,896           |
| Costa Rica  | 2023 |        5        |          281            |
| Guatemala   | 2023 |        7        |          203            |
+-------------+------+-----------------+-------------------------+
```

**Insights:**
* Guatemala tuvo 2.2x más fallecidos absolutos que Costa Rica (19,998 vs 9,085 en 2020-2022)
* Ambos países alcanzaron su pico en 2021
* La mortalidad bajó significativamente en 2022 para ambos países

---

## Query 2: Comparación de fuentes (INE vs OMS) para Guatemala

**Objetivo:** Comparar las cifras de COVID-19 reportadas por INE (nacional) vs OMS para Guatemala.

```sql
SELECT 
    f.fuente,
    CAST(SUBSTRING(f.id_tiempo_mes, 1, 4) AS INT) as anio,
    COUNT(DISTINCT f.id_tiempo_mes) as meses_con_datos,
    SUM(f.cantidad_fallecidos) as total_fallecidos_covid
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
WHERE c.es_covid = TRUE
  AND f.fuente IN ('INE', 'OMS')
GROUP BY f.fuente, SUBSTRING(f.id_tiempo_mes, 1, 4)
ORDER BY anio, f.fuente;
```

**Utilidad:**
* Detectar discrepancias entre fuentes oficiales
* Validar calidad de datos
* Identificar posibles rezagos en reportes

**Nota:** Las diferencias pueden deberse a:
* Criterios de clasificación COVID diferentes
* Timing de reporte (fecha de ocurrencia vs fecha de registro)
* Cobertura geográfica (INE puede tener datos más completos a nivel local)

---

## Query 3: Mortalidad COVID en Guatemala durante pandemia (INE departamental)

**Objetivo:** Análisis detallado de COVID-19 en Guatemala con desglose por departamento, sexo y edad.

```sql
SELECT 
    t.anio,
    t.nombre_mes,
    g.nombre_departamento,
    p.sexo,
    p.rango_edad,
    SUM(f.cantidad_fallecidos) as total_fallecidos
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
JOIN covid19.gold.covid19_gold_dim_geografia g 
    ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_perfil p 
    ON f.id_perfil = p.id_perfil
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
WHERE 
    c.es_covid = TRUE
    AND t.periodo = 'Pandemia'
    AND g.pais = 'Guatemala'
    AND f.fuente = 'INE'
GROUP BY t.anio, t.mes, t.nombre_mes, g.nombre_departamento, p.sexo, p.rango_edad
ORDER BY t.anio, t.mes, total_fallecidos DESC
LIMIT 100;
```

**Casos de uso:**
* Identificar hotspots geográficos (departamentos más afectados)
* Análisis de grupos de riesgo por edad
* Distribución por sexo
* Evolución temporal a nivel departamental

---

## Query 4: Análisis por grupo etario (solo INE con desglose)

**Objetivo:** Comparar mortalidad entre grupos etarios en Pre-COVID vs Pandemia.

```sql
SELECT 
    p.rango_edad,
    t.periodo,
    COUNT(DISTINCT f.id_tiempo_mes) as meses_con_datos,
    SUM(f.cantidad_fallecidos) as total_fallecidos,
    ROUND(AVG(f.cantidad_fallecidos), 2) as promedio_mensual,
    ROUND(SUM(f.cantidad_fallecidos) * 100.0 / SUM(SUM(f.cantidad_fallecidos)) OVER (PARTITION BY t.periodo), 2) as porcentaje_del_periodo
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_perfil p 
    ON f.id_perfil = p.id_perfil
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
WHERE f.fuente = 'INE'
  AND p.sexo = 'Ambos'  -- Para evitar duplicación
  AND p.rango_edad != 'Todas'  -- Excluir agregado
GROUP BY p.rango_edad, t.periodo
ORDER BY t.periodo, total_fallecidos DESC;
```

**Métricas calculadas:**
* Total de fallecidos por grupo
* Promedio mensual
* Porcentaje del total en cada periodo

**Insights esperados:**
* ¿Aumentó la mortalidad en adultos mayores durante la pandemia?
* ¿Cambió la distribución etaria de muertes?

---

## Query 5: Eventos civiles vs mortalidad (contexto)

**Objetivo:** Analizar el impacto de COVID-19 en eventos demográficos (nacimientos, matrimonios).

```sql
-- Nacimientos vs Defunciones por año
WITH nacimientos AS (
    SELECT 
        SUBSTRING(id_tiempo_mes, 1, 4) as anio,
        SUM(cantidad) as total_nacimientos
    FROM covid19.gold.covid19_gold_fact_contexto_renap
    WHERE tipo_evento = 'Nacimientos'
    GROUP BY SUBSTRING(id_tiempo_mes, 1, 4)
),
defunciones AS (
    SELECT 
        SUBSTRING(id_tiempo_mes, 1, 4) as anio,
        SUM(cantidad_fallecidos) as total_defunciones
    FROM covid19.gold.covid19_gold_fact_mortalidad_unificada
    WHERE fuente = 'INE'
    GROUP BY SUBSTRING(id_tiempo_mes, 1, 4)
),
matrimonios AS (
    SELECT 
        SUBSTRING(id_tiempo_mes, 1, 4) as anio,
        SUM(cantidad) as total_matrimonios
    FROM covid19.gold.covid19_gold_fact_contexto_renap
    WHERE tipo_evento = 'Matrimonios'
    GROUP BY SUBSTRING(id_tiempo_mes, 1, 4)
)
SELECT 
    n.anio,
    n.total_nacimientos,
    d.total_defunciones,
    m.total_matrimonios,
    n.total_nacimientos - d.total_defunciones as crecimiento_natural,
    ROUND((n.total_nacimientos - d.total_defunciones) * 100.0 / n.total_nacimientos, 2) as tasa_crecimiento_pct
FROM nacimientos n
JOIN defunciones d ON n.anio = d.anio
JOIN matrimonios m ON n.anio = m.anio
ORDER BY n.anio;
```

**Análisis posible:**
* ¿Cayeron los matrimonios durante la pandemia?
* ¿Afectó COVID-19 la natalidad?
* Crecimiento natural poblacional

---

## Query 6: Top departamentos con mayor mortalidad COVID

**Objetivo:** Ranking de departamentos de Guatemala más afectados por COVID-19.

```sql
SELECT 
    g.nombre_departamento,
    COUNT(DISTINCT f.id_tiempo_mes) as meses_con_datos,
    SUM(f.cantidad_fallecidos) as total_fallecidos_covid,
    ROUND(AVG(f.cantidad_fallecidos), 2) as promedio_mensual,
    MIN(f.id_tiempo_mes) as primer_registro,
    MAX(f.id_tiempo_mes) as ultimo_registro
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_geografia g 
    ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
WHERE c.es_covid = TRUE 
  AND f.fuente = 'INE'
  AND g.id_geografia NOT LIKE '%-NA'  -- Excluir agregados nacionales
GROUP BY g.nombre_departamento
ORDER BY total_fallecidos_covid DESC
LIMIT 10;
```

**Visualización sugerida:**
* Mapa de calor de Guatemala
* Gráfico de barras horizontal

---

## Query 7: Mortalidad por sexo y edad (análisis demográfico)

**Objetivo:** Identificar grupos demográficos más vulnerables durante COVID-19.

```sql
SELECT 
    p.sexo,
    p.rango_edad,
    SUM(CASE WHEN c.es_covid = TRUE THEN f.cantidad_fallecidos ELSE 0 END) as fallecidos_covid,
    SUM(CASE WHEN c.es_covid = FALSE THEN f.cantidad_fallecidos ELSE 0 END) as fallecidos_otras_causas,
    SUM(f.cantidad_fallecidos) as total_fallecidos,
    ROUND(
        SUM(CASE WHEN c.es_covid = TRUE THEN f.cantidad_fallecidos ELSE 0 END) * 100.0 / 
        SUM(f.cantidad_fallecidos), 
        2
    ) as porcentaje_covid
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_perfil p 
    ON f.id_perfil = p.id_perfil
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
WHERE f.fuente = 'INE'
  AND t.periodo = 'Pandemia'
  AND p.sexo != 'Ambos'  -- Solo H y M individuales
  AND p.rango_edad != 'Todas'
GROUP BY p.sexo, p.rango_edad
ORDER BY fallecidos_covid DESC;
```

**Insights esperados:**
* Grupos etarios de mayor riesgo
* Diferencias entre hombres y mujeres
* Proporción de muertes atribuibles a COVID vs otras causas

---

## Query 8: Tendencia mensual COVID-19 (ambos países)

**Objetivo:** Visualizar la evolución temporal de COVID-19 en Guatemala y Costa Rica.

```sql
SELECT 
    f.id_tiempo_mes,
    t.anio,
    t.nombre_mes,
    g.pais,
    SUM(f.cantidad_fallecidos) as fallecidos_covid
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
JOIN covid19.gold.covid19_gold_dim_geografia g 
    ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
WHERE c.es_covid = TRUE
  AND f.fuente IN ('OMS', 'CR')
  AND f.id_tiempo_mes >= '2020-03'
GROUP BY f.id_tiempo_mes, t.anio, t.nombre_mes, g.pais
ORDER BY f.id_tiempo_mes, g.pais;
```

**Visualización sugerida:**
* Gráfico de líneas con dos series (GT y CR)
* Identificar olas de contagio
* Comparar patrones temporales

---

## Query 9: Comparación Pre-COVID vs Pandemia

**Objetivo:** Medir el exceso de mortalidad durante la pandemia comparado con años anteriores.

```sql
SELECT 
    t.periodo,
    COUNT(DISTINCT f.id_tiempo_mes) as total_meses,
    SUM(f.cantidad_fallecidos) as total_fallecidos,
    ROUND(AVG(f.cantidad_fallecidos), 2) as promedio_mensual,
    ROUND(STDDEV(f.cantidad_fallecidos), 2) as desviacion_estandar
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
WHERE f.fuente = 'INE'
GROUP BY t.periodo
ORDER BY t.periodo;
```

**Análisis de exceso de mortalidad:**
```sql
-- Comparación año a año
SELECT 
    t.anio,
    t.periodo,
    SUM(f.cantidad_fallecidos) as total_fallecidos,
    SUM(f.cantidad_fallecidos) - LAG(SUM(f.cantidad_fallecidos)) OVER (ORDER BY t.anio) as diferencia_vs_anio_anterior,
    ROUND(
        (SUM(f.cantidad_fallecidos) - LAG(SUM(f.cantidad_fallecidos)) OVER (ORDER BY t.anio)) * 100.0 / 
        LAG(SUM(f.cantidad_fallecidos)) OVER (ORDER BY t.anio), 
        2
    ) as porcentaje_cambio
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
WHERE f.fuente = 'INE'
GROUP BY t.anio, t.periodo
ORDER BY t.anio;
```

---

## Query 10: Causas de muerte más frecuentes

**Objetivo:** Identificar las principales causas de mortalidad en Guatemala (toda la muestra).

```sql
SELECT 
    c.categoria_general,
    c.es_covid,
    COUNT(DISTINCT f.id_tiempo_mes) as meses_registrados,
    SUM(f.cantidad_fallecidos) as total_fallecidos,
    ROUND(SUM(f.cantidad_fallecidos) * 100.0 / SUM(SUM(f.cantidad_fallecidos)) OVER (), 2) as porcentaje_total,
    ROUND(AVG(f.cantidad_fallecidos), 2) as promedio_mensual
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
WHERE f.fuente = 'INE'
GROUP BY c.categoria_general, c.es_covid
ORDER BY total_fallecidos DESC
LIMIT 10;
```

**Dashboard sugerido:**
* Gráfico de pastel (pie chart) de causas
* Evolución temporal de cada categoría
* Comparación Pre-COVID vs Pandemia por causa

---

## 🎨 Visualizaciones Recomendadas

### Para Lakeview Dashboards

1. **KPIs principales:**
   * Total de fallecidos (todas las fuentes)
   * Total COVID-19 (Guatemala + Costa Rica)
   * Tasa de crecimiento poblacional
   * Meses de datos disponibles

2. **Gráfico de líneas:**
   * Tendencia temporal COVID-19 (ambos países)
   * Comparación de fuentes (INE vs OMS)

3. **Mapas:**
   * Mapa de calor de Guatemala (departamentos)
   * Intensidad de COVID-19 por región

4. **Gráficos de barras:**
   * Top 10 departamentos más afectados
   * Mortalidad por grupo etario
   * Distribución por sexo

5. **Gráfico de áreas apiladas:**
   * Causas de muerte a lo largo del tiempo
   * Proporción COVID vs otras causas

6. **Tablas dinámicas:**
   * Desglose detallado por todas las dimensiones
   * Filtros interactivos

---

## 🔧 Tips para Ejecutar las Queries

### Performance
* Use `LIMIT` en queries exploratorias
* Agregue índices virtuales si es necesario (cluster keys en Databricks)
* Pre-filtre por periodo si solo necesita pandemia

### Validación
* Siempre verifique conteos con `COUNT(DISTINCT id_tiempo_mes)`
* Compare totales entre queries para detectar errores
* Use `WHERE` para filtrar fuentes específicas cuando sea necesario

### Modificación
* Cambie `f.fuente IN ('OMS', 'CR')` según la fuente deseada
* Ajuste el rango de fechas con `AND f.id_tiempo_mes >= 'YYYY-MM'`
* Agregue columnas de dimensiones según necesidad

---

## 🔗 Referencias

* [Modelo Completo](../MODELO_ESTRELLA_DOCUMENTACION.md)
* [Diccionario de Datos](DICCIONARIO_DATOS.md)
* [Mapeos de Transformación](MAPEOS_TRANSFORMACIONES.md)
* [Resumen Ejecutivo](RESUMEN_EJECUTIVO.md)

---

**Última actualización:** 21 de junio de 2026  
**Versión:** 1.0
