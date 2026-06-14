# Dataset: who_mortality

**Descripción funcional:** Datos estadísticos de mortalidad de la OMS. Se utiliza como marco de referencia histórico para analizar la distribución de causas de muerte a nivel global y comparar la mortalidad general frente al impacto específico del COVID-19.  
**Fuente:** Databricks (`covid19.bronze.who_mortality`)  
**Sensibilidad:** Media (Datos estadísticos agregados).  
**Frecuencia de actualización:** [Completar... ej. Histórico]  

> **Nota Técnica de Calidad de Datos:** Las columnas de esta tabla en la capa Bronze contienen nombres anómalos (ej. valores como `2000`, `1.00000000`, `unnamed:_10`). Esto indica que el archivo de origen se cargó sin cabeceras o desplazado. Se requiere un proceso de renombrado y tipificación en la capa Silver para corregir el esquema.

---

## Estructura de Campos (Esquema Crudo)

| Campo | Tipo de Dato | Descripción Funcional / Diagnóstico Crudo | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `cg0280` | STRING | Posible código interno de categoría o indicador de la OMS. | Pendiente de homologación. |
| `leprosy` | STRING | Campo de diagnóstico médico. Muestra la patología evaluada (ej. Lepra u otras causas). | Filtro de causa de muerte. |
| `2000` | LONG | Representa el Año del registro o una muestra temporal (Cabecera desplazada). | Formato YYYY mapeado como columna. |
| `all` | STRING | Filtro de desagregación por criterios globales (ej. Total de la población). | Criterio de agrupación. |
| `age_all` | STRING | Indica que el registro abarca todos los rangos de edad combinados. | Filtro demográfico. |
| `[all]` | STRING | Metadato o etiqueta secundaria de agrupación poblacional. | Control de agregación. |
| `1.00000000` | DOUBLE | Métrica decimal cruda (Probablemente tasa de incidencia base o factor de ponderación). | Valor continuo. |
| `0.00148954` | DOUBLE | Métrica decimal cruda (Probablemente proporción o coeficiente de mortalidad). | Valor continuo. |
| `0.00471638` | DOUBLE | Métrica decimal cruda (Probablemente coeficiente epidemiológico secundario). | Valor continuo. |
| `0.00858314` | DOUBLE | Métrica decimal cruda (Probablemente límite o intervalo estadístico). | Valor continuo. |
| `unnamed:_10` | DOUBLE | Columna residual detectada al final del archivo original durante la ingesta. | Columna a descartar en limpieza. |