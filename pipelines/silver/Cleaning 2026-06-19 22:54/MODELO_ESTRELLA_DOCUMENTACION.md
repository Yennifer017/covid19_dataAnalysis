# 📊 Modelo Estrella - Análisis de Mortalidad COVID-19
## Documentación Principal del Pipeline

**Proyecto:** Análisis comparativo de mortalidad COVID-19 (Guatemala y Costa Rica)  
**Pipeline:** Lakeflow Spark Declarative Pipeline  
**Fecha:** Junio 2026  
**Equipo:** Wilson (INE/RENAP), Yeni (OMS), Byron (Costa Rica)

---

## 📂 Índice de Documentación

Esta documentación está organizada en módulos para facilitar la navegación:

* **[📊 Resumen Ejecutivo](docs/RESUMEN_EJECUTIVO.md)** - Métricas clave, estado del proyecto y hallazgos principales
* **[📋 Diccionario de Datos](docs/DICCIONARIO_DATOS.md)** - Definición completa de todas las tablas y columnas
* **[📝 Queries de Ejemplo](docs/QUERIES_EJEMPLO.md)** - 10+ queries listas para ejecutar con casos de uso reales
* **[🗺️ Mapeos y Transformaciones](docs/MAPEOS_TRANSFORMACIONES.md)** - Transformaciones Bronze→Silver→Gold detalladas

---

## 🎯 Resumen del Proyecto

### Estado Actual
✅ **COMPLETAMENTE OPERATIVO** - Modelo estrella funcional con 48,755 registros consolidados

### Métricas Clave
* **Registros totales:** 48,755 (consolidados de 3 fuentes)
* **Periodo:** 2015-2026 (144 meses)
* **Países:** Guatemala (departamental) + Costa Rica (nacional)
* **Total fallecidos:** 703,665 (todas las causas y fuentes)

### Cobertura por Fuente

| Fuente | Registros | Fallecidos | Periodo | Desglose |
|--------|-----------|------------|---------|----------|
| INE (Guatemala) | 48,656 | 674,064 | 2018-2025 | 22 departamentos, sexo, edad, todas causas |
| OMS (Guatemala) | 45 | 20,205 | 2020-2025 | Nacional, solo COVID-19 |
| CR (Costa Rica) | 54 | 9,396 | 2020-2026 | Nacional, solo COVID-19 |

---

## 📐 Arquitectura del Modelo Estrella

### Diseño General

```
                    ┌──────────────────┐
                    │   dim_tiempo     │
                    │  (144 meses)     │
                    └─────────┬────────┘
                              │
                              │
┌──────────────┐              │              ┌──────────────────┐
│ dim_geografia│              │              │  dim_perfil      │
│  (25 lugares)│◄─────────────┼─────────────►│  (12 perfiles)   │
└──────────────┘              │              └──────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │ fact_mortalidad_unificada   │
                │    (Tabla de Hechos)         │
                │   48,755 registros           │
                └─────────────┬───────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ dim_causa_muerte │
                    │   (48 causas)    │
                    └──────────────────┘

                    ┌──────────────────┐
                    │fact_contexto_renap│
                    │ (Eventos civiles) │
                    │   1,943 registros │
                    └──────────────────┘
```

### Tablas Implementadas

#### **Dimensiones (4)**
* `covid19.gold.covid19_gold_dim_tiempo` - 144 meses (2015-2026)
* `covid19.gold.covid19_gold_dim_geografia` - 25 lugares (GT + CR)
* `covid19.gold.covid19_gold_dim_perfil` - 12 perfiles demográficos
* `covid19.gold.covid19_gold_dim_causa_muerte` - 48 causas de muerte

#### **Hechos Parciales (3)**
* `covid19.gold.covid19_gold_fact_parcial_ine` - 48,656 registros ✅
* `covid19.gold.covid19_gold_fact_parcial_oms` - 45 registros ✅
* `covid19.gold.covid19_gold_fact_parcial_costa_rica` - 54 registros ✅

