"""Normalização dos campos antes de comparar pessoas."""

import re
import unicodedata
from collections import Counter
from datetime import date, datetime

NOMES_LIXO = {"NAO DECLARADO", "NAO INFORMADO", "NAO CONSTA", "DESCONHECIDO", "TESTE", "X"}


def nome(valor: str | None) -> str:
    """'  José  da Silva-Júnior ' -> 'JOSE DA SILVA JUNIOR'"""
    if not valor:
        return ""
    sem_acento = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode()
    so_letras = re.sub(r"[^A-Za-z ]+", " ", sem_acento)
    return re.sub(r"\s+", " ", so_letras).strip().upper()


def nome_valido(nome_normalizado: str) -> bool:
    return len(nome_normalizado) >= 3 and nome_normalizado not in NOMES_LIXO


def cpf(valor: str | None) -> str | None:
    """Só dígitos, e só se o CPF for válido (dígitos verificadores). Inválido = desconhecido."""
    if not valor:
        return None
    digitos = re.sub(r"\D", "", str(valor))
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return None
    for tamanho in (9, 10):
        soma = sum(int(d) * (tamanho + 1 - i) for i, d in enumerate(digitos[:tamanho]))
        dv = (soma * 10) % 11 % 10
        if dv != int(digitos[tamanho]):
            return None
    return digitos


def data(valor) -> date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()[:10]
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    return None


def datas_de_preenchimento(datas: list[date | None], limite_repeticao: int) -> set[date]:
    """Datas que não provam nada: ano <= 1900 ou repetidas em muita gente (01/01/1900...)."""
    contagem = Counter(d for d in datas if d)
    return {d for d, q in contagem.items() if d.year <= 1900 or q >= limite_repeticao}


def email(valor: str | None) -> str | None:
    if not valor:
        return None
    texto = str(valor).strip().lower()
    return texto if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", texto) else None


def telefone(valor: str | None) -> str | None:
    if not valor:
        return None
    digitos = re.sub(r"\D", "", str(valor))
    return digitos if len(digitos) >= 10 else None
