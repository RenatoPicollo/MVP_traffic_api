from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

from model.base import Base


class Local(Base):
    __tablename__ = "local"

    id = Column(
        Integer,
        primary_key=True
    )

    nome = Column(
        String(100),
        unique=True,
        nullable=False
    )

    descricao = Column(
        String(250),
        nullable=True
    )

    # Relacionamento ORM:
    # um Local pode possuir vários Registros.
    registros = relationship("Registro")

    def __init__(
        self,
        nome: str,
        descricao: str = None
    ):
        """
        Cria um Local.

        Arguments:
            nome: nome do local de captura.
            descricao: descrição opcional do local.
        """

        self.nome = nome
        self.descricao = descricao