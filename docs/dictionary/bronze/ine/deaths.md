## Dataset: ine_deaths
**Descripción funcional:** Conjunto de datos de defunciones publicado por el Instituto Nacional de Estadística (INE). Incluye información demográfica, geográfica y causas de muerte registradas a nivel nacional. Se utiliza como fuente primaria para análisis de mortalidad y construcción de indicadores de salud pública.

**Fuente:** [Instituto Nacional de Estadística (INE) - Estadísticas Vitales: Defunciones](https://datos.ine.gob.gt/dataset/estadisticas-vitales-defunciones)

**Sensibilidad:** Alta. Contiene microdatos con información demográfica y variables relacionadas con eventos de defunción.

**Frecuencia de actualización:** Anual.

## Estructura de Campos

| Campo | Tipo de Dato | Descripción Funcional | Regla de Uso / Sensibilidad |
| :--- | :--- | :--- | :--- |
| `Depreg` | LONG | Departamento donde se realizó el **registro** de la defunción. | Código geográfico oficial. |
| `Mupreg` | LONG | Municipio donde se realizó el **registro** de la defunción. | Código geográfico oficial. |
| `Mesreg` | LONG | Mes en el que se asentó el registro oficial. | Valores numéricos (1 al 12). |
| `Añoreg` | LONG | Año en el que se asentó el registro oficial. | Formato YYYY. |
| `Depocu` | LONG | Departamento donde **ocurrió** el deceso. | Crucial para mapas de calor epidemiológicos. |
| `Mupocu` | LONG | Municipio donde **ocurrió** el deceso. | Puede diferir del lugar de registro o residencia. |
| `Sexo` | LONG | Sexo asignado al nacer de la persona fallecida. | Generalmente codificado (ej. 1: Hombre, 2: Mujer). |
| `Diaocu` | LONG | Día calendario en el que ocurrió el deceso. | Útil para series temporales exactas. |
| `Mesocu` | LONG | Mes calendario en el que ocurrió el deceso. | Valores numéricos (1 al 12). |
| `Añoocu` | LONG | Año calendario en el que ocurrió el deceso. | Formato YYYY (Base de análisis temporal). |
| `Edadif` | LONG | Edad cronológica del difunto al momento de fallecer. | Permite agrupar por cohortes o rangos de edad. |
| `Perdif` | LONG | Período de la edad (indica si la edad en `Edadif` son días, meses o años). | Esencial para analizar mortalidad neonatal e infantil. |
| `Puedif` | LONG | Pueblo o pertenencia étnica declarada del difunto. | Para análisis de vulnerabilidad y equidad en salud. |
| `Ecidif` | LONG | Estado civil o conyugal de la persona fallecida. | Categorías estadísticas estándar. |
| `Escodif` | LONG | Escolaridad o nivel educativo máximo alcanzado por el difunto. | Indicador socioeconómico proxy. |
| `Ciuodif` | LONG | Ocupación habitual u oficio del difunto. | Útil para identificar factores de riesgo laborales. |
| `Pnadif` | LONG | País de nacimiento del difunto. | Control de población extranjera o migrante. |
| `Dnadif` | LONG | Departamento de nacimiento del difunto. | Datos de origen geográfico. |
| `Mnadif` | LONG | Municipio de nacimiento del difunto. | Datos de origen geográfico. |
| `Nacdif` | LONG | Nacionalidad legal de la persona fallecida. | Filtro demográfico. |
| `Predif` | LONG | País de residencia habitual del difunto. | Identifica si el fallecido era residente local o visitante. |
| `Dredif` | LONG | Departamento de residencia habitual del difunto. | Permite mapear la mortalidad según el entorno del hogar. |
| `Mredif` | LONG | Municipio de residencia habitual del difunto. | Permite evaluar coberturas de salud locales. |
| `Caudef` | STRING | Causa de la defunción (Código Alfanumérico **CIE-10**). | **Campo Crítico.** Identifica si el deceso fue por COVID-19. |
| `Asist` | LONG | Tipo de asistencia médica recibida antes de fallecer (ej. médica, sin asistencia). | Evalúa el acceso al sistema de salud. |
| `Ocur` | LONG | Lugar físico donde ocurrió el deceso (ej. hospital, hogar, vía pública). | Clave para analizar saturación hospitalaria. |
| `Cerdef` | LONG | Tipo de persona que certificó legalmente la muerte (ej. médico, forense, autoridad). | Indicador de la calidad/confiabilidad del dato. |
| `source_file` | STRING | Nombre del archivo fuente de origen cargado en el Data Lake. | Metadato técnico de linaje y trazabilidad. |
| `bronze_processing_date` | TIMESTAMP | Fecha y hora exacta en la que el registro ingresó a la capa Bronze. | Auditoría técnica del pipeline de ingesta. |