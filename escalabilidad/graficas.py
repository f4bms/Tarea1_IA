"""Gráficas y resumen del estudio de escalabilidad.

Lee el resultados.csv que produce escalabilidad.bateria y genera:

  * tendencia_tiempo_N.png    tiempo vs N (una línea por K), un panel por agente
  * tendencia_tiempo_K.png    tiempo vs K (una línea por N), un panel por agente
  * tendencia_esfuerzo_N.png  nodos expandidos / evaluaciones vs N
  * calidad_colocadas_N.png   % de fichas colocadas vs N
  * calidad_ocupadas_K.png    celdas ocupadas al terminar vs K
  * mapa_limite.png           en cuántas semillas cada agente colocó todo
                              dentro del límite, por (N, K)
  * resumen.csv               media y desviación estándar por agente, N y K

La tabla resumen reporta además la desviación estándar.

El notebook analisis.ipynb importa estas mismas funciones.
"""

# --- permite correr el archivo directo o desde otra carpeta -------------------
import os as _os
import sys as _sys

_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _RAIZ not in _sys.path:
    _sys.path.insert(0, _RAIZ)
if not _os.path.isdir(_os.path.join(_RAIZ, "motor")):
    _sys.exit("Error: no se encuentra la carpeta 'motor' junto a 'escalabilidad'.\n"
              "La carpeta escalabilidad/ debe estar en la raiz del repositorio, al mismo\n"
              f"nivel que motor/, evolutivo/ y search_algorythm/ (ahora esta en {_RAIZ}).")

import math
import os
import sys

import matplotlib

if __name__ == "__main__":
    matplotlib.use("Agg")  # sin ventana cuando se corre desde la terminal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Estilo
# ---------------------------------------------------------------------------

SUPERFICIE = "#fcfcfb"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
REJILLA = "#e4e3df"
LIMITE = "#e34948"

# rampa azul de un solo tono (N y K son ordinales: claro = pequeño, oscuro = grande)
RAMPA = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6",
         "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
RAMPA_MAPA = ["#f0efec", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
MARCADORES = ["o", "s", "^", "D", "v", "P", "X", "h", "<", ">"]

NOMBRE_AGENTE = {"busqueda": "Agente de búsqueda", "evolutivo": "Agente evolutivo"}
NOMBRE_ESFUERZO = {"busqueda": "nodos expandidos", "evolutivo": "evaluaciones de aptitud"}
NOMBRE_PARAM = {"N": "N (lado del tablero)", "K": "K (cantidad de colores)"}


def estilo():
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "axes.edgecolor": REJILLA,
        "axes.labelcolor": TEXTO_2,
        "axes.titlecolor": TEXTO,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": REJILLA,
        "grid.linewidth": 0.8,
        "xtick.color": TEXTO_2,
        "ytick.color": TEXTO_2,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "font.size": 9.5,
        "figure.dpi": 110,
        "savefig.dpi": 160,
    })


def _colores(n):
    """n pasos de la rampa, del más claro al más oscuro."""
    if n == 1:
        return [RAMPA[4]]
    idx = [round(i * (len(RAMPA) - 1) / (n - 1)) for i in range(n)]
    return [RAMPA[i] for i in idx]


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------

def cargar(ruta_csv):
    df = pd.read_csv(ruta_csv)
    df["pct_colocadas"] = 100 * df["frac_colocadas"]
    df["pct_ocupadas"] = 100 * df["frac_ocupadas"]
    # "terminó dentro del límite": colocó toda la secuencia sin pasarse del tiempo
    df["exito"] = ((df["meta"] == 1) & (df["excedio_limite"] == 0)).astype(int)
    df["corte_tiempo"] = (df["estado"] == "limite_tiempo").astype(int)
    return df


def resumen(df):
    """Media y desviación estándar por agente, N y K (entre semillas)."""
    g = df.groupby(["agente", "N", "K", "M"])
    tabla = g.agg(
        semillas=("semilla", "count"),
        colocadas_media=("colocadas", "mean"),
        colocadas_std=("colocadas", "std"),
        pct_colocadas_media=("pct_colocadas", "mean"),
        ocupadas_media=("ocupadas", "mean"),
        ocupadas_std=("ocupadas", "std"),
        tiempo_media=("tiempo_s", "mean"),
        tiempo_std=("tiempo_s", "std"),
        esfuerzo_media=("esfuerzo", "mean"),
        esfuerzo_std=("esfuerzo", "std"),
        exitos=("exito", "sum"),
        cortes_tiempo=("corte_tiempo", "sum"),
        ilegales=("legal", lambda s: int((s == 0).sum())),
    ).reset_index()
    return tabla.round(3)


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

