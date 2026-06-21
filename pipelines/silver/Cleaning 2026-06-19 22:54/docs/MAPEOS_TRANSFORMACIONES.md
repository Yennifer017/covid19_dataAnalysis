# 🗺️ Mapeos y Transformaciones - Modelo Estrella COVID-19

**Proyecto:** Análisis comparativo de mortalidad COVID-19  
**Última actualización:** 21 de junio de 2026

Este documento describe cómo las fuentes de datos bronze/silver se transforman y mapean a las dimensiones y hechos del modelo gold.

---

## Índice

1. [Mapeo INE → Dimensiones](#mapeo-ine--dimensiones)
2. [Mapeo OMS → Dimensiones](#mapeo-oms--dimensiones-guatemala-y-costa-rica)
3. [Mapeo RENAP → fact_contexto](#mapeo-renap--fact_contexto)
4. [Flujo Completo de Transformación](#flujo-completo-de-transformación)
5. [Reglas de Limpieza de Datos](#reglas-de-limpieza-de-datos)

---

## Mapeo INE → Dimensiones

**Fuente Bronze:** `covid19.silver.silver_ine_deaths` (ya procesada desde varias fuentes INE)

**Tabla de Hechos Destino:** `covid19.gold.covid19_gold_fact_parcial_ine`

### Mapeo de Campos

| Campo Bronze/Silver | Tipo | Dimensión Destino | Campo Destino | Lógica de Transformación |
|---------------------|------|-------------------|---------------|--------------------------|
| `anoreg` | INT | dim_tiempo | `id_tiempo_mes` | `CONCAT(anoreg, '-', LPAD(mesreg, 2, '0'))` |
| `mesreg` | INT | dim_tiempo | `id_tiempo_mes` | Ej: anoreg=2020, mesreg=3 → "2020-03" |
| `depocu` | INT | dim_geografia | `id_geografia` | `CONCAT('GT-', depocu)` |
|  |  |  |  | Ej: depocu=1 → "GT-1" (Guatemala capital) |
| `sexo` | STRING | dim_perfil | `id_perfil` | Ver tabla de mapeo sexo-edad abajo |
| `Edadif` | INT | dim_perfil | `id_perfil` | Clasificación por rangos de edad |
| `Caudef` | STRING | dim_causa_muerte | `id_causa` | Clasificación CIE-10 (ver abajo) |
| `COUNT(*)` | — | fact | `cantidad_fallecidos` | Agregación de registros por combinación |

### Mapeo de Sexo y Edad → id_perfil

**Lógica implementada:**

```python
def mapear_perfil(sexo, edad):
    # Mapeo de sexo
    if sexo == 1:
        letra_sexo = 'H'  # Hombre
    elif sexo == 2:
        letra_sexo = 'M'  # Mujer
    else:
        letra_sexo = 'A'  # Ambos (para agregados)
    
    # Clasificación de edad
    if edad is None or edad < 0:
        rango_edad = 'Todas'
    elif edad <= 14:
        rango_edad = '0-14'
    elif edad <= 64:
        rango_edad = '15-64'
    else:  # edad >= 65
        rango_edad = '65+'
    
    return f"{letra_sexo}-{rango_edad}"

# Ejemplos:
# sexo=1, edad=30 → "H-15-64"
# sexo=2, edad=70 → "M-65+"
# sexo=1, edad=10 → "H-0-14"
```

### Clasificación de Causas de Muerte (CIE-10)

**Lógica implementada:**

```python
def clasificar_causa(caudef_texto):
    """
    Clasifica la causa de muerte según descripción y código CIE-10
    """
    if caudef_texto is None or caudef_texto == '':
        return 'DESCONOCIDA'
    
    caudef_upper = caudef_texto.upper()
    
    # COVID-19
    if 'COVID' in caudef_upper or 'U07' in caudef_upper:
        return 'COVID'
    
    # Enfermedades Respiratorias (J00-J99)
    if 'RESPIRAT' in caudef_upper or any(f'J{i:02d}' in caudef_upper for i in range(0, 100)):
        return 'RESP'
    
    # Enfermedades Cardiovasculares (I00-I99)
    if 'CARDIO' in caudef_upper or 'CORAZON' in caudef_upper:
        return 'CARDIO'
    if any(f'I{i:02d}' in caudef_upper for i in range(0, 100)):
        return 'CARDIO'
    
    # Cáncer / Neoplasias (C00-D48)
    if 'CANCER' in caudef_upper or 'NEOPLAS' in caudef_upper or 'TUMOR' in caudef_upper:
        return 'CANCER'
    if any(f'C{i:02d}' in caudef_upper for i in range(0, 100)):
        return 'CANCER'
    
    # Causas Externas (V00-Y99) - Accidentes, violencia
    if caudef_upper.startswith(('V', 'W', 'X', 'Y')):
        return 'EXTERNA'
    if 'ACCIDENT' in caudef_upper or 'TRAUMA' in caudef_upper or 'HERIDA' in caudef_upper:
        return 'EXTERNA'
    
    # Otras causas
    return 'OTRA'
```

**Mapeo a dim_causa_muerte:**

| Resultado clasificación | id_causa | categoria_general | es_covid |
|------------------------|----------|-------------------|----------|
| COVID | COVID | COVID-19 | TRUE |
| RESP | RESP | Enfermedad Respiratoria | FALSE |
| CARDIO | CARDIO | Enfermedad Cardiovascular | FALSE |
| CANCER | CANCER | Cáncer | FALSE |
| EXTERNA | EXTERNA | Causa Externa | FALSE |
| OTRA | OTRA | Otra | FALSE |
| DESCONOCIDA | DESCONOCIDA | Desconocida | FALSE |

### Ejemplo Completo de Transformación INE

**Registro Bronze:**
```
anoreg: 2020
mesreg: 10
depocu: 1
sexo: 1
Edadif: 68
Caudef: "COVID-19, VIRUS IDENTIFICADO (U07.1)"
```

**Transformación:**
```python
id_tiempo_mes = "2020-10"
id_geografia = "GT-1"  # Guatemala capital
id_perfil = "H-65+"     # Hombre, 65+
id_causa = "COVID"
```

**Registro Gold (fact_parcial_ine):**
```
id_tiempo_mes: "2020-10"
id_geografia: "GT-1"
id_perfil: "H-65+"
id_causa: "COVID"
cantidad_fallecidos: 1
fuente: "INE"
```

---

## Mapeo OMS → Dimensiones (Guatemala y Costa Rica)

**Fuente Bronze:** `covid19.bronze.who_covid_19_global_daily_data`

**Tablas de Hechos Destino:**
* `covid19.gold.covid19_gold_fact_parcial_oms` (Guatemala)
* `covid19.gold.covid19_gold_fact_parcial_costa_rica` (Costa Rica)

### Mapeo de Campos

| Campo Bronze | Tipo | Dimensión Destino | Campo Destino | Lógica de Transformación |
|--------------|------|-------------------|---------------|--------------------------|
| `date_reported` | STRING | dim_tiempo | `id_tiempo_mes` | `DATE_FORMAT(date_reported, 'yyyy-MM')` |
|  |  |  |  | Ej: "2020-03-15" → "2020-03" |
| `country` | STRING | dim_geografia | `id_geografia` | Guatemala → "GT-NA" |
|  |  |  |  | Costa Rica → "CR-NA" |
| — | — | dim_perfil | `id_perfil` | Hardcoded: "A-Todas" |
|  |  |  |  | (sin desglose en fuente) |
| — | — | dim_causa_muerte | `id_causa` | Hardcoded: "COVID" |
|  |  |  |  | (datos exclusivos COVID-19) |
| `new_deaths` | DOUBLE | fact | `cantidad_fallecidos` | Agregación mensual, limpieza NaN |

### Transformación de Datos Diarios a Mensuales

**Lógica implementada:**

```python
# 1. Filtrar país específico
df_pais = df.filter(F.col("country") == "Guatemala")  # o "Costa Rica"

# 2. Filtrar desde inicio de pandemia
df_pais = df_pais.filter(F.col("date_reported") >= "2020-01-01")

# 3. Limpiar NaN en new_deaths
df_pais = df_pais.withColumn(
    "new_deaths_clean",
    F.when(
        F.isnan(F.col("new_deaths")) | F.col("new_deaths").isNull(),
        F.lit(0)
    ).otherwise(F.col("new_deaths"))
)

# 4. Extraer mes
df_pais = df_pais.withColumn(
    "id_tiempo_mes",
    F.date_format(F.to_date("date_reported", "yyyy-MM-dd"), "yyyy-MM")
)

# 5. Agregar por mes
df_agregado = df_pais.groupBy("id_tiempo_mes").agg(
    F.sum("new_deaths_clean").cast("long").alias("cantidad_fallecidos")
)

# 6. Filtrar meses con fallecidos > 0
df_final = df_agregado.filter(F.col("cantidad_fallecidos") > 0)
```

### Ejemplo Completo de Transformación OMS

**Registros Bronze (diarios):**
```
2020-10-01, Guatemala, new_deaths: 23.0
2020-10-02, Guatemala, new_deaths: 17.0
2020-10-03, Guatemala, new_deaths: NaN
...
2020-10-31, Guatemala, new_deaths: 19.0
```

**Transformación:**
```
Suma del mes: 23 + 17 + 0 + ... + 19 = 540 fallecidos
id_tiempo_mes: "2020-10"
id_geografia: "GT-NA"
id_perfil: "A-Todas"
id_causa: "COVID"
```

**Registro Gold (fact_parcial_oms):**
```
id_tiempo_mes: "2020-10"
id_geografia: "GT-NA"
id_perfil: "A-Todas"
id_causa: "COVID"
cantidad_fallecidos: 540
fuente: "OMS"
```

---

## Mapeo RENAP → fact_contexto

**Fuente Bronze:** 12 tablas `covid19.bronze.desagregados_por_evento_2015` a `2026`

**Transformación Silver:** `covid19.silver.silver_eventos_unificados` → `covid19.silver.silver_eventos_por_mes`

**Tabla de Hechos Destino:** `covid19.gold.covid19_gold_fact_contexto_renap`

### Flujo de Transformación

#### Paso 1: Unificación (Bronze → Silver)

**Problema:** Las 12 tablas RENAP tienen esquemas inconsistentes:
* 2016: Sin columna `diciembre`
* 2025-2026: Columna `total` en vez de `total_anual`
* 2015: Meses en DOUBLE en vez de BIGINT

**Solución (silver_eventos_unificados):**

```python
# Normalizar cada tabla a formato estándar
def normalizar_renap(anio):
    df = spark.read.table(f"covid19.bronze.desagregados_por_evento_{anio}")
    
    # Agregar diciembre si falta (2016)
    if 'diciembre' not in df.columns:
        df = df.withColumn('diciembre', F.lit(0))
    
    # Renombrar total si es necesario
    if 'total' in df.columns and 'total_anual' not in df.columns:
        df = df.withColumnRenamed('total', 'total_anual')
    
    # Cast de meses a BIGINT
    for mes in ['enero', 'febrero', ..., 'diciembre']:
        df = df.withColumn(mes, F.col(mes).cast('bigint'))
    
    return df
```

#### Paso 2: UNPIVOT (Silver → Silver)

**Transformación de formato ancho a largo:**

```python
# Antes (formato ancho - silver_eventos_unificados):
evento           | enero | febrero | marzo | ... | diciembre | total_anual
NACIMIENTOS      | 35000 | 32000   | 34000 | ... | 33000     | 400000

# Después (formato largo - silver_eventos_por_mes):
evento       | mes      | cantidad
NACIMIENTOS  | enero    | 35000
NACIMIENTOS  | febrero  | 32000
NACIMIENTOS  | marzo    | 34000
...
```

**Código PySpark:**

```python
# UNPIVOT usando stack()
meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

df_long = df_wide.selectExpr(
    "evento",
    "anio",
    f"stack(12, {', '.join([f\"'{mes}', {mes}\" for mes in meses])}) as (mes, cantidad)"
)
```

#### Paso 3: Creación de id_tiempo_mes (Silver → Gold)

**Mapeo de Campos:**

| Campo Silver | Tipo | Campo Gold | Transformación |
|--------------|------|------------|----------------|
| `anio` | INT | `id_tiempo_mes` | `CONCAT(anio, '-', numero_mes)` |
| `mes` | STRING | `id_tiempo_mes` | Mapear nombre → número |
| `evento` | STRING | `tipo_evento` | Normalización capitalización |
| `cantidad` | BIGINT | `cantidad` | Directo |

**Mapeo de nombres de meses a números:**

```python
mes_a_numero = {
    'enero': '01', 'febrero': '02', 'marzo': '03',
    'abril': '04', 'mayo': '05', 'junio': '06',
    'julio': '07', 'agosto': '08', 'septiembre': '09',
    'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

df = df.withColumn(
    "id_tiempo_mes",
    F.concat(
        F.col("anio").cast("string"),
        F.lit("-"),
        F.lit(mes_a_numero[mes_nombre])
    )
)
```

#### Paso 4: Normalización de Eventos

**Problema:** Eventos con capitalización inconsistente entre años.

**Solución:**

```python
normalizacion_eventos = {
    'NACIMIENTO': 'Nacimientos',
    'Nacimientos': 'Nacimientos',
    'nacimiento': 'Nacimientos',
    'DEFUNCION': 'Defunciones',
    'Defunciones': 'Defunciones',
    'defuncion': 'Defunciones',
    # ... etc para los 11 tipos
}

df = df.withColumn(
    "tipo_evento_normalizado",
    F.when(F.col("evento") == 'NACIMIENTO', 'Nacimientos')
     .when(F.col("evento") == 'DEFUNCION', 'Defunciones')
     # ... etc
     .otherwise(F.col("evento"))
)
```

### Ejemplo Completo de Transformación RENAP

**Registro Bronze (2020):**
```
evento: "NACIMIENTO"
enero: 35000
febrero: 32000
...
diciembre: 33000
total_anual: 400000
```

**Transformación:**
```
UNPIVOT → 12 registros (uno por mes)
id_tiempo_mes: "2020-01", "2020-02", ..., "2020-12"
tipo_evento: "Nacimientos" (normalizado)
cantidad: 35000, 32000, ..., 33000
```

**Registros Gold (fact_contexto_renap):**
```
id_tiempo_mes: "2020-01", tipo_evento: "Nacimientos", cantidad: 35000, fuente: "RENAP"
id_tiempo_mes: "2020-02", tipo_evento: "Nacimientos", cantidad: 32000, fuente: "RENAP"
...
id_tiempo_mes: "2020-12", tipo_evento: "Nacimientos", cantidad: 33000, fuente: "RENAP"
```

---

## Flujo Completo de Transformación

### Arquitectura Medallion (Bronze → Silver → Gold)

```
┌─────────────── BRONZE ───────────────┐
│                                       │
│ • desagregados_por_evento_2015-2026   │
│ • who_covid_19_global_daily_data      │
│ • inacif_*                            │
│                                       │
└───────────────┬───────────────────────┘
                │
                │ Normalización, Limpieza
                ▼
┌─────────────── SILVER ──────────────┐
│                                      │
│ • silver_ine_deaths                  │
│ • silver_eventos_unificados          │
│ • silver_eventos_por_mes             │
│                                      │
└───────────────┬──────────────────────┘
                │
                │ Mapeo, Agregación, Clasificación
                ▼
┌─────────────── GOLD ────────────────┐
│                                      │
│ Dimensiones:                         │
│ • dim_tiempo                         │
│ • dim_geografia                      │
│ • dim_perfil                         │
│ • dim_causa_muerte                   │
│                                      │
│ Hechos Parciales:                    │
│ • fact_parcial_ine                   │
│ • fact_parcial_oms                   │
│ • fact_parcial_costa_rica            │
│ • fact_contexto_renap                │
│                                      │
│ Consolidación:                       │
│ • fact_mortalidad_unificada          │
│                                      │
└──────────────────────────────────────┘
```

---

## Reglas de Limpieza de Datos

### Valores NaN y NULL

| Fuente | Campo | Tratamiento |
|--------|-------|-------------|
| OMS | `new_deaths` | NaN → 0 (días sin reporte) |
| INE | `Caudef` | NULL → "DESCONOCIDA" |
| INE | `Edadif` | < 0 → NULL → rango "Todas" |
| RENAP | Meses | NULL → 0 |

### Validaciones Implementadas

#### 1. Validación de Claves Foráneas

```python
# Verificar que todas las FK existen en dimensiones
df_validado = df_fact.filter(
    F.col("id_tiempo_mes").isNotNull() &
    F.col("id_geografia").isNotNull() &
    F.col("id_perfil").isNotNull() &
    F.col("id_causa").isNotNull()
)
```

#### 2. Validación de Cantidades

```python
# Solo incluir registros con cantidad > 0
df_validado = df_validado.filter(F.col("cantidad_fallecidos") > 0)
```

#### 3. Deduplicación

```python
# Agregar por dimensiones (eliminar duplicados)
df_agregado = df.groupBy(
    "id_tiempo_mes",
    "id_geografia",
    "id_perfil",
    "id_causa"
).agg(
    F.sum("cantidad_fallecidos").alias("cantidad_fallecidos")
)
```

---

## 📊 Resumen de Transformaciones

### Por Fuente

| Fuente | Registros Bronze | Registros Gold | Tipo de Agregación | Dimensiones Usadas |
|--------|------------------|----------------|--------------------|--------------------|
| INE | ~674K (individuales) | 48,656 (mensuales) | Agrupación mensual por dims | Todas (4) |
| OMS GT | ~2,300 (diarios) | 45 (mensuales) | Suma mensual | Tiempo, COVID, GT-NA, A-Todas |
| OMS CR | ~2,300 (diarios) | 54 (mensuales) | Suma mensual | Tiempo, COVID, CR-NA, A-Todas |
| RENAP | 12 tablas × 11 eventos | 1,943 (mensuales) | UNPIVOT + normalización | Solo Tiempo |

### Niveles de Granularidad

| Tabla | Granularidad Temporal | Granularidad Geográfica | Granularidad Demográfica |
|-------|----------------------|-------------------------|--------------------------|
| fact_parcial_ine | Mensual | 22 departamentos | 12 perfiles (sexo×edad) |
| fact_parcial_oms | Mensual | Nacional (GT-NA) | Agregado (A-Todas) |
| fact_parcial_costa_rica | Mensual | Nacional (CR-NA) | Agregado (A-Todas) |
| fact_contexto_renap | Mensual | N/A (nacional implícito) | N/A |

---

## 🔗 Referencias

* [Modelo Completo](../MODELO_ESTRELLA_DOCUMENTACION.md)
* [Diccionario de Datos](DICCIONARIO_DATOS.md)
* [Queries de Ejemplo](QUERIES_EJEMPLO.md)
* [Resumen Ejecutivo](RESUMEN_EJECUTIVO.md)

---

**Última actualización:** 21 de junio de 2026  
**Versión:** 1.0
