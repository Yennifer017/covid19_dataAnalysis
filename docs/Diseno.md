# 📐 Resumen del Diseño - Pipeline COVID-19 Bronze Layer

## 🎯 Visión General

Pipeline de ingesta multi-fuente que consolida datos de mortalidad por COVID-19 de 4 fuentes diferentes en la capa Bronze de Databricks, usando arquitectura medallion (Bronze → Silver → Gold).

---

## 🏗️ Arquitectura de Datos

### **Capa Bronze (Actual)**
```
covid19.bronze/
│
├── 📊 INE Guatemala (S3)
│   └── ine_deaths (674K filas)
│       • Fuente: Archivos Excel en S3
│       • Particionado por: source_file
│       • Tipo: Materialized View
│
├── 🌍 WHO Global (SharePoint)
│   └── who_covid_19_global_daily_data (558K filas)
│       • Fuente: SharePoint Online
│       • Tipo: Materialized View
│
├── 🏥 WHO Guatemala (Google Drive)
│   └── who_mortality (1.6K filas)
│       • Fuente: CSV en Google Drive
│       • Tipo: Materialized View
│
├── 🇨🇷 OMS Costa Rica (SharePoint)
│   ├── mortalidad_categorias_2020/2021/2022
│   ├── mortalidad_indicadores
│   └── mortalidad_por_edades
│       • Fuente: SharePoint Online
│       • Tipo: Materialized View (5 tablas)
│
└── 🔬 INACIF MySQL (Lakehouse Federation)
    ├── inacif_necropsias (75K filas) ⭐ Principal
    ├── inacif_causas_muerte (41 filas)
    ├── inacif_departamentos (23 filas)
    └── inacif_municipios (347 filas)
        • Fuente: MySQL RDS 8.0
        • Método: Unity Catalog Foreign Catalog
        • Auditoría: bronze_loaded_at, bronze_batch_id, bronze_source
```

**Total:** 12 tablas, ~1.3M filas

---

## 🔄 Flujo de Ingesta

### **Método 1: Pipeline SDP (8 tablas)**
```python
@dp.table()  # o @dp.materialized_view()
def dataset():
    return spark.read.format("cloudFiles") \
        .option(...) \
        .load(source_path)
```

* **INE, WHO, OMS:** Auto-actualizadas por el pipeline
* **Ejecución:** Serverless, sin errores
* **Refresh:** Full (overwrite) cada ejecución

### **Método 2: Notebook + Lakehouse Federation (4 tablas INACIF)**
```python
# Via Foreign Catalog
spark.read.table("inacif_mysql.proyecto_necropsias.table")
    .withColumn("bronze_loaded_at", current_timestamp())
    .withColumn("bronze_batch_id", lit(batch_id))
    .write.mode("overwrite").saveAsTable("covid19.bronze.inacif_*")
```

* **Ventaja:** No requiere driver JDBC, usa Unity Catalog
* **Seguridad:** Credenciales en Databricks Secrets
* **Ejecución:** Manual via notebook o Job programado

---

## 🛠️ Componentes Técnicos

### **Pipeline Settings**
```yaml
catalog: covid19
schema: bronze
channel: PREVIEW
serverless: true
libraries:
  - ine_data_transformation.py
  - oms_and_who_centroamerica_data.py
  - who_data_transformation.py
```

### **Seguridad INACIF (Unity Catalog)**
```sql
-- 1. UC Connection
CREATE CONNECTION mysql_rds_inacif
TYPE mysql
OPTIONS (
  host secret('mysql_credentials', 'mysql_host'),
  port secret('mysql_credentials', 'mysql_port'),
  user secret('mysql_credentials', 'mysql_user'),
  password secret('mysql_credentials', 'mysql_password')
);

-- 2. Foreign Catalog
CREATE FOREIGN CATALOG inacif_mysql
USING CONNECTION mysql_rds_inacif
OPTIONS (database 'proyecto_necropsias');
```

