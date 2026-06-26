# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# === PREDICCIÓN DE MORTALIDAD COVID-19 CON RIDGE Y LASSO ===

# 1. IMPORTAR LIBRERÍAS
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

print("="*70)
print("MODELO DE PREDICCIÓN DE MORTALIDAD COVID-19")
print("Técnicas: Ridge Regression vs Lasso Regression")
print("="*70)

# 2. CARGAR DATOS
print("\n[1/8] Cargando datos...")
df_mortalidad = spark.table("covid19.gold.covid19_gold_fact_mortalidad_unificada").toPandas()
df_contexto = spark.table("covid19.gold.covid19_gold_fact_contexto_renap").toPandas()

print(f"  ✓ Mortalidad: {df_mortalidad.shape[0]:,} registros")
print(f"  ✓ Contexto RENAP: {df_contexto.shape[0]:,} registros")

# 3. PREPARAR DATOS DE CONTEXTO (PIVOT)
print("\n[2/8] Pivotando datos de contexto RENAP...")
df_contexto_pivot = df_contexto.pivot_table(
    index='id_tiempo_mes',
    columns='tipo_evento',
    values='cantidad',
    aggfunc='sum',
    fill_value=0
).reset_index()

df_contexto_pivot.columns = ['id_tiempo_mes'] + [f'renap_{col.replace(" ", "_").lower()}' for col in df_contexto_pivot.columns[1:]]
print(f"  ✓ {df_contexto_pivot.shape[1]-1} variables RENAP creadas")

# 4. UNIR DATOS Y FEATURE ENGINEERING
print("\n[3/8] Uniendo datos y creando features...")
df = df_mortalidad.merge(df_contexto_pivot, on='id_tiempo_mes', how='left')
renap_cols = [col for col in df.columns if col.startswith('renap_')]
df[renap_cols] = df[renap_cols].fillna(0)
df['año'] = df['id_tiempo_mes'].str[:4].astype(int)
df['mes'] = df['id_tiempo_mes'].str[5:7].astype(int)
df_encoded = pd.get_dummies(df, columns=['id_geografia', 'id_perfil', 'id_causa'], drop_first=False)
print(f"  ✓ Dataset final: {df_encoded.shape[0]:,} registros, {df_encoded.shape[1]} features")

# 5. PREPARAR X E Y
print("\n[4/8] Preparando features y target...")
columnas_excluir = ['id_tiempo_mes', 'fuente', 'fecha_actualizacion', 'cantidad_fallecidos']
feature_cols = [col for col in df_encoded.columns if col not in columnas_excluir]
X = df_encoded[feature_cols].select_dtypes(include=[np.number])
y = df_encoded['cantidad_fallecidos']
print(f"  ✓ {X.shape[1]} features seleccionados")
print(f"  ✓ Target → Media: {y.mean():.2f}, Min: {y.min()}, Max: {y.max()}")

# 6. TRAIN/TEST SPLIT
print("\n[5/8] Dividiendo datos (80% train / 20% test)...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print(f"  ✓ Train: {X_train.shape[0]:,} registros")
print(f"  ✓ Test:  {X_test.shape[0]:,} registros")

# 7. ENTRENAR MODELOS
print("\n[6/8] Entrenando modelos...")
ridge_model = Ridge(alpha=1.0, random_state=42)
ridge_model.fit(X_train_scaled, y_train)
y_pred_ridge = ridge_model.predict(X_test_scaled)
print("  ✓ Ridge entrenado")

lasso_model = Lasso(alpha=1.0, random_state=42)
lasso_model.fit(X_train_scaled, y_train)
y_pred_lasso = lasso_model.predict(X_test_scaled)
print("  ✓ Lasso entrenado")

# 8. EVALUAR Y COMPARAR
print("\n[7/8] Evaluando modelos...")
rmse_ridge = np.sqrt(mean_squared_error(y_test, y_pred_ridge))
r2_ridge = r2_score(y_test, y_pred_ridge)
mae_ridge = mean_absolute_error(y_test, y_pred_ridge)
rmse_lasso = np.sqrt(mean_squared_error(y_test, y_pred_lasso))
r2_lasso = r2_score(y_test, y_pred_lasso)
mae_lasso = mean_absolute_error(y_test, y_pred_lasso)

resultados = pd.DataFrame({
    'Modelo': ['Ridge', 'Lasso'],
    'RMSE': [rmse_ridge, rmse_lasso],
    'R²': [r2_ridge, r2_lasso],
    'MAE': [mae_ridge, mae_lasso]
})

print("\n" + "="*70)
print("RESULTADOS - COMPARACIÓN DE MODELOS")
print("="*70)
display(resultados)

mejor_modelo = 'Ridge' if r2_ridge > r2_lasso else 'Lasso'
mejor_r2 = max(r2_ridge, r2_lasso)
print(f"\n🏆 MEJOR MODELO: {mejor_modelo} (R² = {mejor_r2:.4f})")

# 9. VISUALIZACIONES
print("\n[8/8] Generando visualizaciones...")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].scatter(y_test, y_pred_ridge, alpha=0.5, s=20)
axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
axes[0].set_xlabel('Valores Reales', fontsize=11)
axes[0].set_ylabel('Predicciones', fontsize=11)
axes[0].set_title(f'Ridge - R² = {r2_ridge:.4f}, RMSE = {rmse_ridge:.2f}', fontsize=12, fontweight='bold')
axes[0].grid(True, alpha=0.3)

axes[1].scatter(y_test, y_pred_lasso, alpha=0.5, s=20, color='orange')
axes[1].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
axes[1].set_xlabel('Valores Reales', fontsize=11)
axes[1].set_ylabel('Predicciones', fontsize=11)
axes[1].set_title(f'Lasso - R² = {r2_lasso:.4f}, RMSE = {rmse_lasso:.2f}', fontsize=12, fontweight='bold')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Gráfico 2: Top Features
best_model = ridge_model if r2_ridge > r2_lasso else lasso_model
model_name = 'Ridge' if r2_ridge > r2_lasso else 'Lasso'

coef_df = pd.DataFrame({'Feature': X.columns, 'Coeficiente': best_model.coef_})
coef_df['Abs_Coef'] = np.abs(coef_df['Coeficiente'])
coef_df_top = coef_df.sort_values('Abs_Coef', ascending=False).head(15)

plt.figure(figsize=(10, 6))
plt.barh(range(len(coef_df_top)), coef_df_top['Coeficiente'], 
         color=['green' if x > 0 else 'red' for x in coef_df_top['Coeficiente']])
plt.yticks(range(len(coef_df_top)), coef_df_top['Feature'], fontsize=9)
plt.xlabel('Coeficiente', fontsize=11)
plt.title(f'Top 15 Features más Importantes - Modelo {model_name}', fontsize=12, fontweight='bold')
plt.axvline(x=0, color='black', linestyle='--', linewidth=0.8)
plt.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.show()

print("\n" + "="*70)
print("✓ ANÁLISIS COMPLETADO")
print("="*70)

