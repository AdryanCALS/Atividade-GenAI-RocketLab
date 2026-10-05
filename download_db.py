"""
Módulo para download automático e empacotamento do banco de dados CineData (SQLite).

Permite que o repositório seja hospedado no GitHub sem versionar o arquivo de ~581 MB.
O banco é obtido sob demanda via GitHub Releases (ou qualquer outra URL configurada).
"""

import argparse
import os
import shutil
import sqlite3
import sys
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional

# Diretórios padrão
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "cinerocket.db"
ZIP_PATH = PROJECT_ROOT / "cinerocket.db.zip"

# URL padrão para download do release no GitHub (pode ser sobrescrita via .env ou CLI)
DEFAULT_RELEASE_URL = os.getenv(
    "CINEDATA_DB_URL",
    "https://github.com/SEU_USUARIO/SEU_REPOSITORIO/releases/download/v1.0.0/cinerocket.db.zip",
)


def is_database_ready(db_path: Optional[Path] = None) -> bool:
    """Verifica se o banco existe localmente e possui tamanho mínimo válido."""
    target = db_path or DB_PATH
    if not target.exists() or not target.is_file():
        return False
    # Tamanho mínimo razoável para o cinerocket (mais de 10 MB)
    return target.stat().st_size > 10 * 1024 * 1024


