#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis de los resultados de la evaluación — capítulo de Evaluación y
resultados.

Lee la planilla exportada por el evaluador, calcula los seis indicadores
definidos en el apartado del trabajo donde se definen los indicadores, y escribe
la tabla resumen, las dos figuras y el listado de casos para revisión manual.

El documento del trabajo no incluye código. Este archivo forma parte del
material complementario, publicado en un repositorio al que el documento remite
mediante el enlace al release (apartado 5.1, Instrumento y conjunto de
preguntas). Está pensado para leerse de arriba abajo y para que un tercero
reproduzca los números del capítulo con la misma planilla, sin pasos manuales
intermedios.

La planilla NO se modifica. Si hay que corregir un valor, se corrige en el
archivo de origen y se vuelve a exportar. Antes de leerla, el script comprueba su
huella SHA-256 contra la del capítulo y corta si no coincide.

Uso:
    pip install -r requirements.txt
    python3 analisis_evaluacion.py
"""

import hashlib
from pathlib import Path

import matplotlib

# Backend sin ventana gráfica: el script corre en un contenedor sin display y
# solo guarda archivos PNG.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (después de fijar el backend)
import pandas as pd  # noqa: E402

# ---------------------------------------------------------------------------
# Constantes de configuración
# ---------------------------------------------------------------------------

# Directorio del script: todas las rutas se resuelven relativas a él, para que
# el script funcione sin importar desde dónde se lo invoque.
DIR_BASE = Path(__file__).resolve().parent

CSV_PATH = DIR_BASE / "eval_n8n_test_results_20260424_171917_anonim.csv"
DIR_SALIDAS = DIR_BASE / "salidas"

# Huella SHA-256 de la planilla con la que se produjeron los números del
# capítulo. El apartado 6 de las instrucciones pide guardar la planilla en ese
# estado exacto: si el archivo cambia, aunque sea en una celda, las salidas dejan
# de reproducir lo que dice el capítulo y pasan a ser engañosas. La huella lo
# detecta antes de calcular, en vez de que se descubra por un número distinto.
CSV_SHA256 = "55f6269833b8d40051c7708b526fd25a4a301862441393da46279f61ed089fca"

# WF1 es el flujo del buscador y WF2 el flujo del chat. En tablas y figuras se
# usan siempre los nombres del documento, nunca "WF1"/"WF2".
FLUJOS = {"WF1": "buscador", "WF2": "chat"}

REPETICIONES = (1, 2, 3)

# Escala ordinal de calidad y de estabilidad. El 0 de correctitud queda fuera a
# propósito: marca "no respondió" y no pertenece a la escala.
ESCALA = (1, 2, 3, 4, 5)

DPI = 200  # resolución de las figuras, suficiente para impresión

# Colores de las dos series, constantes entre las dos figuras.
COLORES = {"buscador": "#4C72B0", "chat": "#DD8452"}

# Precondiciones de la planilla declaradas en el apartado 1 de las
# instrucciones. Si el archivo de origen cambia, la verificación las detecta.
N_PREGUNTAS = 179
N_RESPUESTAS = N_PREGUNTAS * len(REPETICIONES)  # 537 respuestas por flujo

# Valores esperados del documento. No son un cálculo nuevo: son la referencia
# contra la cual el script se autoverifica al final de la ejecución.
ESPERADO = {
    "buscador": {
        "tasa_respuesta": (522, 537),
        "atribucion": (522, 537),
        "correspondencia_fuente": (519, 522),
        "abstencion_correcta": (15, 15),
        "correctitud_media": 4.67,
        "correctitud_mediana": 5,
        "correctitud_dist": {1: 10, 2: 9, 3: 22, 4: 61, 5: 420},
        "estabilidad_media": 4.67,
        "estabilidad_dist": {1: 1, 2: 4, 3: 1, 4: 41, 5: 132},
        "casos_correctitud_baja": 41,
    },
    "chat": {
        "tasa_respuesta": (523, 537),
        "atribucion": (527, 537),
        "correspondencia_fuente": (520, 523),
        "abstencion_correcta": (14, 14),
        "correctitud_media": 4.71,
        "correctitud_mediana": 5,
        "correctitud_dist": {1: 6, 2: 7, 3: 22, 4: 61, 5: 427},
        "estabilidad_media": 4.65,
        "estabilidad_dist": {1: 3, 2: 2, 3: 8, 4: 29, 5: 137},
        "casos_correctitud_baja": 35,
    },
}

# Anomalía descrita en el apartado 4.4, punto 4, de instrucciones.md: respuestas
# que no contestaron y sin embargo citaron un enlace. Son las cuatro derivaciones del chat a la sección de concursos.

ESPERADO_ABSTENCION_CON_ENLACE = 4


# ---------------------------------------------------------------------------
# Carga de la planilla
# ---------------------------------------------------------------------------

def columnas_numericas():
    """Nombres de las columnas que intervienen en el cálculo.

    Son cuatro por flujo y repetición (24 en total) más el puntaje de
    estabilidad, que se asigna una vez por pregunta y por flujo (2 más): 26.
    """
    columnas = []
    for wf in FLUJOS:
        for n in REPETICIONES:
            columnas += [
                f"{wf}_Response_{n}_Answered",
                f"{wf}_Response_{n}_Source",
                f"{wf}_Response_{n}_Source_Ok",
                f"{wf}_Response_{n}_Correctness",
            ]
        columnas.append(f"{wf}_Stability_Score")
    return columnas


def columnas_de_texto():
    """Nombres de las columnas de texto que necesita el listado del apartado 4.4
    de instrucciones.md.

    No intervienen en ningún cálculo; se leen aparte y solo para volcar los
    casos a revisar con su texto completo.
    """
    columnas = ["Question", "Expected Answer"]
    for wf in FLUJOS:
        for n in REPETICIONES:
            columnas += [
                f"{wf}_Response_{n}",
                f"{wf}_Response_{n}_Answered_Reason",
                f"{wf}_Response_{n}_Correctness_Reason",
            ]
    return columnas


def huella_planilla():
    """Devuelve el SHA-256 de la planilla.

    Se lee en modo binario y de a un megabyte: así la huella no depende de la
    codificación ni de cómo pandas interprete el archivo, y no hace falta cargarlo
    entero en memoria. La planilla se abre solo para leerla.
    """
    resumen = hashlib.sha256()
    with open(CSV_PATH, "rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def verificar_integridad():
    """Corta la ejecución si la planilla no es la que produjo el capítulo.

    La verificación contra los valores ESPERADO, al final de la corrida, detecta
    que los números cambiaron; esta detecta que cambió el archivo, que es
    anterior y más general: alcanza para una celda de texto que no interviene en
    ningún cálculo.

    Corta en vez de advertir porque cualquier salida producida con otra planilla
    ya no es la del capítulo, y publicarla es exactamente el escenario que el
    apartado 6 de las instrucciones describe como engañoso.
    """
    obtenida = huella_planilla()
    if obtenida != CSV_SHA256:
        raise SystemExit(
            "\nLa planilla no es la que produjo los números del capítulo.\n"
            f"  archivo:  {CSV_PATH.name}\n"
            f"  esperada: {CSV_SHA256}\n"
            f"  obtenida: {obtenida}\n\n"
            "La planilla no se corrige a mano ni desde el script: se corrige en\n"
            "el archivo de origen y se vuelve a exportar (apartado 6 de\n"
            "instrucciones.md). Si el archivo nuevo es el correcto, hay que\n"
            "actualizar CSV_SHA256 y revisar si los valores del capítulo siguen\n"
            "siendo los mismos.\n"
        )


def cargar_numerico():
    """Lee de la planilla solo las columnas del cálculo.

    Las columnas de texto se descartan al cargar (usecols). El archivo de
    origen queda intacto: lo que se recorta es la lectura, no la planilla.
    """
    # La integridad se comprueba acá y no en main() porque
    # preguntas_correctitud_baja.py importa esta función: escrita en un solo
    # lugar, la comprobación cubre a los dos scripts.
    verificar_integridad()
    df = pd.read_csv(CSV_PATH, usecols=columnas_numericas())
    return df[columnas_numericas()]  # orden estable, independiente del archivo


def cargar_texto():
    """Lee de la planilla solo las columnas de texto del listado del apartado 4.4
    de instrucciones.md."""
    df = pd.read_csv(CSV_PATH, usecols=columnas_de_texto())
    return df[columnas_de_texto()]


def a_formato_largo(numerico):
    """Reordena la planilla a una fila por respuesta individual.

    La unidad de análisis es la respuesta individual (apartado 2 de
    instrucciones.md), no la pregunta: 179 preguntas x 3 repeticiones x 2
    flujos = 1074 filas. Con la tabla en este formato cada indicador se expresa
    como un filtro de una línea, en vez de repetir el mismo bloque de código
    seis veces por flujo.

    La estabilidad no entra acá porque tiene otra base (179 por flujo) y se
    calcula directamente sobre la tabla original.
    """
    partes = []
    for wf, flujo in FLUJOS.items():
        for n in REPETICIONES:
            partes.append(
                pd.DataFrame(
                    {
                        "flujo": flujo,
                        # Número de fila de la planilla (1 = primera pregunta),
                        # para poder volver al caso concreto en la revisión.
                        "pregunta_fila": numerico.index + 1,
                        "repeticion": n,
                        "answered": numerico[f"{wf}_Response_{n}_Answered"],
                        "source": numerico[f"{wf}_Response_{n}_Source"],
                        "source_ok": numerico[f"{wf}_Response_{n}_Source_Ok"],
                        "correctness": numerico[f"{wf}_Response_{n}_Correctness"],
                    }
                )
            )
    return pd.concat(partes, ignore_index=True)


# ---------------------------------------------------------------------------
# Indicadores (apartado 3 de instrucciones.md; numeración 3.1 a 3.6 abajo)
# ---------------------------------------------------------------------------

def calcular_indicadores(largo, numerico, flujo, wf):
    """Calcula los seis indicadores de un flujo.

    Las proporciones se devuelven como par (numerador, denominador) y no como
    porcentaje: la tabla resumen tiene que mostrar los conteos absolutos,
    porque con estas magnitudes las diferencias entre flujos son de una a
    cuatro respuestas y el porcentaje solo las oculta.
    """
    r = largo[largo["flujo"] == flujo]
    base = len(r)  # 537 respuestas

    # 3.1 Tasa de respuesta: proporción de respuestas que contestaron.
    tasa_respuesta = (int(r["answered"].sum()), base)

    # 3.2 Atribución: proporción que incluyó un enlace, sin importar cuál.
    atribucion = (int(r["source"].sum()), base)

    # 3.3 Correspondencia de la fuente: de las respuestas que contestaron Y
    # citaron un enlace, cuántas citaron el correcto.
    #
    # El denominador no es 537 ni el total de source == 1: se calcula solo
    # sobre las respuestas que contestaron y citaron algo, porque una
    # abstención no puede tener fuente correcta ni incorrecta. Eso deja fuera
    # los casos con answered == 0 and source == 1 (la anomalía del apartado
    # 4.4, punto 4, de instrucciones.md).
    contesto_y_cito = r[(r["answered"] == 1) & (r["source"] == 1)]
    correspondencia_fuente = (
        int((contesto_y_cito["source_ok"] == 1).sum()),
        len(contesto_y_cito),
    )

    # 3.4 Abstención correcta: casos en que el sistema no respondió y esa
    # decisión fue correcta.
    #
    # El evaluador registra la correspondencia de la fuente y la abstención
    # correcta en el mismo campo (Source_Ok), porque en los dos casos considera
    # correcta la atribución. Acá se separan cruzando ese campo con Answered.
    # Es una recodificación de datos existentes, no un dato nuevo.
    abstenciones = r[r["answered"] == 0]
    abstencion_correcta = (
        int((abstenciones["source_ok"] == 1).sum()),
        len(abstenciones),
    )

    # 3.5 Correctitud: escala de 1 a 5, solo sobre las respuestas que
    # contestaron. El valor 0 marca "no respondió" y no pertenece a la escala
    # de calidad; incluirlo mezclaría dos poblaciones y bajaría la media por
    # una razón que no es de calidad.
    correctitud = r.loc[r["answered"] == 1, "correctness"]
    correctitud_dist = {v: int((correctitud == v).sum()) for v in ESCALA}

    # 3.6 Estabilidad: se asigna una vez por pregunta y por flujo, así que su
    # base es de 179 valores, no 537.
    estabilidad = numerico[f"{wf}_Stability_Score"]
    estabilidad_dist = {v: int((estabilidad == v).sum()) for v in ESCALA}

    return {
        "tasa_respuesta": tasa_respuesta,
        "atribucion": atribucion,
        "correspondencia_fuente": correspondencia_fuente,
        "abstencion_correcta": abstencion_correcta,
        "correctitud_media": float(correctitud.mean()),
        "correctitud_mediana": float(correctitud.median()),
        "correctitud_dist": correctitud_dist,
        "correctitud_base": int(len(correctitud)),
        "estabilidad_media": float(estabilidad.mean()),
        "estabilidad_dist": estabilidad_dist,
        "estabilidad_base": int(len(estabilidad)),
    }


# ---------------------------------------------------------------------------
# Salida 4.1 de instrucciones.md — tabla resumen
# ---------------------------------------------------------------------------

def formato_proporcion(numerador, denominador):
    """Devuelve '97,2 % (522/537)'.

    Coma decimal y un decimal, como en el documento. Cuando la proporción es
    exacta se escribe '100 %' sin decimales, para no sugerir una precisión que
    no aporta.
    """
    porcentaje = 100.0 * numerador / denominador
    if numerador == denominador:
        texto = "100 %"
    else:
        texto = f"{porcentaje:.1f}".replace(".", ",") + " %"
    return f"{texto} ({numerador}/{denominador})"


def formato_media(valor, decimales=2):
    """Devuelve una media con coma decimal: 4,67."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def construir_tabla(indicadores):
    """Arma la tabla resumen: seis filas (indicadores) x dos columnas (flujos)."""
    filas = []

    def fila(etiqueta, celda_por_flujo):
        filas.append(
            {
                "Indicador": etiqueta,
                **{
                    nombre.capitalize(): celda_por_flujo(indicadores[nombre])
                    for nombre in FLUJOS.values()
                },
            }
        )

    fila("Tasa de respuesta", lambda i: formato_proporcion(*i["tasa_respuesta"]))
    fila("Atribución", lambda i: formato_proporcion(*i["atribucion"]))
    fila(
        "Correspondencia de la fuente",
        lambda i: formato_proporcion(*i["correspondencia_fuente"]),
    )
    fila(
        "Abstención correcta",
        lambda i: formato_proporcion(*i["abstencion_correcta"]),
    )
    fila(
        "Correctitud media (respondidas)",
        lambda i: (
            f"{formato_media(i['correctitud_media'])} "
            f"(mediana {formato_media(i['correctitud_mediana'], 0)}; "
            f"n={i['correctitud_base']})"
        ),
    )
    fila(
        "Estabilidad media",
        lambda i: f"{formato_media(i['estabilidad_media'])} (n={i['estabilidad_base']})",
    )

    return pd.DataFrame(filas)


