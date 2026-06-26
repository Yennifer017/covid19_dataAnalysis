# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,📋 Modelo Híbrido - Documentación
# MAGIC %md
# MAGIC # 🔄 MODELO HÍBRIDO: Diseño Dimensional Mejorado
# MAGIC
# MAGIC ## Estrategia de Implementación
# MAGIC
# MAGIC ### **Modelo A: INE Desagregado (Granular)**
# MAGIC - **Fuente**: INE (filtrado)
# MAGIC - **JOIN**: Con todas las dimensiones (geografía, perfil, causa, tiempo)
# MAGIC - **Features**: Descriptivos (sexo, rango_edad, categoria_general, departamento) + RENAP total
# MAGIC - **Target**: cantidad_fallecidos (por registro desagregado)
# MAGIC - **Objetivo**: Predecir mortalidad granular por departamento/causa/perfil
# MAGIC
# MAGIC ### **Modelo B: RENAP Agregado (Total Mensual)**
# MAGIC - **Fuente**: RENAP Defunciones
# MAGIC - **Features**: Eventos RENAP (nacimientos, matrimonios, etc.) + tiempo
# MAGIC - **Target**: total_defunciones_renap (mensual)
# MAGIC - **Objetivo**: Predecir total mensual nacional
# MAGIC
# MAGIC ### **Validación Cruzada**
# MAGIC - Agregar predicciones del Modelo A por mes
# MAGIC - Comparar con predicciones del Modelo B
# MAGIC - Calcular error entre ambos enfoques
# MAGIC - Verificar consistencia
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Características del Modelo Híbrido
# MAGIC
# MAGIC ### Modelo A (INE Desagregado)
# MAGIC - ✅ Fuente: Solo INE (filtrado, sin mezclas)
# MAGIC - ✅ Dimensiones: JOIN completo con dim_geografia, dim_perfil, dim_causa, dim_tiempo
# MAGIC - ✅ Features: Descriptivos (sexo, rango_edad, categoria_general, departamento)
# MAGIC - ✅ Flag COVID: es_covid como feature binaria
# MAGIC - ✅ RENAP: Total defunciones mensual como contexto
# MAGIC
# MAGIC ### Modelo B (RENAP Agregado)
# MAGIC - ✅ Fuente: RENAP oficial (registro civil)
# MAGIC - ✅ Features: 22 eventos RENAP + variables temporales (25 total)
# MAGIC - ✅ Target: total_defunciones (precisión oficial)
# MAGIC - ✅ Cobertura: 136 meses históricos

# COMMAND ----------

# DBTITLE 1,Importaciones para Modelo Híbrido
# Importaciones necesarias para el Modelo Híbrido
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

print("✓ Librerías importadas para Modelo Híbrido")

# COMMAND ----------

# DBTITLE 1,Modelo A: INE Desagregado con Dimensiones
# === MODELO A: INE DESAGREGADO CON DISEÑO DIMENSIONAL ===

print("\n" + "="*70)
print("MODELO A: INE DESAGREGADO + DIMENSIONES")
print("="*70)

# 1. CARGAR DATOS FILTRADOS (SOLO INE)
print("\n[A1] Cargando datos INE y dimensiones...")
df_mortalidad_ine = spark.sql("""
    SELECT * 
    FROM covid19.gold.covid19_gold_fact_mortalidad_unificada
    WHERE fuente = 'INE'
""").toPandas()

dim_geografia = spark.table("covid19.gold.covid19_gold_dim_geografia").toPandas()
dim_perfil = spark.table("covid19.gold.covid19_gold_dim_perfil").toPandas()
dim_causa = spark.table("covid19.gold.covid19_gold_dim_causa_muerte").toPandas()
dim_tiempo = spark.table("covid19.silver.covid19_gold_dim_tiempo").toPandas()

print(f"  ✓ Mortalidad INE: {df_mortalidad_ine.shape[0]:,} registros")
print(f"  ✓ Geografía: {dim_geografia.shape[0]} departamentos")
print(f"  ✓ Perfil: {dim_perfil.shape[0]} perfiles (sexo x edad)")
print(f"  ✓ Causa: {dim_causa.shape[0]} causas de muerte")
print(f"  ✓ Tiempo: {dim_tiempo.shape[0]} períodos")

# 2. AGREGAR RENAP DEFUNCIONES (TOTAL MENSUAL)
print("\n[A2] Agregando RENAP Defunciones como feature...")
renap_defunciones = spark.sql("""
    SELECT id_tiempo_mes, cantidad as total_defunciones_renap
    FROM covid19.gold.covid19_gold_fact_contexto_renap
    WHERE tipo_evento = 'Defunciones'
""").toPandas()

print(f"  ✓ RENAP Defunciones: {renap_defunciones.shape[0]} meses")

# 3. JOIN CON TODAS LAS DIMENSIONES
print("\n[A3] Haciendo JOIN dimensional...")
df_a = df_mortalidad_ine\
    .merge(dim_geografia, on='id_geografia', how='left')\
    .merge(dim_perfil, on='id_perfil', how='left')\
    .merge(dim_causa, on='id_causa', how='left')\
    .merge(dim_tiempo, on='id_tiempo_mes', how='left')\
    .merge(renap_defunciones, on='id_tiempo_mes', how='left')

