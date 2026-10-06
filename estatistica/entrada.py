"""Leitura de dados numéricos do terminal e de arquivos CSV."""

import csv
import io
import math
from pathlib import Path


class ErroEntrada(ValueError):
    """Um dado informado não pode ser processado como número finito."""


def _numero(texto: str, contexto: str, decimal_virgula: bool = False) -> float:
    valor = texto.strip()
    if not valor:
        raise ErroEntrada(f"{contexto}: campo vazio; informe um número.")
    if decimal_virgula:
        valor = valor.replace(",", ".")
    try:
        numero = float(valor)
    except (ValueError, OverflowError) as exc:
        raise ErroEntrada(f"{contexto}: {texto!r} não é um número válido.") from exc
    if not math.isfinite(numero):
        raise ErroEntrada(f"{contexto}: {texto!r} não é um número finito (NaN/inf).")
    return numero


def ler_dados_manuais(texto: str) -> list[float]:
    """Aceita vírgula entre números com ponto decimal, ou ; com vírgula decimal."""
    if not texto.strip():
        raise ErroEntrada("Nenhum dado informado; digite pelo menos um número.")
    separador = ";" if ";" in texto else ","
    return [
        _numero(valor, f"Valor {indice}", decimal_virgula=separador == ";")
        for indice, valor in enumerate(texto.split(separador), start=1)
    ]


def _delimitador(texto: str) -> str:
    """Prioriza ;/tab para que uma vírgula decimal não vire um separador."""
    amostra = texto[:65536]
    try:
        detector = csv.Sniffer()
        detector.preferred = [";", "\t", ","]
        return detector.sniff(amostra, delimiters=";\t,").delimiter
    except csv.Error:
        # Arquivos de uma coluna podem não ter separador. Em arquivos irregulares,
        # a validação posterior deve apontar a célula problemática sem descartá-la.
        linhas = [linha for linha in amostra.splitlines() if linha.strip()]
        primeira = linhas[0] if linhas else ""
        if ";" in primeira:
            return ";"
        if "\t" in primeira:
            return "\t"
        return ","


def ler_csv(
    caminho: str | Path,
    coluna: str | int | None = None,
    cabecalho: bool = False,
) -> list[float]:
    """Lê todas as células numéricas ou uma coluna (nome ou índice a partir de 1).

    Cabeçalhos nunca são inferidos: devem ser solicitados explicitamente.
    Só linhas fisicamente vazias são ignoradas; campos vazios são erros.
    """
    arquivo = Path(caminho)
    try:
        texto = arquivo.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ErroEntrada(f"Arquivo não encontrado: {arquivo}.") from exc
    except PermissionError as exc:
        raise ErroEntrada(f"Sem permissão para ler o arquivo: {arquivo}.") from exc
    except UnicodeError as exc:
        raise ErroEntrada(f"O arquivo {arquivo} deve estar codificado em UTF-8.") from exc
    except OSError as exc:
        raise ErroEntrada(f"Não foi possível ler {arquivo}: {exc}.") from exc

    if not texto.strip():
        raise ErroEntrada(f"O arquivo {arquivo} está vazio.")
    delimitador = _delimitador(texto)
    linhas_fisicas = texto.splitlines(keepends=True)
    leitor = csv.reader(io.StringIO(texto, newline=""), delimiter=delimitador, strict=True)
    dados: list[float] = []
    indice_coluna: int | None = None
    nome_coluna: str | None = None
    if coluna is not None:
        if isinstance(coluna, int) or str(coluna).strip().lstrip("+-").isdigit():
            indice_coluna = int(coluna) - 1
            if indice_coluna < 0:
                raise ErroEntrada("O índice de --coluna deve ser um inteiro a partir de 1.")
        else:
            nome_coluna = str(coluna).strip()
            if not nome_coluna:
                raise ErroEntrada("O nome de --coluna não pode estar vazio.")
            if not cabecalho:
                raise ErroEntrada("Para selecionar uma coluna por nome, use --cabecalho.")

    primeira_linha = True
    linha_anterior = 0
    try:
        for registro in leitor:
            inicio_linha = linha_anterior + 1
            fim_linha = leitor.line_num
            linha_anterior = fim_linha
            original = "".join(linhas_fisicas[inicio_linha - 1 : fim_linha])
            if not original.strip():
                continue
            if primeira_linha and cabecalho:
                primeira_linha = False
                nomes = [valor.strip() for valor in registro]
                if nome_coluna is not None:
                    ocorrencias = [i for i, nome in enumerate(nomes) if nome == nome_coluna]
                    if not ocorrencias:
                        raise ErroEntrada(
                            f"Linha {inicio_linha}: coluna {nome_coluna!r} não encontrada no cabeçalho."
                        )
                    if len(ocorrencias) > 1:
                        raise ErroEntrada(
                            f"Linha {inicio_linha}: coluna {nome_coluna!r} aparece mais de uma vez; "
                            "selecione pelo índice."
                        )
                    indice_coluna = ocorrencias[0]
                elif indice_coluna is not None and indice_coluna >= len(registro):
                    raise ErroEntrada(
                        f"Linha {inicio_linha}: cabeçalho possui {len(registro)} coluna(s); "
                        f"a coluna {indice_coluna + 1} não existe."
                    )
                continue
            primeira_linha = False
            if indice_coluna is not None:
                if indice_coluna >= len(registro):
                    raise ErroEntrada(
                        f"Linha {inicio_linha}: possui {len(registro)} coluna(s); "
                        f"a coluna {indice_coluna + 1} não existe."
                    )
                celulas = [(indice_coluna, registro[indice_coluna])]
            else:
                celulas = list(enumerate(registro))
            for indice, valor in celulas:
                dados.append(
                    _numero(
                        valor,
                        f"Linha {inicio_linha}, coluna {indice + 1}",
                        decimal_virgula=delimitador in (";", "\t"),
                    )
                )
    except csv.Error as exc:
        raise ErroEntrada(f"CSV inválido próximo à linha {leitor.line_num}: {exc}.") from exc
    if not dados:
        raise ErroEntrada(f"O arquivo {arquivo} não contém dados numéricos para analisar.")
    return dados
