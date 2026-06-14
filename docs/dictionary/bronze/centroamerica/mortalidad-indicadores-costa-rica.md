# Datasets: mortalidad_indicadores_costa_rica / mortalidad_por_edades_costa_rica

**Descripción funcional:** Conjuntos de datos estadísticos de mortalidad para Costa Rica. Este documento unifica **dos tablas independientes** de la capa Bronze que distribuyen la información bajo ópticas distintas: una orientada a indicadores macro y otra enfocada estrictamente en la segmentación por cohortes etarias. Ambos datasets proveen métricas de volumen, proporciones y tasas ajustadas para análisis demográfico.  
**Tablas Físicas de Origen:**
* `covid19.bronze.mortalidad_indicadores_costa_rica`  
* `covid19.bronze.mortalidad_por_edades_costa_rica`  
**Sensibilidad:** Media (Datos estadísticos agregados de salud pública).  
**Frecuencia de actualización:** Anual / Histórico.  

> 💡 **Nota de Análisis Funcional:** Aunque estas dos tablas comparten el mismo esquema técnico de columnas, se diferencian por el nivel de agregación en sus filas:
> * `mortalidad_indicadores_costa_rica` suele contener los totales nacionales o tasas estandarizadas globales por indicador.
> * `mortalidad_por_edades_costa_rica` desglosa esas mismas métricas abriendo el detalle fila por fila para cada grupo etario registrado en el país.

---

## Estructura de Campos Común

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `indicator_code` | STRING | Código alfanumérico estandarizado de la causa o indicador médico evaluado. | Clave de catálogo técnico. |
| `indicator_name` | LONG | Identificador numérico largo asignado al nombre del indicador. | ID de relación para cruzar con catálogos verbales. |
| `year` | STRING | Año al que corresponde la muestra estadística recopilada. | Formato YYYY. |
| `sex` | STRING | Género de la población evaluada en la cohorte. | Valores estándar: Male, Female, Total. |
| `age_group_code` | STRING | Código único asignado al bloque de rango de edad. | Clave de catálogo demográfico. |
| `age_group` | DOUBLE | Identificador numérico continuo para ordenar lógicamente el grupo de edad. | Útil para ordenamiento de filas en reportes y gráficos. |
| `number` | DOUBLE | Cantidad absoluta de defunciones registradas para esa cohorte específica. | Métrica de volumen real de decesos. |
| `percentage_of_cause_specific_deaths_out_of_total_deaths` | DOUBLE | Porcentaje que representa esa causa de muerte sobre el total de fallecimientos del grupo. | Valor porcentual continuo (Rango de 0 a 100). |
| `age_standardized_death_rate_per_100_000_standard_population` | DOUBLE | Tasa de mortalidad estandarizada por edad por cada 100,000 habitantes de la población estándar. | **Métrica Clave:** Permite realizar comparaciones epidemiológicas internacionales sin sesgo por la pirámide de edad del país. |
| `death_rate_per_100_000_population` | DOUBLE | Tasa bruta de mortalidad registrada por cada 100,000 habitantes de la población real. | Métrica epidemiológica base de incidencia. |