#### **Consolidación (1)**
* `covid19.gold.covid19_gold_fact_mortalidad_unificada` - 48,755 registros ✅

#### **Contexto (1)**
* `covid19.gold.covid19_gold_fact_contexto_renap` - 1,943 registros ✅

---

## 🗂️ Estructura de Capas del Pipeline

### **Capa BRONZE** (Datos crudos)
* `covid19.bronze.desagregados_por_evento_2015...2026` - RENAP eventos civiles (12 tablas)
* `covid19.bronze.inacif_departamentos` - Catálogo de departamentos Guatemala
* `covid19.bronze.inacif_causas_muerte` - Catálogo de causas de muerte
* `covid19.bronze.who_covid_19_global_daily_data` - Datos COVID-19 OMS (diarios)

### **Capa SILVER** (Datos limpios y normalizados)
* `covid19.silver.silver_ine_deaths` - Defunciones INE procesadas
* `covid19.silver.silver_eventos_unificados` - RENAP formato ancho (12 meses)
* `covid19.silver.silver_eventos_por_mes` - RENAP formato largo (UNPIVOT)

### **Capa GOLD** (Modelo dimensional)
Ver sección "Arquitectura del Modelo Estrella" arriba.

---

## 🔄 Estrategia de Trabajo en Paralelo

### **FASE 1: Dimensiones Maestras** ✅
Creadas por el equipo, sirven como diccionario compartido.

**Ubicación:** `transformations/gold/dimensiones.py`

**Dimensiones creadas:**
* dim_tiempo (144 meses con clasificación Pre-COVID/Pandemia)
* dim_geografia (25 lugares: 22 GT, 1 GT-NA, 1 CR-NA, 1 legacy)
* dim_perfil (12 combinaciones sexo × edad)
* dim_causa_muerte (48 causas con flag COVID)

---

### **FASE 2: Trabajo Individual (Tablas Parciales)** ✅

#### **Wilson (INE + RENAP)** ✅
* **Archivos:** `fact_parcial_ine.py`, `fact_contexto_renap.py`
* **Cobertura:** Guatemala departamental con desglose completo
* **Registros:** 48,656 (mortalidad) + 1,943 (eventos)

#### **Yeni (OMS Guatemala)** ✅
* **Archivo:** `fact_parcial_oms.py`
* **Cobertura:** Guatemala nacional, solo COVID-19
* **Registros:** 45 meses (2020-2025)
* **Total fallecidos:** 20,205

#### **Byron (Costa Rica)** ✅
* **Archivo:** `fact_parcial_costa_rica.py`
* **Cobertura:** Costa Rica nacional, solo COVID-19
* **Registros:** 54 meses (2020-2026)
* **Total fallecidos:** 9,396
* **Metodología:** Misma fuente OMS que Guatemala para consistencia

---

### **FASE 3: Consolidación Final** ✅

**Archivo:** `transformations/gold/consolidacion_final.py`

**Lógica:**
```sql
fact_mortalidad_unificada = 
    fact_parcial_ine         (48,656 registros)
    UNION ALL fact_parcial_oms       (45 registros)
    UNION ALL fact_parcial_costa_rica (54 registros)
    
Total: 48,755 registros
```

---

## 🚀 Ejecución del Pipeline

### Comando Completo

```python
# Dry run (validación sin ejecutar)
startPipelineDryRun()

# Ejecución completa
startPipelineUpdate(
    fullRefresh=False,
    refreshSelectionByDataset=[
        "covid19_gold_dim_tiempo",
        "covid19_gold_dim_geografia",
        "covid19_gold_dim_perfil",
        "covid19_gold_dim_causa_muerte",
        "covid19_gold_fact_parcial_ine",
        "covid19_gold_fact_contexto_renap",
        "covid19_gold_fact_parcial_oms",
        "covid19_gold_fact_parcial_costa_rica",
        "covid19_gold_fact_mortalidad_unificada"
    ]
)
```

### Ejecución Selectiva

