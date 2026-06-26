# Predicción de Mortalidad COVID-19: Modelo Híbrido Ridge y Lasso

## 📋 Resumen Ejecutivo

Este proyecto implementa un **Modelo Híbrido** de Machine Learning para predecir mortalidad por COVID-19 en Guatemala, utilizando regresión Ridge y Lasso en dos enfoques complementarios:
- **Modelo A**: Predicción granular (INE desagregado con diseño dimensional)
- **Modelo B**: Predicción agregada mensual (RENAP oficial)

**🏆 Resultado:** El Modelo B alcanzó **R² = 0.31**, el mejor resultado entre ambos enfoques.

---

## 🎯 Problema de Machine Learning

**Objetivo:** Predecir mortalidad relacionada con COVID-19 usando dos enfoques:
1. **Granular:** Por departamento, perfil demográfico y causa
2. **Agregado:** Total mensual nacional

**Tipo de problema:** Regresión supervisada con regularización (Ridge/Lasso)

---

## 📊 Datos Utilizados

### 1. Tabla Principal: `covid19.gold.covid19_gold_fact_mortalidad_unificada`
- **Registros totales:** 48,755
- **Registros INE filtrados:** 48,656 (99.8%)
- **Fuentes:** INE (principal), CR, OMS
- **Columnas clave:** id_tiempo_mes, id_geografia, id_perfil, id_causa, cantidad_fallecidos
- **Uso:** Modelo A (solo fuente INE)

### 2. Tabla de Contexto: `covid19.gold.covid19_gold_fact_contexto_renap`
- **Registros:** 1,943
- **Evento clave:** "Defunciones" (136 meses, 1,098,282 total)
- **Otros eventos:** Nacimientos, matrimonios, divorcios, etc. (22 tipos)
- **Uso:** Modelo B (target) y Modelo A (feature adicional)

### 3. Dimensiones del Modelo Estrella
- **dim_geografia:** 25 departamentos de Guatemala
- **dim_perfil:** 12 perfiles (sexo × rango_edad)
- **dim_causa_muerte:** 48 causas (incluye flag `es_covid`)
- **dim_tiempo:** 144 períodos mensuales

---

## 🔧 Metodología: Modelo Híbrido

### **Modelo A: INE Desagregado + Diseño Dimensional**

**Objetivo:** Predicción granular por departamento, causa y perfil

**Pasos:**
1. **Filtrado:** Solo fuente INE (48,656 registros)
2. **JOIN dimensional:** Geografía, perfil, causa, tiempo
3. **Features adicionales:**
   - Flag `es_covid_int` (0/1) - identifica casos COVID
   - Encoding circular del mes (sin/cos) - captura estacionalidad
   - Total defunciones RENAP - contexto agregado
4. **One-hot encoding:** Categorías descriptivas
   - sexo (Hombre/Mujer/Ambos)
   - rango_edad (0-14, 15-64, 65+, Todas)
   - categoria_general (COVID-19, Cardiovascular, Cáncer, etc.)
   - nombre_departamento (22 departamentos)
5. **Features finales:** 5 variables numéricas
6. **Target:** cantidad_fallecidos (desagregado)
7. **Train/Test:** 80/20 split
8. **Normalización:** StandardScaler

### **Modelo B: RENAP Agregado Mensual**

**Objetivo:** Predicción de total mensual nacional

**Pasos:**
1. **Fuente:** RENAP Defunciones (registro civil oficial)
2. **Target:** total_defunciones (mensual)
3. **Features:**
   - 22 eventos RENAP pivotados (nacimientos, matrimonios, divorcios, etc.)
   - Variables temporales (mes_sin, mes_cos, año_desde_inicio)
4. **Features finales:** 25 variables
5. **Granularidad:** Mensual agregado (136 meses)
6. **Train/Test:** 80/20 split
7. **Normalización:** StandardScaler

### **Validación Cruzada**

**Objetivo:** Verificar consistencia entre modelos

**Proceso:**
1. Agregar predicciones del Modelo A por mes
2. Comparar con predicciones del Modelo B
3. Calcular correlación y diferencias porcentuales

---

## 📈 Resultados

### Tabla de Resultados Comparativa

| Modelo | Tipo | R² | RMSE | MAE | Features | Registros |
|--------|------|-----|------|-----|----------|-----------|
| Modelo A - Ridge | Híbrido A | 0.0052 | 28.07 | 13.83 | 5 | 48,656 |
| Modelo A - Lasso | Híbrido A | 0.0027 | 28.11 | 13.90 | 5 | 48,656 |
| Modelo B - Ridge | Híbrido B | 0.2930 | 975.51 | 785.52 | 25 | 136 |
| **🏆 Modelo B - Lasso** | **Híbrido B** | **0.3052** | **967.08** | **783.14** | **25** | **136** |

### 🏆 Mejor Modelo: Modelo B - Lasso (RENAP Agregado)

**Métricas:**
- **R² = 0.3052** - Explica 30.5% de la varianza
- **RMSE = 967** defunciones (escala mensual)
- **MAE = 783** defunciones

---

## 💡 Interpretación y Conclusiones

### 1. **Modelo B superó significativamente al Modelo A**

| Aspecto | Modelo A | Modelo B |
|---------|----------|----------|
| R² | 0.0052 | **0.3052** |
| Escala | Granular (ruido alto) | Agregado (ruido bajo) |
| Cobertura | 90 meses | **136 meses** |
| Fuente | INE (desagregado) | **RENAP (oficial)** |

