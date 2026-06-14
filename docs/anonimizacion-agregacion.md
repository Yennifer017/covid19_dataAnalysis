# Anonimización y Agregación de Datos

## Objetivo

Definir cómo se tratan los datos sensibles de mortalidad antes de su uso analítico,
garantizando el cumplimiento del **EU Data Act** y los principios de manejo ético de
datos sensibles de salud establecidos en los Términos de Referencia del proyecto
(convenio PNUD–MSPAS).

---

## Marco normativo aplicado

| Norma | Aplicación en este proyecto |
|---|---|
| **EU Data Act (2023)** | Rige el tratamiento de datos de salud en el contexto del acuerdo de cooperación PNUD con centros de investigación europeos |
| **RGPD Art. 9** | Los datos de salud y mortalidad son datos sensibles por categoría especial |
| **Estándar CIE-10 (OMS)** | Codificación estandarizada de causas de muerte — permite comparabilidad sin exponer datos individuales |
| **Estándar estadístico internacional** | Supresión de celdas con menos de 5 casos (CDC, Eurostat, INE) |

---

## 1. Clasificación de datos por tabla

Se analizaron las 12 tablas de la capa Bronce del catálogo `covid19.bronze`.
Se identificaron tres niveles de sensibilidad:

### Nivel ALTO — Datos cuasi-individuales (requieren tratamiento antes de Silver)

#### `bronze.inacif_necropsias`
Fuente: INACIF Guatemala vía RDS MySQL.
Una fila representa **una necropsia — una persona fallecida**.

| Campo | Sensibilidad | Razón |
|---|---|---|
| `numero_correlativo` | Alta | Identificador de caso individual |
| `edad` | Media | Edad exacta en años |
| `dia`, `mes`, `anio` | Media | Fecha exacta de muerte — combinada con municipio puede identificar a alguien |
| `municipio_id` | Media | Localización geográfica específica |
| `sexo` | Baja | Por sí solo no identifica, pero combinado con otros campos sí |
| `causa_muerte_id` | Baja | Código referencial, no descripción directa |

**Riesgo real:** La combinación (municipio + fecha exacta + edad + sexo) puede ser suficiente
para re-identificar a una persona en municipios pequeños.

#### `bronze.ine_deaths`
Fuente: INE Guatemala — archivo defunciones-2018.xlsx.
Una fila representa **una defunción registrada**.

| Campo | Sensibilidad | Razón |
|---|---|---|
| `Diaocu`, `Mesocu`, `Añoocu` | Media | Fecha exacta de ocurrencia |
| `Edadif` | Media | Edad exacta del fallecido |
| `Mupocu`, `Depocu` | Media | Municipio y departamento de ocurrencia |
| `Caudef` | Baja | Código CIE-10 de causa de muerte |
| `Sexo` | Baja | Sexo del fallecido |
| `Pnadif`, `Dnadif`, `Mnadif` | Media | País, departamento y municipio de nacimiento |

### Nivel BAJO — Datos de catálogo o ya agregados (sin riesgo de re-identificación)

| Tabla | Razón |
|---|---|
| `bronze.inacif_causas_muerte` | Solo contiene ID y nombre de causa de muerte. Es un catálogo de referencia |
| `bronze.inacif_departamentos` | Catálogo geográfico — solo nombres de departamentos |
| `bronze.inacif_municipios` | Catálogo geográfico — solo nombres de municipios |
| `bronze.mortalidad_categorias_costa_rica_2020` | Datos agregados INEC CR — conteos por categoría CIE-10 y año |
| `bronze.mortalidad_categorias_costa_rica_2021` | Datos agregados INEC CR |
| `bronze.mortalidad_categorias_costa_rica_2022` | Datos agregados INEC CR |
| `bronze.mortalidad_indicadores_costa_rica` | Indicadores estadísticos calculados — sin datos individuales |
| `bronze.mortalidad_por_edades_costa_rica` | Conteos por grupo etario y año — agregados |
| `bronze.who_covid_19_global_daily_data` | Datos oficiales OMS — agregados por país y fecha |
| `bronze.who_mortality` | Estadísticas OMS de mortalidad — agregadas por país |

---

## 2. Técnicas de anonimización aplicadas por capa

### Capa Bronce — Preservación fiel con documentación de riesgo

La capa Bronce almacena los datos **tal como llegaron de la fuente**, sin transformación
destructiva. Esto es intencional: el Bronce es la zona de auditoría y reproceso.

