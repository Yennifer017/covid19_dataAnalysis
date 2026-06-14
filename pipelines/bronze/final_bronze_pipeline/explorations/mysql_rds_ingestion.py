# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
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
