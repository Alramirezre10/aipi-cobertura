import os
from pathlib import Path

import msal
import requests


GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


def get_access_token() -> str:
    tenant_id = os.environ["TENANT_ID"]
    client_id = os.environ["CLIENT_ID"]
    client_secret = os.environ["CLIENT_SECRET"]

    authority = f"https://login.microsoftonline.com/{tenant_id}"

    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=authority,
        client_credential=client_secret,
    )

    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )

    if "access_token" not in result:
        raise RuntimeError(f"No se pudo obtener token: {result}")

    return result["access_token"]


def get_headers() -> dict:
    token = get_access_token()
    return {"Authorization": f"Bearer {token}"}


def list_folder_files(onedrive_folder: str) -> list[dict]:
    headers = get_headers()

    url = (
        f"{GRAPH_BASE_URL}/users/{os.environ['ONEDRIVE_USER_ID']}"
        f"/drive/root:/{onedrive_folder}:/children"
    )

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json().get("value", [])


def download_file(download_url: str, local_file_path: str) -> None:
    try:
        print(
            f"Iniciando descarga: {local_file_path}",
            flush=True,
        )

        response = requests.get(
            download_url,
            timeout=120,
        )

        response.raise_for_status()

        with open(local_file_path, "wb") as file:
            file.write(response.content)

        print(
            f"Descarga completada: {local_file_path}",
            flush=True,
        )

    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response else "desconocido"

        print(
            f"ERROR descargando archivo: {local_file_path}",
            flush=True,
        )
        print(
            f"Código HTTP: {status_code}",
            flush=True,
        )
        print(
            f"URL final: {response.url}",
            flush=True,
        )
        print(
            f"Respuesta: {response.text[:500]}",
            flush=True,
        )

        raise


def download_folder_xlsx(onedrive_folder: str, local_folder: Path) -> None:
    local_folder.mkdir(parents=True, exist_ok=True)

    files = list_folder_files(onedrive_folder)

    for item in files:
        name = item["name"]

        if not name.lower().endswith(".xlsx"):
            continue

        if name.startswith("~$"):
            continue

        onedrive_file_path = f"{onedrive_folder}/{name}"
        local_file_path = local_folder / name

        print(f"Descargando: {onedrive_file_path} -> {local_file_path}")
        download_file(onedrive_file_path, local_file_path)


def upload_file(local_file_path: Path, onedrive_folder: str) -> None:
    headers = get_headers()

    file_name = local_file_path.name

    url = (
        f"{GRAPH_BASE_URL}/users/{os.environ['ONEDRIVE_USER_ID']}"
        f"/drive/root:/{onedrive_folder}/{file_name}:/content"
    )

    response = requests.put(
        url,
        headers=headers,
        data=local_file_path.read_bytes(),
    )
    response.raise_for_status()

    print(f"Subido a OneDrive: {onedrive_folder}/{file_name}")


def upload_folder(local_folder: Path, onedrive_folder: str) -> None:
    for file_path in local_folder.iterdir():
        if file_path.is_file():
            upload_file(file_path, onedrive_folder)
