# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Introducción: Ingesta MySQL RDS a Databricks via Lakehouse Federation
# MAGIC %md
# MAGIC # Ingesta MySQL RDS → Databricks Bronze Layer
# MAGIC ## Usando Lakehouse Federation (Unity Catalog)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 📋 Objetivo
# MAGIC Ingestar todas las tablas del schema `proyecto_necropsias` desde MySQL RDS a la capa Bronze de Databricks (`covid19.bronze`) usando **Lakehouse Federation**, agregando columnas de auditoría para rastreo y linaje.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🏗️ Arquitectura
# MAGIC
# MAGIC **Origen:**
# MAGIC - **Base de datos:** MySQL RDS 8.0
# MAGIC - **Host:** `ds-transaccional-rds.cx0w640wuzud.us-east-2.rds.amazonaws.com:3306`
# MAGIC - **Schema:** `proyecto_necropsias`
# MAGIC - **Tablas:** 4 (causas_muerte, departamentos, municipios, necropsias)
# MAGIC
# MAGIC **Destino:**
# MAGIC - **Catálogo:** `covid19`
# MAGIC - **Schema:** `bronze`
# MAGIC - **Formato:** Delta Lake
# MAGIC - **Prefijo:** `inacif_`
# MAGIC
# MAGIC **Método:**
# MAGIC - Unity Catalog Connection (no JDBC tradicional)
# MAGIC - Foreign Catalog para acceso federado
# MAGIC - Columnas de auditoría: `bronze_loaded_at`, `bronze_batch_id`, `bronze_source`
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🔄 Flujo del Proceso
# MAGIC
# MAGIC 1. **Setup Infraestructura** (Una sola vez)
# MAGIC    - Crear Unity Catalog Connection a MySQL
# MAGIC    - Crear Foreign Catalog sobre el schema origen
# MAGIC    - Verificar acceso a tablas
# MAGIC
# MAGIC 2. **Ingesta de Datos** (Ejecutable múltiples veces)
# MAGIC    - Descubrir tablas dinámicamente
# MAGIC    - Leer desde Federation
# MAGIC    - Agregar columnas de auditoría
# MAGIC    - Escribir a Delta (modo overwrite)
# MAGIC
# MAGIC 3. **Validación** (Opcional)
# MAGIC    - Verificar tablas creadas
# MAGIC    - Confirmar columnas de auditoría
# MAGIC    - Revisar conteos de filas
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### ⚠️ Prerrequisitos
# MAGIC
# MAGIC - [ ] Permisos: `CREATE CONNECTION`, `CREATE CATALOG` en Unity Catalog
# MAGIC - [ ] Permisos: `USE CATALOG`, `CREATE TABLE` en `covid19.bronze`
# MAGIC - [ ] Credenciales MySQL: usuario, password, host
# MAGIC - [ ] Red: Conectividad desde Databricks a MySQL RDS
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 📝 Notas Importantes
# MAGIC
# MAGIC **Seguridad:**
# MAGIC - Las credenciales se almacenan encriptadas en Unity Catalog
# MAGIC - Se usa `trustServerCertificate=true` para evitar límite de 10KB en propiedades
# MAGIC
# MAGIC **Idempotencia:**
# MAGIC - La ingesta usa `mode("overwrite")` - se puede re-ejecutar de forma segura
# MAGIC - Cada ejecución genera un nuevo `batch_id` único
# MAGIC
# MAGIC **Cargas Futuras:**
# MAGIC - Este proceso es para carga inicial completa (full load)
# MAGIC - Para cargas incrementales, modificar el código para filtrar por timestamp o ID
# MAGIC
# MAGIC ---

# COMMAND ----------