def _agentes(df):
    return [a for a in ("busqueda", "evolutivo") if a in set(df["agente"])]


def figura_tendencia(df, metrica, x="N", serie="K", log=False, titulo=None,
                     etiqueta_y=None, linea_limite=False, compartir_y=True):
    """Una fila de paneles (uno por agente): `metrica` vs `x`, una línea por `serie`.

    Punto = media entre semillas; barra = rango (mínimo a máximo) entre semillas.
    Se usa el rango y no la desviación estándar porque con 3 semillas la
    desviación es poco estable y, en escala log, media - std suele ser negativa.
    """
    estilo()
    agentes = _agentes(df)
    fig, ejes = plt.subplots(1, len(agentes), figsize=(5.2 * len(agentes), 3.9),
                             sharey=compartir_y, squeeze=False)
    ejes = ejes[0]
    valores_serie = sorted(df[serie].unique())
    colores = _colores(len(valores_serie))
    n_x = len(df[x].unique())
    desplaz = 0.012 * (df[x].max() - df[x].min() or 1)  # para que las barras no se tapen

    finales = {}
    for ax, agente in zip(ejes, agentes):
        sub = df[df["agente"] == agente]
        g = sub.groupby([serie, x])[metrica].agg(["mean", "min", "max"]).reset_index()
        finales[ax] = []
        for i, v in enumerate(valores_serie):
            d = g[g[serie] == v].sort_values(x)
            if d.empty:
                continue
            dx = (i - (len(valores_serie) - 1) / 2) * desplaz if n_x > 1 else 0
            ax.errorbar(d[x] + dx, d["mean"],
                        yerr=[d["mean"] - d["min"], d["max"] - d["mean"]],
                        color=colores[i], marker=MARCADORES[i % len(MARCADORES)],
                        markersize=6, linewidth=2, capsize=3, elinewidth=1.2,
                        markeredgecolor=SUPERFICIE, markeredgewidth=1,
                        label=f"{serie}={v}")
            ult = d.iloc[-1]
            finales[ax].append((ult[x] + dx, ult["mean"], f"{serie}={v}"))
        if linea_limite and "limite_s" in sub:
            lim = sub["limite_s"].max()
            ax.axhline(lim, color=LIMITE, linewidth=1.2, linestyle="--")
            ax.annotate(f"límite = {lim:g} s", (ax.get_xlim()[0], lim),
                        xytext=(4, 4), textcoords="offset points",
                        fontsize=8.5, color=LIMITE)
        if log:
            ax.set_yscale("log")
        ax.set_xticks(sorted(df[x].unique()))
        ax.set_title(NOMBRE_AGENTE.get(agente, agente), loc="left")
        ax.set_xlabel(NOMBRE_PARAM.get(x, x))
        et = etiqueta_y
        if metrica == "esfuerzo":
            et = NOMBRE_ESFUERZO.get(agente, "esfuerzo")
        if et and (ax is ejes[0] or not compartir_y):
            ax.set_ylabel(et)
        ax.margins(x=0.14)

    # etiquetas directas al final de cada línea, separadas para que no se solapen
    if len(valores_serie) <= 4:
        for ax, puntos in finales.items():
            ax.autoscale_view()
            a_ejes = ax.transAxes.inverted()
            pos = []
            for px, py, texto in puntos:
                fx, fy = a_ejes.transform(ax.transData.transform((px, py)))
                pos.append([fy, fx, texto])
            pos.sort()
            hueco = 0.065
            for j in range(1, len(pos)):
                pos[j][0] = max(pos[j][0], pos[j - 1][0] + hueco)
            exceso = pos[-1][0] - 0.98 if pos else 0
            if exceso > 0:
                for p in pos:
                    p[0] -= exceso
                for j in range(len(pos) - 2, -1, -1):
                    pos[j][0] = min(pos[j][0], pos[j + 1][0] - hueco)
            columna = max((p[1] for p in pos), default=0) + 0.025
            for fy, _, texto in pos:
                ax.annotate(texto, xy=(columna, fy), xycoords="axes fraction",
                            va="center", fontsize=8.5, color=TEXTO_2)

    ejes[-1].legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), title=serie)
    if titulo:
        fig.suptitle(titulo, x=0.01, ha="left", fontsize=12, fontweight="bold", color=TEXTO)
    fig.tight_layout()
    return fig


