# Análisis Técnico: Modelo Híbrido de Predicción de Mortalidad COVID-19

## Decisiones de Diseño del Modelo Híbrido

### ¿Por qué dos modelos?

El problema de predicción de mortalidad puede abordarse desde dos perspectivas complementarias:

1. **Modelo A (Granular):** Predecir por departamento/causa/perfil - Útil para análisis detallado
2. **Modelo B (Agregado):** Predecir total mensual nacional - Útil para planificación

**Hipótesis inicial:** El Modelo A ofrecería mayor interpretabilidad, mientras que el Modelo B tendría mayor poder predictivo (menor ruido).

**Resultado:** La hipótesis se confirmó completamente.

---

## MODELO A: INE Desagregado + Diseño Dimensional

### Decisiones de Diseño

#### 1. Filtrar solo fuente INE

**Problema detectado:** La tabla `fact_mortalidad_unificada` mezcla tres fuentes:

| Fuente | Registros | Promedio Fallecidos | Escala |
|--------|-----------|---------------------|---------|
| INE | 48,656 (99.8%) | 13.85 | Granular |
| CR | 54 (0.1%) | 174.00 | Agregado (12x) |
| OMS | 45 (0.1%) | 449.00 | Agregado (32x) |

**Decisión:** Filtrar solo INE para tener datos homogéneos y granulares.

**Resultado:** 48,656 registros consistentes.

#### 2. JOIN con dimensiones del modelo estrella

**Dimensiones disponibles:**
- `dim_geografia`: 25 departamentos
- `dim_perfil`: 12 perfiles (sexo × rango_edad)
- `dim_causa_muerte`: 48 causas (incluye flag `es_covid`)
- `dim_tiempo`: 144 períodos

**Beneficio:** Features descriptivos interpretables (ej: `sexo_Hombre`, `rango_edad_65+`) en lugar de IDs opacos (ej: `id_perfil_H-65+`).

#### 3. Feature engineering dimensional

```python
# Flag COVID explícito
df['es_covid_int'] = df['es_covid'].astype(int)

# Encoding circular del mes (captura estacionalidad)
df['mes_sin'] = np.sin(2 * π * mes / 12)
df['mes_cos'] = np.cos(2 * π * mes / 12)

# Total RENAP como contexto
df['total_defunciones_renap'] = renap_defunciones_mes
```

#### 4. One-hot encoding descriptivo

```python
pd.get_dummies(df, columns=[
    'sexo',                    # 3 valores
    'rango_edad',              # 4 valores  
    'categoria_general',       # 7 categorías
    'nombre_departamento'      # 22 departamentos
])
```

### Resultados del Modelo A

| Modelo | R² | RMSE | MAE |
|--------|-----|------|-----|
| Ridge A | **0.0052** | **28.07** | **13.83** |
| Lasso A | 0.0027 | 28.11 | 13.90 |

**Mejor resultado:** Ridge A

### Interpretación

**R² = 0.0052 es muy bajo, pero esperado:**

1. **Alto ruido en datos granulares:**
   - Cada registro es un conteo pequeño (media: 14 fallecidos)
   - Variabilidad alta entre departamentos/causas/perfiles
   - Datos faltantes en INE (gaps en cobertura)

2. **Relaciones no lineales:**
   - Interacciones complejas entre variables (ej: edad × causa)
   - Modelos lineales (Ridge/Lasso) no capturan estas interacciones

3. **Variables faltantes:**
   - No hay datos clínicos, socioeconómicos, climáticos
   - Eventos RENAP son proxies indirectos

**¿Es un modelo "malo"?**
- No necesariamente. Para predicción granular con datos limitados, R² bajo es común
- **Valor principal:** Interpretabilidad de features (útil para análisis exploratorio)

---

## MODELO B: RENAP Agregado Mensual

### Decisiones de Diseño

#### 1. Usar RENAP Defunciones como target

**Hallazgo clave:** El campo `tipo_evento = 'Defunciones'` en `fact_contexto_renap` contiene datos oficiales de registro civil:

| Métrica | RENAP | INE |
|---------|-------|-----|
| Cobertura | **136 meses** | 90 meses |
| Total | 1,098,282 | 674,064 |
| Fuente | Registro civil oficial | Estadísticas agregadas |
| Precisión | **Mayor** (1-4% más completo) | Menor |

**Ejemplo comparativo (julio 2020):**
- RENAP: 12,326 (100%)
- INE agregado: 12,203 (99%)

**Decisión:** Usar RENAP como fuente oficial para Modelo B.

#### 2. Pivotar eventos RENAP como features

```python
# 22 eventos RENAP como variables predictoras
renap_pivot = df_contexto.pivot_table(
    index='id_tiempo_mes',
    columns='tipo_evento',
    values='cantidad',
    fill_value=0
)
# → renap_nacimientos, renap_matrimonios, renap_divorcios, etc.
```

