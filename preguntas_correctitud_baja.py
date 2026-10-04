#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Listado de preguntas con correctitud baja — insumo del análisis de fallos.

Complementa a `analisis_evaluacion.py`, que emite `salidas/casos_revision.csv`
con una fila por respuesta individual. Ese formato sirve para revisar respuestas
sueltas, pero dispersa las seis respuestas de una misma pregunta entre las de
todas las demás. Acá la unidad es la **pregunta**: una fila por pregunta con al
menos una respuesta de correctitud baja, con las seis respuestas enfrentadas y
ordenadas de mayor a menor cantidad de repeticiones fallidas, de modo que las
preguntas que fallan siempre queden arriba.

No calcula ningún indicador nuevo: es una vista pivoteada de los mismos datos
que `analisis_evaluacion.py` ya selecciona bajo el criterio `correctitud_baja`
del apartado 4.4 de instrucciones.md.

Como el resto del repositorio, este archivo es material complementario: el
documento del trabajo no incluye código y remite a él mediante el enlace al
release.

Criterio de fallo: correctitud 1, 2 o 3 **entre las respuestas que contestaron**
(`Answered == 1`). El valor 0 marca "no respondió" y no pertenece a la escala de
calidad (apartado 3.5 de instrucciones.md), así que una abstención no cuenta
como fallo de correctitud.

La planilla NO se modifica. Si hay que corregir un valor, se corrige en el
archivo de origen y se vuelve a exportar.

Uso:
    pip install -r requirements.txt
    python3 preguntas_correctitud_baja.py
