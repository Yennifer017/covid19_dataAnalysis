# Dataset: who_covid_19_global_daily_data

**Descripción funcional:** Serie temporal diaria oficial provista por la Organización Mundial de la Salud (OMS). Registra la evolución del COVID-19 a nivel mundial, detallando el conteo diario y acumulado de casos positivos y decesos confirmados por cada país y región epidemiológica.  
**Fuente:** Databricks (`covid19.bronze.who_covid_19_global_daily_data`)  
**Sensibilidad:** Baja (Datos públicos de agregación global).  
**Frecuencia de actualización:** Diario / Semanal.  

---

## Estructura de Campos

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `date_reported` | STRING | Fecha en la que la OMS consolida el reporte epidemiológico. | Formato YYYY-MM-DD. Eje temporal. |
| `country_code` | STRING | Código internacional de dos dígitos asignado al país. | Formato ISO (ej. "GT", "CR", "US"). |
| `country` | STRING | Nombre oficial del país o territorio reportante. | Texto libre en inglés o estandarizado. |
| `who_region` | STRING | Código de la región sanitaria de la OMS a la que pertenece el país. | Ej: AMRO (Américas), EURO (Europa), etc. |
| `new_cases` | DOUBLE | Cantidad de nuevos casos positivos confirmados en las últimas 24 horas. | Métrica de velocidad de contagio. |
| `cumulative_cases` | LONG | Total acumulado de casos positivos desde el inicio de la pandemia. | Métrica de volumen histórico. |
| `new_deaths` | DOUBLE | Cantidad de nuevos decesos confirmados por COVID-19 en el día. | Métrica de letalidad diaria. |
| `cumulative_deaths` | LONG | Total acumulado de decesos confirmados desde el inicio de la pandemia. | Usado para calcular tasas de letalidad global. |