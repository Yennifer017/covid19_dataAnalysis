# 📊 Modelo Estrella - Análisis de Mortalidad COVID-19
## Documentación completa del Pipeline

**Proyecto:** Análisis comparativo de mortalidad COVID-19 (Guatemala y Costa Rica)  
**Pipeline:** Lakeflow Spark Declarative Pipeline  
**Fecha:** Junio 2026  
**Equipo:** Wilson (INE/RENAP), Yeni (OMS), Byron (Costa Rica)

---

## 🎯 Objetivos del Proyecto

Crear un modelo estrella dimensional que permita:
* Análisis temporal de mortalidad (Pre-COVID vs Pandemia)
* Comparación geográfica (Guatemala departamental vs Costa Rica nacional)
* Segmentación demográfica (sexo y edad)
* Clasificación por causa de muerte (COVID-19 vs otras)
* Consolidación de múltiples fuentes de datos

---

## 📐 Arquitectura del Modelo Estrella

### Diseño General

```
                    ┌──────────────────┐
                    │   dim_tiempo     │
                    │  (144 meses)     │
                    └─────────┬────────┘
                              │
                              │
┌──────────────┐              │              ┌──────────────────┐
│ dim_geografia│              │              │  dim_perfil      │
│  (24 lugares)│◄─────────────┼─────────────►│  (12 perfiles)   │
└──────────────┘              │              └──────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │ fact_mortalidad_unificada   │
                │    (Tabla de Hechos)         │
                │   48,656+ registros          │
                └─────────────┬───────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ dim_causa_muerte │
                    │   (48 causas)    │
                    └──────────────────┘

                    ┌──────────────────┐
                    │fact_contexto_renap│
                    │ (Eventos civiles) │
                    │   1,943 registros │
                    └──────────────────┘
```

---

## 🗂️ Estructura de Capas del Pipeline

### **Capa BRONZE** (Datos crudos)
* `covid19.bronze.desagregados_por_evento_2015...2026` - RENAP eventos civiles (12 tablas)
* `covid19.bronze.inacif_departamentos` - Catálogo de departamentos Guatemala
* `covid19.bronze.inacif_causas_muerte` - Catálogo de causas de muerte
* `covid19.bronze.inacif_municipios` - Catálogo de municipios
* `covid19.bronze.inacif_necropsias` - Necropsias INACIF

### **Capa SILVER** (Datos limpios y normalizados)
* `covid19.silver.silver_ine_deaths` - Defunciones INE procesadas
* `covid19.silver.silver_eventos_unificados` - RENAP formato ancho (12 meses)
* `covid19.silver.silver_eventos_por_mes` - RENAP formato largo (UNPIVOT)

### **Capa GOLD** (Modelo dimensional)

#### **FASE 1: Dimensiones Maestras**
* `covid19.gold.covid19_gold_dim_tiempo`
* `covid19.gold.covid19_gold_dim_geografia`
* `covid19.gold.covid19_gold_dim_perfil`
* `covid19.gold.covid19_gold_dim_causa_muerte`

#### **FASE 2: Tablas de Hechos Parciales**
* `covid19.gold.covid19_gold_fact_parcial_ine` ✅ (Wilson - Completa)
* `covid19.gold.covid19_gold_fact_contexto_renap` ✅ (Wilson - Completa)
* `covid19.gold.covid19_gold_fact_parcial_oms` ⏳ (Yeni - Plantilla)
* `covid19.gold.covid19_gold_fact_parcial_costa_rica` ⏳ (Byron - Plantilla)

#### **FASE 3: Consolidación**
* `covid19.gold.covid19_gold_fact_mortalidad_unificada` (UNION ALL final)

---

## 📋 Diccionario de Datos

### 1️⃣ **dim_tiempo** (144 registros)

Dimensión temporal con clasificación de periodos Pre-COVID y Pandemia.

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id_tiempo_mes` | STRING | Clave primaria formato YYYY-MM | "2020-03" |
| `anio` | LONG | Año | 2020 |
| `mes` | LONG | Mes (1-12) | 3 |
| `nombre_mes` | STRING | Nombre del mes en español | "Marzo" |
| `periodo` | STRING | Clasificación de periodo | "Pandemia" |

**Regla de negocio:**
* `periodo = "Pre-COVID"` → Antes de marzo 2020
* `periodo = "Pandemia"` → Marzo 2020 en adelante

**Rango de datos:** Enero 2015 a Diciembre 2026

---

### 2️⃣ **dim_geografia** (24 registros)

Dimensión geográfica con departamentos de Guatemala y Costa Rica.

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id_geografia` | STRING | Clave primaria | "GT-1", "CR-NA" |
| `pais` | STRING | Nombre del país | "Guatemala", "Costa Rica" |
| `id_departamento` | LONG | Código interno departamento | 1, 2, ..., 22, 0 |
| `nombre_departamento` | STRING | Nombre del departamento | "Guatemala", "Nacional" |

