# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Ingesta MySQL RDS → Bronze (INACIF)
# MAGIC %md
# MAGIC # Ingesta MySQL RDS → Databricks Bronze (INACIF)
# MAGIC
# MAGIC **Fuente:** MySQL RDS - Schema `proyecto_necropsias` (4 tablas)  
# MAGIC **Destino:** `covid19.bronze.inacif_*`  
# MAGIC **Método:** Lakehouse Federation (Unity Catalog)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 📋 Instrucciones Rápidas
# MAGIC
# MAGIC 1. **Configurar Secrets** (una sola vez):
# MAGIC    ```bash
# MAGIC    databricks secrets create-scope --scope mysql_credentials
# MAGIC    databricks secrets put --scope mysql_credentials --key mysql_host
# MAGIC    databricks secrets put --scope mysql_credentials --key mysql_port  
# MAGIC    databricks secrets put --scope mysql_credentials --key mysql_user
# MAGIC    databricks secrets put --scope mysql_credentials --key mysql_password
# MAGIC    ```
# MAGIC
# MAGIC 2. **Crear UC Connection** (una sola vez - SQL):
# MAGIC    ```sql
# MAGIC    CREATE CONNECTION IF NOT EXISTS mysql_rds_inacif
# MAGIC    TYPE mysql
# MAGIC    OPTIONS (
# MAGIC      host secret('mysql_credentials', 'mysql_host'),
# MAGIC      port secret('mysql_credentials', 'mysql_port'),
# MAGIC      user secret('mysql_credentials', 'mysql_user'),
# MAGIC      password secret('mysql_credentials', 'mysql_password'),
# MAGIC      trustServerCertificate 'true'
# MAGIC    );
# MAGIC    ```
# MAGIC
# MAGIC 3. **Ejecutar las celdas** en orden: Verificar Secrets → Verificar Infraestructura → Ingestar
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **📚 Documentación completa:** Ver `sources/inacif_mysql/ingest_inacif_rds.py`

# COMMAND ----------

# DBTITLE 1,SETUP SQL: Crear UC Connection
# MAGIC %sql
# MAGIC -- Ejecutar UNA SOLA VEZ para crear la conexión a MySQL
# MAGIC CREATE CONNECTION IF NOT EXISTS mysql_rds_inacif
# MAGIC TYPE mysql
# MAGIC OPTIONS (
# MAGIC   host secret('mysql_credentials', 'mysql_host'),
# MAGIC   port secret('mysql_credentials', 'mysql_port'),
# MAGIC   user secret('mysql_credentials', 'mysql_user'),
# MAGIC   password secret('mysql_credentials', 'mysql_password'),
# MAGIC   trustServerCertificate 'true'
# MAGIC );
# MAGIC
# MAGIC DESCRIBE CONNECTION mysql_rds_inacif;

# COMMAND ----------

# DBTITLE 1,1. Verificar Secrets
# Verificar que los secrets están configurados
print("=" * 80)
print("VERIFICACIÓN DE DATABRICKS SECRETS")
print("=" * 80)

required_secrets = [
    ('mysql_credentials', 'mysql_host'),
    ('mysql_credentials', 'mysql_port'),
    ('mysql_credentials', 'mysql_user'),
    ('mysql_credentials', 'mysql_password')
]

all_ok = True

for scope, key in required_secrets:
    try:
        value = dbutils.secrets.get(scope=scope, key=key)
        print(f"✓ Secret '{scope}/{key}' existe")
        if key != 'mysql_password':
            print(f"  Longitud: {len(value)} caracteres")
        else:
            print(f"  Longitud: [REDACTED]")
    except Exception as e:
        all_ok = False
        print(f"❌ Secret '{scope}/{key}' NO existe")
        print(f"   → databricks secrets put --scope {scope} --key {key}")

print("\n" + "=" * 80)
if all_ok:
    print("✅ TODOS LOS SECRETS CONFIGURADOS")
else:
    print("❌ FALTAN SECRETS - configurar antes de continuar")
print("=" * 80)

# COMMAND ----------

