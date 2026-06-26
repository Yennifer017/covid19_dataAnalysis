# Predicción de Mortalidad COVID-19: Modelo Híbrido Ridge y Lasso

## 📋 Resumen Ejecutivo

Este proyecto implementa un **Modelo Híbrido** de Machine Learning para predecir mortalidad por COVID-19 en Guatemala, utilizando regresión Ridge y Lasso en dos enfoques complementarios:
- **Modelo A**: Predicción granular (INE desagregado con diseño dimensional)
- **Modelo B**: Predicción agregada mensual (RENAP oficial)

**🏆 Resultado:** El Modelo B alcanzó **R² = 0.31**, superando al baseline en **7,309%**.

---

## 🎯 Problema de Machine Learning

**Objetivo:** Predecir mortalidad relacionada con COVID-19 usando dos enfoques:
1. **Granular:** Por departamento, perfil demográfico y causa
2. **Agregado:** Total mensual nacional

**Tipo de problema:** Regresión supervisada con regularización (Ridge/Lasso)

---

## 📊 Datos Utilizados

### 1. Tabla Principal: `covid19.gold.covid19_gold_fact_mortalidad_unificada`
- **Registros:** 48,755 (filtrado INE: 48,656)
- **Fuentes:** INE (99.8%), CR (0.1%), OMS (0.1%)
- **Columnas clave:** id_tiempo_mes, id_geografia, id_perfil, id_causa, cantidad_fallecidos
- **Uso:** Baseline y Modelo A (solo fuente INE)

### 2. Tabla de Contexto: `covid19.gold.covid19_gold_fact_contexto_renap`
- **Registros:** 1,943
- **Evento clave:** "Defunciones" (136 meses, 1,098,282 total)
- **Otros eventos:** Nacimientos, matrimonios, divorcios, etc. (22 tipos)
- **Uso:** Modelo B (target) y Modelo A (feature)

### 3. Dimensiones del Modelo Estrella
- **dim_geografia:** 25 departamentos
- **dim_perfil:** 12 perfiles (sexo × rango_edad)
- **dim_causa_muerte:** 48 causas (incluye flag `es_covid`)
- **dim_tiempo:** 144 períodos

---

## 🔧 Metodología: Tres Modelos Implementados

### **Baseline (Modelo Original)**
- **Fuentes:** Mezcla INE+CR+OMS sin filtrar
- **Features:** 24 (IDs con one-hot encoding)
- **Target:** cantidad_fallecidos
- **Diseño dimensional:** ❌ No usa

### **Modelo A: INE Desagregado + Diseño Dimensional**
1. **Filtrado:** Solo fuente INE (48,656 registros)
2. **JOIN dimensional:** Geografía, perfil, causa, tiempo
3. **Features adicionales:**
   - Flag `es_covid_int` (0/1)
   - Encoding circular del mes (sin/cos)
   - Total defunciones RENAP (contexto)
4. **One-hot:** Categorías descriptivas (sexo, rango_edad, categoria_general, departamento)
5. **Features finales:** 5 (tras normalización)
6. **Target:** cantidad_fallecidos (desagregado)

### **Modelo B: RENAP Agregado Mensual**
1. **Target:** total_defunciones (RENAP oficial)
2. **Features:**
   - 22 eventos RENAP (nacimientos, matrimonios, etc.)
   - Variables temporales (mes_sin, mes_cos, año_desde_inicio)
3. **Features finales:** 25
4. **Granularidad:** Mensual agregado (136 meses)

### **Validación Cruzada**
- Agregar predicciones Modelo A por mes
- Comparar con predicciones Modelo B
- Medir correlación y diferencias porcentuales

---

## 📈 Resultados Comparativos

### Tabla de Resultados

| Modelo | Tipo | R² | RMSE | MAE | Features | Registros |
|--------|------|-----|------|-----|----------|-----------|
| Baseline Ridge | Baseline | 0.0041 | 37.02 | 15.09 | 24 | 48,755 |
| Baseline Lasso | Baseline | 0.0035 | 37.03 | 15.09 | 24 | 48,755 |
| Modelo A - Ridge | Híbrido A | 0.0052 | 28.07 | 13.83 | 5 | 48,656 |
| Modelo A - Lasso | Híbrido A | 0.0027 | 28.11 | 13.90 | 5 | 48,656 |
| Modelo B - Ridge | Híbrido B | 0.2930 | 975.51 | 785.52 | 25 | 136 |
| **🏆 Modelo B - Lasso** | **Híbrido B** | **0.3052** | **967.08** | **783.14** | **25** | **136** |