**Cobertura:**
* Guatemala: 22 departamentos (GT-1 a GT-22)
* Costa Rica: 1 nivel nacional (CR-NA)

**Fuente de datos:** `covid19.bronze.inacif_departamentos` + registro sintético Costa Rica

---

### 3️⃣ **dim_perfil** (12 registros)

Dimensión de perfil demográfico (sexo × edad).

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id_perfil` | STRING | Clave primaria formato X-rango | "H-15-64", "M-65+" |
| `sexo` | STRING | Sexo | "Hombre", "Mujer", "Ambos" |
| `rango_edad` | STRING | Rango de edad | "0-14", "15-64", "65+", "Todas" |

**Combinaciones disponibles:**
* 3 sexos: Hombre (H), Mujer (M), Ambos (A)
* 4 rangos: 0-14, 15-64, 65+, Todas
* Total: 12 perfiles

---

### 4️⃣ **dim_causa_muerte** (48 registros)

Dimensión de causas de muerte con clasificación y flag COVID.

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id_causa` | STRING | Clave primaria | "COVID", "RESP", "INACIF-1" |
| `categoria_general` | STRING | Categoría amplia | "COVID-19", "Enfermedad Respiratoria" |
| `nombre_causa` | STRING | Descripción detallada | "COVID-19 (U07.1 o U07.2)" |
| `es_covid` | BOOLEAN | Flag para filtrar COVID | TRUE, FALSE |

**Categorías generales:**
* COVID-19
* Enfermedad Respiratoria
* Enfermedad Cardiovascular
* Cáncer
* Causa Externa (accidentes, violencia)
* Otra
* Desconocida

**Fuentes:**
* Causas INACIF (id_causa = "INACIF-X")
* Causas sintéticas para mapeo (id_causa = "COVID", "RESP", etc.)

---

### 5️⃣ **fact_mortalidad_unificada** (48,656+ registros)

Tabla de hechos maestra con mortalidad de todas las fuentes.

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id_tiempo_mes` | STRING | FK a dim_tiempo | "2020-03" |
| `id_geografia` | STRING | FK a dim_geografia | "GT-1" |
| `id_perfil` | STRING | FK a dim_perfil | "H-15-64" |
| `id_causa` | STRING | FK a dim_causa_muerte | "COVID" |
| `cantidad_fallecidos` | LONG | Métrica: número de fallecidos | 276 |
| `fuente` | STRING | Fuente de datos | "INE", "OMS", "CR" |
| `fecha_actualizacion` | TIMESTAMP | Timestamp de procesamiento | 2026-06-21 |

**Granularidad:** Una fila por combinación única de mes-geografía-perfil-causa-fuente

**Fuentes consolidadas:**
* `INE` - Instituto Nacional de Estadística Guatemala
* `OMS` - Organización Mundial de la Salud (datos globales)
* `CR` - Costa Rica (fuente nacional)

---

### 6️⃣ **fact_contexto_renap** (1,943 registros)

Tabla de hechos satélite con eventos civiles del RENAP.

| Columna | Tipo | Descripción | Ejemplo |
|---------|------|-------------|---------|
| `id_tiempo_mes` | STRING | FK a dim_tiempo | "2020-03" |
| `tipo_evento` | STRING | Tipo de evento civil | "Nacimientos", "Matrimonios" |
| `cantidad` | LONG | Métrica: número de eventos | 35000 |
| `fuente` | STRING | Fuente de datos | "RENAP" |

**Tipos de eventos incluidos:**
* Nacimientos
* Defunciones
* Matrimonios
* Divorcios
* Reconocimientos
* Identificación de Persona
* Adopciones
* Cambio de Nombre
* Unión de Hecho
* Naturalizaciones
* Extranjeros Domiciliados

**Nota:** Esta tabla NO usa las dimensiones geografia/perfil/causa porque son eventos contextuales, no de mortalidad.

---

## 🔄 Estrategia de Trabajo en Paralelo

### **FASE 1: Dimensiones Maestras** ✅ (Completa)
Creadas una sola vez por el equipo, sirven como diccionario compartido.

**Ubicación:** `transformations/gold/dimensiones.py`

**Estado:** ✅ Las 4 dimensiones están operativas con datos reales

---

### **FASE 2: Trabajo Individual (Tablas Parciales)**

Cada miembro del equipo procesa sus fuentes de forma independiente.

#### **Wilson (INE + RENAP)** ✅ Completo

**Archivos:**
* `transformations/gold/fact_parcial_ine.py` - 48,656 registros
* `transformations/gold/fact_contexto_renap.py` - 1,943 registros

**Fuentes procesadas:**
* `covid19.silver.silver_ine_deaths` → Mortalidad Guatemala
* `covid19.silver.silver_eventos_por_mes` → Eventos civiles

**Mapeos implementados:**
* Tiempo: `anoreg + mesreg` → `id_tiempo_mes`
* Geografía: `depocu` (departamento ocurrencia) → `id_geografia`
* Perfil: `sexo + Edadif` → `id_perfil`
* Causa: `Caudef` → `id_causa` (clasificación CIE-10)

---

#### **Yeni (OMS)** ⏳ Plantilla lista

**Archivo:** `transformations/gold/fact_parcial_oms.py`

**Estructura obligatoria:**
```python
return DataFrame con:
  - id_tiempo_mes: STRING
  - id_geografia: STRING
  - id_perfil: STRING
  - id_causa: STRING
  - cantidad_fallecidos: LONG
  - fuente: STRING = "OMS"
