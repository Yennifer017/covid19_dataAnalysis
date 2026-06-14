# Dataset: inacif_municipios

**Descripción funcional:** Catálogo geográfico de segundo nivel que detalla los municipios de la república, vinculados directamente a su departamento correspondiente. Crucial para realizar análisis demográficos con granularidad municipal.  
**Fuente:** Databricks (`covid19.bronze.inacif_municipios`)  
**Sensibilidad:** Baja (Catálogo geográfico público).  
**Frecuencia de actualización:** [Completar... ej. Estático]  

---

## Estructura de Campos

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `id` | INT | Código identificador único del municipio. | Llave primaria. |
| `nombre` | STRING | Nombre oficial del municipio. | Texto libre. |
| `departamento_id` | INT | ID del departamento al que pertenece el municipio. | Llave foránea conectada a `inacif_departamentos.id`. |
| `bronze_loaded_at` | TIMESTAMP | Fecha y hora exacta de la carga en la capa Bronze. | Auditoría del pipeline. |
| `bronze_batch_id` | STRING | ID único del lote de ejecución del pipeline (ID de Run). | Trazabilidad técnica. |
| `bronze_source` | STRING | Ruta o nombre del archivo origen de la extracción. | Metadato de linaje. |