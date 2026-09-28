from pydantic import BaseModel
from typing import Optional, List

from model.local import Local


class LocalSchema(BaseModel):
    """
    Define os dados necessários para cadastrar um novo local.
    """
    nome: str
    descricao: Optional[str] = None


class LocalViewSchema(BaseModel):
    """
    Define como um local será retornado pela API.
    """
    id: int
    nome: str
    descricao: Optional[str] = None


class ListagemLocaisSchema(BaseModel):
    """
    Define como a listagem de locais será retornada.
    """
    locais: List[LocalViewSchema]


def apresenta_local(local: Local):
    """
    Converte um objeto Local do SQLAlchemy
    para uma representação apropriada para a API.
    """
    return {
        "id": local.id,
        "nome": local.nome,
        "descricao": local.descricao
    }


def apresenta_locais(locais: List[Local]):
    """
    Converte uma lista de objetos Local
    para uma representação apropriada para a API.
    """
    resultado = []

    for local in locais:
        resultado.append(
            apresenta_local(local)
        )

    return {
        "locais": resultado
    }