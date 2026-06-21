# 📋 Reglas de Transformación Auditable y Source-to-Target Mapping
## Proyecto: Análisis de Mortalidad COVID-19

**Pipeline:** Lakeflow Spark Declarative Pipeline  
**Fecha:** Junio 2026  
**Capas:** Bronze → Silver → Gold

---

## 1. Listado de Reglas de Transformación Auditable

| ID Regla | Nombre de la Regla | Tipo | Descripción | Acción |
|----------|-------------------|------|-------------|--------|
| **RT-COV-001** | Agregación temporal diaria a mensual | Transformación | Convertir datos diarios de OMS a agregación mensual. | Agrupar `date_reported` por `YYYY-MM`, sumar `new_deaths`. |
| **RT-COV-002** | Gestión de valores NaN en fallecidos | Calidad | Reemplazar NaN/NULL en columnas de fallecidos. | Convertir NaN → 0 en `new_deaths` antes de agregación. |
| **RT-COV-003** | Estandarización de identificadores geográficos | Estandarización | Generar códigos uniformes de geografía. | `depocu` → `GT-{depocu}`, Nacional → `GT-NA`, `CR-NA`. |
| **RT-COV-004** | Clasificación de rangos etarios | Transformación | Agrupar edades en rangos OMS estándar. | Edad 0-14 → `0-14`, 15-64 → `15-64`, 65+ → `65+`. |
| **RT-COV-005** | Codificación de sexo | Transformación | Convertir códigos numéricos a letras estándar. | 1 → `H` (Hombre), 2 → `M` (Mujer), NULL → `A` (Ambos). |
| **RT-COV-006** | Generación de surrogate key perfil | DW | Crear clave artificial para perfiles demográficos. | `id_perfil = "{letra_sexo}-{rango_edad}"`. |
| **RT-COV-007** | Generación de surrogate key tiempo | DW | Crear clave temporal formato YYYY-MM. | `id_tiempo_mes = CONCAT(anio, '-', LPAD(mes, 2, '0'))`. |
| **RT-COV-008** | Clasificación de causas CIE-10 | Negocio | Categorizar causas según códigos CIE-10. | COVID (U07), Respiratoria (J00-J99), Cardiovascular (I00-I99), etc. |
| **RT-COV-009** | Flag de periodo pandemia | Negocio | Clasificar registros pre/post COVID. | Antes marzo 2020 → `Pre-COVID`, desde marzo 2020 → `Pandemia`. |
| **RT-COV-010** | Filtrado de registros sin fallecidos | Calidad | Eliminar meses con 0 fallecidos en OMS. | `WHERE cantidad_fallecidos > 0` post-agregación. |
| **RT-COV-011** | Normalización de esquemas RENAP | Calidad | Homogeneizar columnas entre tablas 2015-2026. | Crear columna `diciembre` faltante, renombrar `total` → `total_anual`. |
| **RT-COV-012** | Conversión de tipos RENAP | Calidad | Estandarizar tipos de datos en columnas de meses. | `DOUBLE` → `BIGINT` para columnas enero-diciembre. |
| **RT-COV-013** | Unpivot de meses RENAP | Transformación | Convertir formato ancho (12 columnas) a largo. | UNPIVOT 12 columnas (enero-diciembre) → filas individuales. |
| **RT-COV-014** | Validación de rango de meses | Calidad | Rechazar meses inválidos. | Validar mes entre 1-12 en datos mensuales. |
| **RT-COV-015** | Eliminación de columnas técnicas | Privacidad | Remover metadatos no analíticos. | Excluir `bronze_loaded_at`, `bronze_batch_id`, `bronze_source`. |
| **RT-COV-016** | Generación de flag COVID | Negocio | Identificar registros de causa COVID-19. | `es_covid = TRUE` si `id_causa = 'COVID'`, sino `FALSE`. |
| **RT-COV-017** | Consolidación de fuentes | Integración | Unificar registros de múltiples fuentes. | `UNION ALL` de fact_parcial_ine + oms + costa_rica. |
| **RT-COV-018** | Hardcode de perfiles OMS | Transformación | Asignar perfil agregado a datos sin desglose. | OMS/CR → `id_perfil = 'A-Todas'` (sin sexo/edad). |
| **RT-COV-019** | Hardcode de causa OMS | Transformación | Asignar causa COVID a datos OMS. | OMS/CR → `id_causa = 'COVID'` (única causa reportada). |
| **RT-COV-020** | Agregación por combinación dimensional | Gold | Generar métricas por todas las combinaciones. | `GROUP BY id_tiempo_mes, id_geografia, id_perfil, id_causa`. |
| **RT-COV-021** | Filtrado de país en OMS | Calidad | Separar datos por país específico. | Filtrar `country = 'Guatemala'` o `'Costa Rica'` antes de procesar. |
| **RT-COV-022** | Ventana temporal COVID | Calidad | Limitar datos a periodo relevante. | OMS: Filtrar `date_reported >= '2020-01-01'`. |
| **RT-COV-023** | Generación de nombres de mes | Transformación | Traducir número de mes a texto español. | 1 → "Enero", 2 → "Febrero", ..., 12 → "Diciembre". |
| **RT-COV-024** | Preservación de trazabilidad | Gobierno | Registrar fuente de origen. | Agregar columna `fuente`: "INE", "OMS", "RENAP". |
| **RT-COV-025** | Validación referencial geográfica | Integridad | Verificar existencia de departamentos. | JOIN con `inacif_departamentos` para validar `depocu`. |