```

**Guía de implementación:**
1. Leer tablas bronze de OMS
2. Mapear fechas a `id_tiempo_mes` (formato "YYYY-MM")
3. Mapear países a `id_geografia` (ej: "GT-NA" para Guatemala nacional)
4. Mapear sexo y edad a `id_perfil` (usar dim_perfil como referencia)
5. Mapear causas a `id_causa` (usar dim_causa_muerte)
6. Agrupar y contar fallecidos
7. Agregar `fuente = "OMS"`

---

#### **Byron (Costa Rica)** ⏳ Plantilla lista

**Archivo:** `transformations/gold/fact_parcial_costa_rica.py`

**Estructura obligatoria:**
```python
return DataFrame con:
  - id_tiempo_mes: STRING
  - id_geografia: STRING = "CR-NA"
  - id_perfil: STRING
  - id_causa: STRING
  - cantidad_fallecidos: LONG
  - fuente: STRING = "CR"
```

**Notas importantes:**
* **NO usar** las siguientes tablas (según instrucciones):
  - `desagregados_por_departamento_20xx`
  - `mortalidad_indicadores_costa_rica`
  - `mortalidad_por_edades_costa_rica`
  - `mortalidad_categorias_costa_rica_2020`
* Costa Rica solo tiene nivel nacional: siempre usar `id_geografia = "CR-NA"`

---

### **FASE 3: Consolidación Final** ⏳ Automática

**Archivo:** `transformations/gold/consolidacion_final.py`

**Lógica:**
```python
fact_mortalidad_unificada = 
    fact_parcial_ine
    UNION ALL fact_parcial_oms
    UNION ALL fact_parcial_costa_rica
```

**Se ejecuta automáticamente** cuando Yeni y Byron completen sus tablas parciales.

---

## 📝 Queries de Ejemplo

### Query 1: Mortalidad COVID en Guatemala durante pandemia

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
GROUP BY t.anio, t.nombre_mes, g.nombre_departamento, p.sexo, p.rango_edad
ORDER BY t.anio, t.mes, total_fallecidos DESC;
```

---

### Query 2: Comparación Guatemala vs Costa Rica

```sql
SELECT 
    g.pais,
    t.anio,
    c.categoria_general,
    SUM(f.cantidad_fallecidos) as total_fallecidos
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_geografia g 
    ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
JOIN covid19.gold.covid19_gold_dim_causa_muerte c 
    ON f.id_causa = c.id_causa
WHERE t.anio IN (2020, 2021, 2022)
GROUP BY g.pais, t.anio, c.categoria_general
ORDER BY g.pais, t.anio, total_fallecidos DESC;
```

---