df_a['total_defunciones_renap'] = df_a['total_defunciones_renap'].fillna(0)

print(f"  ✓ Dataset con dimensiones: {df_a.shape[0]:,} registros, {df_a.shape[1]} columnas")

# 4. FEATURE ENGINEERING DIMENSIONAL
print("\n[A4] Feature engineering dimensional...")
df_a['es_covid_int'] = df_a['es_covid'].astype(int)
df_a['mes_sin'] = np.sin(2 * np.pi * df_a['mes'] / 12)
df_a['mes_cos'] = np.cos(2 * np.pi * df_a['mes'] / 12)

print(f"  ✓ Flag COVID creado (es_covid_int)")
print(f"  ✓ Encoding circular de mes (sin/cos)")

# 5. ONE-HOT ENCODING DE CATEGORÍAS DESCRIPTIVAS
print("\n[A5] One-hot encoding de categorías descriptivas...")
df_a_encoded = pd.get_dummies(df_a, columns=[
    'sexo', 
    'rango_edad', 
    'categoria_general',
    'nombre_departamento'
], drop_first=False)

print(f"  ✓ Dataset encoded: {df_a_encoded.shape[1]} features totales")

# 6. PREPARAR X e Y
print("\n[A6] Preparando features y target...")
cols_excluir_a = ['id_tiempo_mes', 'id_geografia', 'id_perfil', 'id_causa', 
                  'fuente', 'fecha_actualizacion', 'cantidad_fallecidos',
                  'pais', 'id_departamento', 'nombre_causa', 'es_covid',
                  'anio', 'nombre_mes', 'periodo']

feature_cols_a = [col for col in df_a_encoded.columns if col not in cols_excluir_a]
X_a = df_a_encoded[feature_cols_a].select_dtypes(include=[np.number])
y_a = df_a_encoded['cantidad_fallecidos']

print(f"  ✓ Features finales: {X_a.shape[1]}")
print(f"  ✓ Target → Media: {y_a.mean():.2f}, Min: {y_a.min()}, Max: {y_a.max()}")

# 7. TRAIN/TEST SPLIT Y NORMALIZACIÓN
print("\n[A7] Train/Test split (80/20)...")
X_a_train, X_a_test, y_a_train, y_a_test = train_test_split(
    X_a, y_a, test_size=0.2, random_state=42
)

scaler_a = StandardScaler()
X_a_train_scaled = scaler_a.fit_transform(X_a_train)
X_a_test_scaled = scaler_a.transform(X_a_test)

print(f"  ✓ Train: {X_a_train.shape[0]:,}")
print(f"  ✓ Test: {X_a_test.shape[0]:,}")

# 8. ENTRENAR RIDGE Y LASSO
print("\n[A8] Entrenando Ridge y Lasso...")
ridge_a = Ridge(alpha=1.0, random_state=42)
ridge_a.fit(X_a_train_scaled, y_a_train)
y_pred_ridge_a = ridge_a.predict(X_a_test_scaled)

lasso_a = Lasso(alpha=1.0, random_state=42)
lasso_a.fit(X_a_train_scaled, y_a_train)
y_pred_lasso_a = lasso_a.predict(X_a_test_scaled)

print("  ✓ Ridge A entrenado")
print("  ✓ Lasso A entrenado")

# 9. MÉTRICAS MODELO A
print("\n[A9] Evaluando Modelo A...")
rmse_ridge_a = np.sqrt(mean_squared_error(y_a_test, y_pred_ridge_a))
r2_ridge_a = r2_score(y_a_test, y_pred_ridge_a)
mae_ridge_a = mean_absolute_error(y_a_test, y_pred_ridge_a)

rmse_lasso_a = np.sqrt(mean_squared_error(y_a_test, y_pred_lasso_a))
r2_lasso_a = r2_score(y_a_test, y_pred_lasso_a)
mae_lasso_a = mean_absolute_error(y_a_test, y_pred_lasso_a)

resultados_a = pd.DataFrame({
    'Modelo': ['Ridge A', 'Lasso A'],
    'RMSE': [rmse_ridge_a, rmse_lasso_a],
    'R²': [r2_ridge_a, r2_lasso_a],
    'MAE': [mae_ridge_a, mae_lasso_a]
})

print("\n" + "="*70)
print("RESULTADOS MODELO A (INE DESAGREGADO)")
print("="*70)
display(resultados_a)

mejor_a = 'Ridge A' if r2_ridge_a > r2_lasso_a else 'Lasso A'
print(f"\n🏆 Mejor en Modelo A: {mejor_a} (R² = {max(r2_ridge_a, r2_lasso_a):.4f})")

# 10. GUARDAR PARA VALIDACIÓN CRUZADA
test_indices_a = X_a_test.index
df_test_a = df_a_encoded.loc[test_indices_a, ['id_tiempo_mes', 'cantidad_fallecidos']].copy()
df_test_a['pred_ridge_a'] = y_pred_ridge_a
df_test_a['pred_lasso_a'] = y_pred_lasso_a

