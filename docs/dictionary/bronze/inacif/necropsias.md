# Dataset: inacif_necropsias

**Descripción funcional:** Tabla de hechos principal que registra los peritajes y necropsias clínico-legales practicadas por INACIF. Contiene los datos demográficos individuales de las personas fallecidas y las variables de análisis temporal, geográfico y de causa médica que permiten evaluar tendencias de mortalidad forense.  
**Fuente:** Databricks (`covid19.bronze.inacif_necropsias`)  
**Sensibilidad:** Alta (Contiene microdatos forenses sensibles e información demográfica de personas fallecidas).  
**Frecuencia de actualización:** [Completar... ej. Mensual / Semestral]  

---

## Estructura de Campos

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `id` | INT | Identificador único incremental del registro de necropsia. | Llave primaria. |
| `numero_correlativo` | STRING | Número de caso o expediente forense oficial asignado por INACIF. | **Dato Sensible**. Identificador administrativo de control. |
| `anio` | INT | Año de ocurrencia o realización del peritaje. | Formato YYYY (Eje temporal principal). |
| `mes` | BYTE | Mes de ocurrencia en formato numérico compacto. | Valores de 1 a 12. |
| `dia` | BYTE | Día calendario de ocurrencia en formato numérico compacto. | Valores de 1 a 31. |
| `dia_semana` | STRING | Nombre del día de la semana en que ocurrió el deceso. | Útil para análisis de comportamiento y estacionalidad. |
| `municipio_id` | INT | ID del municipio donde ocurrió o se procesó el deceso. | Llave foránea vinculada a `inacif_municipios.id`. |
| `causa_muerte_id` | INT | Código que vincula el deceso al catálogo maestro de diagnósticos. | Llave foránea vinculada a `inacif_causas_muerte.id`. |
| `sexo` | STRING | Género registrado de la persona fallecida. | Valores estandarizados (ej. "Masculino", "Femenino"). |
| `edad` | STRING | Edad cronológica de la persona. Puede venir formateada en texto. | Clave para segmentación demográfica. |
| `rango_60_mas` | STRING | Bandera/Indicador que evalúa si el fallecido pertenecía a la tercera edad. | Filtro poblacional de alto riesgo (ej. "Sí", "No"). |
| `rango_80_mas` | STRING | Bandera/Indicador que evalúa si el fallecido pertenecía a la cohorte de extrema vejez. | Filtro epidemiológico específico. |
| `rango_quinquenal` | STRING | Agrupación demográfica de la edad en bloques de 5 años. | Facilita la creación de pirámides poblacionales. |
| `es_menor_mayor` | STRING | Clasificación legal rápida del rango de edad. | Valores habituales (ej. "Mayor de edad", "Menor de edad"). |
| `evaluacion_mn` | STRING | Evaluación forense de muerte natural o violenta/en investigación. | Clasificación macro de la naturaleza del deceso. |
| `rango_ninez_adolescencia` | STRING | Segmentación específica orientada a la protección y análisis de menores. | Categorías de minoría de edad. |
| `bronze_loaded_at` | TIMESTAMP | Fecha y hora exacta de la carga en la capa Bronze. | Auditoría técnica. |
| `bronze_batch_id` | STRING | ID único del lote de ejecución del pipeline (ID de Run). | Trazabilidad técnica. |
| `bronze_source` | STRING | Ruta o nombre del archivo CSV/XLSX de origen del portal de datos. | Metadato de linaje. |