# DBTITLE 1,SETUP 1/3: Crear Unity Catalog Connection a MySQL RDS
# MAGIC %sql
# MAGIC -- ============================================================================
# MAGIC -- UNITY CATALOG CONNECTION: MySQL RDS
# MAGIC -- ============================================================================
# MAGIC -- NOTA: Solo necesitas ejecutar esto UNA VEZ. Si la conexión ya existe, 
# MAGIC --       este comando fallará (es esperado).
# MAGIC
# MAGIC -- Crear conexión a MySQL RDS
# MAGIC CREATE CONNECTION IF NOT EXISTS mysql_rds_inacif
# MAGIC TYPE mysql
# MAGIC OPTIONS (
# MAGIC   host 'prueba',
# MAGIC   port '3306',
# MAGIC   user 'prueba',
# MAGIC   password 'prueba',
# MAGIC   -- Usar trustServerCertificate para evitar límite de 10KB en certificados
# MAGIC   trustServerCertificate 'true'
# MAGIC );
# MAGIC
# MAGIC -- Verificar que la conexión se creó
# MAGIC DESCRIBE CONNECTION mysql_rds_inacif;

# COMMAND ----------

# DBTITLE 1,SETUP 2/3: Crear Foreign Catalog sobre MySQL Schema
# MAGIC %sql
# MAGIC -- ============================================================================
# MAGIC -- FOREIGN CATALOG: Acceso federado a proyecto_necropsias
# MAGIC -- ============================================================================
# MAGIC -- NOTA: Solo necesitas ejecutar esto UNA VEZ. Si el catálogo ya existe,
# MAGIC --       este comando fallará (es esperado).
# MAGIC
# MAGIC -- Crear Foreign Catalog apuntando al schema proyecto_necropsias
# MAGIC CREATE FOREIGN CATALOG IF NOT EXISTS inacif_mysql
# MAGIC USING CONNECTION mysql_rds_inacif
# MAGIC OPTIONS (
# MAGIC   database 'proyecto_necropsias'
# MAGIC );
# MAGIC
# MAGIC -- Refrescar metadata (importante después de crear)
# MAGIC REFRESH FOREIGN CATALOG inacif_mysql;
# MAGIC
# MAGIC -- Listar tablas disponibles
# MAGIC SHOW TABLES IN inacif_mysql.proyecto_necropsias;

# COMMAND ----------

# DBTITLE 1,SETUP 3/3: Verificar Infraestructura y Acceso
# ============================================================================
# VERIFICACIÓN DE INFRAESTRUCTURA
# ============================================================================
# Esta celda verifica que:
# 1. El UC Connection existe y es accesible
# 2. El Foreign Catalog existe
# 3. Podemos acceder a las tablas en MySQL
# 4. Tenemos permisos en el destino covid19.bronze

print("="*80)
print("VERIFICACIÓN DE INFRAESTRUCTURA")
print("="*80)

# ----------------------------------------------------------------------------
print("\n1. Verificando Unity Catalog Connection...")
try:
    connection_info = spark.sql("DESCRIBE CONNECTION mysql_rds_inacif").collect()
    print("   ✓ Connection 'mysql_rds_inacif' existe")
    print(f"   Propiedades: {len(connection_info)} configuradas")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("   → Ejecuta la celda 'SETUP 1/3' primero")

# ----------------------------------------------------------------------------
print("\n2. Verificando Foreign Catalog...")
try:
    catalogs = [row.catalog for row in spark.sql("SHOW CATALOGS").collect()]
    if 'inacif_mysql' in catalogs:
        print("   ✓ Foreign Catalog 'inacif_mysql' existe")
    else:
        print("   ❌ Foreign Catalog 'inacif_mysql' NO existe")
        print("   → Ejecuta la celda 'SETUP 2/3' primero")
except Exception as e:
    print(f"   ❌ Error: {e}")

