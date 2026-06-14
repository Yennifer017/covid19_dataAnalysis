# Datasets: mortalidad_categorias_costa_rica (2020 / 2021 / 2022)

**Descripción funcional:** Registros estadísticos e indicadores demográficos de mortalidad para Costa Rica. Este documento cubre de forma unificada las **tres tablas independientes** de la capa Bronze particionadas por año en el origen. Permite analizar el impacto anual del COVID-19 y la evolución de las tasas de mortalidad bruta y estandarizada distribuidas por sexo y grupos de edad.  
**Tablas Físicas de Origen:** * `covid19.bronze.mortalidad_categorias_costa_rica_2020`  
* `covid19.bronze.mortalidad_categorias_costa_rica_2021`  
* `covid19.bronze.mortalidad_categorias_costa_rica_2022`  
**Sensibilidad:** Media (Datos estadísticos de salud pública agregados por cohortes).  
**Frecuencia de actualización:** Histórico (Carga estática anual).  

> **Nota de Arquitectura de Datos:** Aunque en la capa Bronze los datos se encuentran separados en tres tablas físicas distintas (respetando la estructura de extracción as-is del proveedor), comparten exactamente el mismo esquema técnico. Estas tablas son candidatas ideales para ser consolidadas mediante un proceso de unificación (`UNION ALL`) en una única tabla histórica con partición temporal al transicionar a la capa Silver.

---

## Estructura de Campos Común

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `indicator_code` | STRING | Código alfanumérico estandarizado de la causa o indicador médico evaluado. | Clave de catálogo técnico. |
| `indicator_name` | LONG | Identificador numérico largo asignado al nombre del indicador. | ID de relación para cruzar con catálogos verbales. |
| `year` | STRING | Año al que corresponde la muestra estadística recopilada. | Formato YYYY (Valores fijos "2020", "2021" o "2022" según la tabla). |
| `sex` | STRING | Género de la población evaluada en la cohorte. | Valores estándar: Male, Female, Total. |
| `age_group_code` | STRING | Código único asignado al bloque de rango de edad. | Clave de catálogo demográfico. |
| `age_group` | DOUBLE | Identificador numérico continuo para ordenar lógicamente el grupo de edad. | Útil para ordenamiento de filas en reportes y gráficos. |
| `number` | DOUBLE | Cantidad absoluta de defunciones registradas para esa cohorte específica. | Métrica de volumen real de decesos. |
| `percentage_of_cause_specific_deaths_out_of_total_deaths` | DOUBLE | Porcentaje que representa esa causa de muerte sobre el total de fallecimientos del grupo. | Valor porcentual continuo (Rango de 0 a 100). |
| `age_standardized_death_rate_per_100_000_standard_population` | DOUBLE | Tasa de mortalidad estandarizada por edad por cada 100,000 habitantes de la población estándar. | **Métrica Clave:** Permite realizar comparaciones epidemiológicas internacionales sin sesgo por la pirámide de edad del país. |
| `death_rate_per_100_000_population` | DOUBLE | Tasa bruta de mortalidad registrada por cada 100,000 habitantes de la población real. | Métrica epidemiológica base de incidencia. |