def verify_database_integrity(db_path: Optional[Path] = None) -> bool:
    """Executa checagem básica de integridade no SQLite."""
    target = db_path or DB_PATH
    if not target.exists():
        return False
    try:
        conn = sqlite3.connect(f"file:{target.resolve()}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("PRAGMA quick_check;")
        result = cur.fetchone()
        conn.close()
        return result is not None and result[0] == "ok"
    except Exception:
        return False


def package_database(
    source_db: Optional[Path] = None,
    output_zip: Optional[Path] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Path:
    """
    Compacta o cinerocket.db local em um arquivo .zip otimizado para upload no GitHub Releases.
    """
    src = source_db or DB_PATH
    out = output_zip or ZIP_PATH

    if not src.exists():
        raise FileNotFoundError(f"Banco de dados de origem não encontrado em: {src}")

    if progress_callback:
        progress_callback(f"Compactando {src.name} em {out.name}...")

    start_time = time.time()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(src, arcname=src.name)

    elapsed = time.time() - start_time
    size_mb = out.stat().st_size / (1024 * 1024)

    if progress_callback:
        progress_callback(
            f"Arquivo pronto: {out.name} ({size_mb:.1f} MB) gerado em {elapsed:.1f}s."
        )

    return out


def download_database(
    url: Optional[str] = None,
    dest_db: Optional[Path] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    """
    Faz o download do banco de dados (zip ou db direto) a partir de uma URL.

    - Exibe progresso através do callback `progress_callback(progresso_0_a_1, texto_status)`.
    - Realiza o download para um arquivo temporário antes de substituir o final.
    - Se o arquivo for .zip, descompacta automaticamente cinerocket.db na pasta data/.
    - Valida integridade do SQLite após o término.
    """
    target_db = dest_db or DB_PATH
    download_url = url or DEFAULT_RELEASE_URL

    if is_database_ready(target_db):
        if progress_callback:
            progress_callback(1.0, f"Banco já disponível em: {target_db}")
        return target_db

    target_db.parent.mkdir(parents=True, exist_ok=True)

    is_zip = download_url.lower().endswith(".zip")
    temp_download = target_db.parent / ("download_temp.zip" if is_zip else "download_temp.db")

    if progress_callback:
        progress_callback(0.0, f"Conectando a {download_url}...")

    # Headers para emular cliente e evitar bloqueios por User-Agent genérico
    headers = {"User-Agent": "CineData-Analytics/1.0"}
    req = urllib.request.Request(download_url, headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            total_size = response.getheader("Content-Length")
            total_bytes = int(total_size) if total_size and total_size.isdigit() else 0

            downloaded_bytes = 0
            chunk_size = 1024 * 1024  # 1 MB por bloco

            with open(temp_download, "wb") as f_out:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    downloaded_bytes += len(chunk)

                    if progress_callback:
                        if total_bytes > 0:
                            fraction = min(1.0, downloaded_bytes / total_bytes)
                            mb_done = downloaded_bytes / (1024 * 1024)
                            mb_total = total_bytes / (1024 * 1024)
                            msg = f"Baixando: {mb_done:.1f} MB / {mb_total:.1f} MB ({fraction * 100:.1f}%)"
                        else:
                            mb_done = downloaded_bytes / (1024 * 1024)
                            fraction = 0.5
                            msg = f"Baixando: {mb_done:.1f} MB recebidos..."
                        progress_callback(fraction, msg)

        # Processamento após download
        if is_zip:
            if progress_callback:
                progress_callback(0.95, "Extraindo banco de dados compactado...")

            with zipfile.ZipFile(temp_download, "r") as zf:
                # Procura por cinerocket.db dentro do zip
                db_member = None
                for member in zf.namelist():
                    if member.endswith(".db"):
                        db_member = member
                        break

                if not db_member:
                    raise ValueError("O arquivo .zip baixado não contém nenhum arquivo .db!")

                # Extrai o arquivo
                with zf.open(db_member) as source_f, open(target_db, "wb") as target_f:
                    shutil.copyfileobj(source_f, target_f)

            if temp_download.exists():
                temp_download.unlink()
        else:
            if target_db.exists():
                target_db.unlink()
            shutil.move(temp_download, target_db)

        if progress_callback:
            progress_callback(0.98, "Validando integridade do banco SQLite...")

        if not verify_database_integrity(target_db):
            raise RuntimeError(
                "Falha na validação de integridade do arquivo SQLite baixado. O download pode estar incompleto."
            )

        if progress_callback:
            progress_callback(1.0, "Banco de dados pronto para uso!")

        return target_db

    except Exception as e:
        if temp_download.exists():
            try:
                temp_download.unlink()
            except OSError:
                pass
        raise RuntimeError(f"Erro ao obter o banco de dados de {download_url}: {e}") from e


def cli_progress(fraction: float, msg: str) -> None:
    """Barra de progresso de linha de comando no terminal."""
    bar_length = 30
    filled = int(round(bar_length * fraction))
    bar = "=" * filled + "-" * (bar_length - filled)
    percent = int(fraction * 100)
    sys.stdout.write(f"\r[{bar}] {percent}% | {msg}")
    sys.stdout.flush()
    if fraction >= 1.0:
        sys.stdout.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Utilitário de banco de dados do CineData Analytics (download e empacotamento)."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="URL customizada para download do arquivo (cinerocket.db.zip ou cinerocket.db).",
    )
    parser.add_argument(
        "--package",
        action="store_true",
        help="Empacota o cinerocket.db local em cinerocket.db.zip para upload no GitHub Releases.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Força o download mesmo que o banco de dados já exista localmente.",
    )

    args = parser.parse_args()

    if args.package:
        print("Empacotando banco de dados local...")
        out = package_database(progress_callback=print)
        print(f"\nSucesso! Arquivo pronto para anexar no GitHub Releases:\n-> {out.resolve()}")
        return

    if args.force and DB_PATH.exists():
        print(f"Removendo banco atual ({DB_PATH.name}) para forçar novo download...")
        DB_PATH.unlink()

    if is_database_ready():
        size_mb = DB_PATH.stat().st_size / (1024 * 1024)
        print(f"O banco de dados já está presente e íntegro: {DB_PATH} ({size_mb:.1f} MB)")
        return

    url = args.url or DEFAULT_RELEASE_URL
    print(f"Iniciando download de {url}...")
    try:
        download_database(url=url, progress_callback=cli_progress)
        print(f"Download concluído com sucesso em: {DB_PATH}")
    except Exception as err:
        print(f"\n[ERRO] {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
