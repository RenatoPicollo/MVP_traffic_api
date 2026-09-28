from pydantic import BaseModel
from typing import List
from datetime import date, time

from model.registro import Registro


class RegistroFormSchema(BaseModel):
    """
    Define os dados enviados junto com a imagem
    para criar um novo registro.
    """
    local_id: int


class RegistroBuscaSchema(BaseModel):
    """
    Define os dados necessários para buscar
    um registro pela sua chave primária.
    """
    id: str


class RegistroViewSchema(BaseModel):
    """
    Define como um registro será retornado pela API.
    """
    id: str
    placa_criptografada: str
    data: date
    hora: time
    local_id: int
    local_nome: str


class ListagemRegistrosSchema(BaseModel):
    """
    Define como a listagem de registros será retornada.
    """
    registros: List[RegistroViewSchema]


class RegistroDelSchema(BaseModel):
    """
    Define a resposta após a exclusão de um registro.
    """
    message: str
    id: str


def apresenta_registro(registro: Registro):
    """
    Converte um objeto Registro do SQLAlchemy
    para uma representação apropriada para a API.
    """

    return {
        "id": registro.id,
        "placa_criptografada": registro.placa_criptografada,
        "data": registro.data.isoformat(),
        "hora": registro.hora.isoformat(timespec="seconds"),
        "local_id": registro.local_id,
        "local_nome": registro.local.nome
    }


def apresenta_registros(registros: List[Registro]):
    """
    Converte uma lista de objetos Registro
    para uma representação apropriada para a API.
    """

    resultado = []

    for registro in registros:
        resultado.append(
            apresenta_registro(registro)
        )

    return {
        "registros": resultado
    }