def escribir_tabla(tabla):
    """Guarda la tabla resumen en CSV y en Markdown, para copiar al documento."""
    ruta_csv = DIR_SALIDAS / "tabla_resumen.csv"
    ruta_md = DIR_SALIDAS / "tabla_resumen.md"

    tabla.to_csv(ruta_csv, index=False, encoding="utf-8")

    # to_markdown() depende de tabulate, que no está entre las dependencias
    # permitidas, así que la tabla Markdown se arma a mano.
    columnas = list(tabla.columns)
    lineas = [
        "| " + " | ".join(columnas) + " |",
        "|" + "|".join(["---"] * len(columnas)) + "|",
    ]
    for _, f in tabla.iterrows():
        lineas.append("| " + " | ".join(str(f[c]) for c in columnas) + " |")
    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    return ruta_csv, ruta_md


# ---------------------------------------------------------------------------
# Salidas 4.2 y 4.3 de instrucciones.md — figuras
# ---------------------------------------------------------------------------

def barras_agrupadas(ax, distribuciones, valores):
    """Dibuja una serie de barras por flujo sobre los valores indicados."""
    ancho = 0.38
    for desplazamiento, (flujo, dist) in zip(
        (-ancho / 2, ancho / 2), distribuciones.items()
    ):
        posiciones = [v + desplazamiento for v in range(len(valores))]
        alturas = [dist[v] for v in valores]
        barras = ax.bar(
            posiciones, alturas, ancho, label=flujo, color=COLORES[flujo]
        )
        # El conteo exacto sobre cada barra: con estas magnitudes la diferencia
        # entre flujos es de pocas respuestas y no se distingue por la altura.
        ax.bar_label(barras, fontsize=8, padding=2)

    ax.set_xticks(range(len(valores)))
    ax.set_xticklabels([str(v) for v in valores])
    # Aire arriba para que las etiquetas de las barras más altas no queden
    # pegadas al borde del panel.
    ax.margins(y=0.14)
    ax.set_ylim(bottom=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)


