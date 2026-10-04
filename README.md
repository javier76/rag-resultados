# Material complementario — Evaluación y resultados

Este repositorio acompaña el capítulo de Evaluación y resultados del trabajo
final. Contiene la planilla de resultados, los scripts que la procesan y las
salidas usadas en el documento, que remite acá desde el apartado 5.1.

El objetivo es que un tercero, con la misma planilla, obtenga exactamente los
mismos números y figuras del capítulo. El detalle de qué se calcula y por qué
está en [instrucciones.md](instrucciones.md).

## Planilla

`eval_n8n_test_results_20260424_171917_anonim.csv` es la salida del evaluador:
179 filas (una por pregunta) y 48 columnas.

- **Anonimizada.** Nombres, correos, teléfonos, internos, domicilios y dominios
  se reemplazaron por marcadores como `[email_1]`. Un mismo dato lleva siempre el
  mismo marcador. Ninguna columna del cálculo se modificó.
- **Incluye la revisión manual** descrita en los apartados 5.1 y 5.2. En las
  abstenciones sin enlace (`Source = 0`), el equipo marcó `Source_Ok = 1` cuando
  no responder era lo correcto. Son 25 de las 29 abstenciones (15 del buscador y
  10 del chat); las otras 4 son derivaciones con enlace. Por eso `Source_Ok = 1`
  con `Source = 0` no es un error: es lo que mide la abstención correcta.
- **Unidad de análisis:** cada respuesta. Son 179 preguntas × 3 repeticiones = 537
  respuestas por flujo. La estabilidad es la excepción: un valor por pregunta y
  por flujo (179).

Huella SHA-256 de la planilla usada en el capítulo:

```
55f6269833b8d40051c7708b526fd25a4a301862441393da46279f61ed089fca
```

## Scripts

### `analisis_evaluacion.py`

Calcula los seis indicadores (tasa de respuesta, atribución, correspondencia de
la fuente, abstención correcta, correctitud y estabilidad) y escribe en
`salidas/`:

| Archivo | Contenido |
|---|---|
| `tabla_resumen.md` / `.csv` | Tabla 1 del capítulo: los seis indicadores por flujo, con porcentaje y conteo. |
| `fig1_correctitud.png` | Distribución de correctitud por flujo (1 a 5, solo respuestas contestadas). |
| `fig2_estabilidad.png` | Distribución de estabilidad por flujo (1 a 5). |
| `casos_revision.csv` | Las 105 respuestas revisadas a mano en el análisis de fallos. |

Las figuras muestran el conteo sobre cada barra para que se puedan leer los
valores bajos.

### `preguntas_correctitud_baja.py`

Genera `salidas/preguntas_correctitud_menor_a_3.csv`: las 25 preguntas con al
menos una respuesta de correctitud 1, 2 o 3, con sus seis respuestas lado a
lado. Agrupa por pregunta los mismos casos de `casos_revision.csv`; no calcula
indicadores.

## Cómo ejecutar

Probado con Python 3.10.17, pandas 2.3.3 y matplotlib 3.10.9.

```
pip install -r requirements.txt
python analisis_evaluacion.py
python preguntas_correctitud_baja.py
```

El orden no importa y se pueden ejecutar desde cualquier carpeta. Las salidas se
sobrescriben en cada corrida.

## Controles

- **Integridad de la planilla.** Antes de leerla, los scripts comparan su
  SHA-256 con la huella esperada. Si no coincide, se detienen sin calcular nada.
- **Valores esperados.** Al terminar, `analisis_evaluacion.py` compara sus 25
  resultados con el bloque `ESPERADO` e informa OK o DIFERENCIA en cada uno.
  Esos valores no salen de una corrida previa del script: son los publicados en
  el capítulo. Así, cualquier diferencia entre lo calculado y lo impreso queda
  a la vista.

## La planilla no se edita

No se modifica ni a mano ni desde los scripts. Si hay que corregir algo, se
corrige en el origen y se vuelve a exportar. Después hay que actualizar la
huella `CSV_SHA256`, volver a correr los scripts y revisar si cambió algún valor.
Si cambió, se corrige el capítulo, no el bloque `ESPERADO`.

## Licencia

El código (`*.py` y `requirements.txt`) se distribuye bajo licencia MIT; ver
[LICENSE](LICENSE).

La planilla y la carpeta `salidas/` quedan excluidas. Se publican solo para
consultar y verificar los resultados del trabajo final; no se autoriza su
reutilización.
