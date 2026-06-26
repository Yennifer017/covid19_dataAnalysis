# Fase 3: Modelado Predictivo y Análisis

## Descripción

Desarrollo e implementación de modelos de Machine Learning para predicción de mortalidad por COVID-19 en Guatemala, utilizando arquitectura de modelo híbrido con regresión Ridge y Lasso.

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

## Documentación

- [Análisis Técnico del Modelo Híbrido](analisis-modelo-hibrido.md) - Análisis completo de decisiones de diseño, resultados y lecciones aprendidas
- Notebook implementado: `Predicción Mortalidad COVID-19 Ridge Lasso.ipynb`
- Ubicación: `/Mortalidad ML/` en el workspace

## Resultados Principales

| Modelo | R² | RMSE | MAE | Uso Recomendado |
|--------|-----|------|-----|-----------------|
| A - Ridge | 0.0052 | 28.07 | 13.83 | Análisis exploratorio |
| A - Lasso | 0.0027 | 28.11 | 13.90 | Análisis exploratorio |
| B - Ridge | 0.2930 | 975.51 | 785.52 | Proyección operacional |
| **B - Lasso** | **0.3052** | **967.08** | **783.14** | **Proyección operacional** |

## Validación

- Validación cruzada entre modelos confirmó que el Modelo B (agregado) es superior para predicción de totales mensuales
- Diferencia del 81% entre suma de predicciones granulares vs predicción directa agregada
- Correlación moderada-baja (0.47) indica que predecir agregados directamente es más efectivo

## Tecnologías Utilizadas

- Python 3.x con PySpark
- Scikit-learn (Ridge, Lasso, métricas)
- Pandas y NumPy
- Databricks Notebooks
- Unity Catalog (tablas Gold)

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