def figura_correctitud(indicadores):
    """Figura de distribución de correctitud por flujo.

    El título incrustado no lleva número: la numeración la pone el documento,
    que rotula la figura por fuera de la imagen.

    Un solo panel con la escala completa (1 a 5), sin recortes ni escalas
    especiales en el eje y. El conteo exacto sobre cada barra (ver
    barras_agrupadas) permite leer las diferencias entre flujos en los
    valores bajos aunque las barras de 420/427 respuestas dominen la altura.
    """
    distribuciones = {
        flujo: indicadores[flujo]["correctitud_dist"] for flujo in FLUJOS.values()
    }

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    barras_agrupadas(ax, distribuciones, ESCALA)
    ax.set_xlabel("Correctitud (1 a 5)")
    ax.set_ylabel("Cantidad de respuestas")
    ax.set_title(
        "Distribución de correctitud por flujo\n"
        f"(solo respuestas que contestaron: "
        f"{indicadores['buscador']['correctitud_base']} en el buscador, "
        f"{indicadores['chat']['correctitud_base']} en el chat)",
        fontsize=12,
    )
    ax.legend(frameon=False)
    fig.tight_layout()

    ruta = DIR_SALIDAS / "fig1_correctitud.png"
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)
    return ruta


def figura_estabilidad(indicadores):
    """Figura de distribución de estabilidad por flujo (179 valores por flujo).

    Sin número en el título, por el mismo motivo que figura_correctitud.
    """
    distribuciones = {
        flujo: indicadores[flujo]["estabilidad_dist"] for flujo in FLUJOS.values()
    }

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    barras_agrupadas(ax, distribuciones, ESCALA)
    ax.set_xlabel("Estabilidad (1 a 5)")
    ax.set_ylabel("Cantidad de preguntas")
    ax.set_title(
        "Distribución de estabilidad por flujo\n"
        f"(un valor por pregunta: {indicadores['buscador']['estabilidad_base']} "
        "por flujo)",
        fontsize=12,
    )
    ax.legend(frameon=False)
    fig.tight_layout()

    ruta = DIR_SALIDAS / "fig2_estabilidad.png"
    fig.savefig(ruta, dpi=DPI)
    plt.close(fig)
    return ruta