Sin embargo, se aplican las siguientes salvaguardas desde la ingesta:

- **No se almacenan nombres propios de personas fallecidas.** Ninguna de las 12 tablas
  contiene nombre completo de la persona fallecida. El campo `nombre` en
  `inacif_causas_muerte` refiere al nombre de la *causa de muerte*, no de la persona.
- **No se almacenan DPI, cédula ni número de identificación personal** en ninguna tabla.
- **No se almacenan direcciones exactas** (calle, número de casa). Solo se almacenan
  códigos de municipio y departamento.
- **El campo `numero_correlativo`** en `inacif_necropsias` es un identificador interno
  del INACIF, no vinculable a registros civiles sin acceso al sistema fuente.

### Capa Silver — Transformaciones de anonimización obligatorias

Antes de que los datos de `inacif_necropsias` e `ine_deaths` pasen a Silver,
se aplican las siguientes transformaciones:

**1. Generalización de edad exacta a grupo etario**
```
edad exacta (ej: 43) → grupo quinquenal (ej: "40-44")
```

**2. Supresión de fecha exacta — conservar solo año y mes**
```
dia + mes + anio → anio + mes  (el campo "dia" se descarta en Silver)
```
Una fecha exacta de muerte combinada con municipio y edad puede identificar a alguien
en comunidades pequeñas.

**3. Supresión de celdas pequeñas**
Cualquier combinación de (causa + municipio + mes + grupo_etario + sexo) con
**menos de 5 defunciones** se suprime o agrupa en categoría "Otros" antes de
llegar a Gold y a las visualizaciones BI.

**4. Eliminación del numero_correlativo en Silver**
El campo `numero_correlativo` de `inacif_necropsias` se descarta en Silver.
No aporta valor analítico y representa un riesgo de trazabilidad al individuo.

**5. Generalización geográfica para municipios pequeños**
Municipios con menos de 10,000 habitantes se agrupan al nivel departamento para
el análisis comparativo.

---

## 3. Casos en los que NO se publicará información granular

1. Cualquier celda con **conteo menor a 5** defunciones para una combinación específica
2. Causa de muerte con **menos de 10 casos anuales** en un departamento → se agrupa
   en capítulo CIE-10 padre
3. Cruce de municipio pequeño + causa rara + grupo etario específico → se sube a nivel departamento
4. Datos que puedan referir a **menores de edad** → solo se presentan a nivel nacional

---

## 4. Resumen de campos eliminados o transformados por capa

| Campo original | Tabla | Acción en Silver | Justificación |
|---|---|---|---|
| `dia` | `inacif_necropsias` | **Eliminar** | Fecha exacta es identificatoria |
| `Diaocu` | `ine_deaths` | **Eliminar** | Fecha exacta es identificatoria |
| `numero_correlativo` | `inacif_necropsias` | **Eliminar** | Identificador de caso individual |
| `edad` (exacta) | `inacif_necropsias` | **Transformar** a grupo quinquenal | Edad exacta + municipio = re-identificable |
| `Edadif` (exacta) | `ine_deaths` | **Transformar** a grupo quinquenal | Igual razón |
| `municipio_id` pequeño | `inacif_necropsias` | **Generalizar** a departamento si municipio < 10k hab | Riesgo geográfico |

---

## 5. Cumplimiento EU Data Act

| Requisito | Implementación en el proyecto |
|---|---|
| Art. 5 — Acceso a datos | Todas las fuentes son públicas o solicitadas formalmente. Se documenta procedencia en `data-lineage.md` |
| Art. 6 — Protección de personas físicas | Datos cuasi-individuales (INACIF, INE) se anonimizan en Silver antes de cualquier análisis o visualización |
| Art. 12 — Uso secundario de datos | Los datos se usan exclusivamente para análisis comparativo de mortalidad pre/post-COVID con fines de política pública PNUD-MSPAS |
| Considerando 35 — Datos de salud | Se aplican supresión de celdas pequeñas, generalización de edad y eliminación de fecha exacta |

---

## 6. Compromisos éticos del equipo

- **No se cruzan** datos de mortalidad con registros civiles, electorales o fiscales
- **No se publican** datos a nivel individual en ninguna visualización BI
- **No se comparten** los datos crudos del Bronce con terceros fuera del equipo
- **No se usan** los datos para ningún fin distinto al análisis académico de mortalidad pre/post-COVID
- **No se almacenan** datos en sistemas sin control de acceso — todos los datos están en
  Databricks Unity Catalog con autenticación requerida