# Fase 2: Desarrollo del Pipeline ETL

## Descripción

En esta fase se desarrolla el pipeline completo de extracción, transformación y carga (ETL) para el análisis de mortalidad COVID-19. El pipeline implementa arquitectura medallion (Bronze → Silver → Gold) utilizando Lakeflow Spark Declarative Pipelines.

## Componentes Principales

### 1. Arquitectura del Pipeline

* **Capa Bronze:** Ingestión de datos crudos de múltiples fuentes
  * INE Guatemala (mortalidad departamental)
  * OMS (datos COVID-19 globales)
  * RENAP (eventos civiles)
  * INACIF (catálogos de causas y geografía)

* **Capa Silver:** Limpieza y normalización de datos
  * Estandarización de esquemas
  * Limpieza de valores NaN/NULL
  * Normalización de tipos de datos
  * Unpivot de estructuras anchas a largas

* **Capa Gold:** Modelo dimensional (Star Schema)
  * 4 dimensiones maestras
  * 3 tablas de hechos parciales
  * 1 tabla consolidada
  * 1 tabla de contexto

### 2. Modelo Dimensional

**Dimensiones:**
* `dim_tiempo` - 144 meses (2015-2026) con clasificación Pre-COVID/Pandemia
* `dim_geografia` - 25 lugares (22 departamentos GT + agregados)
* `dim_perfil` - 12 perfiles demográficos (sexo × edad)
* `dim_causa_muerte` - 48 causas con clasificación CIE-10

**Tablas de Hechos:**
* `fact_parcial_ine` - 48,656 registros (Guatemala departamental)
* `fact_parcial_oms` - 45 registros (Guatemala nacional COVID)
* `fact_parcial_costa_rica` - 54 registros (Costa Rica nacional COVID)
* `fact_mortalidad_unificada` - 48,755 registros (consolidado)
* `fact_contexto_renap` - 1,943 registros (eventos civiles)

### 3. Transformaciones Implementadas

El pipeline implementa 25 reglas de transformación auditable, categorizadas en:

* **Calidad de Datos:** Gestión de NaN, validaciones, normalización de esquemas
* **Transformaciones de Negocio:** Clasificación CIE-10, rangos etarios, periodos pandemia
* **Data Warehouse:** Generación de surrogate keys, agregaciones dimensionales
* **Integración:** Consolidación de fuentes, preservación de trazabilidad

📋 **Documentación completa:** [STM y Reglas de Transformación Auditable](../stm-reglas-transformacion.md)

### 4. Estrategia de Trabajo en Equipo

El desarrollo se organizó en 3 fases secuenciales:

**FASE 1: Dimensiones Maestras** (Trabajo colaborativo)
* Creación de diccionarios compartidos
* Definición de convenciones de nomenclatura
* Generación de datos sintéticos para agregaciones

**FASE 2: Tablas Parciales** (Trabajo paralelo)
* Wilson: INE + RENAP (Guatemala departamental)
* Yeni: OMS Guatemala (nacional COVID)
* Byron: OMS Costa Rica (nacional COVID)

**FASE 3: Consolidación** (Trabajo colaborativo)
* UNION ALL de tablas parciales
* Validaciones de integridad referencial
* Pruebas de calidad de datos

## Entregables

### Código del Pipeline

**Ubicación:** `/pipelines/silver/Cleaning 2026-06-19 22:54/`

* `transformations/gold/dimensiones.py` - 4 dimensiones maestras
* `transformations/gold/fact_parcial_ine.py` - Tabla parcial INE
* `transformations/gold/fact_parcial_oms.py` - Tabla parcial OMS Guatemala
* `transformations/gold/fact_parcial_costa_rica.py` - Tabla parcial Costa Rica
* `transformations/gold/fact_contexto_renap.py` - Contexto RENAP
* `transformations/gold/consolidacion_final.py` - Consolidación final
* `transformations/eventos_unificados.py` - Silver RENAP
* `transformations/ine.py` - Silver INE
* `utilities/Functions 2026-06-20 16:20:49.py` - Funciones utilitarias

### Documentación Técnica

* **[STM y Reglas de Transformación Auditable](../stm-reglas-transformacion.md)** ⭐ *NUEVO*
  * 25 reglas de transformación documentadas
  * Mapeos completos Source-to-Target
  * Linaje de datos por fuente
  * Validaciones de integridad referencial