---

## 2. Source-to-Target Mapping (STM)

### 2.1 Dimensión: **dim_tiempo**

**Descripción:** Dimensión temporal con 144 meses (2015-2026) y clasificación de periodo pandemia.

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| — | Generación sintética | Rango 2015-2026 | `dim_tiempo` | `anio` | — |
| — | Generación sintética | 1 a 12 | `dim_tiempo` | `mes` | — |
| — | Derivación | `CONCAT(anio, '-', LPAD(mes, 2, '0'))` | `dim_tiempo` | `id_tiempo_mes` | RT-COV-007 |
| — | Derivación | Traducción numérica | `dim_tiempo` | `nombre_mes` | RT-COV-023 |
| — | Derivación | `IF(id_tiempo_mes >= '2020-03', 'Pandemia', 'Pre-COVID')` | `dim_tiempo` | `periodo` | RT-COV-009 |

**Campos Generados:**
* `id_tiempo_mes` (PK): "2015-01" a "2026-12"
* `nombre_mes`: "Enero", "Febrero", ..., "Diciembre"
* `periodo`: "Pre-COVID" o "Pandemia"

---

### 2.2 Dimensión: **dim_geografia**

**Descripción:** 25 lugares (22 departamentos GT + 1 nacional GT + 1 nacional CR + 1 legacy).

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| `inacif_departamentos` | `id` | `CONCAT('GT-', id)` | `dim_geografia` | `id_geografia` | RT-COV-003 |
| `inacif_departamentos` | `nombre` | Trim y normalización | `dim_geografia` | `nombre_departamento` | — |
| `inacif_departamentos` | `id` | Copia directa | `dim_geografia` | `id_departamento` | — |
| — | Hardcode | "Guatemala" | `dim_geografia` | `pais` | — |
| — | Sintético | "GT-NA" | `dim_geografia` | `id_geografia` | RT-COV-003 |
| — | Sintético | "Nacional" (GT) | `dim_geografia` | `nombre_departamento` | — |
| — | Sintético | "CR-NA" | `dim_geografia` | `id_geografia` | RT-COV-003 |
| — | Sintético | "Nacional" (CR) | `dim_geografia` | `nombre_departamento` | — |
| — | Sintético | "Costa Rica" | `dim_geografia` | `pais` | — |

**Tipos de Registros:**
* **Departamentales GT:** `id_geografia = "GT-1"` a `"GT-22"` (22 registros)
* **Nacional GT:** `id_geografia = "GT-NA"` (1 registro) → Para datos OMS Guatemala
* **Nacional CR:** `id_geografia = "CR-NA"` (1 registro) → Para datos OMS Costa Rica
* **Legacy:** `id_geografia = "GT-99"` (1 registro) → Datos históricos sin desglose

