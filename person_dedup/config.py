"""Leitura do YAML e das pessoas (CSV ou banco)."""

import csv
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from person_dedup.sql_export import ConfigSql, Referencia

CAMPOS = ("id", "nome", "cpf", "nascimento", "email", "telefone", "familia", "vinculos")


@dataclass
class Config:
    fonte_csv: str | None
    fonte_url: str | None
    fonte_sql: str | None
    colunas: dict[str, str]
    limite_data_repetida: int
    limiar_grafia: float
    sql: ConfigSql | None


def _expandir(valor: str) -> str:
    expandido = os.path.expandvars(valor)
    if "${" in expandido:
        raise ValueError(f"Variável de ambiente não definida em: {valor}")
    return expandido


def carregar(caminho: str | Path) -> Config:
    with open(caminho, encoding="utf-8") as arquivo:
        bruto = yaml.safe_load(arquivo)

    fonte = bruto["fonte"]
    colunas = {campo: campo for campo in CAMPOS} | (bruto.get("colunas") or {})

    sql = None
    if bruto.get("sql"):
        s = bruto["sql"]
        sql = ConfigSql(
            tabela_pessoa=s["tabela_pessoa"],
            pk_pessoa=s.get("pk_pessoa", colunas["id"]),
            colunas=colunas,
            referencias=[Referencia(**r) for r in s.get("referencias", [])],
            sufixo=s.get("sufixo") or f"{date.today():%Y%m%d}",
        )

    return Config(
        fonte_csv=fonte.get("csv"),
        fonte_url=_expandir(fonte["url"]) if fonte.get("url") else None,
        fonte_sql=fonte.get("sql"),
        colunas=colunas,
        limite_data_repetida=int(bruto.get("limite_data_repetida", 15)),
        limiar_grafia=float(bruto.get("limiar_grafia", 0.92)),
        sql=sql,
    )


def ler_pessoas(cfg: Config) -> list[dict]:
    """Devolve as linhas já com os nomes de campo do programa (id, nome, cpf...)."""
    if cfg.fonte_csv:
        with open(cfg.fonte_csv, encoding="utf-8-sig", newline="") as arquivo:
            brutas = list(csv.DictReader(arquivo, delimiter=";"))
    else:
        from sqlalchemy import create_engine, text

        with create_engine(cfg.fonte_url).connect() as conexao:
            brutas = [dict(l) for l in conexao.execute(text(cfg.fonte_sql)).mappings()]

    return [{campo: linha.get(coluna) for campo, coluna in cfg.colunas.items()} for linha in brutas]