### **Columnas de Auditoría (INACIF)**
| Campo | Tipo | Propósito |
|-------|------|-----------|
| `bronze_loaded_at` | timestamp | Cuándo se ingirió |
| `bronze_batch_id` | string (UUID) | Rastrear lotes |
| `bronze_source` | string | Sistema origen |

---

## 🎨 Decisiones de Diseño Clave

### **1. Separación de Métodos de Ingesta**
* **Pipeline SDP:** Fuentes file-based (S3, SharePoint, Drive)
* **Notebook:** Fuentes federadas (MySQL via UC)
* **Razón:** Permisos y compatibilidad

### **2. Materialized Views (No Streaming Tables)**
* Fuentes históricas batch, no streaming continuo
* Full refresh aceptable por volumen de datos

### **3. Sin JDBC Directo**
* **Lakehouse Federation** en lugar de JDBC tradicional
* Ventajas:
  - Integrado con Unity Catalog
  - Sin drivers en cluster
  - Credenciales centralizadas
  - Gobierno unificado

### **4. Auditoría desde Bronze**
* Rastreo completo desde el inicio
* Permite troubleshooting y lineage

### **5. Idempotencia**
* Overwrite mode - re-ejecutable sin duplicados
* Batch IDs únicos por ejecución

---

## 📊 Modelo de Datos INACIF

```
necropsias (75K)
├── FK: municipio_id → municipios (347)
│   └── FK: departamento_id → departamentos (23)
└── FK: causa_muerte_id → causas_muerte (41)
```

**Campos clave:**
* Temporales: anio, mes, dia, dia_semana
* Demográficos: sexo, edad, rangos etarios
* Geográficos: municipio_id, departamento_id
* Médicos: causa_muerte_id, evaluacion_mn

---

## 🚀 Estado Actual

### ✅ **Funcional para Presentación**
* Pipeline: 0 errores en dry run y ejecución completa
* Datos: 12 tablas disponibles en bronze
* Validación: Todas las tablas verificadas

### ⚠️ **Limitaciones Conocidas**
* INACIF no está en el pipeline (requiere permisos Foreign Catalog)
* Full refresh - no incremental todavía
* Sin transformaciones Silver/Gold aún

---

## 🔮 Roadmap Futuro

### **Corto Plazo**
1. ✅ Ingesta Bronze completa (HECHO)
2. 🔄 Automatizar ingesta INACIF con Job
3. 📊 Crear capa Silver con joins y transformaciones

### **Mediano Plazo**
4. 📈 Capa Gold con agregaciones analíticas
5. 🔄 Implementar cargas incrementales (CDC)
6. 📊 Dashboards y reportes en Lakeview

### **Largo Plazo**
7. 🤖 ML models para predicción de mortalidad
8. 🔍 Optimizaciones (partitioning, clustering)
9. 📝 Data Quality Expectations
10. 🔔 Alertas y monitoreo automatizado

---

## 📁 Estructura del Proyecto

```
final_bronze_pipeline/
├── transformations/           # Código SDP activo
│   ├── ine_data_transformation.py
│   ├── oms_and_who_centroamerica_data.py
│   ├── who_data_transformation.py
│   └── ingest_inacif_rds.py  (código SDP, no usado)
│
├── explorations/              # Notebooks de análisis
│   └── MySQL RDS Ingestion - Lakehouse Federation
│
└── docs/                      # Documentación
    └── source_inacif_documentation.py (archivo actual)
```

---

## 🎓 Lecciones Aprendidas

1. **Lakehouse Federation > JDBC** para simplicidad y gobierno
2. **Auditoría temprana** facilita troubleshooting
3. **Separar código de documentación** mantiene pipeline limpio
4. **Secrets desde día 1** - nunca hardcodear credenciales
5. **Idempotencia** permite re-ejecuciones seguras