### Query 3: Análisis por grupo etario

```sql
SELECT 
    p.rango_edad,
    t.periodo,
    COUNT(DISTINCT f.id_tiempo_mes) as meses_con_datos,
    SUM(f.cantidad_fallecidos) as total_fallecidos,
    AVG(f.cantidad_fallecidos) as promedio_mensual
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_perfil p 
    ON f.id_perfil = p.id_perfil
JOIN covid19.gold.covid19_gold_dim_tiempo t 
    ON f.id_tiempo_mes = t.id_tiempo_mes
WHERE f.fuente = 'INE'
GROUP BY p.rango_edad, t.periodo
ORDER BY p.rango_edad, t.periodo;
```

---

### Query 4: Eventos civiles vs mortalidad (contexto)

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
)
SELECT 
    n.anio,
    n.total_nacimientos,
    d.total_defunciones,
    n.total_nacimientos - d.total_defunciones as crecimiento_natural
FROM nacimientos n
JOIN defunciones d ON n.anio = d.anio
ORDER BY n.anio;
```

---

## 🗺️ Mapeo de Fuentes a Dimensiones

### Mapeo INE → Dimensiones

| Campo INE | Dimensión | ID Dimensión | Lógica de Mapeo |
|-----------|-----------|--------------|-----------------|
| `anoreg`, `mesreg` | dim_tiempo | id_tiempo_mes | `CONCAT(anoreg, '-', LPAD(mesreg, 2, '0'))` |
| `depocu` | dim_geografia | id_geografia | `CONCAT('GT-', depocu)` |
| `sexo`, `Edadif` | dim_perfil | id_perfil | `sexo_letra + '-' + rango_edad` |
| `Caudef` | dim_causa_muerte | id_causa | Clasificación CIE-10 a categorías |

**Clasificación de causas INE:**
* COVID: Contiene "COVID" o código "U07"
* RESP: Contiene "RESPIRAT" o códigos "J00-J99"
* CARDIO: Contiene "CARDIO" o códigos "I00-I99"
* CANCER: Contiene "CANCER", "NEOPLAS" o códigos "C00-C99"
* EXTERNA: Accidentes/violencia, códigos "V00-Y99"
* OTRA: Resto de causas
* DESCONOCIDA: NULL o vacío

---

### Mapeo RENAP → fact_contexto

| Campo RENAP | Campo Destino | Transformación |
|-------------|---------------|----------------|
| `fecha` | id_tiempo_mes | `DATE_FORMAT(fecha, 'yyyy-MM')` |
| `evento` | tipo_evento | Normalización capitalización |
| `cantidad` | cantidad | Directo |

**Normalización de eventos:**
* Variantes de "NACIMIENTO"/"Nacimientos" → "Nacimientos"
* Variantes de "DEFUNCION"/"Defunciones" → "Defunciones"
* Etc.

---

## 📊 Resumen de Registros

| Tabla | Registros | Estado |
|-------|-----------|--------|
| dim_tiempo | 144 | ✅ Completa |
| dim_geografia | 24 | ✅ Completa |
| dim_perfil | 12 | ✅ Completa |
| dim_causa_muerte | 48 | ✅ Completa |
| **fact_parcial_ine** | **48,656** | ✅ **Completa** |
| **fact_contexto_renap** | **1,943** | ✅ **Completa** |
| fact_parcial_oms | 0 | ⏳ Plantilla |
| fact_parcial_costa_rica | 0 | ⏳ Plantilla |
| fact_mortalidad_unificada | Pendiente | ⏳ Esperando OMS y CR |

---

## 🚀 Ejecución del Pipeline

### Comando para ejecutar todo el pipeline

```python
# Dry run (validación sin ejecutar)
startPipelineDryRun()

