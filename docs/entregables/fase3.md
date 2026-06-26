# Fase 3: Modelado Predictivo y Análisis

## Descripción

Desarrollo e implementación de modelos de Machine Learning para predicción de mortalidad por COVID-19 en Guatemala, utilizando arquitectura de modelo híbrido con regresión Ridge y Lasso.

## Entregables de la Fase 3

**Carpeta de Google Drive:** [Entregables Fase 3](https://drive.google.com/drive/folders/1Urbp5TExVfD38XosDqN6UbG5lkw6mAKv?usp=drive_link)

La carpeta contiene los siguientes documentos:

- **Presupuesto** - Desglose de costos del proyecto
- **Cronograma** - Planificación temporal de actividades
- **WBS (Work Breakdown Structure)** - Estructura de desglose del trabajo
- **Presentación: COVID-19 Storytelling** - Presentación narrativa de los hallazgos
- **Informe de consultoría** - Documento ejecutivo del proyecto
- **Visualizaciones COVID-19 Power BI.pbix** - Dashboard interactivo desarrollado en Power BI Desktop

## Enfoque del Modelo Híbrido

Se implementaron dos modelos complementarios:

**Modelo A - Predicción Granular (INE Desagregado):**
- Predicción por departamento, causa de muerte y perfil demográfico
- Usa diseño dimensional completo con JOIN de tablas Gold
- Features descriptivos e interpretables
- Útil para análisis exploratorio detallado

**Modelo B - Predicción Agregada (RENAP Mensual):**
- Predicción de total nacional mensual
- Usa datos oficiales de registro civil (RENAP)
- Mayor poder predictivo (R² = 0.31)
- Recomendado para proyecciones operacionales

## Documentación Técnica

- [Análisis Técnico del Modelo Híbrido](analisis-modelo-hibrido.md) - Análisis completo de decisiones de diseño, resultados, lecciones aprendidas y visualizaciones
- Notebook implementado: `Predicción Mortalidad COVID-19 Ridge Lasso.ipynb`
- Ubicación: `/Mortalidad ML/` en el workspace

## Resultados Principales

| Modelo | R² | RMSE | MAE | Uso Recomendado |
|--------|-----|------|-----|-----------------|
| A - Ridge | 0.0052 | 28.07 | 13.83 | Análisis exploratorio |
| A - Lasso | 0.0027 | 28.11 | 13.90 | Análisis exploratorio |
| B - Ridge | 0.2930 | 975.51 | 785.52 | Proyección operacional |
| **B - Lasso** | **0.3052** | **967.08** | **783.14** | **Proyección operacional** |

## Visualizaciones del Modelo

El notebook incluye visualizaciones completas del Modelo B (mejor desempeño):

1. **Serie Temporal** - Predicciones vs valores reales a lo largo del tiempo
2. **Scatter Plot** - Relación entre predicciones y valores reales
3. **Análisis de Residuos** - Detección de patrones en errores de predicción
4. **Distribución de Residuos** - Verificación de normalidad en los errores
5. **Feature Importance** - Top 10 variables más influyentes

Ver la sección completa de [Visualizaciones del Modelo](analisis-modelo-hibrido.md#visualizaciones-del-modelo) en el análisis técnico.

## Validación

- Validación cruzada entre modelos confirmó que el Modelo B (agregado) es superior para predicción de totales mensuales
- Diferencia del 81% entre suma de predicciones granulares vs predicción directa agregada
- Correlación moderada-baja (0.47) indica que predecir agregados directamente es más efectivo

## Tecnologías Utilizadas

- Python 3.x con PySpark
- Scikit-learn (Ridge, Lasso, métricas)
- Pandas y NumPy
- Matplotlib y Seaborn (visualizaciones)
- Databricks Notebooks
- Unity Catalog (tablas Gold)
- Power BI Desktop (dashboards)

## Conclusiones Clave

1. **Granularidad vs Ruido:** Los datos agregados reducen el ruido y mejoran el poder predictivo (59x mejora)
2. **Calidad de Fuentes:** RENAP oficial supera a INE desagregado para predicción de totales
3. **Diseño Dimensional:** Mejora interpretabilidad pero no garantiza mejor R² con datos ruidosos
4. **Agregación Post-Predicción:** Predecir directamente agregados es superior a sumar predicciones granulares

## Trabajo Futuro

**Para Modelo A:**
- Implementar modelos no lineales (Random Forest, XGBoost)
- Agregar features climáticas y de movilidad
- Técnicas para manejo de causas minoritarias (SMOTE)

**Para Modelo B:**
- Implementar modelos de series de tiempo (ARIMA, Prophet, LSTM)
- Incorporar variables externas (índices de rigor, indicadores económicos)
- Ensambles con múltiples modelos
