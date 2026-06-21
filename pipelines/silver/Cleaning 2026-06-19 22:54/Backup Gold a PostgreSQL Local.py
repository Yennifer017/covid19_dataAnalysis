# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,📋 Instrucciones
# MAGIC %md
# MAGIC # Backup Modelo Gold a PostgreSQL Local
# MAGIC
# MAGIC ## 🎯 Objetivo
# MAGIC Exportar las 6 tablas del modelo Gold para cargarlas en PostgreSQL local (201.216.147.250)
# MAGIC
# MAGIC ## ⚠️ Restricciones del Workspace
# MAGIC * Sin clusters tradicionales (serverless)
# MAGIC * DBFS público deshabilitado
# MAGIC * Workspace filesystem no permite escritura Spark
# MAGIC
# MAGIC ## ✅ Solución Simple
# MAGIC **Usa el botón "Download" en cada resultado**
# MAGIC
# MAGIC ### Pasos:
# MAGIC 1. **Ejecuta todas las celdas** (Run All)
# MAGIC 2. **Descarga cada tabla**:
# MAGIC    * Click en el botón ⬇️ "Download" sobre cada resultado
# MAGIC    * Selecciona "CSV"
# MAGIC    * Guarda con el nombre indicado en la celda
# MAGIC
# MAGIC 3. **Importa en PostgreSQL**:
# MAGIC ```sql
# MAGIC psql -U covid19_admin -d covid19_backup
# MAGIC
# MAGIC SET search_path TO covid19_gold_backup;
# MAGIC
# MAGIC -- Limpiar tablas
# MAGIC TRUNCATE TABLE dim_tiempo, dim_geografia, dim_perfil, dim_causa_muerte, 
# MAGIC                 fact_mortalidad_unificada, fact_contexto_renap CASCADE;
# MAGIC
# MAGIC -- Importar (ajusta las rutas)
# MAGIC \COPY dim_tiempo FROM '/ruta/dim_tiempo.csv' WITH (FORMAT csv, HEADER true);
# MAGIC \COPY dim_geografia FROM '/ruta/dim_geografia.csv' WITH (FORMAT csv, HEADER true);
# MAGIC \COPY dim_perfil FROM '/ruta/dim_perfil.csv' WITH (FORMAT csv, HEADER true);
# MAGIC \COPY dim_causa_muerte FROM '/ruta/dim_causa_muerte.csv' WITH (FORMAT csv, HEADER true);
# MAGIC \COPY fact_mortalidad_unificada FROM '/ruta/fact_mortalidad_unificada.csv' WITH (FORMAT csv, HEADER true);
# MAGIC \COPY fact_contexto_renap FROM '/ruta/fact_contexto_renap.csv' WITH (FORMAT csv, HEADER true);
# MAGIC
# MAGIC -- Validar
# MAGIC SELECT 'dim_tiempo', COUNT(*) FROM dim_tiempo
# MAGIC UNION ALL SELECT 'dim_geografia', COUNT(*) FROM dim_geografia
# MAGIC UNION ALL SELECT 'dim_perfil', COUNT(*) FROM dim_perfil
# MAGIC UNION ALL SELECT 'dim_causa_muerte', COUNT(*) FROM dim_causa_muerte
# MAGIC UNION ALL SELECT 'fact_mortalidad_unificada', COUNT(*) FROM fact_mortalidad_unificada
# MAGIC UNION ALL SELECT 'fact_contexto_renap', COUNT(*) FROM fact_contexto_renap;
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Ejecuta las celdas siguientes ⬇️**

# COMMAND ----------

# DBTITLE 1,1️⃣ dim_tiempo → Descarga como: dim_tiempo.csv
# MAGIC %sql
# MAGIC SELECT * FROM covid19.gold.covid19_gold_dim_tiempo ORDER BY id_tiempo_mes

# COMMAND ----------

# DBTITLE 1,2️⃣ dim_geografia → Descarga como: dim_geografia.csv
# MAGIC %sql
# MAGIC SELECT * FROM covid19.gold.covid19_gold_dim_geografia ORDER BY id_geografia

# COMMAND ----------

# DBTITLE 1,3️⃣ dim_perfil → Descarga como: dim_perfil.csv
# MAGIC %sql
# MAGIC SELECT * FROM covid19.gold.covid19_gold_dim_perfil ORDER BY id_perfil

# COMMAND ----------

# DBTITLE 1,4️⃣ dim_causa_muerte → Descarga como: dim_causa_muerte.csv
# MAGIC %sql
# MAGIC SELECT * FROM covid19.gold.covid19_gold_dim_causa_muerte ORDER BY id_causa

# COMMAND ----------

# DBTITLE 1,5️⃣ fact_mortalidad_unificada → Descarga como: fact_mortalidad_unificada.csv
# MAGIC %sql
# MAGIC SELECT * FROM covid19.gold.covid19_gold_fact_mortalidad_unificada ORDER BY id_tiempo_mes, id_geografia

# COMMAND ----------

# DBTITLE 1,6️⃣ fact_contexto_renap → Descarga como: fact_contexto_renap.csv
# MAGIC %sql
# MAGIC SELECT * FROM covid19.gold.covid19_gold_fact_contexto_renap ORDER BY id_tiempo_mes
