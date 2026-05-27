# ============================================================
# AIPI COBERTURA - PROCESO AUTOMATIZABLE EN GITHUB ACTIONS
# ============================================================

import os
import re
from pathlib import Path

import pandas as pd


# ============================================================
# 0. CONFIGURACIÓN
# ============================================================

# En local puedes definir AIPI_BASE_DIR. En GitHub Actions usa ./data por defecto.
BASE_DIR = Path(os.getenv("AIPI_BASE_DIR", "data"))

RAW_INSTITUCIONAL_8H = BASE_DIR / "INSTITUCIONAL_8H"
RAW_JARDINES_INTEGRALES = BASE_DIR / "JARDINES_INTEGRALES"
OUTPUT_DIR = Path(os.getenv("AIPI_OUTPUT_DIR", "output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DICCIONARIO_PATH = BASE_DIR / "DICCIONARIO.xlsx"

COLUMNAS_ESTANDAR = [
    "numero_contrato",
    "entidad",
    "modalidad",
    "cupos_totales_contrato",
    "id_sede",
    "nombre_sede",
    "comuna_sede",
    "fecha_inicio_atención",
    "fecha_fin_atención",
    "cupos_sede_salas_generales",
    "cupos_sede_salas_cunas",
    "matriculados_salas_generales",
    "matriculados_salas_cunas",
]

COLUMNAS_TECNICAS = [
    "fecha_corte",
    "archivo_origen",
    "fecha_carga",
]


# ============================================================
# 1. FUNCIONES
# ============================================================

def aplicar_diccionario_sedes(
    df: pd.DataFrame,
    df_diccionario: pd.DataFrame
) -> pd.DataFrame:
    df = df.copy()
    df["id_sede"] = df["id_sede"].astype(str).str.strip()

    df = df.drop(columns=["nombre_sede", "modalidad", "comuna_sede"], errors="ignore")

    df = df.merge(
        df_diccionario,
        on="id_sede",
        how="left",
        validate="many_to_one"
    )

    sedes_sin_diccionario = df[df["nombre_sede"].isna()]["id_sede"].drop_duplicates()

    if len(sedes_sin_diccionario) > 0:
        raise ValueError(
            "Hay id_sede que no existen en el DICCIONARIO.xlsx: "
            f"{sedes_sin_diccionario.tolist()}"
        )

    return df

def leer_diccionario_sedes(path_diccionario: Path) -> pd.DataFrame:
    if not path_diccionario.exists():
        raise FileNotFoundError(f"No se encontró el diccionario: {path_diccionario}")

    df_diccionario = pd.read_excel(path_diccionario, sheet_name="DICCIONARIO")

    columnas_requeridas = [
        "id_sede",
        "nombre_sede",
        "modalidad",
        "comuna_sede",
    ]

    faltantes = [
        col for col in columnas_requeridas
        if col not in df_diccionario.columns
    ]

    if faltantes:
        raise ValueError(
            f"El diccionario tiene columnas faltantes: {faltantes}"
        )

    df_diccionario = df_diccionario[columnas_requeridas].copy()
    df_diccionario["id_sede"] = df_diccionario["id_sede"].astype(str).str.strip()

    df_diccionario = df_diccionario.drop_duplicates(subset=["id_sede"], keep="last")

    return df_diccionario

def extraer_fecha_corte(nombre_archivo: str) -> pd.Timestamp:
    """
    Extrae fecha de corte desde nombres tipo:
    20260521_i8h.xlsx
    20260521_ji.xlsx
    """
    patron = r"^(\d{8})_"
    match = re.match(patron, nombre_archivo)

    if not match:
        raise ValueError(f"Nombre de archivo inválido: {nombre_archivo}")

    return pd.to_datetime(match.group(1), format="%Y%m%d")


def listar_archivos_excel(carpeta: Path) -> list[Path]:
    """Lista archivos Excel dentro de una carpeta, excluyendo temporales."""
    if not carpeta.exists():
        print(f"Advertencia: la carpeta no existe: {carpeta}")
        return []

    return [
        archivo
        for archivo in carpeta.glob("*.xlsx")
        if not archivo.name.startswith("~$")
    ]


def leer_archivo_estandar(path_archivo: Path) -> pd.DataFrame:
    return pd.read_excel(path_archivo)


def validar_columnas_estandar(df: pd.DataFrame, path_archivo: Path) -> bool:
    columnas_archivo = list(df.columns)

    columnas_faltantes = [
        col for col in COLUMNAS_ESTANDAR
        if col not in columnas_archivo
    ]

    if columnas_faltantes:
        raise ValueError(
            f"El archivo {path_archivo.name} tiene columnas faltantes: {columnas_faltantes}"
        )

    return True


def procesar_archivo(path_archivo: Path) -> pd.DataFrame:
    fecha_corte = extraer_fecha_corte(path_archivo.name)
    df = leer_archivo_estandar(path_archivo)
    validar_columnas_estandar(df, path_archivo)

    df = df[COLUMNAS_ESTANDAR].copy()
    df["fecha_corte"] = fecha_corte
    df["archivo_origen"] = path_archivo.name
    df["fecha_carga"] = pd.Timestamp.now(tz="America/Bogota").tz_localize(None)

    return df


def transformar_formato_largo(df: pd.DataFrame) -> pd.DataFrame:
    columnas_fijas = [
        "numero_contrato",
        "entidad",
        "modalidad",
        "cupos_totales_contrato",
        "id_sede",
        "nombre_sede",
        "comuna_sede",
        "fecha_inicio_atención",
        "fecha_fin_atención",
        "fecha_corte",
        "archivo_origen",
        "fecha_carga",
    ]

    df_generales = df[columnas_fijas].copy()
    df_generales["tipo_sala"] = "salas_generales"
    df_generales["cupos"] = df["cupos_sede_salas_generales"]
    df_generales["matriculados"] = df["matriculados_salas_generales"]
    df_generales["disponibles"] = df_generales["cupos"] - df_generales["matriculados"]

    df_cunas = df[columnas_fijas].copy()
    df_cunas["tipo_sala"] = "salas_cunas"
    df_cunas["cupos"] = df["cupos_sede_salas_cunas"]
    df_cunas["matriculados"] = df["matriculados_salas_cunas"]
    df_cunas["disponibles"] = df_cunas["cupos"] - df_cunas["matriculados"]

    df_salas = pd.concat([df_generales, df_cunas], ignore_index=True)

    return df_salas.melt(
        id_vars=columnas_fijas + ["tipo_sala"],
        value_vars=["cupos", "matriculados", "disponibles"],
        var_name="metrica",
        value_name="valor",
    )


def main() -> None:
    df_diccionario = leer_diccionario_sedes(DICCIONARIO_PATH)
    
    archivos_institucional_8h = listar_archivos_excel(RAW_INSTITUCIONAL_8H)
    archivos_jardines_integrales = listar_archivos_excel(RAW_JARDINES_INTEGRALES)
    archivos_totales = archivos_institucional_8h + archivos_jardines_integrales

    if not archivos_totales:
        raise ValueError(
            "No se encontraron archivos Excel para procesar. "
            f"Revisa las carpetas: {RAW_INSTITUCIONAL_8H} y {RAW_JARDINES_INTEGRALES}"
        )

    dfs = []
    for archivo in archivos_totales:
        print(f"Procesando: {archivo.name}")
        dfs.append(procesar_archivo(archivo))

    df_consolidado = pd.concat(dfs, ignore_index=True)

    df_consolidado = aplicar_diccionario_sedes(
        df_consolidado,
        df_diccionario
    )
    
    df_consolidado = df_consolidado[COLUMNAS_ESTANDAR + COLUMNAS_TECNICAS]
    df_largo = transformar_formato_largo(df_consolidado)

    df_auditoria_archivos = pd.DataFrame({
        "archivo_origen": [archivo.name for archivo in archivos_totales]
    })
    df_auditoria_archivos["fecha_corte"] = pd.to_datetime(
        df_auditoria_archivos["archivo_origen"].str.extract(r"^(\d{8})_")[0],
        format="%Y%m%d",
    )
    df_auditoria_archivos["fecha_carga"] = pd.Timestamp.now(tz="America/Bogota").tz_localize(None)

    output_parquet = OUTPUT_DIR / "AIPI_COBERTURA.parquet"
    output_excel = OUTPUT_DIR / "AIPI_COBERTURA.xlsx"

    df_largo.to_parquet(output_parquet, index=False)

    with pd.ExcelWriter(output_excel) as writer:
        df_largo.to_excel(writer, sheet_name="AIPI_COBERTURA", index=False)
        df_auditoria_archivos.to_excel(writer, sheet_name="AUD_ARCHIVOS", index=False)

    print("Proceso terminado correctamente.")
    print(f"Filas analíticas: {len(df_largo):,}")
    print(f"Parquet generado: {output_parquet}")
    print(f"Excel generado: {output_excel}")


if __name__ == "__main__":
    main()