---

### 2.3 Dimensión: **dim_perfil**

**Descripción:** 12 perfiles demográficos (3 rangos edad × 2 sexos × 2 tipos agregado).

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| — | Sintético | "Hombre", "Mujer", "Ambos" | `dim_perfil` | `sexo` | — |
| — | Sintético | "0-14", "15-64", "65+", "Todas" | `dim_perfil` | `rango_edad` | RT-COV-004 |
| — | Derivación | `"{letra_sexo}-{rango_edad}"` | `dim_perfil` | `id_perfil` | RT-COV-006 |

**Combinaciones Generadas (12 perfiles):**

| id_perfil | sexo | rango_edad |
|-----------|------|------------|
| H-0-14 | Hombre | 0-14 |
| H-15-64 | Hombre | 15-64 |
| H-65+ | Hombre | 65+ |
| H-Todas | Hombre | Todas |
| M-0-14 | Mujer | 0-14 |
| M-15-64 | Mujer | 15-64 |
| M-65+ | Mujer | 65+ |
| M-Todas | Mujer | Todas |
| A-0-14 | Ambos | 0-14 |
| A-15-64 | Ambos | 15-64 |
| A-65+ | Ambos | 65+ |
| A-Todas | Ambos | Todas |

---

### 2.4 Dimensión: **dim_causa_muerte**

**Descripción:** 48 causas de muerte con clasificación CIE-10 y flag COVID.

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| `inacif_causas_muerte` | `id` | `CONCAT('INACIF-', id)` | `dim_causa_muerte` | `id_causa` | — |
| `inacif_causas_muerte` | `nombre` | Normalización | `dim_causa_muerte` | `nombre_causa` | — |
| `inacif_causas_muerte` | `nombre` | Clasificación CIE-10 | `dim_causa_muerte` | `categoria_general` | RT-COV-008 |
| — | Sintéticos | "COVID", "RESP", "CARDIO", "CANCER", "EXTERNA", "OTRA", "DESCONOCIDA" | `dim_causa_muerte` | `id_causa` | RT-COV-008 |
| — | Derivación | `IF(id_causa = 'COVID', TRUE, FALSE)` | `dim_causa_muerte` | `es_covid` | RT-COV-016 |

**Clasificación CIE-10 Implementada:**

| Código/Palabra Clave | Categoría General | id_causa | es_covid |
|----------------------|-------------------|----------|----------|
| U07.1, U07.2, "COVID" | COVID-19 | COVID | TRUE |
| J00-J99, "RESPIRAT" | Enfermedad Respiratoria | RESP | FALSE |
| I00-I99, "CARDIO" | Enfermedad Cardiovascular | CARDIO | FALSE |
| C00-C99, "CANCER", "NEOPLAS" | Cáncer | CANCER | FALSE |
| V00-Y99, "ACCIDENT", "TRAUMA" | Causa Externa | EXTERNA | FALSE |
| R99, "" | Desconocida | DESCONOCIDA | FALSE |
| Otros | Otra | OTRA | FALSE |

---

### 2.5 Tabla de Hechos: **fact_parcial_ine** (48,656 registros)

**Fuente:** `covid19.silver.silver_ine_deaths` (INE Guatemala, departamental con desglose completo)

**Periodo:** 2018-2025

**Desglose:** Departamento × Sexo × Edad × Causa

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| `silver_ine_deaths` | `anoreg`, `mesreg` | `CONCAT(anoreg, '-', LPAD(mesreg, 2, '0'))` | `fact_parcial_ine` | `id_tiempo_mes` | RT-COV-007 |
| `silver_ine_deaths` | `depocu` | `CONCAT('GT-', depocu)` | `fact_parcial_ine` | `id_geografia` | RT-COV-003 |
| `silver_ine_deaths` | `sexo`, `Edadif` | Clasificación sexo-edad | `fact_parcial_ine` | `id_perfil` | RT-COV-004, RT-COV-005, RT-COV-006 |
| `silver_ine_deaths` | `Caudef` | Clasificación CIE-10 | `fact_parcial_ine` | `id_causa` | RT-COV-008 |
| `silver_ine_deaths` | `COUNT(*)` | Agregación | `fact_parcial_ine` | `cantidad_fallecidos` | RT-COV-020 |
| — | Hardcode | "INE" | `fact_parcial_ine` | `fuente` | RT-COV-024 |

