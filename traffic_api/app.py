from datetime import datetime

from flask import redirect, request
from flask_cors import CORS
from flask_openapi3 import OpenAPI, Info, Tag
from sqlalchemy.exc import IntegrityError

from logger import logger

# Você implementará estes elementos seguindo o padrão da aula.
from model import Session, Registro, Local

from schemas import (
    RegistroFormSchema,
    RegistroBuscaSchema,
    RegistroViewSchema,
    ListagemRegistrosSchema,
    RegistroDelSchema,
    LocalSchema,
    LocalViewSchema,
    ListagemLocaisSchema,
    ErrorSchema,
    apresenta_registro,
    apresenta_registros,
    apresenta_locais,
)

from services.reconhecimento import (
    reconhecer_placa,
    PlacaNaoIdentificadaError,
)

from services.criptografia import (
    criptografar_placa,
    gerar_id_registro,
)


info = Info(
    title="API de Controle de Tráfego Veicular",
    version="1.0",
)

app = OpenAPI(__name__, info=info)
CORS(app)

# Limite de 8 MB para upload da imagem.
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


home_tag = Tag(
    name="Documentação",
    description="Documentação da API.",
)

registro_tag = Tag(
    name="Registro",
    description=(
        "Reconhecimento, criptografia, cadastro, "
        "consulta e exclusão de registros veiculares."
    ),
)

local_tag = Tag(
    name="Local",
    description="Cadastro e listagem dos locais de acesso.",
)


@app.get("/", tags=[home_tag])
def home():
    """Redireciona para a documentação OpenAPI."""
    return redirect("/openapi")


@app.post(
    "/registro",
    tags=[registro_tag],
    responses={
        "201": RegistroViewSchema,
        "400": ErrorSchema,
        "404": ErrorSchema,
        "422": ErrorSchema,
    },
)
def add_registro(form: RegistroFormSchema):
    """
    Cria um novo registro veicular.

    multipart/form-data:
    - imagem: arquivo JPG, PNG ou WEBP;
    - local_id: ID do local escolhido no frontend.
    """
    session = Session()

    try:
        # 1) Valida o local antes de executar o OCR.
        local = (
            session.query(Local)
            .filter(Local.id == form.local_id)
            .first()
        )

        if not local:
            return {"message": "Local não encontrado."}, 404

        # 2) Obtém a imagem enviada pelo frontend.
        arquivo = request.files.get("imagem")

        if arquivo is None or arquivo.filename == "":
            return {"message": "Nenhuma imagem foi enviada."}, 400

        tipos_permitidos = {
            "image/jpeg",
            "image/png",
            "image/webp",
        }

        if arquivo.mimetype not in tipos_permitidos:
            return {
                "message": "Utilize uma imagem JPG, PNG ou WEBP."
            }, 400

        imagem_bytes = arquivo.read()

        # 3) Reconhecimento da placa.
        placa = reconhecer_placa(imagem_bytes)

        # Não registre a placa em claro no log.
        logger.info("Placa reconhecida com sucesso.")

        # 4) Criptografia.
        placa_criptografada = criptografar_placa(placa)

        # 5) Data e hora.
        agora = datetime.now()
        data_registro = agora.date()
        hora_registro = agora.time().replace(microsecond=0)

        # 6) ID derivada da placa criptografada + timestamp.
        id_registro = gerar_id_registro(
            placa_criptografada,
            agora,
        )

        # 7) Objeto ORM.
        registro = Registro(
            id=id_registro,
            placa_criptografada=placa_criptografada,
            data=data_registro,
            hora=hora_registro,
            local_id=form.local_id,
        )

        session.add(registro)
        session.commit()

        logger.info(
            "Registro veicular criado: id=%s local_id=%s",
            id_registro,
            form.local_id,
        )

        return apresenta_registro(registro), 201

    except PlacaNaoIdentificadaError as exc:
        session.rollback()
        return {"message": str(exc)}, 422

    except (ValueError, RuntimeError) as exc:
        session.rollback()
        logger.warning("Falha de processamento: %s", exc)
        return {"message": str(exc)}, 400

    except Exception:
        session.rollback()
        logger.exception("Erro inesperado ao criar registro.")
        return {"message": "Não foi possível criar o registro."}, 400

    finally:
        session.close()


@app.get(
    "/registros",
    tags=[registro_tag],
    responses={"200": ListagemRegistrosSchema},
)
def get_registros():
    """Lista todos os registros."""
    session = Session()

    try:
        registros = (
            session.query(Registro)
            .order_by(Registro.data.desc(), Registro.hora.desc())
            .all()
        )

        return apresenta_registros(registros), 200

    finally:
        session.close()


@app.get(
    "/registro",
    tags=[registro_tag],
    responses={
        "200": RegistroViewSchema,
        "404": ErrorSchema,
    },
)
def get_registro(query: RegistroBuscaSchema):
    """Busca um registro por ID."""
    session = Session()

    try:
        registro = (
            session.query(Registro)
            .filter(Registro.id == query.id)
            .first()
        )

        if not registro:
            return {"message": "Registro não encontrado."}, 404

        return apresenta_registro(registro), 200

    finally:
        session.close()


@app.delete(
    "/registro",
    tags=[registro_tag],
    responses={
        "200": RegistroDelSchema,
        "404": ErrorSchema,
    },
)
def del_registro(query: RegistroBuscaSchema):
    """Exclui um registro por ID."""
    session = Session()

    try:
        registro = (
            session.query(Registro)
            .filter(Registro.id == query.id)
            .first()
        )

        if not registro:
            return {"message": "Registro não encontrado."}, 404

        session.delete(registro)
        session.commit()

        return {
            "message": "Registro removido com sucesso.",
            "id": query.id,
        }, 200

    finally:
        session.close()


@app.get(
    "/locais",
    tags=[local_tag],
    responses={"200": ListagemLocaisSchema},
)
def get_locais():
    """
    Lista locais cadastrados.

    O frontend usa esta rota para preencher a lista suspensa.
    """
    session = Session()

    try:
        locais = (
            session.query(Local)
            .order_by(Local.nome)
            .all()
        )

        return apresenta_locais(locais), 200

    finally:
        session.close()


@app.post(
    "/local",
    tags=[local_tag],
    responses={
        "201": LocalViewSchema,
        "409": ErrorSchema,
        "400": ErrorSchema,
    },
)
def add_local(form: LocalSchema):
    """Cadastra um novo local."""
    session = Session()

    try:
        local = Local(
            nome=form.nome,
            descricao=form.descricao,
        )

        session.add(local)
        session.commit()

        return {
            "id": local.id,
            "nome": local.nome,
            "descricao": local.descricao,
        }, 201

    except IntegrityError:
        session.rollback()
        return {"message": "Já existe um local com esse nome."}, 409

    except Exception:
        session.rollback()
        logger.exception("Erro inesperado ao cadastrar local.")
        return {"message": "Não foi possível cadastrar o local."}, 400

    finally:
        session.close()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