```python
# Solo una tabla específica
startPipelineUpdate(
    fullRefresh=False,
    refreshSelectionByDataset=["covid19_gold_fact_parcial_costa_rica"]
)

# Solo consolidación final
startPipelineUpdate(
    fullRefresh=False,
    refreshSelectionByDataset=["covid19_gold_fact_mortalidad_unificada"]
)
```

---

## 📚 Estructura de Archivos del Pipeline

```
/Workspace/Users/yenniferdelion@gmail.com/covid19_dataAnalysis/pipelines/silver/Cleaning 2026-06-19 22:54/
│
├── MODELO_ESTRELLA_DOCUMENTACION.md   # Este archivo (índice principal)
│
├── docs/                               # Documentación modular
│   ├── RESUMEN_EJECUTIVO.md           # Métricas y hallazgos clave
│   ├── DICCIONARIO_DATOS.md           # Definiciones completas de tablas
│   ├── QUERIES_EJEMPLO.md             # 10+ queries listas para usar
│   └── MAPEOS_TRANSFORMACIONES.md     # Transformaciones detalladas
│
├── transformations/
│   ├── eventos_unificados.py          # Silver: RENAP normalizado
│   ├── ine.py                         # Silver: INE deaths
│   │
│   └── gold/
│       ├── dimensiones.py             # 4 dimensiones maestras ✅
│       ├── fact_parcial_ine.py        # Wilson: INE mortalidad ✅
│       ├── fact_contexto_renap.py     # Wilson: RENAP eventos ✅
│       ├── fact_parcial_oms.py        # Yeni: OMS Guatemala ✅
│       ├── fact_parcial_costa_rica.py # Byron: OMS Costa Rica ✅
│       └── consolidacion_final.py     # UNION ALL final ✅
│
└── utilities/
    └── Functions 2026-06-20 16:20:49.py
```

---

## ✅ Estado de Completitud

### Dimensiones ✅
- [x] dim_tiempo (144 meses)
- [x] dim_geografia (25 lugares con GT-NA y CR-NA)
- [x] dim_perfil (12 perfiles)
- [x] dim_causa_muerte (48 causas)

### Hechos Parciales ✅
- [x] fact_parcial_ine (Wilson - 48,656)
- [x] fact_contexto_renap (Wilson - 1,943)
- [x] fact_parcial_oms (Yeni - 45)
- [x] fact_parcial_costa_rica (Byron - 54)

### Consolidación ✅
- [x] fact_mortalidad_unificada (48,755)
- [x] Validación de JOINs
- [x] Verificación de totales

### Próximos Pasos
- [ ] Dashboards de visualización
- [ ] Análisis estadístico avanzado
- [ ] Reportes ejecutivos
- [ ] Publicación de hallazgos

---

## 🌎 Análisis Comparativo Guatemala vs Costa Rica

### Mortalidad COVID-19 (2020-2022)

| País | 2020 | 2021 | 2022 | Total | Tasa per cápita* |
|------|------|------|------|-------|------------------|
| **Guatemala** | 4,803 | 11,299 | 3,896 | **19,998** | 117 por 100K |
| **Costa Rica** | 2,156 | 5,198 | 1,731 | **9,085** | 175 por 100K |

\* Estimado con poblaciones aproximadas: Guatemala 17.1M, Costa Rica 5.2M

**Observaciones:**
* Guatemala: 2.2x más fallecidos absolutos
* Costa Rica: 1.5x mayor tasa per cápita
* Ambos países: Pico en 2021, decrecimiento en 2022

---

## ⚠️ Consideraciones Importantes

### Limitaciones de Datos

#### Fuentes OMS (Guatemala y Costa Rica)
* ⚠️ Solo nivel nacional (sin desglose geográfico interno)
* ⚠️ Sin desglose por sexo ni edad
* ⚠️ Solo mortalidad COVID-19
* ✅ Metodología consistente para comparación internacional

#### Fuente INE (Guatemala)
* ✅ Desglose departamental completo
* ✅ Desglose por sexo y edad
* ✅ Todas las causas de muerte
* ⚠️ Posibles diferencias vs OMS en clasificación COVID