# Ejecución completa (cuando Yeni y Byron terminen)
startPipelineUpdate(
    fullRefresh=False,
    refreshSelectionByDataset=[
        "covid19_gold_dim_tiempo",
        "covid19_gold_dim_geografia",
        "covid19_gold_dim_perfil",
        "covid19_gold_dim_causa_muerte",
        "covid19_gold_fact_parcial_ine",
        "covid19_gold_fact_contexto_renap",
        "covid19_gold_fact_parcial_oms",
        "covid19_gold_fact_parcial_costa_rica",
        "covid19_gold_fact_mortalidad_unificada"
    ]
)
```

### Ejecución selectiva (solo tu trabajo)

```python
# Solo dimensiones y tus hechos (Wilson)
startPipelineUpdate(
    fullRefresh=False,
    refreshSelectionByDataset=[
        "covid19_gold_fact_parcial_ine",
        "covid19_gold_fact_contexto_renap"
    ]
)
```

---

## ⚠️ Problemas Conocidos y Soluciones

### 1. Esquema Gold creado correctamente

**Estado:** ✅ Las tablas Gold ahora están correctamente en `covid19.gold.*`

El pipeline fue reconfigurado con `schema: gold` y todas las tablas Gold se crearon exitosamente en el esquema correcto.

### 2. Datos RENAP con diferentes formatos

**Problema:** Las 12 tablas RENAP (2015-2026) tenían:
* 2016: Sin columna `diciembre`
* 2025-2026: Columna `total` en vez de `total_anual`
* 2015: Meses en tipo DOUBLE en vez de BIGINT

**Solución:** ✅ Ya resuelto en `silver_eventos_unificados` que normaliza todo.

### 3. Nombres de eventos duplicados en RENAP

**Problema:** Eventos con capitalización inconsistente (ej: "DEFUNCION", "Defunciones", "defuncion")

**Solución:** ✅ Ya normalizado en `fact_contexto_renap` con estandarización.

---

## 📚 Referencias

### Archivos del Pipeline

```
/Workspace/Users/yenniferdelion@gmail.com/covid19_dataAnalysis/pipelines/silver/Cleaning 2026-06-19 22:54/
│
├── transformations/
│   ├── eventos_unificados.py          # Silver: RENAP normalizado
│   ├── ine.py                         # Silver: INE deaths
│   │
│   └── gold/
│       ├── dimensiones.py             # 4 dimensiones maestras
│       ├── fact_parcial_ine.py        # Wilson: INE mortalidad
│       ├── fact_contexto_renap.py     # Wilson: RENAP eventos
│       ├── fact_parcial_oms.py        # Yeni: OMS plantilla
│       ├── fact_parcial_costa_rica.py # Byron: CR plantilla
│       └── consolidacion_final.py     # UNION ALL final
│
└── utilities/
    └── Functions 2026-06-20 16:20:49.py
```

### Tablas Bronze Usadas

**RENAP:**
* `covid19.bronze.desagregados_por_evento_2015` a `2026` (12 tablas)

**INACIF:**
* `covid19.bronze.inacif_departamentos`
* `covid19.bronze.inacif_causas_muerte`
* `covid19.bronze.inacif_municipios` (catalogada, no usada aún)
* `covid19.bronze.inacif_necropsias` (catalogada, no usada aún)

**INE:**
* Ya procesada en Silver: `covid19.silver.silver_ine_deaths`

---

## ✅ Checklist de Validación

### Para Wilson (Tú)
- [x] Esquema `covid19.gold` creado
- [x] Dimensiones maestras creadas en Gold
- [x] fact_parcial_ine con 48,656 registros en Gold
- [x] fact_contexto_renap con 1,943 registros en Gold
- [x] JOINs funcionan correctamente
- [x] Documentación completa y actualizada

### Para Yeni
- [ ] Leer plantilla `fact_parcial_oms.py`
- [ ] Identificar tablas bronze de OMS
- [ ] Implementar transformación
- [ ] Validar estructura de salida
- [ ] Ejecutar dry run
- [ ] Ejecutar pipeline

### Para Byron
- [ ] Leer plantilla `fact_parcial_costa_rica.py`
- [ ] Identificar tablas válidas (excluir las listadas)
- [ ] Implementar transformación
- [ ] Validar estructura de salida (id_geografia = "CR-NA")
- [ ] Ejecutar dry run
- [ ] Ejecutar pipeline

### Para el Equipo
- [ ] Revisar fact_mortalidad_unificada cuando todos terminen
- [ ] Validar conteos totales
- [ ] Ejecutar queries de análisis
- [ ] Crear dashboards

---

## 📞 Contacto y Soporte

**Preguntas sobre:**
* Dimensiones y arquitectura → Wilson
* Plantilla OMS → Yeni
* Plantilla Costa Rica → Byron
* Pipeline técnico → Equipo completo

---

**Última actualización:** 21 de junio de 2026  
**Versión del documento:** 1.1  
**Cambios:** Migración exitosa al esquema `covid19.gold`