print(f"\n✓ Datos de test guardados para validación cruzada")

# COMMAND ----------

# DBTITLE 1,Modelo B: RENAP Agregado Mensual
# === MODELO B: RENAP AGREGADO MENSUAL ===

print("\n" + "="*70)
print("MODELO B: RENAP AGREGADO (TOTAL MENSUAL)")
print("="*70)

# 1. CARGAR DATOS RENAP AGREGADOS
print("\n[B1] Cargando datos RENAP agregados...")
df_renap_base = spark.sql("""
    SELECT 
        r.id_tiempo_mes,
        r.cantidad as total_defunciones,
        t.anio,
        t.mes,
        t.nombre_mes
    FROM covid19.gold.covid19_gold_fact_contexto_renap r
    JOIN covid19.silver.covid19_gold_dim_tiempo t 
        ON r.id_tiempo_mes = t.id_tiempo_mes
    WHERE r.tipo_evento = 'Defunciones'
    ORDER BY r.id_tiempo_mes
""").toPandas()

print(f"  ✓ RENAP Defunciones: {df_renap_base.shape[0]} meses")
print(f"  ✓ Total defunciones: {df_renap_base['total_defunciones'].sum():,}")

# 2. AGREGAR EVENTOS RENAP COMO FEATURES
print("\n[B2] Pivotando todos los eventos RENAP...")
df_contexto_completo = spark.table("covid19.gold.covid19_gold_fact_contexto_renap").toPandas()

renap_pivot_b = df_contexto_completo.pivot_table(
    index='id_tiempo_mes',
    columns='tipo_evento',
    values='cantidad',
    aggfunc='sum',
    fill_value=0
).reset_index()

renap_pivot_b.columns = ['id_tiempo_mes'] + [f'renap_{col.replace(" ", "_").lower()}' for col in renap_pivot_b.columns[1:]]
print(f"  ✓ {renap_pivot_b.shape[1]-1} eventos RENAP como features")

# 3. UNIR DATOS
print("\n[B3] Uniendo datos...")
df_b = df_renap_base.merge(renap_pivot_b, on='id_tiempo_mes', how='left')
renap_feature_cols = [col for col in df_b.columns if col.startswith('renap_')]

# Eliminar 'renap_defunciones' si existe (es el target)
if 'renap_defunciones' in renap_feature_cols:
    renap_feature_cols.remove('renap_defunciones')
    df_b = df_b.drop(columns=['renap_defunciones'])

df_b[renap_feature_cols] = df_b[renap_feature_cols].fillna(0)

print(f"  ✓ Dataset B: {df_b.shape[0]} meses, {df_b.shape[1]} columnas")

# 4. FEATURE ENGINEERING TEMPORAL
print("\n[B4] Feature engineering temporal...")
df_b['mes_sin'] = np.sin(2 * np.pi * df_b['mes'] / 12)
df_b['mes_cos'] = np.cos(2 * np.pi * df_b['mes'] / 12)
df_b['año_desde_inicio'] = df_b['anio'] - df_b['anio'].min()

print(f"  ✓ Encoding circular de mes")
print(f"  ✓ Años desde inicio: {df_b['año_desde_inicio'].min()} - {df_b['año_desde_inicio'].max()}")

# 5. PREPARAR X e Y
print("\n[B5] Preparando features y target...")
cols_excluir_b = ['id_tiempo_mes', 'total_defunciones', 'anio', 'nombre_mes']
feature_cols_b = [col for col in df_b.columns if col not in cols_excluir_b]

X_b = df_b[feature_cols_b].select_dtypes(include=[np.number])
y_b = df_b['total_defunciones']

print(f"  ✓ Features: {X_b.shape[1]}")
print(f"  ✓ Target → Media: {y_b.mean():.2f}, Min: {y_b.min()}, Max: {y_b.max()}")

# 6. TRAIN/TEST SPLIT (mismo random_state para consistencia)
print("\n[B6] Train/Test split (80/20)...")
X_b_train, X_b_test, y_b_train, y_b_test = train_test_split(
    X_b, y_b, test_size=0.2, random_state=42
)

scaler_b = StandardScaler()
X_b_train_scaled = scaler_b.fit_transform(X_b_train)
X_b_test_scaled = scaler_b.transform(X_b_test)

print(f"  ✓ Train: {X_b_train.shape[0]} meses")
print(f"  ✓ Test: {X_b_test.shape[0]} meses")

# 7. ENTRENAR RIDGE Y LASSO
print("\n[B7] Entrenando Ridge y Lasso...")
ridge_b = Ridge(alpha=1.0, random_state=42)
ridge_b.fit(X_b_train_scaled, y_b_train)
y_pred_ridge_b = ridge_b.predict(X_b_test_scaled)

lasso_b = Lasso(alpha=1.0, random_state=42)
lasso_b.fit(X_b_train_scaled, y_b_train)
y_pred_lasso_b = lasso_b.predict(X_b_test_scaled)