# ---------------------------------------------------------------------------
# Salida 4.4 de instrucciones.md — listado de casos para revisión manual
# ---------------------------------------------------------------------------

def listar_casos(largo, texto):
    """Arma el CSV auxiliar con los casos a revisar en el análisis de fallos.

    No es una figura ni un indicador: es el insumo para que el análisis de
    fallos se haga sobre casos concretos, con su texto completo.

    Una misma respuesta puede cumplir más de un criterio (por ejemplo, una
    abstención que además citó un enlace), así que se emite una sola fila por
    respuesta y la columna 'motivos' lista todos los criterios que cumple.
    """
    criterios = {
        # 1. Respuestas con correctitud 1, 2 o 3.
        "correctitud_baja": (largo["answered"] == 1)
        & largo["correctness"].isin([1, 2, 3]),
        # 2. Fuente incorrecta.
        "fuente_incorrecta": largo["source_ok"] == 0,
        # 3. Abstenciones, para verificar el motivo.
        "abstencion": largo["answered"] == 0,
        # 4. No respondió y sin embargo citó un enlace. Anomalía menor, sin
        #    explicación confirmada todavía.
        "abstencion_con_enlace": (largo["answered"] == 0) & (largo["source"] == 1),
    }

    marcado = largo.copy()
    for nombre, condicion in criterios.items():
        marcado[nombre] = condicion

    seleccion = marcado[marcado[list(criterios)].any(axis=1)].copy()
    seleccion["motivos"] = seleccion.apply(
        lambda f: "; ".join(n for n in criterios if f[n]), axis=1
    )

    # Se pega el texto de cada caso buscándolo por flujo, fila y repetición.
    inverso = {flujo: wf for wf, flujo in FLUJOS.items()}

    def texto_de(fila, sufijo):
        wf = inverso[fila["flujo"]]
        columna = f"{wf}_Response_{fila['repeticion']}{sufijo}"
        return texto.at[fila["pregunta_fila"] - 1, columna]

    seleccion["Question"] = seleccion["pregunta_fila"].map(
        lambda i: texto.at[i - 1, "Question"]
    )
    seleccion["Expected Answer"] = seleccion["pregunta_fila"].map(
        lambda i: texto.at[i - 1, "Expected Answer"]
    )
    seleccion["Respuesta"] = seleccion.apply(texto_de, sufijo="", axis=1)
    seleccion["Answered_Reason"] = seleccion.apply(
        texto_de, sufijo="_Answered_Reason", axis=1
    )
    seleccion["Correctness_Reason"] = seleccion.apply(
        texto_de, sufijo="_Correctness_Reason", axis=1
    )

    columnas = [
        "flujo",
        "pregunta_fila",
        "repeticion",
        "motivos",
        "Question",
        "Expected Answer",
        "Respuesta",
        "answered",
        "source",
        "source_ok",
        "correctness",
        "Answered_Reason",
        "Correctness_Reason",
    ]
    seleccion = seleccion[columnas].sort_values(
        ["flujo", "pregunta_fila", "repeticion"]
    )

    ruta = DIR_SALIDAS / "casos_revision.csv"
    seleccion.to_csv(ruta, index=False, encoding="utf-8")
    return ruta, seleccion


