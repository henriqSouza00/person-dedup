"""Gera os scripts SQL (MySQL) para aplicar a unificação no banco.

Segue o método: 01 só confere (SELECT), 02 faz backup e aplica dentro de
transação com o COMMIT comentado, 03 desfaz a partir do backup.
Os scripts podem ser rodados de novo sem duplicar nada.
"""

from dataclasses import dataclass
from pathlib import Path

from person_dedup.matcher import Resultado


@dataclass
class Referencia:
    """Coluna de outra tabela que aponta para a pessoa."""

    tabela: str
    coluna: str
    pk: str


@dataclass
class ConfigSql:
    tabela_pessoa: str
    pk_pessoa: str
    colunas: dict[str, str]          # campo lógico -> coluna real na tabela de pessoa
    referencias: list[Referencia]
    sufixo: str


def _texto(valor: str) -> str:
    return "'" + str(valor).replace("\\", "\\\\").replace("'", "''") + "'"


def _lista(ids: list[int]) -> str:
    linhas, atual = [], []
    for i in ids:
        atual.append(str(i))
        if len(atual) == 20:
            linhas.append(", ".join(atual))
            atual = []
    if atual:
        linhas.append(", ".join(atual))
    return ",\n  ".join(linhas)


def _cabecalho(titulo: str, cfg: ConfigSql, resultado: Resultado) -> list[str]:
    return [
        "-- " + "=" * 70,
        f"-- {titulo}",
        f"-- Tabela: {cfg.tabela_pessoa} · {len(resultado.unificacoes)} cópias a unificar",
        "-- Gerado pelo person-dedup. Conferir antes de rodar.",
        "-- " + "=" * 70,
        "",
    ]


def conferir(resultado: Resultado, cfg: ConfigSql) -> str:
    copias = [u.id_copia for u in resultado.unificacoes]
    fica = sorted({u.id_fica for u in resultado.unificacoes})
    t, pk = cfg.tabela_pessoa, cfg.pk_pessoa
    sql = _cabecalho("01 — CONFERIR ANTES (só SELECT)", cfg, resultado)
    sql += [
        f"-- ESPERADO: {len(copias)} (todas as cópias ainda existem)",
        f"SELECT COUNT(*) AS copias FROM {t} WHERE {pk} IN (\n  {_lista(copias)}\n);",
        "",
        f"-- ESPERADO: {len(fica)} (todos que ficam existem)",
        f"SELECT COUNT(*) AS quem_fica FROM {t} WHERE {pk} IN (\n  {_lista(fica)}\n);",
        "",
    ]
    for ref in cfg.referencias:
        sql += [
            f"-- Linhas de {ref.tabela}.{ref.coluna} que serão repontadas",
            f"SELECT COUNT(*) AS {ref.tabela}_a_repontar FROM {ref.tabela}",
            f"WHERE {ref.coluna} IN (\n  {_lista(copias)}\n);",
            "",
        ]
    return "\n".join(sql)