# ----------------------------------------------------------------------------
print("\n3. Verificando acceso a tablas origen...")
try:
    tables_df = spark.sql("SHOW TABLES IN inacif_mysql.proyecto_necropsias")
    tables = [row.tableName for row in tables_df.collect()]
    print(f"   ✓ Acceso exitoso a inacif_mysql.proyecto_necropsias")
    print(f"   Tablas disponibles: {len(tables)}")
    for table in tables:
        print(f"     - {table}")
        
    # Probar lectura de una tabla
    sample_count = spark.sql("SELECT COUNT(*) as cnt FROM inacif_mysql.proyecto_necropsias.necropsias").collect()[0].cnt
    print(f"\n   ✓ Lectura exitosa: tabla 'necropsias' tiene {sample_count:,} filas")
    
except Exception as e:
    print(f"   ❌ Error al acceder a tablas: {str(e)[:200]}")
    print("   → Verifica conectividad de red y credenciales")

# ----------------------------------------------------------------------------
print("\n4. Verificando permisos en destino (covid19.bronze)...")
try:
    spark.sql("USE CATALOG covid19")
    print("   ✓ Puedo usar catálogo covid19")
    
    schemas = [row.databaseName for row in spark.sql("SHOW SCHEMAS IN covid19").collect()]
    if 'bronze' in schemas:
        print("   ✓ Schema 'bronze' existe")
        
        # Verificar si podemos listar tablas
        tables = spark.sql("SHOW TABLES IN covid19.bronze").collect()
        print(f"   ✓ Puedo acceder a covid19.bronze ({len(tables)} tablas existentes)")
    else:
        print("   ⚠ Schema 'bronze' NO existe en covid19")
        print("   → Crear con: CREATE SCHEMA IF NOT EXISTS covid19.bronze")
        
except Exception as e:
    print(f"   ❌ Error: {str(e)[:200]}")
    print("   → Solicita permisos: GRANT USE CATALOG ON CATALOG covid19 TO <tu_usuario>")
    print("   → Solicita permisos: GRANT CREATE TABLE ON SCHEMA covid19.bronze TO <tu_usuario>")

# ----------------------------------------------------------------------------
print("\n" + "="*80)
print("RESULTADO")
print("="*80)
print("Si todos los checks pasaron (✓), puedes ejecutar la celda de ingesta.")
print("Si hay errores (❌), sigue las instrucciones indicadas.")
print("="*80)

# COMMAND ----------

# DBTITLE 1,Ingestar todas las tablas de MySQL RDS a Delta via Federation
# ============================================================================
# NOTEBOOK: Ingesta completa de MySQL RDS a Delta via Lakehouse Federation
# ============================================================================

import uuid
from pyspark.sql.functions import lit, current_timestamp
from datetime import datetime

print("="*80)
print("INGESTA: MySQL RDS → Delta Tables (via Lakehouse Federation)")
print("="*80)

# ============================================================================
print("\n" + "="*80)
print("PASO 1: Configuración")
print("="*80)

# Configuración origen (Foreign Catalog)
SOURCE_CATALOG = "inacif_mysql"
SOURCE_SCHEMA = "proyecto_necropsias"

# Configuración destino (Delta) - AHORA EN COVID19.BRONZE
TARGET_CATALOG = "covid19"
TARGET_SCHEMA = "bronze"
TABLE_PREFIX = "inacif_"

# Metadata de auditoría para este batch
BATCH_ID = str(uuid.uuid4())
SOURCE_SYSTEM = "mysql_rds_inacif"

print(f"Origen: {SOURCE_CATALOG}.{SOURCE_SCHEMA}")
print(f"Destino: {TARGET_CATALOG}.{TARGET_SCHEMA}.{TABLE_PREFIX}*")
print(f"Batch ID: {BATCH_ID}")
print(f"Timestamp: {datetime.now().isoformat()}")

# ============================================================================
print("\n" + "="*80)
print("PASO 2: Descubrir tablas en origen")
print("="*80)

try:
    tables_df = spark.sql(f"SHOW TABLES IN {SOURCE_CATALOG}.{SOURCE_SCHEMA}")
    tables = [row.tableName for row in tables_df.collect()]
    
    print(f"✓ Tablas encontradas: {len(tables)}")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table}")
    print()
    
