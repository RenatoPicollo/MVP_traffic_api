from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# importando os elementos definidos no modelo
from model.base import Base
from model.registro import Registro
from model.local import Local

db_path = "database/"
# Verifica se o diretorio não existe
if not os.path.exists(db_path):
   # então cria o diretorio
   os.makedirs(db_path)

# url de acesso ao banco (essa é uma url de acesso ao sqlite local)
db_url = 'sqlite:///%s/db.sqlite3' % db_path

# cria a engine de conexão com o banco
engine = create_engine(db_url, echo=False)

# Instancia um criador de seção com o banco
Session = sessionmaker(bind=engine)

# cria o banco se ele não existir
if not database_exists(engine.url):
    create_database(engine.url)

# cria as tabelas do banco, caso não existam
Base.metadata.create_all(engine)

# ============================================================
# DADOS INICIAIS
# ============================================================

def inicializar_locais():
    """
    Cria locais padrão caso eles ainda não existam no banco.
    """

    session = Session()

    locais_padrao = [
        {
            "nome": "Av. Santa Cruz",
            "descricao": "Câmera na Av. Santa Cruz"
        },
        {
            "nome": "Av. Cesário de Melo",
            "descricao": "Câmera na Av. Cesário de Melo"
        },
        {
            "nome": "Estrada do Cabuçu",
            "descricao": "Câmera na Estrada do Cabuçu"
        },
        {
            "nome": "Estrada da Cachamorra",
            "descricao": "Câmera na Estrada da Cachamorra"
        }
    ]

    try:

        for dados_local in locais_padrao:

            local_existente = (
                session
                .query(Local)
                .filter(
                    Local.nome == dados_local["nome"]
                )
                .first()
            )

            if not local_existente:

                novo_local = Local(
                    nome=dados_local["nome"],
                    descricao=dados_local["descricao"]
                )

                session.add(
                    novo_local
                )

        session.commit()

    except Exception:

        session.rollback()
        raise

    finally:

        session.close()


inicializar_locais()