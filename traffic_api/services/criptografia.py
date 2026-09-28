import hashlib
import os
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv()


def gerar_nova_chave() -> str:
    """
    Gera uma chave Fernet.

    Execute uma vez e salve o resultado no arquivo .env:

        CHAVE_CRIPTOGRAFIA=...
    """
    return Fernet.generate_key().decode("utf-8")


def _obter_fernet() -> Fernet:
    chave = os.getenv("CHAVE_CRIPTOGRAFIA")

    if not chave:
        raise RuntimeError(
            "A variável CHAVE_CRIPTOGRAFIA não foi configurada no .env."
        )

    try:
        return Fernet(chave.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "CHAVE_CRIPTOGRAFIA inválida."
        ) from exc


def criptografar_placa(placa: str) -> str:
    placa = placa.strip().upper()

    if not placa:
        raise ValueError("A placa não pode ser vazia.")

    return _obter_fernet().encrypt(
        placa.encode("utf-8")
    ).decode("utf-8")


def descriptografar_placa(placa_criptografada: str) -> str:
    try:
        return _obter_fernet().decrypt(
            placa_criptografada.encode("utf-8")
        ).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Não foi possível descriptografar a placa com a chave atual."
        ) from exc


def gerar_id_registro(
    placa_criptografada: str,
    momento: datetime
) -> str:
    """
    ID = SHA-256(placa_criptografada + data/hora)
    """
    conteudo = (
        f"{placa_criptografada}|"
        f"{momento.isoformat(timespec='microseconds')}"
    )

    return hashlib.sha256(
        conteudo.encode("utf-8")
    ).hexdigest()