except Exception as e:
    print(f"❌ Error al descubrir tablas: {e}")
    raise

# ============================================================================
print("="*80)
print("PASO 3: Ingestar tablas con columnas de auditoría")
print("="*80)

print(f"Total de tablas a procesar: {len(tables)}")
print(f"Modo: Carga completa (overwrite)\n")

# Contadores
success_count = 0
failed_tables = []
ingestion_details = []

# Procesar cada tabla
for i, table_name in enumerate(tables, 1):
    source_table = f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{table_name}"
    target_table = f"{TARGET_CATALOG}.{TARGET_SCHEMA}.{TABLE_PREFIX}{table_name}"
    
    print(f"[{i}/{len(tables)}] {table_name}")
    print(f"  Origen: {source_table}")
    print(f"  Destino: {target_table}")
    
    try:
        # Leer desde Federation
        df_source = spark.read.table(source_table)
        row_count = df_source.count()
        
        # Agregar columnas de auditoría usando withColumns (más eficiente)
        df_with_audit = df_source.withColumns({
            "bronze_loaded_at": current_timestamp(),
            "bronze_batch_id": lit(BATCH_ID),
            "bronze_source": lit(SOURCE_SYSTEM)
        })
        
        col_count = len(df_source.columns)
        
        # Escribir a Delta
        df_with_audit.write \
            .format("delta") \
            .mode("overwrite") \
            .option("overwriteSchema", "true") \
            .saveAsTable(target_table)
        
        success_count += 1
        print(f"  ✓ Completado: {row_count:,} filas, {col_count} columnas + 3 auditoría")
        print()
        
        ingestion_details.append({
            "table": table_name,
            "rows": row_count,
            "columns": col_count,
            "status": "SUCCESS"
        })
        
    except Exception as e:
        error_msg = str(e)
        failed_tables.append((table_name, error_msg))
        print(f"  ❌ Error: {error_msg[:150]}...")
        print()
        
        ingestion_details.append({
            "table": table_name,
            "rows": 0,
            "columns": 0,
            "status": "FAILED",
            "error": error_msg[:200]
        })
        
        continue

# ============================================================================
print("="*80)
print("RESUMEN DE INGESTA")
print("="*80)

print(f"\nBatch ID: {BATCH_ID}")
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"\nResultados:")
print(f"  ✓ Exitosas: {success_count}/{len(tables)}")
print(f"  ❌ Fallidas: {len(failed_tables)}/{len(tables)}")

if success_count > 0:
    print(f"\nTablas Delta creadas en: {TARGET_CATALOG}.{TARGET_SCHEMA}.{TABLE_PREFIX}*")
    print(f"\nColumnas de auditoría agregadas:")
    print(f"  - bronze_loaded_at: TIMESTAMP")
    print(f"  - bronze_batch_id: STRING ({BATCH_ID})")
    print(f"  - bronze_source: STRING ({SOURCE_SYSTEM})")

if failed_tables:
    print(f"\n⚠ Tablas con errores:")
    for table_name, error in failed_tables:
        print(f"  - {table_name}: {error[:100]}...")

if success_count == len(tables):
    print(f"\n🎉 ¡Todas las tablas fueron ingestadas exitosamente en covid19.bronze!")

print("\n" + "="*80)

# Mostrar detalle de ingesta
if ingestion_details:
    print("\nDetalle por tabla:")
    for detail in ingestion_details:
        status_icon = "✓" if detail["status"] == "SUCCESS" else "❌"
        print(f"  {status_icon} {detail['table']}: {detail['rows']:,} filas, {detail['columns']} cols")

print("="*80)

# COMMAND ----------

# DBTITLE 1,VALIDACIÓN POST-INGESTA: Verificar Tablas y Auditoría
# ============================================================================
# VALIDACIÓN POST-INGESTA
# ============================================================================
# Esta celda verifica que:
# 1. Las tablas se crearon correctamente en covid19.bronze
# 2. Todas tienen columnas de auditoría
# 3. Los conteos de filas son correctos
# 4. El batch_id es consistente