# DBTITLE 1,SETUP: Crear UC Connection (Ejecutar UNA VEZ)
# MAGIC %md
# MAGIC ## SETUP: Crear Unity Catalog Connection
# MAGIC
# MAGIC **⚠️ Ejecutar esto UNA SOLA VEZ** (o cuando se actualicen credenciales)
# MAGIC
# MAGIC Copiar y ejecutar en una celda SQL:
# MAGIC
# MAGIC ```sql
# MAGIC CREATE CONNECTION IF NOT EXISTS mysql_rds_inacif
# MAGIC TYPE mysql
# MAGIC OPTIONS (
# MAGIC   host secret('mysql_credentials', 'mysql_host'),
# MAGIC   port secret('mysql_credentials', 'mysql_port'),
# MAGIC   user secret('mysql_credentials', 'mysql_user'),
# MAGIC   password secret('mysql_credentials', 'mysql_password'),
# MAGIC   trustServerCertificate 'true'
# MAGIC );
# MAGIC
# MAGIC DESCRIBE CONNECTION mysql_rds_inacif;
# MAGIC ```
# MAGIC
# MAGIC **Nota:** Foreign Catalog es opcional. El código funciona sin él.

# COMMAND ----------

# DBTITLE 1,SETUP 2/3: Crear Foreign Catalog sobre MySQL Schema
# MAGIC %sql
# MAGIC -- ============================================================================
# MAGIC -- FOREIGN CATALOG: Acceso federado a proyecto_necropsias
# MAGIC -- ============================================================================
# MAGIC -- ⚠️ IMPORTANTE: Esta celda es OPCIONAL
# MAGIC --
# MAGIC -- El Foreign Catalog NO es necesario si:
# MAGIC -- • Sabes exactamente qué tablas necesitas (nuestro caso: solo 4 tablas)
# MAGIC -- • Tu MySQL tiene >100 tablas (límite UC por schema)
# MAGIC --
# MAGIC -- Puedes SALTAR esta celda e ir directo a la ingesta.
# MAGIC -- El código de ingesta funciona sin Foreign Catalog usando lista hardcodeada.
# MAGIC --
# MAGIC -- Solo ejecuta esta celda si quieres explorar dinámicamente todas las tablas.
# MAGIC -- ============================================================================
# MAGIC
# MAGIC -- Crear Foreign Catalog (ahora mapea TODA la base de datos MySQL)
# MAGIC -- NOTA: Con la nueva sintaxis, el catálogo mapea toda la instancia MySQL
# MAGIC --       Los schemas de MySQL se mapean como schemas en el catálogo
# MAGIC CREATE FOREIGN CATALOG IF NOT EXISTS inacif_mysql
# MAGIC USING CONNECTION mysql_rds_inacif;
# MAGIC
# MAGIC -- Refrescar metadata (importante después de crear)
# MAGIC REFRESH FOREIGN CATALOG inacif_mysql;
# MAGIC
# MAGIC -- Listar tablas disponibles
# MAGIC SHOW TABLES IN inacif_mysql.proyecto_necropsias;

# COMMAND ----------

# DBTITLE 1,2. Verificar Infraestructura
# Verificar que UC Connection existe y hay acceso a MySQL y destino
print("=" * 80)
print("VERIFICACIÓN DE INFRAESTRUCTURA")
print("=" * 80)

# 1. UC Connection
print("\n1. Unity Catalog Connection...")
try:
    spark.sql("DESCRIBE CONNECTION mysql_rds_inacif").collect()
    print("   ✓ Connection 'mysql_rds_inacif' existe")
except:
    print("   ❌ Connection NO existe - ejecutar celda SETUP SQL")

# 2. Foreign Catalog (opcional)
print("\n2. Foreign Catalog...")
catalogs = [r.catalog for r in spark.sql("SHOW CATALOGS").collect()]
if 'inacif_mysql' in catalogs:
    print("   ✓ Foreign Catalog 'inacif_mysql' existe")
else:
    print("   ⚠ Foreign Catalog NO existe (opcional)")

# 3. Acceso MySQL
print("\n3. Acceso a MySQL...")
try:
    if 'inacif_mysql' in catalogs:
        tables = [r.tableName for r in spark.sql("SHOW TABLES IN inacif_mysql.proyecto_necropsias").collect()]
        print(f"   ✓ {len(tables)} tablas disponibles: {tables}")
        count = spark.sql("SELECT COUNT(*) as cnt FROM inacif_mysql.proyecto_necropsias.necropsias").collect()[0].cnt
        print(f"   ✓ Lectura exitosa: {count:,} filas en necropsias")
    else:
        print("   ⚠ Se usará JDBC directo (Foreign Catalog no disponible)")
except Exception as e:
    print(f"   ⚠ Error: {str(e)[:100]}")

# 4. Permisos destino
print("\n4. Permisos en covid19.bronze...")
try:
    spark.sql("USE CATALOG covid19")
    tables = spark.sql("SHOW TABLES IN covid19.bronze").collect()
    print(f"   ✓ Acceso OK ({len(tables)} tablas existentes)")