**Razones del éxito del Modelo B:**
1. ✅ **Datos agregados** tienen menos ruido que granulares
2. ✅ **RENAP oficial** es la fuente más precisa (registro civil)
3. ✅ **Mayor cobertura temporal** (136 vs 90 meses)
4. ✅ **Predicción directa** de totales vs sumar predicciones

### 2. **Modelo A: Mejor interpretabilidad, menor poder predictivo**

**Ventajas:**
- ✅ Features descriptivos e interpretables (sexo_Hombre, rango_edad_65+)
- ✅ Usa diseño dimensional completo
- ✅ Incluye flag es_covid explícito

**Limitaciones:**
- ⚠️ R² = 0.0052 (muy bajo)
- ⚠️ Predicción granular tiene alto ruido
- ⚠️ Datos faltantes en INE

### 3. **Validación Cruzada: Detectó inconsistencia**

| Métrica | Ridge | Lasso |
|---------|-------|-------|
| Diferencia media | -6,638 fallecidos | -6,578 fallecidos |
| Diferencia % | -81.77% | -80.90% |
| Correlación | 0.4683 | 0.3716 |

**Conclusión:** Modelo A subestima totales. Predecir agregados directamente (Modelo B) es superior a sumar predicciones granulares (Modelo A).

---

## 🔮 Recomendaciones

### Para Uso Operacional
✅ **Usar Modelo B** para proyecciones mensuales nacionales  
✅ Validar predicciones contra datos RENAP actualizados  
✅ Monitorear cambios en patrones temporales

### Para Mejora Futura

#### Modelo A (Granular)
1. **Modelos no lineales:** Random Forest, XGBoost para capturar interacciones
2. **Features adicionales:**
   - Variables climáticas (temperatura, humedad)
   - Movilidad poblacional por departamento
   - Tasa de vacunación regional
3. **Manejo de desbalance:** SMOTE para causas minoritarias

#### Modelo B (Agregado)
1. **Series de tiempo:** ARIMA, Prophet, LSTM para patrones temporales
2. **Variables externas:**
   - Índice de rigor de medidas (Oxford Stringency Index)
   - Indicadores económicos (desempleo, PIB)
3. **Ensambles:** Combinar Ridge/Lasso con modelos de series temporales

---

## 📚 Tecnologías Utilizadas

- **Python 3.x** con PySpark
- **Pandas** y **NumPy** para manipulación de datos
- **Scikit-learn** para Ridge, Lasso, métricas y normalización
- **Matplotlib** para visualizaciones
- **Databricks SQL** para queries y joins dimensionales

---

## 🎓 Lecciones Aprendidas

### Diseño de Datos
1. ✅ **Filtrar fuentes consistentes:** INE desagregado vs RENAP agregado oficial
2. ✅ **Usar diseño dimensional:** JOIN con dimensiones mejora interpretabilidad
3. ✅ **Aprovechar metadatos:** Flag `es_covid` en dim_causa

### Modelado
1. ✅ **Agregación reduce ruido:** Modelo B (agregado) >> Modelo A (granular)
2. ✅ **Regularización funciona:** Ridge/Lasso estables con features limitados
3. ⚠️ **Linealidad limitada:** R² bajo del Modelo A indica relaciones no lineales

### Validación
1. ✅ **Validación cruzada crítica:** Detectó inconsistencia entre enfoques
2. ✅ **Correlación como métrica:** Mide consistencia entre modelos
3. ⚠️ **Agregación post-predicción falla:** Mejor predecir directamente agregados

---

## 📌 Para Informe y Presentación

### Puntos Clave (Diapositivas)

**Slide 1: Problema**
- Predecir mortalidad COVID-19 en Guatemala
- Dos enfoques: granular (departamento/causa) vs agregado (nacional)

**Slide 2: Datos**
- INE: 48,656 registros desagregados (Modelo A)
- RENAP: 136 meses agregados oficiales (Modelo B)
- Dimensiones: geografía, perfil, causa, tiempo

**Slide 3: Resultados**
- Modelo A: R² = 0.005 (predicción granular)
- **Modelo B: R² = 0.31 (predicción agregada) 🏆**
- Validación cruzada: diferencia 81%

**Slide 4: Conclusión**
- Modelo B ganador: RENAP agregado mensual
- Predicción directa de agregados > sumar predicciones granulares
- Trabajo futuro: series temporales, modelos no lineales

### Mensaje Principal

> "Este proyecto demuestra la importancia de la elección de granularidad en Machine Learning. El Modelo B (agregado) alcanzó R² = 0.31 al reducir ruido y usar la fuente oficial RENAP, mientras que el Modelo A (desagregado) ofrece interpretabilidad pero sufre de alto ruido (R² = 0.005). La validación cruzada confirmó que predecir totales directamente es más efectivo que agregar predicciones granulares para este problema."

---

## 👥 Contexto del Proyecto

**Fuentes de datos:** INE (Instituto Nacional de Estadística) y RENAP (Registro Nacional de las Personas)  
**Propósito:** Aplicación práctica de ML a problema real de salud pública en Guatemala  
**Limitaciones:** Free Edition, sin optimización de hiperparámetros (α=1.0 fijo)

---

## 📁 Archivos del Proyecto

- `Predicción Mortalidad COVID-19 Ridge Lasso.ipynb` - Notebook con Modelo Híbrido
- `DOCUMENTACION_PROYECTO.md` - Este documento
- `ANALISIS_CRITICO_Y_PROPUESTA_MEJORADA.md` - Análisis técnico profundo
