# Dataset: mortalidad_por_edades_costa_rica

**Descripción funcional:** Dataset especializado en la distribución fina y estructurada de la mortalidad en Costa Rica según cohortes etarias (grupos de edad). Su propósito principal es aislar el factor edad para facilitar la creación de pirámides de mortalidad y medir con precisión el impacto del COVID-19 en poblaciones vulnerables (adultos mayores) vs. poblaciones jóvenes.  
**Fuente:** Databricks (`covid19.bronze.mortalidad_por_edades_costa_rica`)  
**Sensibilidad:** Media (Datos epidemiológicos por grupos etarios).  
**Frecuencia de actualización:** Histórico / Anual.  

---

## Estructura de Campos

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `indicator_code` | STRING | Código alfanumérico que define la causa de muerte o el corte epidemiológico. | Clave de catálogo técnico. |
| `indicator_name` | LONG | ID numérico largo vinculado a la descripción formal del grupo de indicadores. | ID de relación para maestros. |
| `year` | STRING | Año calendario analizado. | Formato YYYY. |
| `sex` | STRING | Desglose por género dentro del rango de edad evaluado. | Valores: Male, Female, Total. |
| `age_group_code` | STRING | Código específico de la cohorte etaria (ej. códigos para rangos "quinquenales" o "específicos"). | Clave para uniones funcionales de demografía. |
| `age_group` | DOUBLE | Valor numérico asignado para la jerarquía, orden o límite de edad del grupo. | Crucial para ordenar cronológicamente los rangos en reportes. |
| `number` | DOUBLE | Volumen absoluto de defunciones concentradas en este grupo de edad específico. | Métrica clave para curvas de vulnerabilidad. |
| `percentage_of_cause_specific_deaths_out_of_total_deaths` | DOUBLE | Porcentaje que representan los decesos de esta cohorte sobre la mortalidad total. | Rango de 0 a 100. |
| `age_standardized_death_rate_per_100_000_standard_population` | DOUBLE | Tasa ajustada por edad por cada 100k habitantes de la población estándar. | Permite ver la incidencia real controlando el factor población. |
| `death_rate_per_100_000_population` | DOUBLE | Tasa de mortalidad bruta por cada 100k habitantes en ese rango de edad específico. | Métrica de impacto directo por grupo etario. |