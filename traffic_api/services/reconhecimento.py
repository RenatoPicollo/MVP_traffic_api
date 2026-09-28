import re
from functools import lru_cache

import cv2
import easyocr
import numpy as np


# ============================================================
# PADRÕES DE PLACAS BRASILEIRAS
# ============================================================

# Padrão antigo:
# ABC1234
# LLLNNNN
PADRAO_ANTIGO = re.compile(
    r"^[A-Z]{3}[0-9]{4}$"
)

# Padrão Mercosul:
# ABC1D23
# LLLNLNN
PADRAO_MERCOSUL = re.compile(
    r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$"
)


FORMATO_ANTIGO = "LLLNNNN"
FORMATO_MERCOSUL = "LLLNLNN"


# ============================================================
# MAPAS PARA CORREÇÃO DE ERROS TÍPICOS DE OCR
# ============================================================

# Quando naquela posição esperamos uma LETRA,
# mas o OCR reconheceu um NÚMERO.
MAPA_NUMERO_PARA_LETRA = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "4": "A",
    "5": "S",
    "6": "G",
    "8": "B"
}


# Quando naquela posição esperamos um NÚMERO,
# mas o OCR reconheceu uma LETRA.
MAPA_LETRA_PARA_NUMERO = {
    "O": "0",
    "Q": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "A": "4",
    "S": "5",
    "G": "6",
    "B": "8"
}


# ============================================================
# EXCEÇÃO PERSONALIZADA
# ============================================================

class PlacaNaoIdentificadaError(Exception):
    """Erro lançado quando nenhuma placa válida é encontrada na imagem."""
    pass


# ============================================================
# EASY OCR
# ============================================================

@lru_cache(maxsize=1)
def _obter_leitor():
    """
    Carrega o modelo EasyOCR apenas uma vez.

    Como a criação do Reader é relativamente pesada,
    o lru_cache evita recarregar o modelo a cada requisição.
    """

    return easyocr.Reader(
        ["en"],
        gpu=False
    )


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_placa(texto: str) -> str:
    """
    Remove espaços, hífens e símbolos.

    Também converte todas as letras para maiúsculas.

    Exemplos:

        abc-1d23 -> ABC1D23
        ABC 1234 -> ABC1234
    """

    return re.sub(
        r"[^A-Z0-9]",
        "",
        texto.upper()
    )


# ============================================================
# VALIDAÇÃO
# ============================================================

def placa_valida(placa: str) -> bool:
    """
    Verifica se a placa está em um dos formatos aceitos:

    Antigo:
        ABC1234

    Mercosul:
        ABC1D23
    """

    return bool(
        PADRAO_ANTIGO.fullmatch(placa)
        or
        PADRAO_MERCOSUL.fullmatch(placa)
    )


# ============================================================
# CORREÇÃO CONTEXTUAL
# ============================================================

def corrigir_por_padrao(texto: str, formato: str):
    """
    Tenta corrigir erros de OCR usando a posição esperada
    de letras e números.

    formato:
        L = letra
        N = número

    Exemplos:

        02L7H33
        LLLNLNN
        ↓
        OZL7H33

    Retorna:

        (placa_corrigida, quantidade_de_correcoes)

    ou:

        None

    caso a sequência não possa ser corrigida.
    """

    texto = normalizar_placa(texto)

    if len(texto) != len(formato):
        return None

    caracteres = list(texto)

    correcoes = 0

    for posicao, tipo_esperado in enumerate(formato):

        caractere = caracteres[posicao]

        # ----------------------------------------------------
        # Nesta posição deveria existir uma LETRA
        # ----------------------------------------------------

        if tipo_esperado == "L":

            if caractere.isalpha():
                continue

            if caractere in MAPA_NUMERO_PARA_LETRA:

                caracteres[posicao] = (
                    MAPA_NUMERO_PARA_LETRA[caractere]
                )

                correcoes += 1

            else:
                return None

        # ----------------------------------------------------
        # Nesta posição deveria existir um NÚMERO
        # ----------------------------------------------------

        elif tipo_esperado == "N":

            if caractere.isdigit():
                continue

            if caractere in MAPA_LETRA_PARA_NUMERO:

                caracteres[posicao] = (
                    MAPA_LETRA_PARA_NUMERO[caractere]
                )

                correcoes += 1

            else:
                return None

    placa_corrigida = "".join(caracteres)

    return placa_corrigida, correcoes


# ============================================================
# GERA CANDIDATOS DE PLACA
# ============================================================

def gerar_candidatos_placa(texto: str):
    """
    Recebe um texto reconhecido pelo OCR e tenta interpretá-lo
    como placa antiga ou Mercosul.

    Retorna uma lista:

        [
            (placa, numero_de_correcoes),
            ...
        ]
    """

    texto = normalizar_placa(texto)

    candidatos = []

    # --------------------------------------------------------
    # Se já for uma placa válida, não há nada para corrigir.
    # --------------------------------------------------------

    if placa_valida(texto):

        candidatos.append(
            (texto, 0)
        )

        return candidatos

    # --------------------------------------------------------
    # Tenta interpretar como placa antiga
    # --------------------------------------------------------

    resultado_antigo = corrigir_por_padrao(
        texto,
        FORMATO_ANTIGO
    )

    if resultado_antigo:

        placa, correcoes = resultado_antigo

        if PADRAO_ANTIGO.fullmatch(placa):

            candidatos.append(
                (placa, correcoes)
            )

    # --------------------------------------------------------
    # Tenta interpretar como Mercosul
    # --------------------------------------------------------

    resultado_mercosul = corrigir_por_padrao(
        texto,
        FORMATO_MERCOSUL
    )

    if resultado_mercosul:

        placa, correcoes = resultado_mercosul

        if PADRAO_MERCOSUL.fullmatch(placa):

            candidatos.append(
                (placa, correcoes)
            )

    return candidatos


