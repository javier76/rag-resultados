# Instrucciones — Scripts de análisis de resultados

Este documento describe qué tienen que hacer los scripts de Python que procesan
la planilla de salida del evaluador y producen las tablas y figuras del capítulo
de Evaluación y resultados del trabajo final, más los dos listados auxiliares del
análisis de fallos.

El documento del trabajo no incluye código. Los scripts forman parte del
material complementario, publicado en un repositorio al que el documento remite
mediante el enlace al release (apartado 5.1, Instrumento y conjunto de
preguntas). Tienen que ser legibles y reproducibles por un tercero que tenga la
planilla.

---

## 1. Insumo

**Archivo:** `eval_n8n_test_results_20260424_171917_anonim.csv`
(exportado desde Google Sheets, sin modificaciones posteriores). En las columnas
de texto, los datos de contacto y de identificación están reemplazados por
marcadores entre corchetes (`[email_1]`, `[telefono_1]`, etc.); las columnas del
cálculo no se ven afectadas.

**Estructura:** 179 filas (una por pregunta) × 48 columnas. Sin celdas vacías en las columnas del cálculo.

**Columnas relevantes para el cálculo.** Para cada flujo `WF` en {`WF1`, `WF2`}
y cada repetición `N` en {1, 2, 3}:

| Columna | Tipo | Valores |
|---|---|---|
| `{WF}_Response_{N}_Answered` | int | 0 / 1 |
| `{WF}_Response_{N}_Source` | int | 0 / 1 |
| `{WF}_Response_{N}_Source_Ok` | int | 0 / 1 |
| `{WF}_Response_{N}_Correctness` | int | 0 a 5 |

Más, una vez por flujo:

| Columna | Tipo | Valores |
|---|---|---|
| `{WF}_Stability_Score` | int | 1 a 5 |

**Columnas de texto** (`Question`, `Expected Answer`, `{WF}_Response_{N}`,
todas las `*_Reason`): no se usan en el cálculo. El script las descarta al
cargar (`usecols`), pero **no** hay que recortar el archivo de origen: el CSV
que se lee es la planilla completa tal como la exporta el evaluador.

**Nomenclatura en el documento:** WF1 es el flujo del buscador, WF2 el flujo del
chat. Usar esos nombres en las etiquetas de tablas y figuras, no "WF1"/"WF2".

---

## 2. Unidad de análisis

Cada **respuesta individual** es una unidad. Con 179 preguntas × 3 repeticiones,
la base es de **537 respuestas por flujo**.

Excepción: la estabilidad se asigna una vez por pregunta y por flujo, así que su
base es de 179 valores por flujo.

---

## 3. Indicadores a calcular

Los seis indicadores, por flujo, sobre las 537 respuestas.

### 3.1 Tasa de respuesta
Proporción de respuestas que contestaron la pregunta.

    suma de Answered sobre las 3 repeticiones / 537

### 3.2 Atribución
Proporción de respuestas que incluyeron un enlace, sin importar cuál.

    suma de Source sobre las 3 repeticiones / 537

### 3.3 Correspondencia de la fuente
De las respuestas que contestaron **y** citaron un enlace, cuántas citaron el
correcto.

    numerador: Answered == 1 AND Source == 1 AND Source_Ok == 1
    denominador: Answered == 1 AND Source == 1

Atención al denominador: no es 537 ni el total de `Source == 1`. Se calcula solo
sobre las respuestas que **contestaron y** citaron un enlace, porque una
abstención no puede tener fuente correcta ni incorrecta. Esto excluye del
denominador los 4 casos con `Answered == 0 AND Source == 1` descritos en el
apartado 4.4, punto 4.

### 3.4 Abstención correcta
Casos en que el sistema no respondió y esa decisión fue correcta.

    numerador: Answered == 0 AND Source_Ok == 1
    denominador: Answered == 0

Nota: el evaluador registra la correspondencia de la fuente y la abstención
correcta en el mismo campo (`Source_Ok`), porque en los dos casos considera
correcta la atribución. El script los separa cruzando ese campo con `Answered`.
Es una recodificación de datos existentes, no un dato nuevo ni una columna
agregada a la planilla. En las abstenciones sin enlace (Source = 0), ese campo lo completó el equipo durante la revisión manual; ver la sección Insumo del README.

### 3.5 Correctitud
Escala de 1 a 5, **solo sobre las respuestas que contestaron** (`Answered == 1`).
Las abstenciones se excluyen antes de promediar, cualquiera sea el puntaje que les haya asignado el evaluador (en general 0, aunque algunas tienen otro valor); incluirlas mezclaría dos poblaciones.