print("  ✓ Ridge B entrenado")
print("  ✓ Lasso B entrenado")

# 8. MÉTRICAS MODELO B
print("\n[B8] Evaluando Modelo B...")
rmse_ridge_b = np.sqrt(mean_squared_error(y_b_test, y_pred_ridge_b))
r2_ridge_b = r2_score(y_b_test, y_pred_ridge_b)
mae_ridge_b = mean_absolute_error(y_b_test, y_pred_ridge_b)

rmse_lasso_b = np.sqrt(mean_squared_error(y_b_test, y_pred_lasso_b))
r2_lasso_b = r2_score(y_b_test, y_pred_lasso_b)
mae_lasso_b = mean_absolute_error(y_b_test, y_pred_lasso_b)

resultados_b = pd.DataFrame({
    'Modelo': ['Ridge B', 'Lasso B'],
    'RMSE': [rmse_ridge_b, rmse_lasso_b],
    'R²': [r2_ridge_b, r2_lasso_b],
    'MAE': [mae_ridge_b, mae_lasso_b]
})

print("\n" + "="*70)
print("RESULTADOS MODELO B (RENAP AGREGADO)")
print("="*70)
display(resultados_b)

mejor_b = 'Ridge B' if r2_ridge_b > r2_lasso_b else 'Lasso B'
print(f"\n🏆 Mejor en Modelo B: {mejor_b} (R² = {max(r2_ridge_b, r2_lasso_b):.4f})")

# 9. GUARDAR PARA VALIDACIÓN CRUZADA
test_indices_b = X_b_test.index
df_test_b = df_b.loc[test_indices_b, ['id_tiempo_mes', 'total_defunciones']].copy()
df_test_b['pred_ridge_b'] = y_pred_ridge_b
df_test_b['pred_lasso_b'] = y_pred_lasso_b

print(f"\n✓ Datos de test guardados para validación cruzada")

# COMMAND ----------

# DBTITLE 1,Validación Cruzada: Modelo A vs Modelo B
# === VALIDACIÓN CRUZADA: SUMA(MODELO A) vs MODELO B ===

print("\n" + "="*70)
print("VALIDACIÓN CRUZADA: CONSISTENCIA ENTRE MODELOS")
print("="*70)

print("\nObjetivo: Verificar que suma(predicciones Modelo A) ≈ predicciones Modelo B")

# 1. AGREGAR PREDICCIONES DEL MODELO A POR MES
print("\n[V1] Agregando predicciones del Modelo A por mes...")
aggregado_a = df_test_a.groupby('id_tiempo_mes').agg({
    'cantidad_fallecidos': 'sum',
    'pred_ridge_a': 'sum',
    'pred_lasso_a': 'sum'
}).reset_index()

aggregado_a.columns = ['id_tiempo_mes', 'real_sum_a', 'pred_ridge_sum_a', 'pred_lasso_sum_a']
print(f"  ✓ {aggregado_a.shape[0]} meses en test del Modelo A")

# 2. UNIR CON PREDICCIONES DEL MODELO B
print("\n[V2] Comparando con predicciones del Modelo B...")
comparacion = aggregado_a.merge(
    df_test_b[['id_tiempo_mes', 'total_defunciones', 'pred_ridge_b', 'pred_lasso_b']], 
    on='id_tiempo_mes', 
    how='inner'
)

print(f"  ✓ {comparacion.shape[0]} meses comunes en ambos tests")

# 3. CALCULAR DIFERENCIAS
print("\n[V3] Calculando diferencias...")
comparacion['diff_ridge'] = comparacion['pred_ridge_sum_a'] - comparacion['pred_ridge_b']
comparacion['diff_lasso'] = comparacion['pred_lasso_sum_a'] - comparacion['pred_lasso_b']
comparacion['diff_ridge_pct'] = 100 * comparacion['diff_ridge'] / comparacion['pred_ridge_b']
comparacion['diff_lasso_pct'] = 100 * comparacion['diff_lasso'] / comparacion['pred_lasso_b']

# 4. ESTADÍSTICAS DE VALIDACIÓN
print("\n" + "="*70)
print("ESTADÍSTICAS DE VALIDACIÓN CRUZADA")
print("="*70)

print("\n🔹 Ridge:")
print(f"  Diferencia media: {comparacion['diff_ridge'].mean():.2f} fallecidos")
print(f"  Diferencia absoluta media: {comparacion['diff_ridge'].abs().mean():.2f}")
print(f"  Diferencia % media: {comparacion['diff_ridge_pct'].mean():.2f}%")
print(f"  Diferencia % absoluta media: {comparacion['diff_ridge_pct'].abs().mean():.2f}%")

print("\n🔹 Lasso:")
print(f"  Diferencia media: {comparacion['diff_lasso'].mean():.2f} fallecidos")
print(f"  Diferencia absoluta media: {comparacion['diff_lasso'].abs().mean():.2f}")
print(f"  Diferencia % media: {comparacion['diff_lasso_pct'].mean():.2f}%")
print(f"  Diferencia % absoluta media: {comparacion['diff_lasso_pct'].abs().mean():.2f}%")