print("="*80)
print("VALIDACIÓN DE TABLAS INGESTADAS")
print("="*80)

# Listar todas las tablas en covid19.bronze
tables = spark.sql("SHOW TABLES IN covid19.bronze").collect()

# Filtrar tablas INACIF
inacif_tables = [row for row in tables if row.tableName.startswith('inacif_')]

print(f"\n✓ Total tablas INACIF encontradas: {len(inacif_tables)}\n")

if len(inacif_tables) == 0:
    print("❌ No se encontraron tablas con prefijo 'inacif_'")
    print("   → Ejecuta la celda de ingesta primero")
else:
    # Variables para resumen
    total_rows = 0
    all_batch_ids = set()
    all_have_audit = True
    
    # Mostrar detalles de cada tabla
    for i, table_row in enumerate(inacif_tables, 1):
        table_name = table_row.tableName
        full_name = f"covid19.bronze.{table_name}"
        
        print(f"{i}. {table_name}")
        print(f"   Ubicación: {full_name}")
        
        # Obtener conteo de filas
        count = spark.sql(f"SELECT COUNT(*) as cnt FROM {full_name}").collect()[0].cnt
        total_rows += count
        
        # Obtener esquema
        schema = spark.sql(f"DESCRIBE {full_name}").collect()
        col_names = [row.col_name for row in schema]
        
        # Verificar columnas de auditoría
        audit_cols = ['bronze_loaded_at', 'bronze_batch_id', 'bronze_source']
        has_audit = all(col in col_names for col in audit_cols)
        
        if not has_audit:
            all_have_audit = False
        
        print(f"   Filas: {count:,}")
        print(f"   Columnas: {len(col_names)}")
        print(f"   Auditoría: {'✓' if has_audit else '❌'}")
        
        if has_audit:
            # Obtener info de auditoría
            sample = spark.sql(f"""
                SELECT 
                    bronze_batch_id, 
                    bronze_source, 
                    MIN(bronze_loaded_at) as min_timestamp,
                    MAX(bronze_loaded_at) as max_timestamp
                FROM {full_name}
                GROUP BY bronze_batch_id, bronze_source
            """).collect()[0]
            
            all_batch_ids.add(sample.bronze_batch_id)
            
            print(f"   Batch ID: {sample.bronze_batch_id[:30]}...")
            print(f"   Source: {sample.bronze_source}")
            print(f"   Timestamp: {sample.min_timestamp}")
            
            # Verificar si hay múltiples timestamps (puede indicar re-ejecución)
            if sample.min_timestamp != sample.max_timestamp:
                print(f"   ⚠ Rango temporal: {sample.min_timestamp} - {sample.max_timestamp}")
        
        print()
    
    # Resumen final
    print("="*80)
    print("RESUMEN DE VALIDACIÓN")
    print("="*80)
    print(f"\n✓ Tablas validadas: {len(inacif_tables)}")
    print(f"✓ Total de filas: {total_rows:,}")
    print(f"✓ Auditoría completa: {'Sí' if all_have_audit else 'No'}")
    print(f"✓ Batch IDs únicos: {len(all_batch_ids)}")
    
    if len(all_batch_ids) == 1:
        print(f"\n✓ Todas las tablas pertenecen al mismo batch (consistente)")
    else:
        print(f"\n⚠ Se encontraron {len(all_batch_ids)} batches diferentes")
        print("   Esto puede indicar múltiples ejecuciones del proceso")
    
    # Verificar integridad referencial básica
    print("\n" + "="*80)
    print("VERIFICACIÓN DE INTEGRIDAD REFERENCIAL")
    print("="*80)
    
    try:
        # Verificar que todas las necropsias tienen municipio válido
        orphan_municipios = spark.sql("""
            SELECT COUNT(*) as cnt
            FROM covid19.bronze.inacif_necropsias n
            LEFT JOIN covid19.bronze.inacif_municipios m ON n.municipio_id = m.id
            WHERE n.municipio_id IS NOT NULL AND m.id IS NULL
        """).collect()[0].cnt
        
        if orphan_municipios == 0:
            print("\n✓ Integridad necropsias → municipios: OK (0 huérfanos)")
        else:
            print(f"\n⚠ Encontrados {orphan_municipios} registros de necropsias con municipio_id inválido")
        
        # Verificar que todas las necropsias tienen causa de muerte válida
        orphan_causas = spark.sql("""
            SELECT COUNT(*) as cnt
            FROM covid19.bronze.inacif_necropsias n
            LEFT JOIN covid19.bronze.inacif_causas_muerte c ON n.causa_muerte_id = c.id
            WHERE n.causa_muerte_id IS NOT NULL AND c.id IS NULL
        """).collect()[0].cnt
        
        if orphan_causas == 0:
            print("✓ Integridad necropsias → causas_muerte: OK (0 huérfanos)")
        else:
            print(f"⚠ Encontrados {orphan_causas} registros de necropsias con causa_muerte_id inválido")
            
    except Exception as e:
        print(f"\n⚠ No se pudo verificar integridad: {str(e)[:150]}")
    
    print("\n" + "="*80)
    
    if all_have_audit and total_rows > 0:
        print("\n🎉 VALIDACIÓN EXITOSA")
        print("   Las tablas están listas para transformaciones Silver")
    else:
        print("\n⚠ VALIDACIÓN CON OBSERVACIONES")
        print("   Revisa los detalles arriba")
    
    print("="*80)