**Transformación Detallada de Perfil:**

```python
# Paso 1: Mapeo de sexo
CASE
    WHEN sexo = 1 THEN 'H'  # Hombre
    WHEN sexo = 2 THEN 'M'  # Mujer
    ELSE 'A'                 # Ambos (agregados)
END

# Paso 2: Clasificación de edad
CASE
    WHEN Edadif <= 14 THEN '0-14'
    WHEN Edadif <= 64 THEN '15-64'
    WHEN Edadif >= 65 THEN '65+'
    ELSE 'Todas'
END

# Paso 3: Construcción de id_perfil
id_perfil = CONCAT(letra_sexo, '-', rango_edad)
```

**Ejemplo de Transformación:**

| Campo Bronze | Valor | → | Campo Gold | Valor |
|--------------|-------|---|------------|-------|
| anoreg | 2020 | → | id_tiempo_mes | "2020-10" |
| mesreg | 10 | → | (parte de arriba) | |
| depocu | 1 | → | id_geografia | "GT-1" |
| sexo | 1 | → | id_perfil | "H-65+" |
| Edadif | 68 | → | (parte de arriba) | |
| Caudef | "COVID-19 (U07.1)" | → | id_causa | "COVID" |
| COUNT(*) | 1 | → | cantidad_fallecidos | 1 |

---

### 2.6 Tabla de Hechos: **fact_parcial_oms** (45 registros)

**Fuente:** `covid19.bronze.who_covid_19_global_daily_data` filtrado por `country = 'Guatemala'`

**Periodo:** 2020-2025 (solo meses con fallecidos COVID)

**Desglose:** Nacional, sin sexo/edad, solo COVID-19

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| `who_covid_19_global_daily_data` | `date_reported` | `DATE_FORMAT(date_reported, 'yyyy-MM')` | `fact_parcial_oms` | `id_tiempo_mes` | RT-COV-001 |
| `who_covid_19_global_daily_data` | `country` | Filtro + hardcode "GT-NA" | `fact_parcial_oms` | `id_geografia` | RT-COV-003, RT-COV-021 |
| — | Hardcode | "A-Todas" | `fact_parcial_oms` | `id_perfil` | RT-COV-018 |
| — | Hardcode | "COVID" | `fact_parcial_oms` | `id_causa` | RT-COV-019 |
| `who_covid_19_global_daily_data` | `new_deaths` | `SUM(COALESCE(new_deaths, 0))` por mes | `fact_parcial_oms` | `cantidad_fallecidos` | RT-COV-001, RT-COV-002, RT-COV-020 |
| — | Hardcode | "OMS" | `fact_parcial_oms` | `fuente` | RT-COV-024 |

**Proceso de Agregación Temporal:**

```sql
-- Paso 1: Filtrar país y limpiar NaN
SELECT 
    date_reported,
    COALESCE(new_deaths, 0) AS new_deaths_clean
FROM who_covid_19_global_daily_data
WHERE country = 'Guatemala'
  AND date_reported >= '2020-01-01'

-- Paso 2: Agregar a nivel mensual
SELECT 
    DATE_FORMAT(date_reported, 'yyyy-MM') AS id_tiempo_mes,
    'GT-NA' AS id_geografia,
    'A-Todas' AS id_perfil,
    'COVID' AS id_causa,
    SUM(new_deaths_clean) AS cantidad_fallecidos,
    'OMS' AS fuente
FROM [paso1]
GROUP BY DATE_FORMAT(date_reported, 'yyyy-MM')
HAVING cantidad_fallecidos > 0  -- Filtrar meses sin fallecidos
```

---

### 2.7 Tabla de Hechos: **fact_parcial_costa_rica** (54 registros)

**Fuente:** `covid19.bronze.who_covid_19_global_daily_data` filtrado por `country = 'Costa Rica'`

**Periodo:** 2020-2026 (solo meses con fallecidos COVID)