def figura_mapa_limite(df):
    """Mapa N x K: semillas en que el agente colocó todo dentro del límite."""
    estilo()
    agentes = _agentes(df)
    Ns = sorted(df["N"].unique())
    Ks = sorted(df["K"].unique())
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("azul", RAMPA_MAPA)
    fig, ejes = plt.subplots(1, len(agentes), figsize=(4.6 * len(agentes), 3.9), squeeze=False)
    ejes = ejes[0]
    for ax, agente in zip(ejes, agentes):
        sub = df[df["agente"] == agente]
        exitos = sub.pivot_table(index="N", columns="K", values="exito", aggfunc="sum")
        total = sub.pivot_table(index="N", columns="K", values="exito", aggfunc="count")
        cortes = sub.pivot_table(index="N", columns="K", values="corte_tiempo", aggfunc="sum")
        frac = (exitos / total).reindex(index=Ns, columns=Ks)
        ax.imshow(frac.values, cmap=cmap, vmin=0, vmax=1, origin="lower", aspect="auto")
        for i, n in enumerate(Ns):
            for j, k in enumerate(Ks):
                if pd.isna(frac.iloc[i, j]):
                    continue
                e, t = int(exitos.loc[n, k]), int(total.loc[n, k])
                c = int(cortes.loc[n, k]) if agente == "busqueda" else 0
                texto = f"{e}/{t}" + (f"\n{c} por tiempo" if c else "")
                ax.text(j, i, texto, ha="center", va="center", fontsize=8.5,
                        color=SUPERFICIE if frac.iloc[i, j] > 0.6 else TEXTO)
        ax.set_xticks(range(len(Ks)), Ks)
        ax.set_yticks(range(len(Ns)), Ns)
        ax.set_xlabel(NOMBRE_PARAM["K"])
        ax.set_ylabel(NOMBRE_PARAM["N"])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(NOMBRE_AGENTE.get(agente, agente), loc="left")
    fig.suptitle("Semillas que colocan toda la secuencia dentro del límite",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", color=TEXTO)
    fig.tight_layout()
    return fig


def todas_las_figuras(df):
    """Devuelve {nombre_archivo: figura}."""
    return {
        "tendencia_tiempo_N.png": figura_tendencia(
            df, "tiempo_s", x="N", serie="K", log=True, linea_limite=True,
            etiqueta_y="tiempo (s, escala log)",
            titulo="Tiempo de cómputo al crecer el tablero"),
        "tendencia_tiempo_K.png": figura_tendencia(
            df, "tiempo_s", x="K", serie="N", log=True, linea_limite=True,
            etiqueta_y="tiempo (s, escala log)",
            titulo="Tiempo de cómputo al crecer la cantidad de colores"),
        "tendencia_esfuerzo_N.png": figura_tendencia(
            df, "esfuerzo", x="N", serie="K", log=True, compartir_y=False,
            titulo="Esfuerzo del algoritmo al crecer el tablero"),
        "calidad_colocadas_N.png": figura_tendencia(
            df, "pct_colocadas", x="N", serie="K", etiqueta_y="% de fichas colocadas",
            titulo="Fichas colocadas al crecer el tablero"),
        "calidad_ocupadas_K.png": figura_tendencia(
            df, "pct_ocupadas", x="K", serie="N", etiqueta_y="% del tablero ocupado al final",
            titulo="Celdas ocupadas al terminar al crecer la cantidad de colores"),
        "mapa_limite.png": figura_mapa_limite(df),
    }


def guardar_todo(ruta_csv, carpeta):
    df = cargar(ruta_csv)
    os.makedirs(carpeta, exist_ok=True)
    rutas = []
    for nombre, fig in todas_las_figuras(df).items():
        ruta = os.path.join(carpeta, nombre)
        fig.savefig(ruta, bbox_inches="tight")
        plt.close(fig)
        rutas.append(ruta)
    ruta_resumen = os.path.join(carpeta, "resumen.csv")
    resumen(df).to_csv(ruta_resumen, index=False)
    rutas.append(ruta_resumen)
    return rutas


# ---------------------------------------------------------------------------
# Lectura automática (apoyo para escribir el informe)
# ---------------------------------------------------------------------------

def _crecimiento(df, agente, param, otro):
    """Factor por el que crece el tiempo medio de `agente` al llevar `param` de su
    menor a su mayor valor, con `otro` fijo en su menor valor (la configuración
    más fácil). Se mide desde esa esquina porque ahí el tiempo todavía no está
    topado por el límite, que aplanaría la comparación."""
    sub = df[df["agente"] == agente]
    t = sub.groupby([otro, param])["tiempo_s"].mean().unstack(param)
    fila = t.loc[t.index.min()]
    lo, hi = fila.index.min(), fila.index.max()
    if pd.isna(fila[lo]) or pd.isna(fila[hi]):
        return float("nan")
    return float(max(fila[hi], 1e-4) / max(fila[lo], 1e-4))


def lectura(df):
    """Hallazgos clave en texto, calculados desde los datos."""
    lineas = []
    Ns, Ks = sorted(df["N"].unique()), sorted(df["K"].unique())

    for agente in _agentes(df):
        fN = _crecimiento(df, agente, "N", "K")
        fK = _crecimiento(df, agente, "K", "N")
        dom = "N (tamaño del tablero)" if fN >= fK else "K (cantidad de colores)"
        sub = df[df["agente"] == agente]
        topadas = int((sub["tiempo_s"] >= 0.95 * sub["limite_s"]).sum())
        nota = (f" Ojo: {topadas}/{len(sub)} corridas llegan al límite de tiempo, así que en "
                "las configuraciones grandes el tiempo ya no mide el costo real (mire el mapa "
                "de éxitos y las fichas colocadas)." if topadas else "")
        lineas.append(
            f"- {NOMBRE_AGENTE[agente]}: partiendo de N={Ns[0]}, K={Ks[0]}, llevar N hasta "
            f"{Ns[-1]} multiplica el tiempo medio por ~{fN:.0f}; llevar K hasta {Ks[-1]}, "
            f"por ~{fK:.0f}. Crece más con {dom}.{nota}")

    b = df[df["agente"] == "busqueda"]
    if not b.empty:
        fallos = b[b["exito"] == 0]
        if fallos.empty:
            lineas.append("- La búsqueda terminó dentro del límite en todas las configuraciones.")
        else:
            por_k = []
            for k in Ks:
                f = fallos[fallos["K"] == k]
                if not f.empty:
                    n0 = int(f["N"].min())
                    tot = len(b[(b["K"] == k) & (b["N"] == n0)])
                    por_k.append(f"K={k}: desde N={n0} ({len(f[f['N'] == n0])}/{tot} semillas)")
            lineas.append("- Primer N en que la búsqueda deja de colocar todo dentro del "
                          "límite -> " + "; ".join(por_k) + ".")
            cortes = int(b["corte_tiempo"].sum())
            lineas.append(f"- De esos fallos, {cortes} de {len(fallos)} fueron por agotar el "
                          "tiempo (el resto, derrota o frontera vacía).")

            claves = set(zip(fallos["N"], fallos["K"], fallos["semilla"]))
            e = df[df["agente"] == "evolutivo"]
            e = e[[(n, k, s) in claves for n, k, s in zip(e["N"], e["K"], e["semilla"])]]
            if not e.empty:
                lineas.append(
                    f"- En esas mismas {len(e)} corridas el evolutivo colocó en promedio el "
                    f"{e['pct_colocadas'].mean():.1f} % de las fichas, completó la secuencia en "
                    f"{int(e['meta'].sum())}/{len(e)} y tardó {e['tiempo_s'].mean():.2f} s de media.")

    ilegales = int((df["legal"] == 0).sum())
    lineas.append(f"- Soluciones ilegales detectadas al rejugar: {ilegales}.")
    excedidas = df[df["excedio_limite"] == 1]
    if not excedidas.empty:
        exceso = excedidas["tiempo_s"] - excedidas["limite_s"]
        peor = excedidas.loc[exceso.idxmax()]
        por_agente = ", ".join(f"{a}: {n}" for a, n in excedidas["agente"].value_counts().items())
        lineas.append(f"- Corridas que se pasaron del límite de tiempo: {len(excedidas)} "
                      f"({por_agente}); exceso máximo {exceso.max():.2f} s "
                      f"({peor['agente']} N={peor['N']} K={peor['K']} s={peor['semilla']}).")
    return "\n".join(lineas)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    argv = [os.path.abspath(a) for a in argv]  # rutas dadas: relativas a donde se ejecuta
    _os.chdir(_RAIZ)  # rutas por defecto: relativas a la raíz del repo
    ruta_csv = argv[0] if argv else os.path.join("escalabilidad", "resultados", "resultados.csv")
    carpeta = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(ruta_csv), "graficas")
    if not os.path.exists(ruta_csv):
        print(f"Error: no existe {ruta_csv}. Corra primero la batería "
              "(make escalabilidad o python3 -m escalabilidad.bateria).", file=sys.stderr)
        return 1
    for r in guardar_todo(ruta_csv, carpeta):
        print(f"escrito {r}")
    print()
    print(lectura(cargar(ruta_csv)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
