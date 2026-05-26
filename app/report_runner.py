import os
from pathlib import Path

from graph_client import download_folder_xlsx, upload_folder
from cobertura import main as run_cobertura


def main():
    print("Descargando archivos desde OneDrive...")

    download_folder_xlsx(
        os.environ["ONEDRIVE_INPUT_INSTITUCIONAL_8H"],
        Path("data/INSTITUCIONAL_8H"),
    )

    download_folder_xlsx(
        os.environ["ONEDRIVE_INPUT_JARDINES_INTEGRALES"],
        Path("data/JARDINES_INTEGRALES"),
    )

    print("Ejecutando proceso de cobertura...")
    run_cobertura()

    print("Subiendo outputs a OneDrive...")
    upload_folder(
        Path("output"),
        os.environ["ONEDRIVE_OUTPUT_FOLDER"],
    )

    print("Proceso completo.")


if __name__ == "__main__":
    main()
