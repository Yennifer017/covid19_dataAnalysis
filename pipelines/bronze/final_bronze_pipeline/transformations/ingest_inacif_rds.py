"""
================================================================================
INGESTA MYSQL RDS → DATABRICKS BRONZE LAYER
Usando Lakehouse Federation (Unity Catalog)
================================================================================

OBJETIVO
--------
Ingestar todas las tablas del schema `proyecto_necropsias` desde MySQL RDS a 
la capa Bronze de Databricks (`covid19.bronze`) usando Lakehouse Federation, 
agregando columnas de auditoría para rastreo y linaje.

ARQUITECTURA
------------
Origen:
  - Base de datos: MySQL RDS 8.0
  - Host: ds-transaccional-rds.cx0w640wuzud.us-east-2.rds.amazonaws.com:3306
  - Schema: proyecto_necropsias
  - Tablas: 4 (causas_muerte, departamentos, municipios, necropsias)

Destino:
  - Catálogo: covid19
  - Schema: bronze
  - Formato: Delta Lake
  - Prefijo: inacif_

Método:
  - Unity Catalog Connection (no JDBC tradicional)
  - Foreign Catalog para acceso federado
  - Columnas de auditoría: bronze_loaded_at, bronze_batch_id, bronze_source

PRERREQUISITOS
--------------
- [ ] Unity Catalog Connection 'mysql_rds_inacif' creada
- [ ] Foreign Catalog 'inacif_mysql' creado
- [ ] Permisos: USE CATALOG, CREATE TABLE en covid19.bronze

CONFIGURACIÓN
-------------
Ver notebook: explorations/MySQL RDS Ingestion - Lakehouse Federation
Para instrucciones detalladas sobre:
  - Configuración de Databricks Secrets
  - Creación de UC Connection
  - Creación de Foreign Catalog
  - Estrategias de cargas incrementales
  - Optimizaciones de performance
  - Seguridad para repos públicos

================================================================================
CÓDIGO SDP - DEFINICIÓN DE DATASETS
================================================================================
"""

from pyspark import pipelines as dp
from pyspark.sql.functions import lit, current_timestamp
import uuid

# Generar batch_id único para esta ejecución del pipeline
BATCH_ID = str(uuid.uuid4())
SOURCE_SYSTEM = "mysql_rds_inacif"

# ==============================================================================
# TABLA 1: Causas de Muerte
# ==============================================================================

@dp.table(
    name="inacif_causas_muerte",
    comment="Catálogo de causas de muerte - Origen: MySQL INACIF proyecto_necropsias"
)
def ingest_causas_muerte():
    """
    Lee la tabla causas_muerte desde MySQL via Foreign Catalog.
    Agrega columnas de auditoría para rastreo.
    """
    return spark.read.table("inacif_mysql.proyecto_necropsias.causas_muerte") \
        .withColumn("bronze_loaded_at", current_timestamp()) \
        .withColumn("bronze_batch_id", lit(BATCH_ID)) \
        .withColumn("bronze_source", lit(SOURCE_SYSTEM))


# ==============================================================================
# TABLA 2: Departamentos
# ==============================================================================

@dp.table(
    name="inacif_departamentos",
    comment="Catálogo de departamentos de Guatemala - Origen: MySQL INACIF proyecto_necropsias"
)
def ingest_departamentos():
    """
    Lee la tabla departamentos desde MySQL via Foreign Catalog.
    Agrega columnas de auditoría para rastreo.
    """
    return spark.read.table("inacif_mysql.proyecto_necropsias.departamentos") \
        .withColumn("bronze_loaded_at", current_timestamp()) \
        .withColumn("bronze_batch_id", lit(BATCH_ID)) \
        .withColumn("bronze_source", lit(SOURCE_SYSTEM))


# ==============================================================================
# TABLA 3: Municipios
# ==============================================================================

@dp.table(
    name="inacif_municipios",
    comment="Catálogo de municipios de Guatemala - Origen: MySQL INACIF proyecto_necropsias"
)
def ingest_municipios():
    """
    Lee la tabla municipios desde MySQL via Foreign Catalog.
    Agrega columnas de auditoría para rastreo.
    """
    return spark.read.table("inacif_mysql.proyecto_necropsias.municipios") \
        .withColumn("bronze_loaded_at", current_timestamp()) \
        .withColumn("bronze_batch_id", lit(BATCH_ID)) \
        .withColumn("bronze_source", lit(SOURCE_SYSTEM))


# ==============================================================================
# TABLA 4: Necropsias (Tabla Principal)
# ==============================================================================

@dp.table(
    name="inacif_necropsias",
    comment="Registros de necropsias - Origen: MySQL INACIF proyecto_necropsias",
    table_properties={
        "quality": "bronze",
        "delta.enableChangeDataFeed": "true"
    }
)
def ingest_necropsias():
    """
    Lee la tabla necropsias (tabla principal) desde MySQL via Foreign Catalog.
    Contiene ~75K registros con información detallada de cada necropsia.
    Agrega columnas de auditoría para rastreo.
    """
    return spark.read.table("inacif_mysql.proyecto_necropsias.necropsias") \
        .withColumn("bronze_loaded_at", current_timestamp()) \
        .withColumn("bronze_batch_id", lit(BATCH_ID)) \
        .withColumn("bronze_source", lit(SOURCE_SYSTEM))


# ==============================================================================
# NOTAS
# ==============================================================================
"""
MODO DE OPERACIÓN:
------------------
- Cada vez que el pipeline ejecuta, genera un nuevo BATCH_ID
- Las tablas se sobrescriben completamente (modo overwrite por defecto en SDP)
- Para cargas incrementales, modificar a @dp.append_flow() con filtros

DEPENDENCIAS:
-------------
- Requiere que el Foreign Catalog 'inacif_mysql' exista y esté activo
- Requiere conectividad de red desde Databricks a MySQL RDS
- Requiere que las credenciales en el UC Connection sean válidas

PRÓXIMOS PASOS:
---------------
1. Crear capa Silver con transformaciones y joins
2. Implementar cargas incrementales (filtrar por ID o timestamp)
3. Agregar data quality expectations
4. Configurar optimizaciones (particionamiento, clustering)

Ver documentación completa en:
  /explorations/MySQL RDS Ingestion - Lakehouse Federation
"""