Calcular: media, mediana y **distribución completa** (frecuencia de cada valor
de 1 a 5). La distribución importa más que la media, porque es una escala
ordinal.

### 3.6 Estabilidad
Media y distribución de `{WF}_Stability_Score`, sobre 179 valores por flujo.

---

## 4. Salidas

### 4.1 Tabla resumen

Seis filas (una por indicador) × dos columnas (buscador, chat). Formato de
salida: CSV o Markdown, para copiar al documento.

Cada celda con el porcentaje y, entre paréntesis, el conteo absoluto y su base.
Ejemplo: `97,2 % (522/537)`. Los conteos importan porque con estas magnitudes
las diferencias entre flujos son de una a cinco respuestas y el porcentaje solo
las oculta.

Valores esperados (calculados sobre la planilla corregida; sirven como
verificación de que el script está bien):

| Indicador | Buscador (WF1) | Chat (WF2) |
|---|---|---|
| Tasa de respuesta | 97,2 % (522/537) | 97,4 % (523/537) |
| Atribución | 97,2 % (522/537) | 98,1 % (527/537) |
| Correspondencia de la fuente | 99,4 % (519/522) | 99,4 % (520/523) |
| Abstención correcta | 100 % (15/15) | 100 % (14/14) |
| Correctitud media (respondidas) | 4,67 (mediana 5) | 4,71 (mediana 5) |
| Estabilidad media | 4,67 | 4,65 |

### 4.2 Figura de distribución de correctitud por flujo

Barras agrupadas, eje x con los valores 1 a 5, eje y con la cantidad de
respuestas. Dos series: buscador y chat. El título incrustado en la imagen no
lleva número de figura: la numeración la asigna el documento.

Valores esperados:

| Correctitud | Buscador | Chat |
|---|---|---|
| 1 | 10 | 6 |
| 2 | 9 | 7 |
| 3 | 22 | 22 |
| 4 | 61 | 61 |
| 5 | 420 | 427 |

Escala lineal en el eje y, con el conteo exacto impreso sobre cada barra: con 420
respuestas de un lado y 10 del otro, la altura de las barras de la cola no alcanza
para compararlas a simple vista y los números son los que permiten leerlas.

### 4.3 Figura de distribución de estabilidad por flujo

Mismo formato, sobre `Stability_Score` (1 a 5, 179 valores por flujo).

Valores esperados:

| Estabilidad | Buscador | Chat |
|---|---|---|
| 1 | 1 | 3 |
| 2 | 4 | 2 |
| 3 | 1 | 8 |
| 4 | 41 | 29 |
| 5 | 132 | 137 |

### 4.4 Listado de casos para revisión manual (insumo del análisis de fallos)

No es una figura: es un CSV auxiliar para que el análisis de fallos del capítulo
se haga sobre casos concretos. Tiene que incluir, con su texto completo
(pregunta, respuesta esperada, respuesta del sistema y las justificaciones del
evaluador):

1. Las respuestas con correctitud 1, 2 o 3. Son 41 en el buscador y 35 en el
   chat, contando repeticiones.
2. Los casos donde `Source_Ok == 0` (fuente incorrecta).
3. Los casos donde `Answered == 0` (abstenciones), para verificar el motivo.
4. Los casos donde `Answered == 0` **pero** `Source == 1`: el sistema no
   respondió y sin embargo citó un enlace. Son 4 en total, todos en el chat
   (2 en la repetición 1 y 2 en la repetición 3). Corresponden a derivaciones a
   la sección de concursos: el sistema no respondió la pregunta, pero incluyó el
   enlace al servicio correspondiente.

### 4.5 Listado de preguntas con correctitud baja (vista por pregunta)

Segundo CSV auxiliar para el mismo análisis de fallos, con los mismos casos que
selecciona el criterio 1 del apartado 4.4 pero agrupados de otra manera.

El 4.4 emite una fila por respuesta individual, que es la unidad de análisis del
capítulo. Ese formato sirve para revisar respuestas sueltas, pero dispersa las
seis respuestas de una misma pregunta entre las de todas las demás, y en la
revisión manual interesa ver juntas las seis: si una pregunta falla en las seis
repeticiones el problema es de la pregunta o de la fuente, y si falla en una sola
es de esa corrida.

**Unidad:** la pregunta. Una fila por pregunta con al menos una respuesta de
correctitud baja en cualquiera de los dos flujos.