# ---------------------------------------------------------------------------
# Verificación
# ---------------------------------------------------------------------------

def verificar(numerico, indicadores, casos):
    """Compara lo calculado contra los valores esperados del documento.

    No agrega ningún indicador: los valores esperados están publicados en los
    apartados 4.1, 4.2 y 4.3 de instrucciones.md, que reproducen la tabla y las
    figuras del capítulo, justamente como control de que el script está bien.
    Si la planilla de origen cambia, esta función lo hace evidente en vez de
    dejar que el script produzca números distintos a los del capítulo en
    silencio.
    """
    resultados = []

    def comparar(etiqueta, obtenido, esperado):
        resultados.append((etiqueta, obtenido == esperado, obtenido, esperado))

    # Precondiciones de la planilla (apartado 1 de instrucciones.md).
    comparar("filas de la planilla", len(numerico), N_PREGUNTAS)
    comparar("celdas vacías", int(numerico.isna().sum().sum()), 0)

    for flujo in FLUJOS.values():
        i = indicadores[flujo]
        e = ESPERADO[flujo]
        for clave in (
            "tasa_respuesta",
            "atribucion",
            "correspondencia_fuente",
            "abstencion_correcta",
        ):
            comparar(f"{flujo} / {clave}", i[clave], e[clave])

        comparar(
            f"{flujo} / correctitud media",
            round(i["correctitud_media"], 2),
            e["correctitud_media"],
        )
        comparar(
            f"{flujo} / correctitud mediana",
            int(i["correctitud_mediana"]),
            e["correctitud_mediana"],
        )
        comparar(
            f"{flujo} / correctitud dist", i["correctitud_dist"], e["correctitud_dist"]
        )
        comparar(
            f"{flujo} / estabilidad media",
            round(i["estabilidad_media"], 2),
            e["estabilidad_media"],
        )
        comparar(
            f"{flujo} / estabilidad dist", i["estabilidad_dist"], e["estabilidad_dist"]
        )

        # Base de respuestas por flujo (apartado 2 de instrucciones.md).
        comparar(f"{flujo} / base de respuestas", i["tasa_respuesta"][1], N_RESPUESTAS)

        # Cantidad de casos con correctitud baja (apartado 4.4, punto 1, de
        # instrucciones.md).
        cuenta = int(
            (
                (casos["flujo"] == flujo)
                & casos["motivos"].str.contains("correctitud_baja")
            ).sum()
        )
        comparar(
            f"{flujo} / casos correctitud baja", cuenta, e["casos_correctitud_baja"]
        )

    # Anomalía del apartado 4.4, punto 4, de instrucciones.md.
    comparar(
        "abstenciones con enlace (total)",
        int(casos["motivos"].str.contains("abstencion_con_enlace").sum()),
        ESPERADO_ABSTENCION_CON_ENLACE,
    )

    print("\nVerificación contra los valores esperados del documento")
    print("-" * 72)
    for etiqueta, ok, obtenido, esperado in resultados:
        estado = "OK        " if ok else "DIFERENCIA"
        print(f"{estado}  {etiqueta}")
        if not ok:
            print(f"            obtenido: {obtenido}")
            print(f"            esperado: {esperado}")

    fallos = [r for r in resultados if not r[1]]
    print("-" * 72)
    if fallos:
        print(f"{len(fallos)} de {len(resultados)} controles no coinciden.")
        print(
            "La planilla de origen no está en el estado con el que se "
            "produjeron los números del capítulo."
        )
    else:
        print(f"Los {len(resultados)} controles coinciden.")
    return not fallos


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    DIR_SALIDAS.mkdir(exist_ok=True)

    numerico = cargar_numerico()
    texto = cargar_texto()
    largo = a_formato_largo(numerico)

    indicadores = {
        flujo: calcular_indicadores(largo, numerico, flujo, wf)
        for wf, flujo in FLUJOS.items()
    }

    tabla = construir_tabla(indicadores)
    ruta_csv, ruta_md = escribir_tabla(tabla)
    ruta_fig1 = figura_correctitud(indicadores)
    ruta_fig2 = figura_estabilidad(indicadores)
    ruta_casos, casos = listar_casos(largo, texto)

    print(f"Planilla leída: {CSV_PATH.name}")
    print(
        f"{len(numerico)} preguntas, {len(largo)} respuestas individuales "
        f"({N_RESPUESTAS} por flujo).\n"
    )
    print("Tabla resumen")
    print("-" * 72)
    print(tabla.to_string(index=False))

    print("\nArchivos escritos")
    print("-" * 72)
    for ruta in (ruta_md, ruta_csv, ruta_fig1, ruta_fig2, ruta_casos):
        print(f"  {ruta.relative_to(DIR_BASE)}")
    print(f"\n{len(casos)} casos en el listado de revisión manual.")

    verificar(numerico, indicadores, casos)


if __name__ == "__main__":
    main()