* **[Modelo Estrella - Documentación Principal](../../pipelines/silver/Cleaning 2026-06-19 22:54/MODELO_ESTRELLA_DOCUMENTACION.md)**
  * Resumen ejecutivo del proyecto
  * Arquitectura del modelo dimensional
  * Estructura del pipeline

* **[Diccionario de Datos](../../pipelines/silver/Cleaning 2026-06-19 22:54/docs/DICCIONARIO_DATOS.md)**
  * Definiciones de todas las tablas y columnas
  * Reglas de negocio por tabla
  * Casos de uso y ejemplos

* **[Mapeos y Transformaciones](../../pipelines/silver/Cleaning 2026-06-19 22:54/docs/MAPEOS_TRANSFORMACIONES.md)**
  * Transformaciones Bronze→Silver→Gold
  * Reglas de limpieza de datos
  * Ejemplos de transformación

* **[Queries de Ejemplo](../../pipelines/silver/Cleaning 2026-06-19 22:54/docs/QUERIES_EJEMPLO.md)**
  * 10+ queries listas para ejecutar
  * Casos de uso analíticos
  * Ejemplos de agregaciones

* **[Resumen Ejecutivo](../../pipelines/silver/Cleaning 2026-06-19 22:54/docs/RESUMEN_EJECUTIVO.md)**
  * Métricas clave del proyecto
  * Hallazgos principales
  * Estado de completitud

### Diagramas y Modelos

* **[📐 Diagrama de Despliegue](https://drive.google.com/file/d/18b3k_3RjToLoVRJJyAxvWQCRz0q2Xo05/view?usp=drive_link)** (Google Drive)
  * Arquitectura de despliegue del sistema
  * Componentes de infraestructura
  * Flujos de datos entre capas

* **[🗄️ Modelo ERD en Data Modeler](https://drive.google.com/file/d/1wDKIUzympT9m_i_NJar_04tFYun4Ke3_/view?usp=drive_link)** (Google Drive)
  * Diagrama Entidad-Relación completo
  * Relaciones entre dimensiones y hechos
  * Cardinalidades y claves foráneas

* **[📊 Source-to-Target Mapping (Spreadsheet)](https://docs.google.com/spreadsheets/d/1UQjlX1iwqx1P1YFa0uI4anEBj6fUxkGXkwt8yoGjT1w/edit?usp=drive_link)** (Google Sheets)
  * Mapeos tabulares completos
  * Transformaciones campo a campo
  * Referencias cruzadas entre fuentes y destinos

## Métricas de Calidad

**Cobertura de Datos:**
* Total registros: 48,755 (consolidados)
* Periodo: 2015-2026 (144 meses)
* Países: Guatemala (departamental) + Costa Rica (nacional)
* Total fallecidos: 703,665 (todas las causas)

**Integridad Referencial:**
* ✅ 100% de claves foráneas válidas
* ✅ 0 registros con FK huérfanas
* ✅ Todas las dimensiones completas

**Calidad de Transformaciones:**
* ✅ 25 reglas de transformación implementadas
* ✅ NaN/NULL gestionados correctamente
* ✅ Esquemas normalizados (12/12 tablas RENAP)
* ✅ Consolidación verificada: 48,656 + 45 + 54 = 48,755

## Tecnologías Utilizadas

* **Databricks:** Plataforma de procesamiento
* **Lakeflow Spark Declarative Pipelines:** Framework ETL
* **Delta Lake:** Almacenamiento transaccional
* **PySpark:** Transformaciones de datos
* **Unity Catalog:** Gobierno de datos

## Estado de Completitud

✅ **100% COMPLETADO** - Pipeline operativo y documentado

* ✅ Arquitectura medallion implementada
* ✅ Modelo dimensional construido
* ✅ Transformaciones auditables documentadas
* ✅ Validaciones de calidad implementadas
* ✅ Documentación técnica completa

## Próximos Pasos

Ver [Fase 3: Análisis y Visualización](fase3.md) para el desarrollo de dashboards y análisis avanzados.

---

**Actualizado:** Junio 2026  
**Equipo:** Wilson (INE/RENAP), Yeni (OMS), Byron (Costa Rica)
