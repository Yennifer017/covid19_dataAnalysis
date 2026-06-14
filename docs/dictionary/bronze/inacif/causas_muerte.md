# Dataset: inacif_causas_muerte

**Descripción funcional:** Catálogo maestro oficial de las causas de muerte médico-legales dictaminadas por los peritos del INACIF. Este catálogo permite estandarizar y clasificar los decesos para estudios epidemiológicos y forenses, facilitando la identificación de casos vinculados a afecciones pulmonares, COVID-19 o causas externas.  
**Fuente:** Databricks (`covid19.bronze.inacif_causas_muerte`)  
**Sensibilidad:** Baja (Catálogo público de referencia).  
**Frecuencia de actualización:** [Completar... ej. Histórico / Catálogo fijo]  

---

## Estructura de Campos

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `id` | INT | Identificador único y correlativo de la causa de muerte. | Llave primaria de catálogo. |
| `nombre` | STRING | Descripción textual de la causa médica o legal del deceso. | Texto libre estandarizado. |
| `bronze_loaded_at` | TIMESTAMP | Fecha y hora exacta de la carga en la capa Bronze. | Auditoría del pipeline. |
| `bronze_batch_id` | STRING | ID único del lote de ejecución del pipeline (ID de Run). | Trazabilidad técnica. |
| `bronze_source` | STRING | Ruta o nombre del archivo de origen extraído del portal de INACIF. | Metadato de linaje. |