# 5. CORRELACIÓN ENTRE MODELOS
print("\n" + "="*70)
print("CORRELACIÓN ENTRE MODELOS A Y B")
print("="*70)

corr_ridge = np.corrcoef(comparacion['pred_ridge_sum_a'], comparacion['pred_ridge_b'])[0, 1]
corr_lasso = np.corrcoef(comparacion['pred_lasso_sum_a'], comparacion['pred_lasso_b'])[0, 1]

print(f"\nCorrelación Ridge (A vs B): {corr_ridge:.4f}")
print(f"Correlación Lasso (A vs B): {corr_lasso:.4f}")

if corr_ridge > 0.8 and corr_lasso > 0.8:
    print("\n✅ VALIDACIÓN EXITOSA: Alta consistencia entre modelos")
elif corr_ridge > 0.6 and corr_lasso > 0.6:
    print("\n⚠️ VALIDACIÓN PARCIAL: Consistencia moderada")
else:
    print("\n❌ VALIDACIÓN FALLIDA: Baja consistencia entre modelos")

# 6. VISUALIZACIÓN DE VALIDACIÓN
print("\n[V4] Generando visualizaciones de validación...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Gráfico 1: Ridge - Scatter
axes[0, 0].scatter(comparacion['pred_ridge_b'], comparacion['pred_ridge_sum_a'], alpha=0.6, s=50)
axes[0, 0].plot([comparacion['pred_ridge_b'].min(), comparacion['pred_ridge_b'].max()], 
                [comparacion['pred_ridge_b'].min(), comparacion['pred_ridge_b'].max()], 
                'r--', lw=2, label='Línea perfecta')
axes[0, 0].set_xlabel('Modelo B (RENAP agregado)', fontsize=10)
axes[0, 0].set_ylabel('Modelo A agregado (suma INE)', fontsize=10)
axes[0, 0].set_title(f'Ridge: Correlación = {corr_ridge:.4f}', fontsize=11, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Gráfico 2: Lasso - Scatter
axes[0, 1].scatter(comparacion['pred_lasso_b'], comparacion['pred_lasso_sum_a'], alpha=0.6, s=50, color='orange')
axes[0, 1].plot([comparacion['pred_lasso_b'].min(), comparacion['pred_lasso_b'].max()], 
                [comparacion['pred_lasso_b'].min(), comparacion['pred_lasso_b'].max()], 
                'r--', lw=2, label='Línea perfecta')
axes[0, 1].set_xlabel('Modelo B (RENAP agregado)', fontsize=10)
axes[0, 1].set_ylabel('Modelo A agregado (suma INE)', fontsize=10)
axes[0, 1].set_title(f'Lasso: Correlación = {corr_lasso:.4f}', fontsize=11, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Gráfico 3: Ridge - Diferencias
axes[1, 0].bar(range(len(comparacion)), comparacion['diff_ridge_pct'], alpha=0.7)
axes[1, 0].axhline(y=0, color='red', linestyle='--', linewidth=1)
axes[1, 0].set_xlabel('Mes (test set)', fontsize=10)
axes[1, 0].set_ylabel('Diferencia %', fontsize=10)
axes[1, 0].set_title(f'Ridge: Diferencia % (Media: {comparacion["diff_ridge_pct"].mean():.2f}%)', 
                     fontsize=11, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Gráfico 4: Lasso - Diferencias
axes[1, 1].bar(range(len(comparacion)), comparacion['diff_lasso_pct'], alpha=0.7, color='orange')
axes[1, 1].axhline(y=0, color='red', linestyle='--', linewidth=1)
axes[1, 1].set_xlabel('Mes (test set)', fontsize=10)
axes[1, 1].set_ylabel('Diferencia %', fontsize=10)
axes[1, 1].set_title(f'Lasso: Diferencia % (Media: {comparacion["diff_lasso_pct"].mean():.2f}%)', 
                     fontsize=11, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.show()

print("\n✓ Validación cruzada completada")

# COMMAND ----------

# DBTITLE 1,Comparación Final: Baseline vs Modelo Híbrido
# === COMPARACIÓN FINAL: MODELO A vs MODELO B ===

print("\n" + "="*70)
print("COMPARACIÓN FINAL: MODELO HÍBRIDO A vs B")
print("="*70)

# 1. CONSOLIDAR RESULTADOS
print("\n[F1] Consolidando resultados de ambos modelos...")

resultados_final = pd.DataFrame({
    'Modelo': [
        'Modelo A - Ridge (INE + Dim)',
        'Modelo A - Lasso (INE + Dim)',
        'Modelo B - Ridge (RENAP)',
        'Modelo B - Lasso (RENAP)'
    ],
    'Tipo': [
        'Híbrido A',
        'Híbrido A',
        'Híbrido B',
        'Híbrido B'
    ],
    'RMSE': [
        rmse_ridge_a,
        rmse_lasso_a,
        rmse_ridge_b,
        rmse_lasso_b
    ],
    'R²': [
        r2_ridge_a,
        r2_lasso_a,
        r2_ridge_b,
        r2_lasso_b
    ],
    'MAE': [
        mae_ridge_a,
        mae_lasso_a,
        mae_ridge_b,
        mae_lasso_b
    ],
    'Features': [
        X_a.shape[1],
        X_a.shape[1],
        X_b.shape[1],
        X_b.shape[1]
    ],
    'Registros': [
        X_a.shape[0],
        X_a.shape[0],
        X_b.shape[0],
        X_b.shape[0]
    ]
})

print("\n" + "="*70)
print("TABLA COMPARATIVA COMPLETA")
print("="*70)
display(resultados_final)

# 2. ANÁLISIS COMPARATIVO A vs B
print("\n" + "="*70)
print("COMPARACIÓN MODELO A vs MODELO B")
print("="*70)

# Mejor modelo en cada categoría
mejor_a = resultados_final[resultados_final['Tipo'] == 'Híbrido A'].sort_values('R²', ascending=False).iloc[0]
mejor_b = resultados_final[resultados_final['Tipo'] == 'Híbrido B'].sort_values('R²', ascending=False).iloc[0]

print("\n🏆 Mejor en cada categoría:")
print(f"  Modelo A (granular):   {mejor_a['Modelo']} (R² = {mejor_a['R²']:.4f})")
print(f"  Modelo B (agregado):   {mejor_b['Modelo']} (R² = {mejor_b['R²']:.4f})")

# Diferencia entre A y B
if mejor_b['R²'] > mejor_a['R²']:
    factor_mejora = mejor_b['R²'] / mejor_a['R²']
    print(f"\n📈 Modelo B supera a Modelo A:")
    print(f"  Factor de mejora: {factor_mejora:.1f}x")
    print(f"  Diferencia absoluta: {(mejor_b['R²'] - mejor_a['R²']):.4f}")
else:
    print(f"\n⚠️ Modelo A tiene mejor R², pero menor interpretabilidad en escala agregada")

# 3. COMPARACIÓN DE CARACTERÍSTICAS
print("\n" + "="*70)
print("COMPARACIÓN DE CARACTERÍSTICAS")
print("="*70)

comparacion_caracteristicas = pd.DataFrame({
    'Característica': [
        'Fuentes de datos',
        'Usa dimensiones',
        'One-hot encoding',
        'Flag es_covid',
        'RENAP Defunciones',
        'Granularidad',
        'Interpretabilidad',
        'Features totales',
        'Validación cruzada'
    ],
    'Modelo A (INE Desagregado)': [
        '✅ Solo INE (filtrado)',
        '✅ Sí (completo)',
        '✅ Descriptivo',
        '✅ Sí',
        '✅ Sí (feature)',
        'Desagregado (depto/causa/perfil)',
        'Alta',
        f'{X_a.shape[1]}',
        '✅ Sí (vs B)'
    ],
    'Modelo B (RENAP Agregado)': [
        '✅ RENAP oficial',
        'N/A (agregado)',
        'N/A',
        'N/A',
        '✅ Sí (target)',
        'Mensual agregado (nacional)',
        'Media',
        f'{X_b.shape[1]}',
        '✅ Sí (vs A)'
    ]
})

display(comparacion_caracteristicas)

# 4. VISUALIZACIÓN COMPARATIVA
print("\n[F2] Generando visualización comparativa...")

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Gráfico 1: R² Comparison
modelos_nombres = ['A\nRidge', 'A\nLasso', 'B\nRidge', 'B\nLasso']
r2_valores = resultados_final['R²'].values
colores = ['blue', 'blue', 'green', 'green']

axes[0].bar(range(len(modelos_nombres)), r2_valores, color=colores, alpha=0.7)
axes[0].set_xticks(range(len(modelos_nombres)))
axes[0].set_xticklabels(modelos_nombres, fontsize=9)
axes[0].set_ylabel('R²', fontsize=11)
axes[0].set_title('Comparación de R²', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3, axis='y')
axes[0].axhline(y=0, color='red', linestyle='--', linewidth=1)

# Gráfico 2: RMSE Comparison
rmse_valores = resultados_final['RMSE'].values

axes[1].bar(range(len(modelos_nombres)), rmse_valores, color=colores, alpha=0.7)
axes[1].set_xticks(range(len(modelos_nombres)))
axes[1].set_xticklabels(modelos_nombres, fontsize=9)
axes[1].set_ylabel('RMSE', fontsize=11)
axes[1].set_title('Comparación de RMSE (menor es mejor)', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')

# Gráfico 3: Features count
features_count = resultados_final['Features'].values

axes[2].bar(range(len(modelos_nombres)), features_count, color=colores, alpha=0.7)
axes[2].set_xticks(range(len(modelos_nombres)))
axes[2].set_xticklabels(modelos_nombres, fontsize=9)
axes[2].set_ylabel('Número de Features', fontsize=11)
axes[2].set_title('Complejidad del Modelo', fontsize=12, fontweight='bold')
axes[2].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.show()

# 5. RECOMENDACIÓN FINAL
print("\n" + "="*70)
print("🎯 RECOMENDACIÓN FINAL")
print("="*70)

mejor_global = resultados_final.sort_values('R²', ascending=False).iloc[0]

print(f"\n🏆 Mejor modelo global: {mejor_global['Modelo']}")
print(f"   R² = {mejor_global['R²']:.4f}")
print(f"   RMSE = {mejor_global['RMSE']:.2f}")
print(f"   MAE = {mejor_global['MAE']:.2f}")
print(f"   Features = {int(mejor_global['Features'])}")

if 'Modelo A' in mejor_global['Modelo']:
    print("\n✅ VENTAJAS DEL MODELO A (ganador):")
    print("   - Predicción granular (departamento/causa/perfil)")
    print("   - Features descriptivos e interpretables")
    print("   - Usa diseño dimensional completo")
    print("   - Incluye flag es_covid")
    print("   - Validado contra RENAP agregado")
elif 'Modelo B' in mejor_global['Modelo']:
    print("\n✅ VENTAJAS DEL MODELO B (ganador):")
    print("   - Usa fuente más precisa (RENAP oficial)")
    print("   - Predicción de total mensual nacional")
    print("   - Mayor cobertura temporal")
    print("   - Más simple y robusto")
else:
    print("\n✅ VENTAJAS DEL MODELO A (ganador):")
    print("   - Predicción granular (departamento/causa/perfil)")
    print("   - Features descriptivos e interpretables")
    print("   - Usa diseño dimensional completo")
    print("   - Incluye flag es_covid")
    print("   - Validado contra RENAP agregado")

print("\n" + "="*70)
print("✓ ANÁLISIS COMPLETO DEL MODELO HÍBRIDO FINALIZADO")
print("="*70)

# COMMAND ----------

# DBTITLE 1,Visualizaciones Detalladas del Modelo B
# === VISUALIZACIONES DETALLADAS: MODELO B (MEJOR RESULTADO) ===

print("\n" + "="*70)
print("VISUALIZACIONES DETALLADAS - MODELO B")
print("="*70)

# Preparar datos para visualización
df_viz_b = df_test_b.copy()
df_viz_b = df_viz_b.sort_values('id_tiempo_mes')

# Calcular residuos del mejor modelo (Lasso B)
df_viz_b['residuos_lasso'] = df_viz_b['total_defunciones'] - df_viz_b['pred_lasso_b']

print(f"\n[VIZ] Generando 4 visualizaciones para Modelo B Lasso...")

# Crear figura con 4 subplots
fig = plt.figure(figsize=(16, 12))

# ============================================================================
# 1. SERIE TEMPORAL: Predicciones vs Valores Reales
# ============================================================================
ax1 = plt.subplot(2, 2, 1)
ax1.plot(range(len(df_viz_b)), df_viz_b['total_defunciones'], 
         marker='o', linestyle='-', linewidth=2, markersize=5,
         label='Valores Reales (RENAP)', color='black', alpha=0.8)
ax1.plot(range(len(df_viz_b)), df_viz_b['pred_ridge_b'], 
         marker='s', linestyle='--', linewidth=1.5, markersize=4,
         label='Predicciones Ridge B', color='blue', alpha=0.7)
ax1.plot(range(len(df_viz_b)), df_viz_b['pred_lasso_b'], 
         marker='^', linestyle='--', linewidth=1.5, markersize=4,
         label='Predicciones Lasso B (Mejor)', color='green', alpha=0.7)

ax1.set_xlabel('Meses (Test Set)', fontsize=11)
ax1.set_ylabel('Total Defunciones', fontsize=11)
ax1.set_title('Serie Temporal: Predicciones vs Valores Reales\nModelo B (RENAP Agregado)', 
              fontsize=12, fontweight='bold')
ax1.legend(loc='best', fontsize=9)
ax1.grid(True, alpha=0.3)

# Agregar R² como texto
ax1.text(0.02, 0.98, f'R² Lasso B = {r2_lasso_b:.4f}',
         transform=ax1.transAxes, fontsize=10,
         verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# ============================================================================
# 2. SCATTER PLOT: Predicciones vs Reales (Lasso B)
# ============================================================================
ax2 = plt.subplot(2, 2, 2)
ax2.scatter(df_viz_b['pred_lasso_b'], df_viz_b['total_defunciones'], 
            alpha=0.6, s=80, color='green', edgecolors='black', linewidth=0.5)

# Línea de predicción perfecta
min_val = min(df_viz_b['pred_lasso_b'].min(), df_viz_b['total_defunciones'].min())
max_val = max(df_viz_b['pred_lasso_b'].max(), df_viz_b['total_defunciones'].max())
ax2.plot([min_val, max_val], [min_val, max_val], 
         'r--', linewidth=2, label='Predicción Perfecta', alpha=0.8)

ax2.set_xlabel('Predicciones (Lasso B)', fontsize=11)
ax2.set_ylabel('Valores Reales', fontsize=11)
ax2.set_title('Scatter Plot: Predicciones vs Valores Reales\nModelo B Lasso', 
              fontsize=12, fontweight='bold')
ax2.legend(loc='best', fontsize=9)
ax2.grid(True, alpha=0.3)

# Agregar métricas
ax2.text(0.02, 0.98, 
         f'R² = {r2_lasso_b:.4f}\nRMSE = {rmse_lasso_b:.2f}\nMAE = {mae_lasso_b:.2f}',
         transform=ax2.transAxes, fontsize=9,
         verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

# ============================================================================
# 3. ANÁLISIS DE RESIDUOS: Residuos vs Predicciones
# ============================================================================
ax3 = plt.subplot(2, 2, 3)
ax3.scatter(df_viz_b['pred_lasso_b'], df_viz_b['residuos_lasso'], 
            alpha=0.6, s=80, color='orange', edgecolors='black', linewidth=0.5)
ax3.axhline(y=0, color='red', linestyle='--', linewidth=2, label='Residuo = 0')

# Bandas de confianza
std_residuos = df_viz_b['residuos_lasso'].std()
ax3.axhline(y=std_residuos, color='gray', linestyle=':', linewidth=1.5, alpha=0.7)
ax3.axhline(y=-std_residuos, color='gray', linestyle=':', linewidth=1.5, alpha=0.7)
ax3.fill_between(ax3.get_xlim(), -std_residuos, std_residuos, 
                  alpha=0.1, color='gray', label='±1 Desv. Est.')

ax3.set_xlabel('Predicciones (Lasso B)', fontsize=11)
ax3.set_ylabel('Residuos (Real - Predicción)', fontsize=11)
ax3.set_title('Análisis de Residuos\nModelo B Lasso', 
              fontsize=12, fontweight='bold')
ax3.legend(loc='best', fontsize=9)
ax3.grid(True, alpha=0.3)

# Estadísticas de residuos
media_res = df_viz_b['residuos_lasso'].mean()
ax3.text(0.02, 0.98, 
         f'Media residuos = {media_res:.2f}\nDesv. Est. = {std_residuos:.2f}',
         transform=ax3.transAxes, fontsize=9,
         verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

# ============================================================================
# 4. DISTRIBUCIÓN DE RESIDUOS: Histograma + KDE
# ============================================================================
ax4 = plt.subplot(2, 2, 4)
ax4.hist(df_viz_b['residuos_lasso'], bins=15, 
         alpha=0.6, color='purple', edgecolor='black', density=True)

# Agregar KDE
from scipy import stats
kde = stats.gaussian_kde(df_viz_b['residuos_lasso'])
x_range = np.linspace(df_viz_b['residuos_lasso'].min(), 
                      df_viz_b['residuos_lasso'].max(), 100)
ax4.plot(x_range, kde(x_range), 'r-', linewidth=2, label='KDE')

# Línea vertical en media
ax4.axvline(x=media_res, color='green', linestyle='--', 
            linewidth=2, label=f'Media = {media_res:.2f}')

ax4.set_xlabel('Residuos', fontsize=11)
ax4.set_ylabel('Densidad', fontsize=11)
ax4.set_title('Distribución de Residuos\nModelo B Lasso', 
              fontsize=12, fontweight='bold')
ax4.legend(loc='best', fontsize=9)
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.show()

print("\n✓ Visualizaciones generadas")

# ============================================================================
# 5. FEATURE IMPORTANCE: Top 10 Coeficientes
# ============================================================================
print("\n[VIZ] Generando gráfico de Feature Importance...")

# Obtener coeficientes
coeficientes_lasso_b = lasso_b.coef_
feature_names_b = X_b.columns

# Crear DataFrame de importancia
importancia_df = pd.DataFrame({
    'Feature': feature_names_b,
    'Coeficiente': coeficientes_lasso_b,
    'Importancia_Abs': np.abs(coeficientes_lasso_b)
}).sort_values('Importancia_Abs', ascending=False)

# Top 10 features
top_10 = importancia_df.head(10)

# Gráfico
fig, ax = plt.subplots(figsize=(12, 6))
colors = ['green' if x > 0 else 'red' for x in top_10['Coeficiente']]
ax.barh(range(len(top_10)), top_10['Coeficiente'], color=colors, alpha=0.7, edgecolor='black')
ax.set_yticks(range(len(top_10)))
ax.set_yticklabels(top_10['Feature'], fontsize=10)
ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
ax.set_xlabel('Coeficiente (Lasso B)', fontsize=11)
ax.set_title('Top 10 Features más Importantes\nModelo B Lasso (RENAP Agregado)', 
             fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')

# Invertir eje Y para que el más importante esté arriba
ax.invert_yaxis()

plt.tight_layout()
plt.show()

print(f"\n✓ Feature Importance calculado ({len(importancia_df)} features totales)")
print(f"  - Features con coef. > 0: {(coeficientes_lasso_b > 0).sum()}")
print(f"  - Features con coef. = 0 (eliminados por Lasso): {(coeficientes_lasso_b == 0).sum()}")
print(f"  - Features con coef. < 0: {(coeficientes_lasso_b < 0).sum()}")

print("\n" + "="*70)
print("✓ VISUALIZACIONES DETALLADAS COMPLETADAS")
print("="*70)