**Desglose:** Nacional, sin sexo/edad, solo COVID-19

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| `who_covid_19_global_daily_data` | `date_reported` | `DATE_FORMAT(date_reported, 'yyyy-MM')` | `fact_parcial_costa_rica` | `id_tiempo_mes` | RT-COV-001 |
| `who_covid_19_global_daily_data` | `country` | Filtro + hardcode "CR-NA" | `fact_parcial_costa_rica` | `id_geografia` | RT-COV-003, RT-COV-021 |
| — | Hardcode | "A-Todas" | `fact_parcial_costa_rica` | `id_perfil` | RT-COV-018 |
| — | Hardcode | "COVID" | `fact_parcial_costa_rica` | `id_causa` | RT-COV-019 |
| `who_covid_19_global_daily_data` | `new_deaths` | `SUM(COALESCE(new_deaths, 0))` por mes | `fact_parcial_costa_rica` | `cantidad_fallecidos` | RT-COV-001, RT-COV-002, RT-COV-020 |
| — | Hardcode | "OMS" | `fact_parcial_costa_rica` | `fuente` | RT-COV-024 |

**Nota:** La transformación es idéntica a `fact_parcial_oms`, solo cambia el filtro de país y el `id_geografia` destino.

---

### 2.8 Tabla de Hechos: **fact_mortalidad_unificada** (48,755 registros)

**Fuente:** Consolidación de las 3 tablas parciales

**Transformación:** `UNION ALL` de las tablas parciales.

| Tabla Origen | Transformación | Tabla Destino | Regla |
|--------------|----------------|---------------|-------|
| `fact_parcial_ine` | Copia directa | `fact_mortalidad_unificada` | RT-COV-017 |
| `fact_parcial_oms` | Copia directa | `fact_mortalidad_unificada` | RT-COV-017 |
| `fact_parcial_costa_rica` | Copia directa | `fact_mortalidad_unificada` | RT-COV-017 |

**SQL Implementado:**

```sql
CREATE OR REPLACE TABLE covid19.gold.covid19_gold_fact_mortalidad_unificada AS
SELECT * FROM covid19.gold.covid19_gold_fact_parcial_ine
UNION ALL
SELECT * FROM covid19.gold.covid19_gold_fact_parcial_oms
UNION ALL
SELECT * FROM covid19.gold.covid19_gold_fact_parcial_costa_rica;
```

**Distribución de Registros:**
* INE: 48,656 registros (99.8%)
* OMS Guatemala: 45 registros (0.09%)
* Costa Rica: 54 registros (0.11%)
* **Total:** 48,755 registros

---

### 2.9 Tabla de Hechos: **fact_contexto_renap** (1,943 registros)

**Fuente:** `covid19.silver.silver_eventos_por_mes` (transformado desde 12 tablas RENAP)

**Periodo:** 2015-2026

**Desglose:** Mes × Tipo de evento civil (nacimientos, defunciones, matrimonios, divorcios)

#### Flujo de Transformación Bronze → Silver

**Paso 1: Normalización de esquemas (Bronze → silver_eventos_unificados)**

| Problema | Solución | Regla |
|----------|----------|-------|
| 2016 sin columna `diciembre` | Crear columna con valor 0 | RT-COV-011 |
| 2025-2026 tienen `total` en vez de `total_anual` | Renombrar columna | RT-COV-011 |
| 2015 tiene meses en DOUBLE | Convertir a BIGINT | RT-COV-012 |

**Paso 2: Unpivot (silver_eventos_unificados → silver_eventos_por_mes)**

```sql
-- Transformar 12 columnas (enero-diciembre) en filas individuales
UNPIVOT (
    cantidad FOR mes_nombre IN (
        enero AS 1, febrero AS 2, marzo AS 3, abril AS 4,
        mayo AS 5, junio AS 6, julio AS 7, agosto AS 8,
        septiembre AS 9, octubre AS 10, noviembre AS 11, diciembre AS 12
    )
)
```

#### Mapeo Silver → Gold