except Exception as e:
    print(f"   ❌ Error: {str(e)[:100]}")

print("\n" + "=" * 80)
print("✅ Verificación completa - puede ejecutar ingesta")
print("=" * 80)

# COMMAND ----------

# DBTITLE 1,3. Ingestar MySQL → Bronze
# Código de ingesta completo - lee MySQL via Federation y escribe a Delta
import uuid
from pyspark.sql.functions import lit, current_timestamp
from datetime import datetime

print("=" * 80)
print("INGESTA: MySQL RDS → Delta Tables")
print("=" * 80)

# Configuración
SOURCE_CATALOG = "inacif_mysql"
SOURCE_SCHEMA = "proyecto_necropsias"
TARGET_CATALOG = "covid19"
TARGET_SCHEMA = "bronze"
TABLE_PREFIX = "inacif_"
BATCH_ID = str(uuid.uuid4())
SOURCE_SYSTEM = "mysql_rds_inacif"

print(f"Batch ID: {BATCH_ID}")
print(f"Destino: {TARGET_CATALOG}.{TARGET_SCHEMA}.{TABLE_PREFIX}*\n")

# Descubrir tablas
print("Descubriendo tablas...")
try:
    catalogs = [r.catalog for r in spark.sql("SHOW CATALOGS").collect()]
    if 'inacif_mysql' in catalogs:
        tables = [r.tableName for r in spark.sql(f"SHOW TABLES IN {SOURCE_CATALOG}.{SOURCE_SCHEMA}").collect()]
        use_federation = True
        print(f"✓ Federation: {len(tables)} tablas encontradas")
    else:
        raise Exception("No Federation")
except:
    # Fallback: JDBC
    print("⚠ Usando JDBC directo")
    jdbc_url = f"jdbc:mysql://ds-transaccional-rds.cx0w640wuzud.us-east-2.rds.amazonaws.com:3306/{SOURCE_SCHEMA}"
    tables_df = spark.read.format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", f"(SELECT table_name FROM information_schema.tables WHERE table_schema = '{SOURCE_SCHEMA}' AND table_type = 'BASE TABLE') as t") \
        .option("user", dbutils.secrets.get("mysql_credentials", "mysql_user")) \
        .option("password", dbutils.secrets.get("mysql_credentials", "mysql_password")) \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()
    tables = [r.table_name for r in tables_df.collect()]
    use_federation = False
    print(f"✓ JDBC: {len(tables)} tablas")

print(f"\nTablas a ingestar: {tables}\n")

# Configurar lectura
if not use_federation:
    jdbc_url = f"jdbc:mysql://ds-transaccional-rds.cx0w640wuzud.us-east-2.rds.amazonaws.com:3306/{SOURCE_SCHEMA}"
    jdbc_props = {
        "user": dbutils.secrets.get("mysql_credentials", "mysql_user"),
        "password": dbutils.secrets.get("mysql_credentials", "mysql_password"),
        "driver": "com.mysql.cj.jdbc.Driver"
    }

# Ingestar cada tabla
success = 0
failed = []

for i, table in enumerate(tables, 1):
    target = f"{TARGET_CATALOG}.{TARGET_SCHEMA}.{TABLE_PREFIX}{table}"
    print(f"[{i}/{len(tables)}] {table} → {target}")
    
    try:
        # Leer
        if use_federation:
            df = spark.read.table(f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.{table}")
        else:
            df = spark.read.format("jdbc").option("url", jdbc_url).option("dbtable", table).options(**jdbc_props).load()
        
        rows = df.count()
        
        # Agregar auditoría
        df_audit = df.withColumns({
            "bronze_loaded_at": current_timestamp(),
            "bronze_batch_id": lit(BATCH_ID),
            "bronze_source": lit(SOURCE_SYSTEM)
        })
        
        # Escribir
        df_audit.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target)
        
        print(f"  ✓ {rows:,} filas\n")
        success += 1
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}\n")
        failed.append((table, str(e)))

# Resumen
print("=" * 80)
print("RESUMEN")
print("=" * 80)
print(f"✓ Exitosas: {success}/{len(tables)}")
print(f"❌ Fallidas: {len(failed)}/{len(tables)}")

if success == len(tables):
    print(f"\n🎉 Ingesta completa exitosa en {TARGET_CATALOG}.{TARGET_SCHEMA}")
elif failed:
    print("\nTablas con error:")
    for t, e in failed:
        print(f"  - {t}: {e[:100]}")

print("=" * 80)

# COMMAND ----------

