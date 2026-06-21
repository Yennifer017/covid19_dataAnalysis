Listado de Reglas de Transformación auditable 

ID Regla
Nombre de la Regla
Tipo
Descripción
Acción
RT-001
Eliminación de datos sensibles
Privacidad
Remover identificadores sensibles del modelo analítico.
Eliminar numero_correlativo en Gold.
RT-002
Estandarización de nombres
Estandarización
Convertir nombres de columnas a formato snake_case.
Número Correlativo → numero_correlativo.
RT-003
Eliminación de duplicados exactos
Calidad
Detectar registros idénticos en todos sus atributos.
Conservar una única ocurrencia.
RT-004
Conversión de tipos de datos
Calidad
Convertir columnas al tipo definido en el modelo.
anio → INT, mes → BYTE, etc.
RT-005
Gestión de valores nulos
Calidad
Eliminar registros que no contengan información obligatoria.
Rechazar registros sin municipio_id o causa_muerte_id.
RT-006
Estandarización de categorías
Calidad
Homogeneizar valores categóricos.
, Masculino, masculino → Masculino.
RT-007
Validación semántica
Calidad
Validar coherencia lógica de los datos.
Rechazar edades negativas o meses fuera de rango.
RT-008
Eliminación de outliers
Calidad
Detectar valores extremos no válidos.
Rechazar edades >120 años.
RT-009
Eliminación de duplicados semánticos
Calidad
Identificar eventos repetidos.
Consolidar registros equivalentes.
RT-010
Traducción de códigos
Transformación
Convertir códigos a valores descriptivos.
Código de sexo → descripción.
RT-011
Codificación de dimensiones
Transformación
Generar códigos internos para análisis.
Crear sexo_id, evaluacion_id.
RT-012
Generación de atributos derivados
Transformación
Crear variables calculadas.
es_adulto_mayor, anio_mes.
RT-013
Clasificación de causas
Negocio
Agrupar causas en categorías superiores.
Natural, violenta, investigación.
RT-014
Integración geográfica
Integración
Relacionar necropsias con municipios y departamentos.
JOIN con catálogos maestros.
RT-015
Validación referencial
Integridad
Verificar existencia de claves foráneas.
Validar municipio_id y causa_muerte_id.
RT-016
Generación de surrogate keys
DW
Crear claves artificiales para dimensiones.
fecha_key, municipio_key, etc.
RT-017
Gestión SCD
DW
Mantener historial de cambios en dimensiones.
Versionado de catálogos.
RT-018
Rechazo controlado
Gobierno
Enviar registros inválidos a cuarentena.
Registrar en tabla de errores.
RT-019
Gestión de excepciones
Gobierno
Registrar errores y eventos de procesamiento.
Almacenar motivo de rechazo.
RT-020
Agregación analítica
Gold
Generar métricas resumidas.
Totales por sexo, municipio y período.






2. Source-to-Target Mapping (STM)
Tabla de Hechos: fact_necropsias
Tabla Origen
Campo Origen
Transformación
Tabla Destino
Campo Destino
inacif_necropsias
id
Copia directa
fact_necropsias
necropsia_id
inacif_necropsias
anio
Validar tipo
dim_fecha
anio
inacif_necropsias
mes
Validar rango 1-12
dim_fecha
mes
inacif_necropsias
dia
Validar rango 1-31
dim_fecha
dia
inacif_necropsias
dia_semana
Estandarizar texto
dim_fecha
dia_semana
inacif_necropsias
sexo
Estandarizar categoría
fact_necropsias
sexo
inacif_necropsias
edad
Conversión a entero
fact_necropsias
edad
inacif_necropsias
evaluacion_mn
Estandarización
fact_necropsias
evaluacion_mn
inacif_necropsias
municipio_id
Lookup catálogo
fact_necropsias
municipio_key
inacif_necropsias
causa_muerte_id
Lookup catálogo
fact_necropsias
causa_muerte_key
inacif_necropsias
edad
Derivación
fact_necropsias
es_adulto_mayor
inacif_necropsias
edad
Derivación
fact_necropsias
grupo_etario
inacif_necropsias
anio, mes
Derivación
fact_necropsias
anio_mes


Dimensión Municipio
Tabla Origen
Campo Origen
Transformación
Tabla Destino
Campo Destino
inacif_municipios
id
Copia directa
dim_municipio
municipio_id
inacif_municipios
nombre
Trim y normalización
dim_municipio
municipio_nombre
inacif_municipios
departamento_id
Lookup departamento
dim_municipio
departamento_key


Dimensión Departamento
Tabla Origen
Campo Origen
Transformación
Tabla Destino
Campo Destino
inacif_departamentos
id
Copia directa
dim_departamento
departamento_id
inacif_departamentos
nombre
Normalización
dim_departamento
departamento_nombre


Dimensión Causa de Muerte
Tabla Origen
Campo Origen
Transformación
Tabla Destino
Campo Destino
inacif_causas_muerte
id
Copia directa
dim_causa_muerte
causa_id
inacif_causas_muerte
nombre
Normalización
dim_causa_muerte
causa_nombre
inacif_causas_muerte
nombre
Clasificación
dim_causa_muerte
categoria_causa


Campos Excluidos
Campo Origen
Motivo
numero_correlativo
Dato sensible, no requerido para análisis
bronze_loaded_at
Metadato técnico
bronze_batch_id
Metadato técnico
bronze_source
Metadato técnico


