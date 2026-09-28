from sqlalchemy import Column, String, Date, Time, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date, time

from model.base import Base


class Registro(Base):
    __tablename__ = "registro"

    # Chave primária criada a partir do hash SHA-256
    id = Column(String(64), primary_key=True)

    # Placa já criptografada
    placa_criptografada = Column(String, nullable=False)

    # Data e hora em que o registro foi criado
    data = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)

    # Chave estrangeira para a tabela local
    local_id = Column(
        Integer,
        ForeignKey("local.id"),
        nullable=False
    )

    # Relacionamento ORM com a classe Local
    local = relationship("Local")

    def __init__(
        self,
        id: str,
        placa_criptografada: str,
        data: date,
        hora: time,
        local_id: int
    ):
        """
        Cria um Registro de passagem de veículo.

        Arguments:
            id: identificador único do registro.
            placa_criptografada: placa após criptografia.
            data: data da identificação.
            hora: hora da identificação.
            local_id: identificador do local da captura.
        """

        self.id = id
        self.placa_criptografada = placa_criptografada
        self.data = data
        self.hora = hora
        self.local_id = local_id