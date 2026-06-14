# Gobernanza y ética

## Objetivo

Definir las reglas iniciales para el uso responsable de los datos del proyecto.

## Descripción general

Este marco de gobernanza y ética se fundamenta en los principios de la [**EU Data Act (Ley de Datos de la Unión Europea - Reglamento UE 2023/2854)**](https://eur-lex.europa.eu/eli/reg/2023/2854/oj/eng). La Ley de Datos busca fomentar una economía de datos justa al garantizar que los usuarios de productos conectados y servicios relacionados puedan acceder a los datos que generan, al mismo tiempo que se incentiva a los titulares de datos a invertir en la generación de valor. 

En consonancia con el **Artículo 4 y 5** de dicha ley (que regulan la obligación de hacer accesibles los datos al usuario o a terceros autorizados), este proyecto se compromete a mantener la transparencia sobre qué datos se recopilan y cómo se utilizan. Asimismo, en estricto cumplimiento con el **Reglamento General de Protección de Datos (GDPR - Reglamento UE 2016/679)**, el cual actúa en paralelo y prevalece sobre la EU Data Act en materia de datos personales, implementamos salvaguardas robustas como la anonimización y la agregación para proteger los derechos fundamentales de los individuos y mitigar los riesgos de filtración de información sensible o secretos comerciales (**Artículo 8 de la EU Data Act**).

## Plan de anonimización

La anonimización es el proceso de modificar los datos de manera que los sujetos de los datos ya no puedan ser identificados, de forma directa o indirecta, utilizando "todos los medios que probablemente se utilicen" (Recital 26 del GDPR). A diferencia de la seudonimización, la anonimización es un proceso irreversible.

### Estrategia y Técnicas Aplicadas

Para garantizar una anonimización efectiva en este proyecto, se implementarán de forma combinada las siguientes técnicas criptográficas y estadísticas:

1. **Supresión de Identificadores Directos:** Eliminación inmediata en la fase de ingesta de nombres, direcciones de correo electrónico, números de identificación, direcciones IP completas y cualquier otro dato de identificación directa.

2. **Generalización y Agrupamiento (K-Anonimato):** Los atributos indirectos o cuasi-identificadores (como la ubicación geográfica exacta o marcas de tiempo precisas) se transformarán en rangos o categorías amplias.

3. **Perturbación de Datos (Ruido Gaussiano / Privacidad Diferencial):** Se inyectará un nivel controlado de ruido matemático a las variables numéricas continuas. Esto evita que un atacante pueda cruzar estos datos con bases de datos externas para reidentificar a un usuario, manteniendo al mismo tiempo la utilidad estadística del conjunto de datos para análisis del proyecto.

### Proceso de Verificación
* **Pruebas de Reidentificación:** Se realizarán auditorías periódicas de vulnerabilidad mediante ataques de enlace (*linkage attacks*) simulados para comprobar que la probabilidad de inferir la identidad de un sujeto sea estadísticamente insignificante o cercana a cero.

## Plan de agregación

El plan de agregación complementa la anonimización y se enfoca en la presentación y el procesamiento de datos a nivel macro. En lugar de almacenar o mostrar registros individuales (microdatos), la información se compila en resúmenes estadísticos o métricas globales.

### Objetivos de la Agregación en el Proyecto
* **Cumplimiento de la EU Data Act:** Facilitar el intercambio de datos con terceros y socios del proyecto sin revelar secretos comerciales, propiedad intelectual o patrones de comportamiento individuales de los usuarios.
* **Seguridad de la Información:** Minimizar la superficie de ataque; si la base de datos agregada se ve comprometida, la información filtrada carecerá de valor granular para los atacantes.

### Directrices de Implementación
1. **Umbrales Mínimos de Población (Regla del Umbral):** No se generará ni mostrará ninguna métrica o reporte agregado si el grupo de muestra es inferior a un número crítico de individuos (por ejemplo, N < 10). Si un subgrupo tiene muy pocos integrantes, sus datos se fusionarán automáticamente con una categoría superior para evitar la deducibilidad.
2. **Funciones de Agregación Permitidas:** Los datos en reposo accesibles para análisis general solo se expondrán a través de funciones matemáticas cerradas como:
   * Sumatorias y Conteos globales.
   * Promedios y Medianas.
   * Desviaciones estándar y varianzas para análisis de tendencias.
3. **Prevención de Ataques por Diferencia:** Se implementarán restricciones en las consultas (queries) a la base de datos para evitar que un usuario de la plataforma reste dos conjuntos de datos agregados muy similares con el fin de aislar la información de un individuo específico.

!!! note "Consideraciones sobre la Gobernanza y Privacidad de los Datos"
    Los datos analizados en este proyecto provienen exclusivamente de repositorios consolidados de fuentes oficiales e institucionales, descartando el uso de técnicas de levantamiento primario (como encuestas directas). 
    
    Si bien la información suministrada por estas entidades ya cuenta con protocolos previos de desidentificación, el pipeline de datos del proyecto implementa una capa secundaria de validación y control. Este proceso garantiza que el tratamiento de los datos mantenga la anonimización estricta y cumpla con los estándares éticos descritos en las secciones anteriores antes de su almacenamiento definitivo.