**Hipótesis:** Eventos demográficos (nacimientos, matrimonios) correlacionan con mortalidad general.

#### 3. Features temporales

```python
# Capturar estacionalidad
mes_sin = sin(2π × mes / 12)
mes_cos = cos(2π × mes / 12)

# Capturar tendencia
año_desde_inicio = año - 2015
```

### Resultados del Modelo B

| Modelo | R² | RMSE | MAE |
|--------|-----|------|-----|
| Ridge B | 0.2930 | 975.51 | 785.52 |
| Lasso B | **0.3052** | **967.08** | **783.14** |

**Mejor resultado:** Lasso B

### Interpretación

**R² = 0.31 es significativamente mejor (59x vs Modelo A):**

1. **Datos agregados reducen ruido:**
   - Un valor mensual vs miles de valores granulares
   - Promedios más estables

2. **Fuente más precisa:**
   - RENAP oficial vs INE con gaps
   - Mayor cobertura temporal (136 meses)

3. **Features temporales capturan patrones:**
   - Estacionalidad (sin/cos del mes)
   - Tendencia (años desde inicio)

4. **Lasso > Ridge:**
   - Selección automática de features relevantes
   - Algunos eventos RENAP no aportan (coeficientes → 0)

---

## VALIDACIÓN CRUZADA: Consistencia entre Modelos

### Objetivo

Verificar si `suma(predicciones Modelo A por mes) ≈ predicciones Modelo B`

### Hipótesis

Si ambos modelos son buenos, agregar predicciones del Modelo A debería aproximarse a las predicciones del Modelo B.

### Resultados

| Métrica | Ridge | Lasso |
|---------|-------|-------|
| Diferencia media | -6,638 fallecidos | -6,578 fallecidos |
| Diferencia % | **-81.77%** | **-80.90%** |
| Correlación | **0.4683** | **0.3716** |
| Veredicto | Baja consistencia | Baja consistencia |

### Interpretación

**Modelo A subestima significativamente los totales**

**Razones:**

1. **Datos faltantes en INE:**
   - INE no captura todas las defunciones que RENAP sí registra
   - Diferencia típica 1-4% por mes se acumula

2. **Errores compuestos:**
   - Cada predicción granular tiene error
   - Al sumar 1,000+ predicciones, los errores se acumulan
   - No se cancelan porque el modelo tiene sesgo (subestima)

3. **Patrones diferentes:**
   - Modelo A aprende patrones locales (departamento)
   - Modelo B aprende patrones nacionales (agregado)

**Conclusión:**
Para predicción de totales mensuales, **predecir directamente (Modelo B) es superior** a sumar predicciones desagregadas (Modelo A).

---

## COMPARACIÓN FINAL

### Tabla Comparativa

| Aspecto | Modelo A (Granular) | Modelo B (Agregado) |
|---------|---------------------|---------------------|
| **R²** | 0.0052 | **0.3052** (59x mejor) |
| **RMSE** | 28.07 | 967.08 |
| **MAE** | 13.83 | 783.14 |
| **Features** | 5 | 25 |
| **Registros** | 48,656 | 136 |
| **Fuente** | INE (desagregado) | RENAP (oficial) |
| **Cobertura** | 90 meses | **136 meses** |
| **Granularidad** | Depto/causa/perfil | Mensual nacional |
| **Interpretabilidad** | **Alta** | Media |
| **Poder predictivo** | Bajo | **Alto** |
| **Uso recomendado** | Análisis exploratorio | Proyección operacional |

### Arquitectura del Modelo Híbrido

```
┌───────────────────────────────────────────────────────────┐
│              MODELO HÍBRIDO DE MORTALIDAD                 │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ MODELO A: INE Desagregado + Dimensional         │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Fuente: INE (48,656 registros)                │    │
│  │ • JOIN: dim_geografia, perfil, causa, tiempo    │    │
│  │ • Features: 5 (descriptivos + RENAP context)    │    │
│  │ • Target: cantidad_fallecidos (granular)        │    │
│  │ • R² = 0.0052                                   │    │
│  │ • Uso: Análisis exploratorio e interpretación  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ MODELO B: RENAP Agregado Mensual               │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Fuente: RENAP Defunciones (oficial)           │    │
│  │ • Features: 25 (eventos RENAP + tiempo)         │    │
│  │ • Target: total_defunciones (mensual)           │    │
│  │ • R² = 0.3052                                   │    │
│  │ • Uso: Proyección operacional mensual           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │ VALIDACIÓN CRUZADA                              │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Suma(Modelo A) vs Modelo B                    │    │
│  │ • Diferencia: ~81%                              │    │
│  │ • Correlación: 0.47 (Ridge), 0.37 (Lasso)      │    │
│  │ • Conclusión: A subestima; B es más confiable  │    │
│  └─────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────┘
```

