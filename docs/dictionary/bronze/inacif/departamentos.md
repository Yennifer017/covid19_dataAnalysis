# Dataset: inacif_departamentos

**Descripción funcional:** Catálogo geográfico de primer nivel que registra las divisiones políticas (departamentos) donde el INACIF tiene cobertura y jurisdicción para el levantamiento y peritaje de cuerpos.  
**Fuente:** Databricks (`covid19.bronze.inacif_departamentos`)  
**Sensibilidad:** Baja (Catálogo geográfico público).  
**Frecuencia de actualización:** [Completar... ej. Estático]  

---

## Estructura de Campos

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `id` | INT | Código identificador único del departamento. | Llave primaria (normalmente homologada con INE). |
| `nombre` | STRING | Nombre oficial del departamento geográfico. | Texto libre (ej. "Guatemala", "Quetzaltenango"). |
| `bronze_loaded_at` | TIMESTAMP | Fecha y hora exacta de la carga en la capa Bronze. | Auditoría del pipeline. |
| `bronze_batch_id` | STRING | ID único del lote de ejecución del pipeline (ID de Run). | Trazabilidad técnica. |
| `bronze_source` | STRING | Ruta o nombre del archivo origen de la extracción. | Metadato de linaje. |