### Mejoras vs Baseline

| Modelo | Mejora en R² |
|--------|--------------|
| Modelo A - Ridge | +26.5% |
| **Modelo B - Lasso** | **+7,309%** |

---

## 💡 Interpretación y Conclusiones

### 1. **Modelo B es el ganador absoluto**
✅ **R² = 0.31** vs baseline 0.004 (mejora de 75x)  
✅ Usa fuente oficial RENAP (mayor precisión y cobertura)  
✅ Predicción de totales mensuales (menos ruido que granular)  
✅ 136 meses de datos históricos

### 2. **Modelo A mejoró interpretabilidad, no poder predictivo**
✅ Features descriptivos (sexo_Hombre, rango_edad_65+, etc.)  
✅ Usa diseño dimensional completo  
⚠️ R² = 0.0052 (mejora marginal del 26% vs baseline)  
⚠️ Predicción granular tiene mucho ruido

### 3. **Validación Cruzada: Inconsistencia detectada**
❌ Diferencia promedio: ~81% entre suma(Modelo A) y Modelo B  
❌ Correlación baja: 0.47 (Ridge), 0.37 (Lasso)  
📊 **Conclusión:** Modelo A subestima totales; agregación post-predicción introduce errores

### 4. **Por qué Modelo B superó a Modelo A**
1. **Menor ruido:** Datos agregados vs granulares
2. **Fuente más precisa:** RENAP oficial vs INE con gaps
3. **Escala apropiada:** Predecir totales directamente vs sumar predicciones

---

## 🔮 Recomendaciones

### Para Uso Operacional
✅ **Usar Modelo B** para proyecciones de mortalidad mensual nacional  
✅ Validar predicciones contra datos RENAP actualizados  
✅ Monitorear cambios en patrones temporales (COVID vs endémico)

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
1. ✅ **Filtrar fuentes consistentes:** INE (desagregado) vs RENAP (agregado oficial)
2. ✅ **Usar diseño dimensional:** JOIN con dimensiones mejora interpretabilidad
3. ✅ **Aprovechar metadatos:** Flag `es_covid` en dim_causa

### Modelado
1. ✅ **Agregación reduce ruido:** Modelo B (agregado) >> Modelo A (granular)
2. ✅ **Regularización funciona:** Ridge/Lasso estables con features limitados
3. ⚠️ **Linealidad limitada:** R² bajo indica relaciones no lineales

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
- INE: 48,656 registros desagregados (baseline y Modelo A)
- RENAP: 136 meses agregados oficiales (Modelo B)
- Dimensiones: geografía, perfil, causa, tiempo

**Slide 3: Resultados**
- Baseline: R² = 0.004
- Modelo A: R² = 0.005 (+26% vs baseline)
- **Modelo B: R² = 0.31 (+7,309% vs baseline) 🏆**

**Slide 4: Conclusión**
- Modelo B ganador: RENAP agregado mensual
- Predicción directa de agregados > sumar predicciones granulares
- Trabajo futuro: modelos no lineales, series temporales

### Mensaje Principal

> "Este proyecto demuestra la importancia del diseño de datos y la elección de granularidad en Machine Learning. Aunque el Modelo A (desagregado) ofrece mayor interpretabilidad, el Modelo B (agregado) alcanzó R² = 0.31 al reducir ruido y usar la fuente oficial RENAP. La validación cruzada confirmó que predecir totales directamente es más efectivo que agregar predicciones granulares para este problema."

---

## 👥 Contexto del Proyecto

**Fuentes de datos:** INE (Instituto Nacional de Estadística) y RENAP (Registro Nacional de las Personas)  
**Propósito:** Aplicación práctica de ML a problema real de salud pública en Guatemala  
**Limitaciones:** Free Edition, sin optimización de hiperparámetros (α=1.0 fijo)

---

## 📁 Archivos del Proyecto

- `Predicción Mortalidad COVID-19 Ridge Lasso.ipynb` - Notebook con 3 modelos
- `DOCUMENTACION_PROYECTO.md` - Este documento
- `ANALISIS_CRITICO_Y_PROPUESTA_MEJORADA.md` - Análisis de limitaciones
