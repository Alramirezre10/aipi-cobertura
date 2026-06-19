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


def download_file(
    item_id: str,
    local_file_path: Path,
    remote_file_path: str,
) -> None:
    headers = get_headers()

    url = (
        f"{GRAPH_BASE_URL}/users/{os.environ['ONEDRIVE_USER_ID']}"
        f"/drive/items/{item_id}/content"
    )

    print(
        f"Iniciando descarga: {remote_file_path}",
        flush=True,
    )

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=120,
            allow_redirects=True,
        )

        response.raise_for_status()
        local_file_path.write_bytes(response.content)

        print(
            f"Descarga completada: {local_file_path}",
            flush=True,
        )

    except requests.RequestException as exc:
        response = getattr(exc, "response", None)

        status_code = (
            response.status_code
            if response is not None
            else "sin respuesta HTTP"
        )

        detail = (
            response.text[:500]
            if response is not None
            else str(exc)
        )

        print(
            f"ERROR descargando: {remote_file_path}",
            flush=True,
        )
        print(
            f"Item ID: {item_id}",
            flush=True,
        )
        print(
            f"Destino: {local_file_path}",
            flush=True,
        )
        print(
            f"Código HTTP: {status_code}",
            flush=True,
        )
        print(
            f"Detalle: {detail}",
            flush=True,
        )

        raise

def download_file_by_path(
    onedrive_file_path: str,
    local_file_path: Path,
) -> None:
    headers = get_headers()

    clean_path = onedrive_file_path.strip("/")

    url = (
        f"{GRAPH_BASE_URL}/users/{os.environ['ONEDRIVE_USER_ID']}"
        f"/drive/root:/{clean_path}:/content"
    )

    print(
        f"Iniciando descarga: {onedrive_file_path}",
        flush=True,
    )

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=120,
            allow_redirects=True,
        )

        response.raise_for_status()

        local_file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        local_file_path.write_bytes(response.content)

        print(
            f"Descarga completada: {local_file_path}",
            flush=True,
        )

    except requests.RequestException as exc:
        response = getattr(exc, "response", None)

        status_code = (
            response.status_code
            if response is not None
            else "sin respuesta HTTP"
        )

        detail = (
            response.text[:500]
            if response is not None
            else str(exc)
        )

        print(
            f"ERROR descargando: {onedrive_file_path}",
            flush=True,
        )
        print(
            f"Destino: {local_file_path}",
            flush=True,
        )
        print(
            f"Código HTTP: {status_code}",
            flush=True,
        )
        print(
            f"Detalle: {detail}",
            flush=True,
        )

        raise

def download_folder_xlsx(
    onedrive_folder: str,
    local_folder: Path,
) -> None:
    local_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = list_folder_files(onedrive_folder)

    for item in files:
        name = item["name"]

        if not name.lower().endswith(".xlsx"):
            continue

        if name.startswith("~$"):
            continue

        remote_file_path = f"{onedrive_folder}/{name}"
        local_file_path = local_folder / name

        print(
            f"Descargando: {remote_file_path} "
            f"-> {local_file_path}",
            flush=True,
        )

        download_file(
            item_id=item["id"],
            local_file_path=local_file_path,
            remote_file_path=remote_file_path,
        )

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