| Tabla Origen | Campo Origen | Transformación | Tabla Destino | Campo Destino | Regla |
|--------------|--------------|----------------|---------------|---------------|-------|
| `silver_eventos_por_mes` | `anio_registro`, `mes_nombre` | `CONCAT(anio_registro, '-', LPAD(mes_nombre, 2, '0'))` | `fact_contexto_renap` | `id_tiempo_mes` | RT-COV-007 |
| `silver_eventos_por_mes` | `tipo_evento` | Copia directa | `fact_contexto_renap` | `tipo_evento` | — |
| `silver_eventos_por_mes` | `cantidad` | Copia directa | `fact_contexto_renap` | `cantidad_eventos` | — |
| — | Hardcode | "RENAP" | `fact_contexto_renap` | `fuente` | RT-COV-024 |

**Tipos de Eventos:**
* `nacimientos`
* `defunciones`
* `matrimonios`
* `divorcios`

**Ejemplo de Transformación:**

| Tabla Bronze | Campo | Valor |
|--------------|-------|-------|
| `desagregados_por_evento_2020` | `enero` | 25000 |
| | `febrero` | 24000 |
| | ... | ... |

↓ **UNPIVOT** ↓

| Tabla Silver | Campo | Valor |
|--------------|-------|-------|
| `silver_eventos_por_mes` | `anio_registro` | 2020 |
| | `mes_nombre` | 1 |
| | `tipo_evento` | "nacimientos" |
| | `cantidad` | 25000 |

↓ **Mapeo Gold** ↓

| Tabla Gold | Campo | Valor |
|------------|-------|-------|
| `fact_contexto_renap` | `id_tiempo_mes` | "2020-01" |
| | `tipo_evento` | "nacimientos" |
| | `cantidad_eventos` | 25000 |
| | `fuente` | "RENAP" |

---

## 3. Campos Excluidos del Modelo Gold

Campos técnicos que no se propagan a la capa Gold:

| Campo Origen | Capa | Motivo | Regla |
|--------------|------|--------|-------|
| `bronze_loaded_at` | Bronze | Metadato técnico de ingesta | RT-COV-015 |
| `bronze_batch_id` | Bronze | Identificador interno de lote | RT-COV-015 |
| `bronze_source` | Bronze | Ruta de archivo origen | RT-COV-015 |
| `total_anual` | RENAP | Calculado, no necesario en mensual | — |
| `cumulative_deaths` | OMS | Solo se usa `new_deaths` | — |
| `cumulative_cases` | OMS | Fuera de alcance (solo mortalidad) | — |

---

## 4. Validaciones de Integridad Referencial

**Validaciones implementadas en el pipeline:**

| Validación | Regla | SQL de Validación |
|------------|-------|-------------------|
| Todas las claves de tiempo existen en dim_tiempo | RT-COV-007 | `LEFT JOIN dim_tiempo WHERE dim_tiempo.id_tiempo_mes IS NULL` |
| Todas las claves de geografía existen en dim_geografia | RT-COV-025 | `LEFT JOIN dim_geografia WHERE dim_geografia.id_geografia IS NULL` |
| Todas las claves de perfil existen en dim_perfil | RT-COV-006 | `LEFT JOIN dim_perfil WHERE dim_perfil.id_perfil IS NULL` |
| Todas las claves de causa existen en dim_causa_muerte | RT-COV-008 | `LEFT JOIN dim_causa_muerte WHERE dim_causa_muerte.id_causa IS NULL` |
| Meses en rango 1-12 | RT-COV-014 | `WHERE mes NOT BETWEEN 1 AND 12` |
| Edades válidas (0-120) | — | `WHERE Edadif < 0 OR Edadif > 120` |
| Cantidad de fallecidos >= 0 | — | `WHERE cantidad_fallecidos < 0` |

---

## 5. Trazabilidad y Linaje de Datos

**Cadena de transformación por fuente:**

### Flujo INE (Guatemala Departamental)
```
Bronze: Multiple INE Sources
    ↓ (Limpieza básica)
Silver: silver_ine_deaths
    ↓ (RT-COV-003 a RT-COV-008, RT-COV-020)
Gold: fact_parcial_ine
    ↓ (RT-COV-017)
Gold: fact_mortalidad_unificada
```

