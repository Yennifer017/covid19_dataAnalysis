"""
================================================================================
INGESTA MYSQL RDS → DATABRICKS BRONZE LAYER
Usando Lakehouse Federation (Unity Catalog)
================================================================================

📋 OBJETIVO
-----------
Ingestar todas las tablas del schema `proyecto_necropsias` desde MySQL RDS a la 
capa Bronze de Databricks (`covid19.bronze`) usando **Lakehouse Federation**, 
agregando columnas de auditoría para rastreo y linaje.


🏗️ ARQUITECTURA
----------------

ORIGEN:
  • Base de datos: MySQL RDS 8.0
  • Host: ds-transaccional-rds.cx0w640wuzud.us-east-2.rds.amazonaws.com:3306
  • Schema: proyecto_necropsias
  • Tablas: 4 (causas_muerte, departamentos, municipios, necropsias)

DESTINO:
  • Catálogo: covid19
  • Schema: bronze
  • Formato: Delta Lake
  • Prefijo: inacif_

MÉTODO:
  • Unity Catalog Connection (no JDBC tradicional)
  • Foreign Catalog para acceso federado
  • Columnas de auditoría: bronze_loaded_at, bronze_batch_id, bronze_source


🔄 FLUJO DEL PROCESO
--------------------

1. SETUP INFRAESTRUCTURA (Una sola vez)
   - Crear Unity Catalog Connection a MySQL
   - Crear Foreign Catalog sobre el schema origen
   - Verificar acceso a tablas

2. INGESTA DE DATOS (Ejecutable múltiples veces)
   - Descubrir tablas dinámicamente
   - Leer desde Federation
   - Agregar columnas de auditoría
   - Escribir a Delta (modo overwrite)

3. VALIDACIÓN (Opcional)
   - Verificar tablas creadas
   - Confirmar columnas de auditoría
   - Revisar conteos de filas


⚠️ PRERREQUISITOS
------------------
  ☐ Permisos: CREATE CONNECTION, CREATE CATALOG en Unity Catalog
  ☐ Permisos: USE CATALOG, CREATE TABLE en covid19.bronze
  ☐ Credenciales MySQL: usuario, password, host
  ☐ Red: Conectividad desde Databricks a MySQL RDS


🔐 CONFIGURAR DATABRICKS SECRETS
---------------------------------

IMPORTANTE: No expongas credenciales en el código.
Este notebook usa Databricks Secrets para manejar credenciales de forma segura.

PASO 1: Crear Secret Scope (Una sola vez)

Opción A: Databricks CLI (Recomendado)
  
  # Instalar Databricks CLI si no lo tienes
  pip install databricks-cli
  
  # Configurar autenticación
  databricks configure --token
  
  # Crear secret scope
  databricks secrets create-scope --scope mysql_credentials

Opción B: UI de Databricks
  
  1. Ve a: https://<tu-workspace>.cloud.databricks.com/#secrets/createScope
  2. Scope Name: mysql_credentials
  3. Manage Principal: Creator (solo tú puedes leer)
  4. Click Create


PASO 2: Agregar Secrets

  # Agregar cada credencial al scope
  databricks secrets put --scope mysql_credentials --key mysql_host
  databricks secrets put --scope mysql_credentials --key mysql_port
  databricks secrets put --scope mysql_credentials --key mysql_user
  databricks secrets put --scope mysql_credentials --key mysql_password

Valores a usar:
  • mysql_host: Tu host RDS
  • mysql_port: 3306
  • mysql_user: Tu usuario MySQL
  • mysql_password: Tu password MySQL


PASO 3: Verificar Secrets (Opcional)

  # Listar scopes
  databricks secrets list-scopes
  
  # Listar secrets en un scope (no muestra valores)
  databricks secrets list --scope mysql_credentials

Deberías ver:
  mysql_host
  mysql_port
  mysql_user
  mysql_password


🔍 CÓMO FUNCIONAN LOS SECRETS
  • Los valores están encriptados en reposo y en tránsito
  • Solo usuarios autorizados pueden leer el scope
  • No se muestran en logs ni en la UI (aparecen como [REDACTED])
  • Son referencias, no valores hardcodeados


📝 NOTAS IMPORTANTES
--------------------

SEGURIDAD:
  • Las credenciales se almacenan encriptadas en Unity Catalog
  • Se usa trustServerCertificate=true para evitar límite de 10KB en propiedades

IDEMPOTENCIA:
  • La ingesta usa mode("overwrite") - se puede re-ejecutar de forma segura
  • Cada ejecución genera un nuevo batch_id único

CARGAS FUTURAS:
  • Este proceso es para carga inicial completa (full load)
  • Para cargas incrementales, modificar el código para filtrar por timestamp o ID


🚀 PRÓXIMOS PASOS
-----------------

1️⃣ TRANSFORMACIONES SILVER (Limpieza y Enriquecimiento)

Objetivo: Limpiar, normalizar y enriquecer los datos Bronze

Tareas sugeridas:
  • Crear tabla silver.necropsias_enriched con joins a dimensiones
  • Normalizar valores de edad (convertir strings a numérico)
  • Crear dimensión de fechas (año, mes, día, trimestre, día_semana)
  • Manejar valores nulos y outliers
  • Agregar cálculos derivados (grupo etario, categorías)

Ejemplo SQL:

  CREATE OR REPLACE TABLE covid19.silver.necropsias_enriched AS
  SELECT 
    n.*,
    m.nombre as municipio_nombre,
    d.nombre as departamento_nombre,
    c.nombre as causa_muerte_nombre,
    CAST(REGEXP_EXTRACT(n.edad, '\\d+', 0) AS INT) as edad_numerica,
    CASE 
      WHEN edad_numerica < 18 THEN 'Menor'
      WHEN edad_numerica < 60 THEN 'Adulto'
      ELSE 'Adulto Mayor'
    END as grupo_etario
  FROM covid19.bronze.inacif_necropsias n
  LEFT JOIN covid19.bronze.inacif_municipios m ON n.municipio_id = m.id
  LEFT JOIN covid19.bronze.inacif_departamentos d ON m.departamento_id = d.id
  LEFT JOIN covid19.bronze.inacif_causas_muerte c ON n.causa_muerte_id = c.id;


2️⃣ CARGAS INCREMENTALES (Solo Nuevos Datos)

Problema actual: Este notebook hace carga completa (overwrite) cada vez

Solución: Carga incremental basada en timestamp o ID

OPCIÓN A: Basada en ID (si MySQL tiene IDs autoincrementales)

  # Obtener último ID procesado
  max_id = spark.sql(\"\"\"
      SELECT COALESCE(MAX(id), 0) as max_id 
      FROM covid19.bronze.inacif_necropsias
      WHERE bronze_source = 'mysql_rds_inacif'
  \"\"\").collect()[0].max_id
  
  print(f"Último ID procesado: {max_id}")
  
  # Leer solo registros nuevos
  new_data = spark.sql(f\"\"\"
      SELECT * FROM inacif_mysql.proyecto_necropsias.necropsias
      WHERE id > {max_id}
  \"\"\")
  
  # Agregar auditoría y APPEND (no overwrite)
  new_data_with_audit = new_data.withColumns({
      "bronze_loaded_at": current_timestamp(),
      "bronze_batch_id": lit(new_batch_id),
      "bronze_source": lit("mysql_rds_inacif")
  })
  
  new_data_with_audit.write \\
      .format("delta") \\
      .mode("append") \\
      .saveAsTable("covid19.bronze.inacif_necropsias")

OPCIÓN B: Basada en timestamp (si MySQL tiene columnas created_at/updated_at)

  # Obtener último timestamp procesado
  max_timestamp = spark.sql(\"\"\"
      SELECT MAX(bronze_loaded_at) as max_ts
      FROM covid19.bronze.inacif_necropsias
  \"\"\").collect()[0].max_ts
  
  # Leer cambios desde ese timestamp

OPCIÓN C: Change Data Capture (CDC) con MERGE

  from delta.tables import DeltaTable
  
  # Leer estado actual de MySQL
  mysql_current = spark.read.table("inacif_mysql.proyecto_necropsias.necropsias")
  
  # Target Delta table
  target = DeltaTable.forName(spark, "covid19.bronze.inacif_necropsias")
  
  # MERGE: insert nuevos, update modificados
  target.alias("target").merge(
      mysql_current.alias("source"),
      "target.id = source.id"
  ).whenMatchedUpdateAll() \\
   .whenNotMatchedInsertAll() \\
   .execute()


3️⃣ AUTOMATIZACIÓN CON DATABRICKS JOBS

Crear un Job programado para ejecución recurrente

Pasos:
  1. Ir a Workflows → Create Job
  2. Nombre: MySQL_RDS_Ingestion_Daily
  3. Task: Notebook → seleccionar el notebook de ingesta
  4. Schedule: Cron expression
     - Diario a las 2 AM: 0 0 2 * * ?
     - Cada 6 horas: 0 0 */6 * * ?
  5. Notifications: Email en caso de fallo
  6. Compute: Usar serverless o cluster específico


4️⃣ OPTIMIZACIONES DE PERFORMANCE

Particionamiento (para tabla grande necropsias):

  df_with_audit.write \\
      .format("delta") \\
      .mode("overwrite") \\
      .partitionBy("anio") \\
      .saveAsTable("covid19.bronze.inacif_necropsias")

Liquid Clustering (recomendado para Databricks):

  ALTER TABLE covid19.bronze.inacif_necropsias
  CLUSTER BY (anio, mes, municipio_id);

OPTIMIZE + ZORDER:

  -- Compactar archivos pequeños
  OPTIMIZE covid19.bronze.inacif_necropsias;
  
  -- Ordenar por columnas frecuentes en WHERE
  OPTIMIZE covid19.bronze.inacif_necropsias
  ZORDER BY (municipio_id, causa_muerte_id);


5️⃣ MONITOREO Y ALERTAS

Query de monitoreo:

  SELECT 
    DATE(bronze_loaded_at) as fecha_carga,
    bronze_batch_id,
    COUNT(*) as registros_nuevos
  FROM covid19.bronze.inacif_necropsias
  GROUP BY DATE(bronze_loaded_at), bronze_batch_id
  ORDER BY fecha_carga DESC;

Alertas sugeridas:
  ☐ Si la ingesta falla 2 veces consecutivas
  ☐ Si el conteo de filas nuevas es 0 (estancamiento)
  ☐ Si el conteo de filas cae drásticamente (posible problema)
  ☐ Si la duración de ingesta supera umbral (degradación)


6️⃣ DOCUMENTACIÓN Y LINEAGE

Agregar comentarios a tablas:

  COMMENT ON TABLE covid19.bronze.inacif_necropsias IS 
  'Tabla Bronze con datos de necropsias del INACIF. 
  Origen: MySQL RDS (ds-transaccional-rds). 
  Actualización: Diaria via Lakehouse Federation. 
  Contacto: equipo_data@example.com';
  
  COMMENT ON COLUMN covid19.bronze.inacif_necropsias.bronze_batch_id IS 
  'UUID único por ejecución de ingesta. Permite rastrear qué filas llegaron juntas.';

Tags de Unity Catalog (opcional):

  ALTER TABLE covid19.bronze.inacif_necropsias 
  SET TAGS ('source' = 'mysql_rds', 'layer' = 'bronze', 'domain' = 'salud', 'pii' = 'false');


🛡️ SEGURIDAD Y MEJORES PRÁCTICAS PARA REPOS PÚBLICOS
------------------------------------------------------

✅ QUÉ ES SEGURO COMPARTIR:
  • Este notebook - Usa secrets, no tiene credenciales hardcodeadas
  • Estructura del código - Lógica de ingesta, transformaciones
  • Nombres de tablas y schemas - No son sensibles si son internos
  • Queries SQL - Sin WHERE clauses con datos reales de negocio
  • Arquitectura y diagramas - Conceptuales, sin IPs o endpoints

❌ QUÉ NUNCA COMPARTIR:
  • Credenciales - Usuarios, passwords, tokens, API keys
  • IPs y Hostnames privados - Direcciones de bases de datos internas
  • Certificados SSL - Archivos .pem, .crt, .key
  • Datos reales - Resultados de queries con PII o datos de negocio
  • Secrets scope names personales - Si contienen info sensible del org
  • AWS Access Keys - Nunca, jamás, bajo ningún concepto


📝 .GITIGNORE RECOMENDADO
--------------------------

Si vas a subir este proyecto a un repo público, crea un archivo .gitignore:

  # Credenciales y configuración sensible
  *.env
  *.credentials
  .databricks/
  dbconnect/
  
  # Certificados SSL
  *.pem
  *.crt
  *.key
  *.p12
  *.pfx
  
  # Archivos de configuración con credenciales
  config.json
  secrets.json
  dbfs-secrets/
  
  # Outputs de notebooks con datos reales
  *.ipynb_checkpoints/
  output/
  data/
  *.csv
  *.parquet
  
  # Logs que puedan contener datos sensibles
  *.log
  logs/
  
  # Notebooks temporales o de testing con credenciales
  *_test.ipynb
  *_local.ipynb
  *_private.py
  
  # Python
  __pycache__/
  *.pyc
  *.pyo
  .venv/
  .pytest_cache/


🔍 PRE-COMMIT CHECKLIST
------------------------

Antes de hacer git push a un repo público:

  ☐ Buscar credenciales hardcodeadas: grep -r "password" .
  ☐ Buscar IPs privadas: grep -r "10\.\|192\.168\." .
  ☐ Buscar tokens: grep -ri "token\|api[_-]key" .
  ☐ Verificar que todos los notebooks usan secret() o placeholders
  ☐ Remover celdas con outputs de datos reales
  ☐ Verificar que .gitignore está configurado
  ☐ Hacer un git diff final para revisar cambios


🔧 HERRAMIENTAS DE SEGURIDAD
-----------------------------

1. git-secrets (Prevención de commits con credenciales)

  # Instalar
  brew install git-secrets  # macOS
  sudo apt-get install git-secrets  # Linux
  
  # Configurar en tu repo
  git secrets --install
  git secrets --register-aws
  
  # Agregar patrones personalizados
  git secrets --add 'password.*=.*'
  git secrets --add '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'

2. detect-secrets (Escaneo de secretos existentes)

  # Instalar
  pip install detect-secrets
  
  # Escanear repo
  detect-secrets scan > .secrets.baseline
  
  # Auditar findings
  detect-secrets audit .secrets.baseline

3. truffleHog (Buscar secretos en historial de Git)

  # Instalar
  pip install truffleHog
  
  # Escanear todo el historial
  trufflehog --regex --entropy=True .


⚠️ SI YA COMMITEASTE CREDENCIALES
----------------------------------

NO las borres simplemente - quedan en el historial de Git.

Solución: Reescribir historial con BFG

  # Instalar BFG Repo-Cleaner
  brew install bfg  # macOS
  
  # Clonar repo en espejo
  git clone --mirror https://github.com/tu-usuario/tu-repo.git
  
  # Remover credenciales del historial
  bfg --replace-text passwords.txt tu-repo.git
  
  # Forzar push (PELIGROSO - coordinar con equipo)
  cd tu-repo.git
  git reflog expire --expire=now --all
  git gc --prune=now --aggressive
  git push --force

Adicional:
  • Rotar credenciales inmediatamente - Las anteriores ya están comprometidas
  • Revisar logs de acceso - Verificar si hubo accesos no autorizados
  • Notificar al equipo de seguridad


📚 RECURSOS ADICIONALES
-----------------------

  • Lakehouse Federation: https://docs.databricks.com/en/query-federation/index.html
  • Delta Lake Best Practices: https://docs.databricks.com/en/delta/best-practices.html
  • Unity Catalog Connections: https://docs.databricks.com/en/connect/unity-catalog/index.html
  • Databricks Jobs: https://docs.databricks.com/en/workflows/jobs/index.html
  • Databricks Secrets: https://docs.databricks.com/en/security/secrets/index.html
  • GitHub Security: https://docs.github.com/en/code-security/getting-started/best-practices
  • OWASP Secrets Management: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html


================================================================================
EJEMPLO DE README.md PARA DOCUMENTACIÓN PÚBLICA
================================================================================

# MySQL RDS → Databricks Ingestion Pipeline

## Descripción
Pipeline de ingesta automatizada desde MySQL RDS a Databricks usando 
Lakehouse Federation y Unity Catalog.

## Configuración

### 1. Requisitos
- Databricks Workspace con Unity Catalog habilitado
- Permisos: CREATE CONNECTION, CREATE CATALOG
- MySQL 8.0+ con conectividad desde Databricks

### 2. Configurar Credenciales

**IMPORTANTE:** Este proyecto usa Databricks Secrets. No incluyas 
credenciales en el código.

```bash
# Crear secret scope
databricks secrets create-scope --scope mysql_credentials

# Agregar credenciales
databricks secrets put --scope mysql_credentials --key mysql_host
databricks secrets put --scope mysql_credentials --key mysql_port
databricks secrets put --scope mysql_credentials --key mysql_user
databricks secrets put --scope mysql_credentials --key mysql_password
```

### 3. Ejecutar Pipeline

1. Abrir notebook de ingesta
2. Ejecutar celdas en orden
3. Verificar tablas en covid19.bronze

## Arquitectura

[Diagrama sin IPs ni detalles de infraestructura]

## Contribuir

Por favor no incluyas credenciales ni datos reales en PRs.

================================================================================
"""

# Este archivo contiene la documentación completa del proceso de ingesta.
# El código ejecutable está en el notebook:
# "MySQL RDS Ingestion - Lakehouse Federation"