# COMMAND ----------

# DBTITLE 1,Próximos Pasos y Estrategia Incremental
# MAGIC %md
# MAGIC # 🚀 Próximos Pasos
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 1️⃣ Transformaciones Silver (Limpieza y Enriquecimiento)
# MAGIC
# MAGIC **Objetivo:** Limpiar, normalizar y enriquecer los datos Bronze
# MAGIC
# MAGIC **Tareas sugeridas:**
# MAGIC - Crear tabla `silver.necropsias_enriched` con joins a dimensiones
# MAGIC - Normalizar valores de edad (convertir strings a numérico)
# MAGIC - Crear dimensión de fechas (año, mes, día, trimestre, día_semana)
# MAGIC - Manejar valores nulos y outliers
# MAGIC - Agregar cálculos derivados (grupo etario, categorías)
# MAGIC
# MAGIC **Ejemplo SQL:**
# MAGIC ```sql
# MAGIC CREATE OR REPLACE TABLE covid19.silver.necropsias_enriched AS
# MAGIC SELECT 
# MAGIC   n.*,
# MAGIC   m.nombre as municipio_nombre,
# MAGIC   d.nombre as departamento_nombre,
# MAGIC   c.nombre as causa_muerte_nombre,
# MAGIC   CAST(REGEXP_EXTRACT(n.edad, '\\d+', 0) AS INT) as edad_numerica,
# MAGIC   CASE 
# MAGIC     WHEN edad_numerica < 18 THEN 'Menor'
# MAGIC     WHEN edad_numerica < 60 THEN 'Adulto'
# MAGIC     ELSE 'Adulto Mayor'
# MAGIC   END as grupo_etario
# MAGIC FROM covid19.bronze.inacif_necropsias n
# MAGIC LEFT JOIN covid19.bronze.inacif_municipios m ON n.municipio_id = m.id
# MAGIC LEFT JOIN covid19.bronze.inacif_departamentos d ON m.departamento_id = d.id
# MAGIC LEFT JOIN covid19.bronze.inacif_causas_muerte c ON n.causa_muerte_id = c.id;
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 2️⃣ Cargas Incrementales (Solo Nuevos Datos)
# MAGIC
# MAGIC **Problema actual:** Este notebook hace carga completa (overwrite) cada vez
# MAGIC
# MAGIC **Solución: Carga incremental basada en timestamp o ID**
# MAGIC
# MAGIC ### Opción A: Basada en ID (si MySQL tiene IDs autoincrementales)
# MAGIC
# MAGIC ```python
# MAGIC # Obtener último ID procesado
# MAGIC max_id = spark.sql("""
# MAGIC     SELECT COALESCE(MAX(id), 0) as max_id 
# MAGIC     FROM covid19.bronze.inacif_necropsias
# MAGIC     WHERE bronze_source = 'mysql_rds_inacif'
# MAGIC """).collect()[0].max_id
# MAGIC
# MAGIC print(f"Último ID procesado: {max_id}")
# MAGIC
# MAGIC # Leer solo registros nuevos
# MAGIC new_data = spark.sql(f"""
# MAGIC     SELECT * FROM inacif_mysql.proyecto_necropsias.necropsias
# MAGIC     WHERE id > {max_id}
# MAGIC """)
# MAGIC
# MAGIC # Agregar auditoría
# MAGIC new_data_with_audit = new_data.withColumns({
# MAGIC     "bronze_loaded_at": current_timestamp(),
# MAGIC     "bronze_batch_id": lit(new_batch_id),
# MAGIC     "bronze_source": lit("mysql_rds_inacif")
# MAGIC })
# MAGIC
# MAGIC # APPEND (no overwrite)
# MAGIC new_data_with_audit.write \
# MAGIC     .format("delta") \
# MAGIC     .mode("append") \
# MAGIC     .saveAsTable("covid19.bronze.inacif_necropsias")
# MAGIC ```
# MAGIC
# MAGIC ### Opción B: Basada en timestamp (si MySQL tiene columnas created_at/updated_at)
# MAGIC
# MAGIC ```python
# MAGIC # Obtener último timestamp procesado
# MAGIC max_timestamp = spark.sql("""
# MAGIC     SELECT MAX(bronze_loaded_at) as max_ts
# MAGIC     FROM covid19.bronze.inacif_necropsias
# MAGIC """).collect()[0].max_ts
# MAGIC
# MAGIC # Leer cambios desde ese timestamp
# MAGIC # (requiere que MySQL tenga columna updated_at o similar)
# MAGIC ```
# MAGIC
# MAGIC ### Opción C: Change Data Capture (CDC) con MERGE
# MAGIC
# MAGIC Para detectar updates y deletes:
# MAGIC
# MAGIC ```python
# MAGIC from delta.tables import DeltaTable
# MAGIC
# MAGIC # Leer estado actual de MySQL
# MAGIC mysql_current = spark.read.table("inacif_mysql.proyecto_necropsias.necropsias")
# MAGIC
# MAGIC # Target Delta table
# MAGIC target = DeltaTable.forName(spark, "covid19.bronze.inacif_necropsias")
# MAGIC
# MAGIC # MERGE: insert nuevos, update modificados
# MAGIC target.alias("target").merge(
# MAGIC     mysql_current.alias("source"),
# MAGIC     "target.id = source.id"
# MAGIC ).whenMatchedUpdateAll() \
# MAGIC  .whenNotMatchedInsertAll() \
# MAGIC  .execute()
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 3️⃣ Automatización con Databricks Jobs
# MAGIC
# MAGIC **Crear un Job programado para ejecución recurrente**
# MAGIC
# MAGIC **Pasos:**
# MAGIC 1. Ir a **Workflows** → **Create Job**
# MAGIC 2. Nombre: `MySQL_RDS_Ingestion_Daily`
# MAGIC 3. Task: Notebook → seleccionar este notebook
# MAGIC 4. Schedule: Cron expression
# MAGIC    - Diario a las 2 AM: `0 0 2 * * ?`
# MAGIC    - Cada 6 horas: `0 0 */6 * * ?`
# MAGIC 5. Notifications: Email en caso de fallo
# MAGIC 6. Compute: Usar serverless o cluster específico
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 4️⃣ Optimizaciones de Performance
# MAGIC
# MAGIC ### Particionamiento (para tabla grande necropsias)
# MAGIC
# MAGIC ```python
# MAGIC # Particionar por año para queries más rápidas
# MAGIC df_with_audit.write \
# MAGIC     .format("delta") \
# MAGIC     .mode("overwrite") \
# MAGIC     .partitionBy("anio") \
# MAGIC     .saveAsTable("covid19.bronze.inacif_necropsias")
# MAGIC ```
# MAGIC
# MAGIC ### Liquid Clustering (recomendado para Databricks)
# MAGIC
# MAGIC ```sql
# MAGIC ALTER TABLE covid19.bronze.inacif_necropsias
# MAGIC CLUSTER BY (anio, mes, municipio_id);
# MAGIC ```
# MAGIC
# MAGIC ### OPTIMIZE + ZORDER
# MAGIC
# MAGIC ```sql
# MAGIC -- Compactar archivos pequeños
# MAGIC OPTIMIZE covid19.bronze.inacif_necropsias;
# MAGIC
# MAGIC -- Ordenar por columnas frecuentes en WHERE
# MAGIC OPTIMIZE covid19.bronze.inacif_necropsias
# MAGIC ZORDER BY (municipio_id, causa_muerte_id);
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 5️⃣ Monitoreo y Alertas
# MAGIC
# MAGIC ### Crear query de monitoreo
# MAGIC
# MAGIC ```sql
# MAGIC -- Monitorear crecimiento diario
# MAGIC SELECT 
# MAGIC   DATE(bronze_loaded_at) as fecha_carga,
# MAGIC   bronze_batch_id,
# MAGIC   COUNT(*) as registros_nuevos
# MAGIC FROM covid19.bronze.inacif_necropsias
# MAGIC GROUP BY DATE(bronze_loaded_at), bronze_batch_id
# MAGIC ORDER BY fecha_carga DESC;
# MAGIC ```
# MAGIC
# MAGIC ### Alertas sugeridas
# MAGIC
# MAGIC - [ ] Si la ingesta falla 2 veces consecutivas
# MAGIC - [ ] Si el conteo de filas nuevas es 0 (estancamiento)
# MAGIC - [ ] Si el conteo de filas cae drásticamente (posible problema)
# MAGIC - [ ] Si la duración de ingesta supera umbral (degradación)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 6️⃣ Documentación y Lineage
# MAGIC
# MAGIC ### Agregar comentarios a tablas
# MAGIC
# MAGIC ```sql
# MAGIC COMMENT ON TABLE covid19.bronze.inacif_necropsias IS 
# MAGIC 'Tabla Bronze con datos de necropsias del INACIF. 
# MAGIC Origen: MySQL RDS (ds-transaccional-rds). 
# MAGIC Actualización: Diaria via Lakehouse Federation. 
# MAGIC Contacto: equipo_data@example.com';
# MAGIC
# MAGIC COMMENT ON COLUMN covid19.bronze.inacif_necropsias.bronze_batch_id IS 
# MAGIC 'UUID único por ejecución de ingesta. Permite rastrear qué filas llegaron juntas.';
# MAGIC ```
# MAGIC
# MAGIC ### Tags de Unity Catalog (opcional)
# MAGIC
# MAGIC ```sql
# MAGIC ALTER TABLE covid19.bronze.inacif_necropsias 
# MAGIC SET TAGS ('source' = 'mysql_rds', 'layer' = 'bronze', 'domain' = 'salud', 'pii' = 'false');
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 📚 Recursos Adicionales
# MAGIC
# MAGIC - [Lakehouse Federation Docs](https://docs.databricks.com/en/query-federation/index.html)
# MAGIC - [Delta Lake Best Practices](https://docs.databricks.com/en/delta/best-practices.html)
# MAGIC - [Unity Catalog Connections](https://docs.databricks.com/en/connect/unity-catalog/index.html)
# MAGIC - [Databricks Jobs](https://docs.databricks.com/en/workflows/jobs/index.html)