def aplicar(resultado: Resultado, cfg: ConfigSql) -> str:
    t, pk, suf = cfg.tabela_pessoa, cfg.pk_pessoa, cfg.sufixo
    mapa = f"dedup_mapa_{suf}"
    bkp = f"bkp_{t}_{suf}"
    valores = ",\n  ".join(
        f"({u.id_copia}, {u.id_fica}, {_texto(u.motivo)})" for u in resultado.unificacoes
    )
    sql = _cabecalho("02 — APLICAR (só depois de conferir o 01)", cfg, resultado)
    sql += [
        "START TRANSACTION;",
        "",
        "-- 1) Mapa cópia -> quem fica",
        f"CREATE TABLE IF NOT EXISTS {mapa} (",
        "  id_copia INT PRIMARY KEY, id_fica INT NOT NULL, motivo VARCHAR(60)",
        ");",
        f"INSERT IGNORE INTO {mapa} (id_copia, id_fica, motivo) VALUES\n  {valores};",
        "",
        "-- 2) Backup das pessoas envolvidas (cópias e quem fica)",
        f"CREATE TABLE IF NOT EXISTS {bkp} LIKE {t};",
        f"INSERT IGNORE INTO {bkp}",
        f"SELECT * FROM {t} WHERE {pk} IN (SELECT id_copia FROM {mapa})",
        f"   OR {pk} IN (SELECT id_fica FROM {mapa});",
        "",
    ]
    for ref in cfg.referencias:
        bkp_ref = f"bkp_{ref.tabela}_{suf}"
        sql += [
            f"-- 3) {ref.tabela}.{ref.coluna}: backup e reponte",
            f"CREATE TABLE IF NOT EXISTS {bkp_ref} (pk BIGINT PRIMARY KEY, valor_antigo BIGINT);",
            f"INSERT IGNORE INTO {bkp_ref} (pk, valor_antigo)",
            f"SELECT {ref.pk}, {ref.coluna} FROM {ref.tabela}",
            f"WHERE {ref.coluna} IN (SELECT id_copia FROM {mapa});",
            f"UPDATE {ref.tabela} x JOIN {mapa} m ON m.id_copia = x.{ref.coluna}",
            f"SET x.{ref.coluna} = m.id_fica;",
            "",
        ]
    if resultado.preenchimentos:
        sql.append("-- 4) Quem fica recebe os campos que estavam vazios (nunca sobrescreve)")
        for p in resultado.preenchimentos:
            coluna = cfg.colunas.get(p.campo, p.campo)
            sql.append(
                f"UPDATE {t} SET {coluna} = {_texto(p.valor)} WHERE {pk} = {p.id_fica}"
                f" AND ({coluna} IS NULL OR {coluna} = '');  -- veio do {p.vindo_de}"
            )
        sql.append("")
    sql += [
        "-- 5) Apaga as cópias",
        f"DELETE p FROM {t} p JOIN {mapa} m ON m.id_copia = p.{pk};",
        "",
        "-- 6) Conferência — ESPERADO: tudo 0",
        f"SELECT COUNT(*) AS copias_restantes FROM {t} WHERE {pk} IN (SELECT id_copia FROM {mapa});",
    ]
    for ref in cfg.referencias:
        sql.append(
            f"SELECT COUNT(*) AS {ref.tabela}_apontando_para_copia FROM {ref.tabela}"
            f" WHERE {ref.coluna} IN (SELECT id_copia FROM {mapa});"
        )
        sql.append(
            f"SELECT COUNT(*) AS {ref.tabela}_orfaos FROM {ref.tabela} x"
            f" LEFT JOIN {t} p ON p.{pk} = x.{ref.coluna}"
            f" WHERE x.{ref.coluna} IS NOT NULL AND p.{pk} IS NULL;"
        )
    sql += ["", "-- Se os números baterem:", "-- COMMIT;", "-- Se algo estiver errado:", "-- ROLLBACK;", ""]
    return "\n".join(sql)


def desfazer(resultado: Resultado, cfg: ConfigSql) -> str:
    t, pk, suf = cfg.tabela_pessoa, cfg.pk_pessoa, cfg.sufixo
    mapa, bkp = f"dedup_mapa_{suf}", f"bkp_{t}_{suf}"
    campos = sorted({cfg.colunas.get(p.campo, p.campo) for p in resultado.preenchimentos})
    sql = _cabecalho("03 — DESFAZER (volta ao estado do backup)", cfg, resultado)
    sql += [
        "START TRANSACTION;",
        "",
        "-- 1) Devolve as cópias apagadas",
        f"INSERT IGNORE INTO {t} SELECT * FROM {bkp} WHERE {pk} IN (SELECT id_copia FROM {mapa});",
        "",
    ]
    if campos:
        sets = ", ".join(f"p.{c} = b.{c}" for c in campos)
        sql += [
            "-- 2) Devolve os campos de quem ficou",
            f"UPDATE {t} p JOIN {bkp} b ON b.{pk} = p.{pk}",
            f"SET {sets}",
            f"WHERE p.{pk} IN (SELECT id_fica FROM {mapa});",
            "",
        ]
    for ref in cfg.referencias:
        bkp_ref = f"bkp_{ref.tabela}_{suf}"
        sql += [
            f"-- 3) {ref.tabela}.{ref.coluna} volta a apontar para a cópia",
            f"UPDATE {ref.tabela} x JOIN {bkp_ref} b ON b.pk = x.{ref.pk}",
            f"SET x.{ref.coluna} = b.valor_antigo;",
            "",
        ]
    sql += [
        f"-- ESPERADO: {len(resultado.unificacoes)}",
        f"SELECT COUNT(*) AS copias_de_volta FROM {t} WHERE {pk} IN (SELECT id_copia FROM {mapa});",
        "", "-- COMMIT;", "-- ROLLBACK;", "",
    ]
    return "\n".join(sql)


def gravar(resultado: Resultado, cfg: ConfigSql, pasta: Path) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    if not resultado.unificacoes:
        caminho = pasta / "00_nada_a_unificar.txt"
        caminho.write_text("Nenhuma cópia com prova suficiente para unificar.\n", encoding="utf-8")
        return [caminho]
    arquivos = {
        "01_conferir_antes.sql": conferir(resultado, cfg),
        "02_aplicar.sql": aplicar(resultado, cfg),
        "03_desfazer.sql": desfazer(resultado, cfg),
    }
    caminhos = []
    for nome, conteudo in arquivos.items():
        caminho = pasta / nome
        caminho.write_text(conteudo, encoding="utf-8")
        caminhos.append(caminho)
    return caminhos