### Flujo OMS (Guatemala Nacional / Costa Rica)
```
Bronze: who_covid_19_global_daily_data
    ↓ (RT-COV-001, RT-COV-002, RT-COV-021, RT-COV-022)
Silver: (Procesamiento en memoria)
    ↓ (RT-COV-018, RT-COV-019, RT-COV-020)
Gold: fact_parcial_oms / fact_parcial_costa_rica
    ↓ (RT-COV-017)
Gold: fact_mortalidad_unificada
```

### Flujo RENAP (Eventos Civiles)
```
Bronze: desagregados_por_evento_2015...2026 (12 tablas)
    ↓ (RT-COV-011, RT-COV-012)
Silver: silver_eventos_unificados
    ↓ (RT-COV-013)
Silver: silver_eventos_por_mes
    ↓ (RT-COV-007, RT-COV-024)
Gold: fact_contexto_renap
```

---

## 6. Resumen de Cobertura de Datos

| Fuente | Tabla Gold | Registros | Periodo | Desglose Geográfico | Desglose Demográfico | Causas |
|--------|------------|-----------|---------|---------------------|----------------------|--------|
| **INE** | fact_parcial_ine | 48,656 | 2018-2025 | 22 departamentos | Sexo × Edad completo | Todas las causas CIE-10 |
| **OMS GT** | fact_parcial_oms | 45 | 2020-2025 | Nacional | Sin desglose (A-Todas) | Solo COVID-19 |
| **OMS CR** | fact_parcial_costa_rica | 54 | 2020-2026 | Nacional | Sin desglose (A-Todas) | Solo COVID-19 |
| **RENAP** | fact_contexto_renap | 1,943 | 2015-2026 | Nacional (implícito) | Sin desglose | N/A (eventos civiles) |
| **Consolidado** | fact_mortalidad_unificada | **48,755** | **2015-2026** | **23 lugares** | **12 perfiles** | **48 causas** |

---

## 7. Métricas de Calidad de Datos

**Indicadores implementados:**

| Métrica | Descripción | Valor Esperado | Regla Asociada |
|---------|-------------|----------------|----------------|
| **Completitud de claves foráneas** | % registros con FK válidas | 100% | RT-COV-025 |
| **Registros con NaN corregidos** | Conteo de NaN → 0 en OMS | Reportado en logs | RT-COV-002 |
| **Meses con fallecidos = 0 eliminados** | Filtrado post-agregación OMS | Sí | RT-COV-010 |
| **Esquemas RENAP normalizados** | 12 tablas con mismo esquema | 12/12 | RT-COV-011 |
| **Consistencia de consolidación** | fact_parcial_ine + oms + cr = unificada | 48,656 + 45 + 54 = 48,755 | RT-COV-017 |
| **Cobertura temporal** | Meses con al menos 1 registro | 144 meses (2015-2026) | — |

---

## 8. Notas de Implementación

### 8.1 Dependencias entre Tablas

**Orden de ejecución obligatorio:**

1. **Dimensiones** (paralelo):
   * dim_tiempo
   * dim_geografia
   * dim_perfil
   * dim_causa_muerte

2. **Hechos parciales** (paralelo tras dimensiones):
   * fact_parcial_ine
   * fact_parcial_oms
   * fact_parcial_costa_rica
   * fact_contexto_renap

3. **Consolidación** (requiere hechos parciales):
   * fact_mortalidad_unificada

### 8.2 Optimizaciones Implementadas

* **Particionamiento:** No implementado (volumen pequeño)
* **Z-ordering:** No implementado (consultas no requieren)
* **Liquid Clustering:** No aplicado (tablas < 1M registros)
* **Caching:** Dimensiones cacheadas en memoria durante ejecución

### 8.3 Estrategia de Refreshes

* **Full Refresh:** Todas las tablas Gold se reconstruyen completamente
* **Incremental:** No implementado (fuentes no soportan append)
* **Frecuencia recomendada:** Mensual (al recibir nuevos datos INE/OMS)

---

**Fin del Documento**

*Última actualización: Junio 2026*  
*Mantenido por: Equipo COVID-19 Analysis (Wilson, Yeni, Byron)*