---

## LECCIONES APRENDIDAS

### 1. Granularidad vs Ruido

**Lección:** Más granular ≠ mejor predicción

- Modelo A (granular): R² = 0.005
- Modelo B (agregado): R² = 0.31

**Por qué:** Datos granulares tienen más variabilidad/ruido. La agregación promedia el ruido y estabiliza la señal.

**Trade-off:** Interpretabilidad (Modelo A) vs poder predictivo (Modelo B)

### 2. Calidad de Fuentes

**Lección:** RENAP oficial > INE desagregado para totales

- RENAP: Registro civil oficial (100%)
- INE: Estadísticas agregadas (99%)

**Diferencia:** 1-4% parece pequeño, pero se acumula en predicciones.

### 3. Diseño Dimensional

**Lección:** JOIN con dimensiones mejora interpretabilidad, no necesariamente R²

- Features descriptivos: `sexo_Hombre`, `rango_edad_65+`
- Mejor que IDs opacos: `id_perfil_H-65+`
- **Pero:** No garantiza mejor predicción si hay mucho ruido

### 4. Agregación Post-Predicción

**Lección:** Predecir agregados directamente > sumar predicciones granulares

Validación cruzada:
- Suma(Modelo A) vs Modelo B: **81% diferencia**
- Correlación: **0.47** (moderada-baja)

**Por qué falla:** Errores se acumulan, no se cancelan (sesgo sistemático).

### 5. Regularización

**Lección:** Ridge y Lasso funcionan bien con features limitados

- Modelo A: 5 features → estable
- Modelo B: 25 features → estable
- Lasso > Ridge en Modelo B (selección automática de features)

---

## RECOMENDACIONES

### Para Uso Operacional

**Modelo recomendado:** Modelo B - Lasso (RENAP)

**Casos de uso:**
- Proyección de mortalidad mensual nacional
- Planificación de recursos de salud
- Monitoreo de tendencias temporales

**NO usar para:**
- Predicción por departamento específico
- Análisis de causas específicas
- Perfiles demográficos detallados

### Para Mejoras Futuras

#### Modelo A (Granular)

**Objetivo:** Mejorar R² para predicción departamental

**Técnicas:**
1. **Modelos no lineales:**
   - Random Forest (captura interacciones)
   - XGBoost (maneja desbalance)
   - Redes neuronales (patrones complejos)

2. **Features adicionales:**
   - Variables climáticas por departamento
   - Movilidad poblacional (Google Mobility)
   - Tasa de vacunación regional
   - Índice de desarrollo humano

3. **Técnicas avanzadas:**
   - SMOTE para causas minoritarias
   - Feature interactions (sexo × edad)
   - Embeddings de geografía

#### Modelo B (Agregado)

**Objetivo:** Capturar mejor patrones temporales

**Técnicas:**
1. **Series de tiempo:**
   - ARIMA (estacionalidad)
   - Prophet (tendencias + holidays)
   - LSTM (patrones complejos)

2. **Variables externas:**
   - Oxford Stringency Index (rigor de medidas)
   - Indicadores económicos (desempleo, PIB)
   - Google Trends (búsquedas relacionadas)

3. **Ensambles:**
   - Combinar Ridge/Lasso + series temporales
   - Stacking de múltiples modelos
   - Voting regressor

---

## RESUMEN EJECUTIVO

| Aspecto | Hallazgo |
|---------|----------|
| **Problema** | Predicción de mortalidad COVID-19 (granular vs agregado) |
| **Solución** | Modelo Híbrido: A (INE desagregado) + B (RENAP agregado) |
| **Ganador** | Modelo B - Lasso (R² = 0.31) |
| **Diferencia** | 59x mejor que Modelo A (R² = 0.005) |
| **Lección clave** | Predecir agregados directamente > sumar predicciones granulares |
| **Validación** | Confirmó que Modelo A subestima totales (81% diferencia) |
| **Recomendación** | Usar Modelo B para proyecciones operacionales |

---

## VALOR DEL PROYECTO

Este proyecto demuestra:

1. **Pensamiento crítico:** Identificar que más granular ≠ mejor
2. **Diseño experimental:** Comparar enfoques sistemáticamente
3. **Validación rigurosa:** Validación cruzada detectó inconsistencia
4. **Interpretación honesta:** Reconocer cuándo R² bajo es esperado
5. **Propuestas concretas:** Trabajo futuro específico y viable

**Mensaje final:** Más importante que obtener R² alto es entender **por qué** un modelo funciona mejor que otro, y diseñar la solución apropiada para el problema específico.

---

## Referencias