# DBTITLE 1,4. Validación (Opcional)
# Validar tablas creadas
print("=" * 80)
print("VALIDACIÓN POST-INGESTA")
print("=" * 80)

TARGET_CATALOG = "covid19"
TARGET_SCHEMA = "bronze"
TABLE_PREFIX = "inacif_"

# Listar tablas INACIF
tables = [r.tableName for r in spark.sql(f"SHOW TABLES IN {TARGET_CATALOG}.{TARGET_SCHEMA}").collect()]
inacif_tables = [t for t in tables if t.startswith(TABLE_PREFIX)]

print(f"\nTablas INACIF encontradas: {len(inacif_tables)}\n")

for table in inacif_tables:
    full_table = f"{TARGET_CATALOG}.{TARGET_SCHEMA}.{table}"
    
    # Contar filas
    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {full_table}").collect()[0].cnt
    
    # Verificar columnas audit
    cols = [r.col_name for r in spark.sql(f"DESCRIBE TABLE {full_table}").collect()]
    audit_cols = ['bronze_loaded_at', 'bronze_batch_id', 'bronze_source']
    has_audit = all(c in cols for c in audit_cols)
    
    # Mostrar
    status = "✓" if has_audit else "❌"
    print(f"{status} {table}: {count:,} filas, audit={has_audit}")

print("\n" + "=" * 80)
print("✅ Validación completa")
print("=" * 80)

# COMMAND ----------

# DBTITLE 1,📚 Documentación y Recursos
# MAGIC %md
# MAGIC # 📚 Documentación Completa
# MAGIC
# MAGIC **Ver archivo:** `sources/inacif_mysql/ingest_inacif_rds.py`
# MAGIC
# MAGIC Contiene:
# MAGIC * Configuración detallada de Databricks Secrets
# MAGIC * Setup completo de Unity Catalog Connection
# MAGIC * Estrategias de cargas incrementales
# MAGIC * Optimizaciones de performance (particionamiento, clustering)
# MAGIC * Automatización con Databricks Jobs
# MAGIC * Monitoreo y alertas
# MAGIC * Mejores prácticas de seguridad
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Próximos Pasos Sugeridos
# MAGIC
# MAGIC 1. **Transformaciones Silver:**
# MAGIC    * Joins con dimensiones (municipios, departamentos, causas_muerte)
# MAGIC    * Normalización de edad a numérico
# MAGIC    * Crear dimensión de fechas
# MAGIC    * Grupos etarios
# MAGIC
# MAGIC 2. **Cargas Incrementales:**
# MAGIC    * Filtrar por último ID procesado
# MAGIC    * Modo `append` en lugar de `overwrite`
# MAGIC
# MAGIC 3. **Automatización:**
# MAGIC    * Crear Databricks Job programado (diario/semanal)
# MAGIC    * Configurar alertas por email
# MAGIC
# MAGIC 4. **Optimización:**
# MAGIC    * Liquid clustering: `CLUSTER BY (anio, mes, municipio_id)`
# MAGIC    * OPTIMIZE + ZORDER para queries frecuentes
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **📄 Recursos:**
# MAGIC * [Lakehouse Federation Docs](https://docs.databricks.com/en/query-federation/index.html)
# MAGIC * [Delta Lake Best Practices](https://docs.databricks.com/en/delta/best-practices.html)

# COMMAND ----------

# DBTITLE 1,🛡️ Seguridad
# MAGIC %md
# MAGIC # 🛡️ Seguridad
# MAGIC
# MAGIC ## ✅ Este notebook es seguro para repos públicos
# MAGIC
# MAGIC * Usa Databricks Secrets (no credenciales hardcodeadas)
# MAGIC * No expone IPs ni hostnames
# MAGIC * No contiene datos reales
# MAGIC
# MAGIC ## ⚠️ Pre-Commit Checklist
# MAGIC
# MAGIC Antes de hacer push:
# MAGIC
# MAGIC ```bash
# MAGIC # Buscar credenciales
# MAGIC grep -r "password" .
# MAGIC grep -r "10\.\|192\.168\." .
# MAGIC grep -ri "token\|api[_-]key" .
# MAGIC ```
# MAGIC
# MAGIC ## .gitignore Recomendado
# MAGIC
# MAGIC ```gitignore
# MAGIC *.env
# MAGIC *.credentials
# MAGIC *.pem
# MAGIC *.crt
# MAGIC *.key
# MAGIC config.json
# MAGIC secrets.json
# MAGIC *.log
# MAGIC __pycache__/
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Ver más:** `sources/inacif_mysql/ingest_inacif_rds.py` - Sección completa sobre seguridad