**Criterio de selección:** el mismo del 4.4, punto 1 — correctitud 1, 2 o 3 entre
las respuestas que contestaron (`Answered == 1`). El valor 0 no cuenta como
fallo, por lo dicho en el 3.5: marca "no respondió" y no pertenece a la escala de
calidad.

**Contenido de cada fila:**

- El número de fila de la planilla, la pregunta y la respuesta esperada.
- En cuántas de las tres repeticiones falló cada flujo (0 a 3) y el total sobre
  las seis respuestas.
- Los seis puntajes de correctitud tal como están en la planilla, sin
  recodificar: el 0 de las abstenciones se vuelca como 0, para que se vea por qué
  esa repetición no cuenta como fallo.
- El texto completo de las seis respuestas y de las seis justificaciones de
  correctitud del evaluador.

**Orden:** de mayor a menor cantidad de repeticiones fallidas, y a igualdad por
número de fila, para que las preguntas que fallan siempre queden arriba y el
orden no dependa del orden de lectura del archivo.

Valores esperados:

| | Cantidad |
|---|---|
| Preguntas seleccionadas | 25 |
| Respuestas fallidas del buscador | 41 |
| Respuestas fallidas del chat | 35 |

| Repeticiones fallidas (sobre 6) | Preguntas |
|---|---|
| 6 | 5 |
| 5 | 2 |
| 4 | 3 |
| 3 | 3 |
| 2 | 3 |
| 1 | 9 |

Dos aclaraciones sobre esta salida:

- El conteo de repeticiones fallidas por pregunta y el reparto de la segunda
  tabla son agregaciones **por pregunta**, y la unidad de análisis del capítulo
  es la respuesta individual (apartado 2). Sirven para ordenar la revisión
  manual, no son indicadores. Vale la advertencia del apartado 6: para citar
  cualquiera de esos números en el capítulo hay que definirlos antes ahí.
- La justificación de correctitud puede venir vacía en las repeticiones que
  fueron abstención, porque el evaluador no la completa cuando el sistema no
  respondió. No es un dato faltante.

---

## 5. Requisitos del script

- Dos archivos `.py`, sin notebook y sin pasos manuales intermedios:
  `analisis_evaluacion.py`, que produce las salidas 4.1 a 4.4, y
  `preguntas_correctitud_baja.py`, que produce la del 4.5. El segundo importa del
  primero la ruta de la planilla, los nombres de las columnas, la nomenclatura
  buscador/chat y las funciones de carga, para que esas definiciones estén
  escritas en un solo lugar. No depende de las salidas del primero: el orden de
  ejecución es indistinto.
- Solo pandas y matplotlib. Sin seaborn ni dependencias adicionales.
- Lee el CSV, calcula, escribe la tabla y guarda las figuras. Nada más.
- Ruta del CSV como constante al inicio del archivo, no hardcodeada en medio.
- Verificación de integridad de la planilla antes de leerla: huella SHA-256
  contra una constante del script, cortando la ejecución con un mensaje
  explícito si no coincide. Ver apartado 6.
- Figuras en PNG, resolución suficiente para impresión (150 dpi o más).
- Etiquetas y títulos en español, sin primera persona.
- Comentado lo suficiente como para que se entienda leyéndolo, porque se publica
  como material complementario del trabajo.

---

## 6. Advertencias

**La planilla no se edita.** Si hay que corregir un valor, se corrige en el
archivo de origen y se vuelve a exportar; nunca en el CSV que lee el script ni
dentro del script. El repositorio tiene que describir un procedimiento que otro
pueda reproducir con el mismo archivo.

**Guardar la planilla en el estado exacto con el que se produjeron los números
del documento.** Si después se edita una celda, el script deja de reproducir lo
que dice el capítulo y sus salidas pasan a ser engañosas. El script comprueba
esto automáticamente: calcula la huella SHA-256 de la planilla antes de leerla
y la compara contra una constante fijada en el código. Si no coincide, corta
la ejecución sin calcular nada, con un mensaje que indica la huella esperada y la
obtenida. Si se reemplaza la planilla por una reexportación legítima, hay que
actualizar esa constante y volver a revisar si los valores del capítulo siguen
siendo los mismos.

**No agregar cálculos que no estén acá.** Cualquier indicador nuevo tiene que
estar definido antes en el apartado del documento donde se definen los
indicadores; si el script calcula algo que el documento no define, el capítulo
queda con un número sin respaldo.

**Sin inferencia estadística.** Las diferencias entre flujos son de una a cinco respuestas sobre 537 y no se les atribuye significado. No calcular intervalos de
confianza ni pruebas de hipótesis: con este diseño no corresponde.