# ============================================================
# DECODIFICAÇÃO DA IMAGEM
# ============================================================

def _decodificar_imagem(imagem_bytes: bytes):
    """
    Converte os bytes recebidos pelo Flask
    para uma imagem OpenCV.
    """

    if not imagem_bytes:

        raise ValueError(
            "A imagem recebida está vazia."
        )

    vetor = np.frombuffer(
        imagem_bytes,
        dtype=np.uint8
    )

    imagem = cv2.imdecode(
        vetor,
        cv2.IMREAD_COLOR
    )

    if imagem is None:

        raise ValueError(
            "Não foi possível decodificar a imagem enviada."
        )

    return imagem


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def reconhecer_placa(imagem_bytes: bytes) -> str:
    """
    Recebe os bytes de uma imagem e devolve
    uma placa brasileira normalizada.

    Exemplos:

        ABC1234
        ABC1D23

    O algoritmo:

    1. decodifica a imagem;
    2. cria versões para OCR;
    3. executa EasyOCR;
    4. normaliza os textos;
    5. tenta corrigir erros típicos;
    6. testa placas antiga e Mercosul;
    7. escolhe o melhor candidato.
    """

    imagem = _decodificar_imagem(
        imagem_bytes
    )

    # --------------------------------------------------------
    # Versão em escala de cinza
    # --------------------------------------------------------

    cinza = cv2.cvtColor(
        imagem,
        cv2.COLOR_BGR2GRAY
    )

    # Aumenta o contraste
    cinza = cv2.equalizeHist(
        cinza
    )

    leitor = _obter_leitor()

    candidatos = []

    # --------------------------------------------------------
    # Testamos:
    #
    # 1. imagem original
    # 2. imagem em escala de cinza
    # --------------------------------------------------------

    for imagem_ocr in (
        imagem,
        cinza
    ):

        resultados = leitor.readtext(
            imagem_ocr,
            detail=1,
            allowlist=(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "0123456789"
            )
        )

        textos_encontrados = []

        # ----------------------------------------------------
        # Analisa cada texto individualmente
        # ----------------------------------------------------

        for _, texto, confianca in resultados:

            texto_normalizado = normalizar_placa(
                texto
            )

            confianca = float(
                confianca
            )

            print(
                f"OCR: '{texto}' "
                f"-> '{texto_normalizado}' "
                f"| confiança: {confianca:.2f}"
            )

            textos_encontrados.append(
                (
                    texto_normalizado,
                    confianca
                )
            )

            candidatos_texto = (
                gerar_candidatos_placa(
                    texto_normalizado
                )
            )

            for placa, correcoes in candidatos_texto:

                if placa != texto_normalizado:

                    print(
                        f"Correção contextual: "
                        f"'{texto_normalizado}' "
                        f"-> '{placa}' "
                        f"({correcoes} correção(ões))"
                    )

                candidatos.append(
                    (
                        placa,
                        confianca,
                        correcoes
                    )
                )

        # ----------------------------------------------------
        # Também tenta juntar dois textos consecutivos.
        #
        # Isso ajuda caso o OCR enxergue, por exemplo:
        #
        # ABC
        # 1D23
        #
        # separadamente.
        # ----------------------------------------------------

        for i in range(
            len(textos_encontrados) - 1
        ):

            texto1, confianca1 = (
                textos_encontrados[i]
            )

            texto2, confianca2 = (
                textos_encontrados[i + 1]
            )

            combinado = (
                texto1 + texto2
            )

            # Só faz sentido testar placa de 7 caracteres.
            if len(combinado) != 7:
                continue

            confianca_media = (
                confianca1 + confianca2
            ) / 2

            candidatos_combinados = (
                gerar_candidatos_placa(
                    combinado
                )
            )

            for placa, correcoes in candidatos_combinados:

                print(
                    f"OCR combinado: "
                    f"'{texto1}' + '{texto2}' "
                    f"-> '{placa}'"
                )

                candidatos.append(
                    (
                        placa,
                        confianca_media,
                        correcoes
                    )
                )

    # ========================================================
    # NENHUMA PLACA ENCONTRADA
    # ========================================================

    if not candidatos:

        raise PlacaNaoIdentificadaError(
            "Nenhuma placa brasileira válida "
            "foi identificada na imagem."
        )

    # ========================================================
    # ESCOLHA DO MELHOR CANDIDATO
    # ========================================================
    #
    # Não usamos apenas a confiança do EasyOCR.
    #
    # Também penalizamos candidatos que precisaram de muitas
    # correções.
    #
    # Exemplo:
    #
    # OCR 1:
    # 0217133
    # confiança = 0.47
    # 4 correções
    #
    # OCR 2:
    # 02L7H33
    # confiança = 0.52
    # 2 correções
    #
    # O segundo deve ser favorecido.
    # ========================================================

    def pontuacao(candidato):

        placa, confianca, correcoes = candidato

        penalidade = (
            correcoes * 0.05
        )

        return (
            confianca - penalidade
        )

    melhor = max(
        candidatos,
        key=pontuacao
    )

    placa, confianca, correcoes = melhor

    print(
        f"PLACA ESCOLHIDA: '{placa}' "
        f"| confiança OCR: {confianca:.2f} "
        f"| correções: {correcoes}"
    )

    return placa