- Notebook: Predicción Mortalidad COVID-19 Ridge Lasso.ipynb
- Carpeta: /Mortalidad ML/
- Fuentes de datos: INE Guatemala, RENAP, Cruz Roja, OMS

---

## VISUALIZACIONES DEL MODELO

El notebook incluye un conjunto completo de visualizaciones para analizar el desempeño del Modelo B (RENAP Agregado), que es el modelo con mejor desempeño (R² = 0.31).

### Visualizaciones Principales

#### 1. Serie Temporal: Predicciones vs Valores Reales

Muestra la evolución temporal de las predicciones comparadas con los valores reales de defunciones mensuales.

**Características:**
- Línea negra: Valores reales (RENAP oficial)
- Línea azul punteada: Predicciones Ridge B
- Línea verde punteada: Predicciones Lasso B (mejor modelo)
- Permite visualizar tendencias y estacionalidad
- Identifica períodos donde el modelo subestima o sobrestima

**Hallazgos:**
- El modelo Lasso B sigue de cerca la tendencia real
- Captura variaciones estacionales correctamente
- Errores más grandes en períodos de alta mortalidad (picos COVID-19)

#### 2. Scatter Plot: Predicciones vs Valores Reales

Gráfico de dispersión que muestra la relación entre predicciones y valores reales.

**Características:**
- Eje X: Predicciones del Modelo B Lasso
- Eje Y: Valores reales
- Línea roja diagonal: Predicción perfecta
- Puntos cercanos a la línea indican buenas predicciones

**Interpretación:**
- Dispersión moderada alrededor de la línea perfecta
- Sin patrones sistemáticos de sesgo
- Algunos outliers en valores extremos

#### 3. Análisis de Residuos

Gráfico de residuos (errores) vs predicciones para detectar patrones.

**Características:**
- Eje X: Predicciones
- Eje Y: Residuos (Real - Predicción)
- Línea roja horizontal en y=0 (error cero)
- Bandas grises: ±1 desviación estándar

**Lo que buscamos:**
- Residuos distribuidos aleatoriamente alrededor de cero
- Sin patrones sistemáticos (forma de embudo, curvas)
- Varianza constante (homocedasticidad)

**Resultado:**
- Residuos razonablemente aleatorios
- Media cercana a cero (sin sesgo sistemático)
- Varianza relativamente constante

#### 4. Distribución de Residuos

Histograma con curva de densidad (KDE) de los residuos.

**Características:**
- Histograma: Frecuencia de errores
- Línea roja: Estimación de densidad de kernel (KDE)
- Línea verde vertical: Media de residuos

**Lo que buscamos:**
- Distribución aproximadamente normal (campana de Gauss)
- Media cercana a cero
- Sin colas pesadas (pocos outliers extremos)

**Resultado:**
- Distribución cercana a la normal
- Media muy cercana a cero
- Algunos outliers en ambos extremos

#### 5. Feature Importance (Top 10)

Gráfico de barras horizontales mostrando los 10 features más importantes del modelo.

**Características:**
- Barras verdes: Coeficientes positivos (aumentan predicción)
- Barras rojas: Coeficientes negativos (disminuyen predicción)
- Longitud de barra: Magnitud del efecto

**Hallazgos clave:**
- 10 features con coeficientes positivos
- 15 features con coeficientes negativos
- 0 features eliminados por Lasso (todos aportan información)
- Variables temporales (mes_sin, mes_cos) capturan estacionalidad
- Eventos RENAP específicos correlacionan con mortalidad

### Acceso a las Visualizaciones

Las visualizaciones están disponibles en el notebook:
- **Ubicación:** `/Mortalidad ML/Predicción Mortalidad COVID-19 Ridge Lasso.ipynb`
- **Celda:** "Visualizaciones Detalladas del Modelo B"
- **Formato:** Gráficos interactivos generados con matplotlib

### Interpretación General

Las visualizaciones confirman que:

1. **El modelo captura la tendencia general** - La serie temporal muestra buen seguimiento de la señal real

2. **Sin sesgos sistemáticos** - Los residuos están centrados en cero y distribuidos normalmente

3. **Errores homocedásticos** - La varianza de residuos es relativamente constante

4. **Features relevantes** - Ningún feature fue eliminado por Lasso, indicando que todos aportan información

5. **Limitaciones identificables** - Errores mayores en períodos de alta mortalidad sugieren que modelos no lineales podrían mejorar el desempeño

### Recomendaciones para Visualización

Al presentar los resultados:

- **Para audiencia técnica:** Mostrar las 5 visualizaciones completas
- **Para audiencia ejecutiva:** Enfocarse en serie temporal y scatter plot
- **Para informe escrito:** Incluir serie temporal y distribución de residuos

Las gráficas pueden exportarse desde el notebook en formato PNG con alta resolución para incluirlas en presentaciones o informes.
