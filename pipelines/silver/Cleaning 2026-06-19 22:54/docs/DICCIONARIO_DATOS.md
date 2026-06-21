# 📋 Diccionario de Datos - Modelo Estrella COVID-19

**Proyecto:** Análisis comparativo de mortalidad COVID-19  
**Última actualización:** 21 de junio de 2026

Este documento describe en detalle todas las tablas del modelo dimensional, sus columnas, tipos de datos, y reglas de negocio.

---

## Índice de Tablas

### Dimensiones
1. [dim_tiempo](#1%EF%B8%8F⃣-dim_tiempo-144-registros)
2. [dim_geografia](#2%EF%B8%8F⃣-dim_geografia-25-registros)
3. [dim_perfil](#3%EF%B8%8F⃣-dim_perfil-12-registros)
4. [dim_causa_muerte](#4%EF%B8%8F⃣-dim_causa_muerte-48-registros)

### Tablas de Hechos
5. [fact_mortalidad_unificada](#5%EF%B8%8F⃣-fact_mortalidad_unificada-48755-registros-%E2%9C%85)
6. [fact_contexto_renap](#6%EF%B8%8F⃣-fact_contexto_renap-1943-registros)

---

## 1️⃣ **dim_tiempo** (144 registros)

Dimensión temporal con clasificación de periodos Pre-COVID y Pandemia.

### Columnas

| Columna | Tipo | Nulable | PK | Descripción | Ejemplo |
|---------|------|---------|-------|-------------|---------|
| `id_tiempo_mes` | STRING | NO | ✅ | Clave primaria formato YYYY-MM | "2020-03" |
| `anio` | LONG | NO | | Año | 2020 |
| `mes` | LONG | NO | | Mes (1-12) | 3 |
| `nombre_mes` | STRING | NO | | Nombre del mes en español | "Marzo" |
| `periodo` | STRING | NO | | Clasificación de periodo | "Pandemia" |

### Reglas de Negocio

**Generación de id_tiempo_mes:**
```python
id_tiempo_mes = f"{anio}-{mes:02d}"
# Ejemplo: anio=2020, mes=3 → "2020-03"
```

**Clasificación de periodo:**
* `periodo = "Pre-COVID"` → Todos los meses antes de marzo 2020
* `periodo = "Pandemia"` → Marzo 2020 en adelante (inicio oficial pandemia COVID-19)

**Rango de datos:** Enero 2015 a Diciembre 2026 (144 meses)

**Nombres de meses:** Enero, Febrero, Marzo, Abril, Mayo, Junio, Julio, Agosto, Septiembre, Octubre, Noviembre, Diciembre

### Casos de Uso

* Filtrado por periodo: `WHERE periodo = 'Pandemia'`
* Agrupación anual: `GROUP BY anio`
* Ordenamiento temporal: `ORDER BY id_tiempo_mes`
* Análisis de tendencias: Comparar Pre-COVID vs Pandemia

---

## 2️⃣ **dim_geografia** (25 registros)

Dimensión geográfica con departamentos de Guatemala y Costa Rica.

### Columnas

| Columna | Tipo | Nulable | PK | Descripción | Ejemplo |
|---------|------|---------|-------|-------------|---------|
| `id_geografia` | STRING | NO | ✅ | Clave primaria | "GT-1", "GT-NA", "CR-NA" |
| `pais` | STRING | NO | | Nombre del país | "Guatemala", "Costa Rica" |
| `id_departamento` | LONG | NO | | Código interno departamento | 1, 2, ..., 22, 99, 0 |
| `nombre_departamento` | STRING | NO | | Nombre del departamento | "Guatemala", "Nacional" |

### Reglas de Negocio

**Formato de id_geografia:**
* Guatemala departamental: `"GT-{id_departamento}"` (GT-1 a GT-22)
* Guatemala nacional: `"GT-NA"` (agregación sin desglose departamental)
* Costa Rica nacional: `"CR-NA"` (país completo)

**Cobertura geográfica:**

| id_geografia | pais | id_departamento | nombre_departamento |
|--------------|------|-----------------|---------------------|
| GT-1 | Guatemala | 1 | Guatemala |
| GT-2 | Guatemala | 2 | El Progreso |
| GT-3 | Guatemala | 3 | Sacatepéquez |
| ... | ... | ... | ... |
| GT-22 | Guatemala | 22 | Petén |
| GT-NA | Guatemala | 99 | Nacional |
| CR-NA | Costa Rica | 0 | Nacional |

**Total:** 25 registros (22 departamentos GT + 1 nacional GT + 1 nacional CR + 1 legacy)

### Fuentes de Datos

* **Departamentos Guatemala:** `covid19.bronze.inacif_departamentos`
* **Niveles nacionales:** Registros sintéticos creados para soportar datos OMS

### Casos de Uso

* Filtrado por país: `WHERE pais = 'Guatemala'`
* Análisis departamental: `WHERE id_geografia LIKE 'GT-%' AND id_geografia != 'GT-NA'`
* Comparación internacional: `WHERE id_geografia IN ('GT-NA', 'CR-NA')`

---

## 3️⃣ **dim_perfil** (12 registros)

Dimensión de perfil demográfico (sexo × edad).

### Columnas

| Columna | Tipo | Nulable | PK | Descripción | Ejemplo |
|---------|------|---------|-------|-------------|---------|
| `id_perfil` | STRING | NO | ✅ | Clave primaria formato X-rango | "H-15-64", "M-65+", "A-Todas" |
| `sexo` | STRING | NO | | Sexo | "Hombre", "Mujer", "Ambos" |
| `rango_edad` | STRING | NO | | Rango de edad | "0-14", "15-64", "65+", "Todas" |

### Reglas de Negocio

**Formato de id_perfil:**
```
id_perfil = "{letra_sexo}-{rango_edad}"
```

**Letras de sexo:**
* `H` = Hombre
* `M` = Mujer
* `A` = Ambos (agregado de hombres y mujeres)

**Rangos de edad:**
* `0-14` = Menores de edad (0 a 14 años)
* `15-64` = Población en edad laboral (15 a 64 años)
* `65+` = Adultos mayores (65 años o más)
* `Todas` = Todas las edades (agregado)

**Combinaciones disponibles (12 perfiles):**

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

### Casos de Uso

* Filtrado por sexo: `WHERE sexo = 'Hombre'`
* Análisis por edad: `WHERE rango_edad = '65+'`
* Datos agregados: `WHERE id_perfil = 'A-Todas'`
* Grupos de riesgo COVID: `WHERE rango_edad IN ('65+', '15-64')`

---

## 4️⃣ **dim_causa_muerte** (48 registros)

Dimensión de causas de muerte con clasificación y flag COVID.

### Columnas

| Columna | Tipo | Nulable | PK | Descripción | Ejemplo |
|---------|------|---------|-------|-------------|---------|
| `id_causa` | STRING | NO | ✅ | Clave primaria | "COVID", "RESP", "INACIF-1" |
| `categoria_general` | STRING | NO | | Categoría amplia | "COVID-19", "Enfermedad Respiratoria" |
| `nombre_causa` | STRING | NO | | Descripción detallada | "COVID-19 (U07.1 o U07.2)" |
| `es_covid` | BOOLEAN | NO | | Flag para filtrar COVID | TRUE, FALSE |

### Reglas de Negocio

**Categorías generales:**

| Categoría General | Descripción | Códigos CIE-10 |
|-------------------|-------------|----------------|
| COVID-19 | Mortalidad específica por COVID-19 | U07.1, U07.2 |
| Enfermedad Respiratoria | Enfermedades del sistema respiratorio | J00-J99 |
| Enfermedad Cardiovascular | Enfermedades del sistema circulatorio | I00-I99 |
| Cáncer | Neoplasias malignas | C00-C99 |
| Causa Externa | Accidentes, homicidios, suicidios | V00-Y99 |
| Otra | Otras causas no clasificadas | — |
| Desconocida | Causa no especificada o desconocida | R99 |

**Flag es_covid:**
* `TRUE`: Solo registros de COVID-19 (id_causa = "COVID")
* `FALSE`: Todas las demás causas

**Tipos de id_causa:**
* Sintéticas de mapeo: "COVID", "RESP", "CARDIO", "CANCER", "EXTERNA", "OTRA", "DESCONOCIDA"
* INACIF detalladas: "INACIF-1", "INACIF-2", ... (causas específicas del catálogo INACIF)

### Fuentes de Datos

* **Causas INACIF:** `covid19.bronze.inacif_causas_muerte` (catálogo completo de causas de muerte)
* **Causas sintéticas:** Creadas para mapear categorías generales y facilitar análisis

### Clasificación CIE-10 Implementada

```python
# Clasificación basada en texto y códigos CIE-10
def clasificar_causa(caudef_texto):
    if 'COVID' in caudef_texto or 'U07' in caudef_texto:
        return 'COVID'
    elif 'RESPIRAT' in caudef_texto or any(f'J{i:02d}' in caudef_texto for i in range(0,100)):
        return 'RESP'
    elif 'CARDIO' in caudef_texto or any(f'I{i:02d}' in caudef_texto for i in range(0,100)):
        return 'CARDIO'
    elif 'CANCER' in caudef_texto or 'NEOPLAS' in caudef_texto:
        return 'CANCER'
    elif any(caudef_texto.startswith(prefix) for prefix in ['V', 'W', 'X', 'Y']):
        return 'EXTERNA'
    elif caudef_texto is None or caudef_texto == '':
        return 'DESCONOCIDA'
    else:
        return 'OTRA'
```

### Casos de Uso

* Filtrado COVID: `WHERE es_covid = TRUE`
* Análisis por categoría: `WHERE categoria_general = 'Enfermedad Respiratoria'`
* Causas externas: `WHERE categoria_general = 'Causa Externa'`
* Top causas: `GROUP BY nombre_causa ORDER BY SUM(cantidad_fallecidos) DESC`

---

## 5️⃣ **fact_mortalidad_unificada** (48,755 registros) ✅

Tabla de hechos maestra con mortalidad de todas las fuentes consolidadas.

### Columnas

| Columna | Tipo | Nulable | FK | Descripción | Ejemplo |
|---------|------|---------|-----|-------------|---------|
| `id_tiempo_mes` | STRING | NO | → dim_tiempo | Mes de ocurrencia | "2020-03" |
| `id_geografia` | STRING | NO | → dim_geografia | Lugar de ocurrencia | "GT-1", "GT-NA", "CR-NA" |
| `id_perfil` | STRING | NO | → dim_perfil | Perfil demográfico | "H-15-64", "A-Todas" |
| `id_causa` | STRING | NO | → dim_causa_muerte | Causa de muerte | "COVID" |
| `cantidad_fallecidos` | LONG | NO | | **MÉTRICA:** Número de fallecidos | 276 |
| `fuente` | STRING | NO | | Fuente de datos | "INE", "OMS", "CR" |
| `fecha_actualizacion` | TIMESTAMP | NO | | Timestamp de procesamiento | 2026-06-21 |

### Reglas de Negocio

**Granularidad:**
* Una fila por combinación única de: mes + geografía + perfil + causa + fuente
* Pueden existir múltiples registros para el mismo mes-geografía-perfil-causa si provienen de fuentes diferentes

**Fuentes consolidadas:**

| Fuente | Descripción | Registros | Total Fallecidos | Periodo |
|--------|-------------|-----------|------------------|---------|
| `INE` | Instituto Nacional de Estadística Guatemala | 48,656 | 674,064 | 2018-2025 |
| `OMS` | Organización Mundial de la Salud (Guatemala) | 45 | 20,205 | 2020-2025 |
| `CR` | Costa Rica (OMS) | 54 | 9,396 | 2020-2026 |

**Lógica de consolidación:**
```sql
CREATE OR REFRESH MATERIALIZED VIEW fact_mortalidad_unificada AS
SELECT * FROM fact_parcial_ine
UNION ALL
SELECT * FROM fact_parcial_oms
UNION ALL
SELECT * FROM fact_parcial_costa_rica;
```

### Características por Fuente

#### Fuente INE (Guatemala)
* ✅ Desglose departamental (22 departamentos)
* ✅ Desglose por sexo y edad
* ✅ Todas las causas de muerte
* ✅ Mayor detalle y granularidad

#### Fuente OMS (Guatemala)
* ⚠️ Solo nivel nacional (GT-NA)
* ⚠️ Solo COVID-19
* ⚠️ Sin desglose por sexo/edad (A-Todas)
* ✅ Comparación internacional estándar

#### Fuente CR (Costa Rica)
* ⚠️ Solo nivel nacional (CR-NA)
* ⚠️ Solo COVID-19
* ⚠️ Sin desglose por sexo/edad (A-Todas)
* ✅ Consistencia metodológica con OMS Guatemala

### Integridad Referencial

Todas las claves foráneas están validadas contra sus dimensiones:

```sql
-- Validación de JOINs
SELECT COUNT(*) 
FROM fact_mortalidad_unificada f
LEFT JOIN dim_tiempo t ON f.id_tiempo_mes = t.id_tiempo_mes
LEFT JOIN dim_geografia g ON f.id_geografia = g.id_geografia
LEFT JOIN dim_perfil p ON f.id_perfil = p.id_perfil
LEFT JOIN dim_causa_muerte c ON f.id_causa = c.id_causa
WHERE t.id_tiempo_mes IS NULL 
   OR g.id_geografia IS NULL 
   OR p.id_perfil IS NULL 
   OR c.id_causa IS NULL;
-- Resultado esperado: 0 registros (todas las FKs válidas)
```

### Casos de Uso

1. **Análisis temporal total:**
   ```sql
   SELECT anio, SUM(cantidad_fallecidos)
   FROM fact_mortalidad_unificada f
   JOIN dim_tiempo t ON f.id_tiempo_mes = t.id_tiempo_mes
   GROUP BY anio;
   ```

2. **Comparación de fuentes (Guatemala):**
   ```sql
   SELECT fuente, SUM(cantidad_fallecidos)
   FROM fact_mortalidad_unificada
   WHERE id_geografia LIKE 'GT%'
   GROUP BY fuente;
   ```

3. **Top departamentos COVID (INE):**
   ```sql
   SELECT g.nombre_departamento, SUM(f.cantidad_fallecidos)
   FROM fact_mortalidad_unificada f
   JOIN dim_geografia g ON f.id_geografia = g.id_geografia
   JOIN dim_causa_muerte c ON f.id_causa = c.id_causa
   WHERE c.es_covid = TRUE AND f.fuente = 'INE'
   GROUP BY g.nombre_departamento
   ORDER BY SUM(f.cantidad_fallecidos) DESC;
   ```

---

## 6️⃣ **fact_contexto_renap** (1,943 registros)

Tabla de hechos satélite con eventos civiles del RENAP (contexto demográfico).

### Columnas

| Columna | Tipo | Nulable | FK | Descripción | Ejemplo |
|---------|------|---------|-----|-------------|---------|
| `id_tiempo_mes` | STRING | NO | → dim_tiempo | Mes del evento | "2020-03" |
| `tipo_evento` | STRING | NO | | Tipo de evento civil | "Nacimientos", "Matrimonios" |
| `cantidad` | LONG | NO | | **MÉTRICA:** Número de eventos | 35000 |
| `fuente` | STRING | NO | | Fuente de datos | "RENAP" |

### Reglas de Negocio

**Granularidad:**
* Una fila por combinación única de: mes + tipo_evento
* Esta tabla NO usa las dimensiones geografia/perfil/causa porque son eventos contextuales nacionales

**Tipos de eventos incluidos:**

| tipo_evento | Descripción |
|-------------|-------------|
| Nacimientos | Inscripciones de nacimientos |
| Defunciones | Inscripciones de defunciones (puede diferir de fact_mortalidad) |
| Matrimonios | Inscripciones de matrimonios |
| Divorcios | Inscripciones de divorcios |
| Reconocimientos | Reconocimientos de paternidad/maternidad |
| Identificación de Persona | Emisión de DPI |
| Adopciones | Inscripciones de adopciones |
| Cambio de Nombre | Cambios oficiales de nombre |
| Unión de Hecho | Inscripciones de uniones de hecho |
| Naturalizaciones | Naturalizaciones de extranjeros |
| Extranjeros Domiciliados | Inscripción de extranjeros domiciliados |

### Fuente de Datos

* **RENAP:** `covid19.silver.silver_eventos_por_mes`
  * Originalmente de 12 tablas bronze: `desagregados_por_evento_2015` a `2026`
  * Transformadas a formato largo (UNPIVOT de 12 columnas mensuales)

### Diferencia con fact_mortalidad

**fact_mortalidad_unificada:**
* Defunciones registradas en el sistema de salud (INE, INACIF)
* Fecha de ocurrencia de la muerte
* Desglose por departamento, sexo, edad, causa

**fact_contexto_renap:**
* Defunciones inscritas en el Registro Civil (RENAP)
* Fecha de inscripción del evento
* Sin desglose demográfico (solo totales nacionales)

**Nota:** Las cifras de defunciones pueden diferir debido a:
* Rezago en inscripción (muere en X, se inscribe en X+1)
* Cobertura diferente (no todas las muertes se inscriben inmediatamente)

### Casos de Uso

1. **Crecimiento natural (Nacimientos - Defunciones):**
   ```sql
   WITH eventos AS (
     SELECT 
       id_tiempo_mes,
       MAX(CASE WHEN tipo_evento = 'Nacimientos' THEN cantidad END) as nacimientos,
       MAX(CASE WHEN tipo_evento = 'Defunciones' THEN cantidad END) as defunciones
     FROM fact_contexto_renap
     GROUP BY id_tiempo_mes
   )
   SELECT 
     id_tiempo_mes,
     nacimientos,
     defunciones,
     nacimientos - defunciones as crecimiento_natural
   FROM eventos
   ORDER BY id_tiempo_mes;
   ```

2. **Impacto COVID en matrimonios:**
   ```sql
   SELECT 
     t.periodo,
     AVG(f.cantidad) as promedio_matrimonios
   FROM fact_contexto_renap f
   JOIN dim_tiempo t ON f.id_tiempo_mes = t.id_tiempo_mes
   WHERE tipo_evento = 'Matrimonios'
   GROUP BY t.periodo;
   ```

3. **Eventos totales por año:**
   ```sql
   SELECT 
     SUBSTRING(id_tiempo_mes, 1, 4) as anio,
     tipo_evento,
     SUM(cantidad) as total
   FROM fact_contexto_renap
   GROUP BY SUBSTRING(id_tiempo_mes, 1, 4), tipo_evento
   ORDER BY anio, total DESC;
   ```

---

## 📊 Resumen de Relaciones

```
dim_tiempo (144)
    ↓
    ├── fact_mortalidad_unificada (48,755)
    │       ↓
    │       ├── dim_geografia (25)
    │       ├── dim_perfil (12)
    │       └── dim_causa_muerte (48)
    │
    └── fact_contexto_renap (1,943)
```

**Total de registros en el modelo:** 50,927

---

## 🔗 Referencias

* [Modelo Completo](../MODELO_ESTRELLA_DOCUMENTACION.md)
* [Queries de Ejemplo](QUERIES_EJEMPLO.md)
* [Mapeos de Transformación](MAPEOS_TRANSFORMACIONES.md)
* [Resumen Ejecutivo](RESUMEN_EJECUTIVO.md)

---

**Última actualización:** 21 de junio de 2026  
**Versión:** 1.0