"""

import pandas as pd

# La configuración y la carga viven en analisis_evaluacion.py, para que los
# nombres de las columnas, la ruta de la planilla y la nomenclatura
# buscador/chat estén definidos en un solo lugar. Importarlo no ejecuta nada:
# todo su trabajo está detrás de `if __name__ == "__main__"`.
from analisis_evaluacion import (
    CSV_PATH,
    DIR_SALIDAS,
    FLUJOS,
    REPETICIONES,
    cargar_numerico,
    cargar_texto,
)

# ---------------------------------------------------------------------------
# Constantes de configuración
# ---------------------------------------------------------------------------

NOMBRE_SALIDA = "preguntas_correctitud_menor_a_3.csv"

# Valores de la escala que cuentan como fallo. El 0 queda fuera a propósito
# (ver el encabezado del archivo).
CORRECTITUD_BAJA = (1, 2, 3)

# Valores esperados, para autoverificación. Son los mismos conteos que
# analisis_evaluacion.py ya contrasta contra el documento
# (`casos_correctitud_baja` en su ESPERADO): 41 respuestas de correctitud baja
# en el buscador y 35 en el chat.
ESPERADO_FALLOS = {"buscador": 41, "chat": 35}
ESPERADO_PREGUNTAS = 25


# ---------------------------------------------------------------------------
# Selección
# ---------------------------------------------------------------------------

def es_fallo(numerico, wf, n):
    """Máscara booleana: ¿la repetición `n` del flujo `wf` falló, por pregunta?

    Única definición de "fallo" del script: contestó y el evaluador le puso 1, 2
    o 3. Se aplica seis veces (dos flujos x tres repeticiones) en vez de repetir
    la condición escrita a mano.
    """
    contesto = numerico[f"{wf}_Response_{n}_Answered"] == 1
    baja = numerico[f"{wf}_Response_{n}_Correctness"].isin(CORRECTITUD_BAJA)
    return contesto & baja


def armar_tabla(numerico, texto):
    """Arma la tabla pivoteada: una fila por pregunta seleccionada.

    Se trabaja directo sobre la tabla ancha de la planilla, que ya viene con una
    fila por pregunta; no hace falta pasar por el formato largo de
    analisis_evaluacion.py, porque acá la unidad de análisis no es la respuesta
    individual.
    """
    tabla = pd.DataFrame(
        {
            # Número de fila de la planilla (1 = primera pregunta), igual que en
            # casos_revision.csv, para poder volver al caso concreto.
            "pregunta_fila": numerico.index + 1,
            "Question": texto["Question"],
            "Expected Answer": texto["Expected Answer"],
        }
    )

    # En cuántas de las tres repeticiones falló cada flujo (0 a 3).
    for wf, flujo in FLUJOS.items():
        fallos = sum(es_fallo(numerico, wf, n).astype(int) for n in REPETICIONES)
        tabla[f"fallos_{flujo}"] = fallos

    tabla["fallos_total"] = sum(
        tabla[f"fallos_{flujo}"] for flujo in FLUJOS.values()
    )

    # Los seis puntajes, tal como están en la planilla: el 0 de las abstenciones
    # se vuelca como 0, sin recodificar, para que se vea por qué esa repetición
    # no cuenta como fallo.
    for wf, flujo in FLUJOS.items():
        for n in REPETICIONES:
            tabla[f"{flujo}_correctitud_{n}"] = numerico[
                f"{wf}_Response_{n}_Correctness"
            ]

    # Texto completo de las seis respuestas y de las seis justificaciones de
    # correctitud, que es lo que se lee en la revisión manual.
    for wf, flujo in FLUJOS.items():
        for n in REPETICIONES:
            tabla[f"{flujo}_respuesta_{n}"] = texto[f"{wf}_Response_{n}"]
    for wf, flujo in FLUJOS.items():
        for n in REPETICIONES:
            tabla[f"{flujo}_correctitud_reason_{n}"] = texto[
                f"{wf}_Response_{n}_Correctness_Reason"
            ]

    # Una fila por pregunta con al menos una respuesta de correctitud baja en
    # cualquiera de los dos flujos. El nombre del archivo se conserva por compatibilidad, pero el criterio incluye el valor 3: equivale a "correctitud de 3 o menos", como en el capítulo.
    seleccion = tabla[tabla["fallos_total"] > 0].copy()

    # De mayor a menor cantidad de repeticiones fallidas: las preguntas que
    # fallan siempre quedan arriba. A igualdad, por número de fila, para que el
    # orden sea reproducible y no dependa del orden de lectura.
    return seleccion.sort_values(
        ["fallos_total", "pregunta_fila"], ascending=[False, True]
    )


# ---------------------------------------------------------------------------
# Verificación
# ---------------------------------------------------------------------------

def verificar(seleccion):
    """Controla la salida contra los conteos que analisis_evaluacion.py ya
    verifica.

    Si estos números no coinciden, o la planilla de origen cambió, o el criterio
    de fallo quedó mal escrito: en cualquiera de los dos casos el listado dejó de
    describir los mismos casos que el capítulo.
    """
    columnas_respuesta = [
        c
        for c in seleccion.columns
        if c in ("Question", "Expected Answer")
        or c.endswith(tuple(f"_respuesta_{n}" for n in REPETICIONES))
    ]
    columnas_reason = [
        c
        for c in seleccion.columns
        if c.endswith(tuple(f"_correctitud_reason_{n}" for n in REPETICIONES))
    ]

    controles = [
        ("preguntas seleccionadas", len(seleccion), ESPERADO_PREGUNTAS),
        (
            "coherencia fallos_total",
            bool(
                (
                    seleccion["fallos_total"]
                    == seleccion["fallos_buscador"] + seleccion["fallos_chat"]
                ).all()
                and (seleccion["fallos_total"] > 0).all()
            ),
            True,
        ),
        # Question, Expected Answer y el texto de las seis respuestas no
        # deberían faltar nunca: la planilla no tiene celdas vacías (apartado 1
        # de instrucciones.md) para esas columnas.
        (
            "celdas vacías (pregunta/respuesta)",
            int(seleccion[columnas_respuesta].isna().sum().sum()),
            0,
        ),
    ]
    for flujo, esperado in ESPERADO_FALLOS.items():
        controles.append(
            (f"{flujo} / respuestas fallidas", int(seleccion[f"fallos_{flujo}"].sum()), esperado)
        )

    print("\nVerificación")
    print("-" * 72)
    fallos = 0
    for etiqueta, obtenido, esperado in controles:
        ok = obtenido == esperado
        fallos += not ok
        print(f"{'OK        ' if ok else 'DIFERENCIA'}  {etiqueta}")
        if not ok:
            print(f"            obtenido: {obtenido}")
            print(f"            esperado: {esperado}")

    # Informativo, no es un control de OK/DIFERENCIA: el evaluador no completa
    # Correctness_Reason cuando la repetición fue una abstención (Answered ==
    # 0), así que alguna de las seis columnas de justificación puede quedar
    # vacía para una pregunta seleccionada por otra repetición. Es el mismo
    # comportamiento que ya tiene casos_revision.csv, no un dato faltante.
    vacias_reason = int(seleccion[columnas_reason].isna().sum().sum())
    if vacias_reason:
        print(
            f"Nota: {vacias_reason} celda(s) de justificación de correctitud "
            "vacías, todas correspondientes a repeticiones que fueron "
            "abstención (sin Correctness_Reason en la planilla de origen)."
        )
    print("-" * 72)
    if fallos:
        print(f"{fallos} de {len(controles)} controles no coinciden.")
        print(
            "La planilla de origen no está en el estado con el que se "
            "produjeron los números del capítulo."
        )
    else:
        print(f"Los {len(controles)} controles coinciden.")
    return not fallos


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    DIR_SALIDAS.mkdir(exist_ok=True)

    numerico = cargar_numerico()
    texto = cargar_texto()
    seleccion = armar_tabla(numerico, texto)

    ruta = DIR_SALIDAS / NOMBRE_SALIDA
    seleccion.to_csv(ruta, index=False, encoding="utf-8")

    print(f"Planilla leída: {CSV_PATH.name}")
    print(f"{len(numerico)} preguntas en total.\n")
    print(
        f"{len(seleccion)} preguntas con al menos una respuesta de correctitud "
        "baja (1 a 3):"
    )
    for flujo in FLUJOS.values():
        print(
            f"  {flujo}: {int(seleccion[f'fallos_{flujo}'].sum())} respuestas "
            "fallidas"
        )

    print("\nPreguntas por cantidad de repeticiones fallidas (sobre 6)")
    print("-" * 72)
    reparto = seleccion["fallos_total"].value_counts().sort_index(ascending=False)
    for total, cuenta in reparto.items():
        print(f"  {total} de 6: {cuenta} preguntas")

    print(f"\nArchivo escrito: {ruta.relative_to(DIR_SALIDAS.parent)}")

    verificar(seleccion)


if __name__ == "__main__":
    main()