#### Fuente RENAP (Guatemala)
* ⚠️ Eventos inscritos, no eventos ocurridos
* ⚠️ Puede haber rezago entre ocurrencia e inscripción
* ✅ Contexto demográfico valioso (nacimientos, matrimonios, etc.)

### Diferencias entre Fuentes

**Defunciones RENAP vs INE:**
* RENAP: Fecha de inscripción en registro civil
* INE: Fecha de ocurrencia del fallecimiento
* Posibles discrepancias son esperables y normales

**COVID-19 OMS vs INE:**
* OMS: Reporte oficial internacional
* INE: Registro nacional con criterios locales
* Diferencias del 30-60% observadas (OMS típicamente menor)

---

## 📞 Contacto y Soporte

### Responsables por Módulo
* **Dimensiones y arquitectura** → Wilson
* **Implementación OMS Guatemala** → Yeni (completa, solo ajustes menores)
* **Implementación OMS Costa Rica** → Byron (completa, solo ajustes menores)
* **Análisis comparativo** → Equipo completo
* **Pipeline técnico** → Equipo completo

### Documentación Adicional
* **Detalles técnicos:** [Diccionario de Datos](docs/DICCIONARIO_DATOS.md)
* **Ejemplos de uso:** [Queries de Ejemplo](docs/QUERIES_EJEMPLO.md)
* **Transformaciones:** [Mapeos y Transformaciones](docs/MAPEOS_TRANSFORMACIONES.md)
* **Resumen ejecutivo:** [Resumen Ejecutivo](docs/RESUMEN_EJECUTIVO.md)

---

## 🎓 Casos de Uso Implementados

1. ✅ **Comparación internacional COVID-19** (Guatemala vs Costa Rica)
2. ✅ **Validación cruzada de fuentes** (INE vs OMS)
3. ✅ **Análisis departamental** (22 departamentos Guatemala)
4. ✅ **Análisis demográfico** (sexo × edad)
5. ✅ **Análisis de causas** (COVID vs otras)
6. ✅ **Contexto demográfico** (nacimientos, matrimonios, etc.)
7. ✅ **Análisis temporal** (Pre-COVID vs Pandemia)

---

## 📊 Quick Start: Primeras Queries

### 1. Ver totales por fuente
```sql
SELECT fuente, COUNT(*) as registros, SUM(cantidad_fallecidos) as total
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada
GROUP BY fuente;
```

### 2. Comparar Guatemala vs Costa Rica (COVID-19)
```sql
SELECT g.pais, SUM(f.cantidad_fallecidos) as total_covid
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_geografia g ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_causa_muerte c ON f.id_causa = c.id_causa
WHERE c.es_covid = TRUE AND f.fuente IN ('OMS', 'CR')
GROUP BY g.pais;
```

### 3. Top departamentos COVID (INE)
```sql
SELECT g.nombre_departamento, SUM(f.cantidad_fallecidos) as total
FROM covid19.gold.covid19_gold_fact_mortalidad_unificada f
JOIN covid19.gold.covid19_gold_dim_geografia g ON f.id_geografia = g.id_geografia
JOIN covid19.gold.covid19_gold_dim_causa_muerte c ON f.id_causa = c.id_causa
WHERE c.es_covid = TRUE AND f.fuente = 'INE'
GROUP BY g.nombre_departamento
ORDER BY total DESC
LIMIT 10;
```

**Ver más ejemplos en:** [docs/QUERIES_EJEMPLO.md](docs/QUERIES_EJEMPLO.md)

---

**Última actualización:** 21 de junio de 2026  
**Versión del documento:** 3.0 (Modularizado)  
**Estado:** ✅ Modelo estrella completamente operativo

**Cambios en esta versión:**
* ✅ Documentación separada en módulos especializados
* ✅ Agregado resumen ejecutivo con métricas clave
* ✅ Diccionario de datos completo en archivo separado
* ✅ 10+ queries de ejemplo documentadas
* ✅ Mapeos y transformaciones detallados
* ✅ Navegación simplificada con índice principal
