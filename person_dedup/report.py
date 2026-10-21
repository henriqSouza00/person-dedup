"""Arquivos de saída: CSVs para conferir no Excel e um resumo em Markdown."""

import csv
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from person_dedup.matcher import Resultado

MAX_LINHAS = 15


def _csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    # ; e BOM para o Excel em português abrir certo
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas)


def _tabela(linhas: list[dict]) -> list[str]:
    if not linhas:
        return ["*(nenhum)*"]
    colunas = list(linhas[0].keys())
    saida = ["| " + " | ".join(colunas) + " |", "|" + "---|" * len(colunas)]
    for l in linhas[:MAX_LINHAS]:
        saida.append("| " + " | ".join(str(l[c]) for c in colunas) + " |")
    if len(linhas) > MAX_LINHAS:
        saida.append(f"\n*Mostrando {MAX_LINHAS} de {len(linhas)}. Lista completa no CSV.*")
    return saida


def resumo(r: Resultado) -> str:
    por_motivo_une = Counter(u.motivo for u in r.unificacoes)
    por_motivo_rev = Counter(v.motivo for v in r.revisoes)
    datas = ", ".join(f"{d:%d/%m/%Y}" for d in sorted(r.datas_preenchimento)) or "nenhuma"
    pessoas_depois = r.total - len(r.unificacoes)

    linhas = [
        "# Deduplicação de pessoas",
        "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M}",
        "",
        "## Resumo",
        "",
        "| | Quantidade |",
        "|---|---|",
        f"| Pessoas no cadastro | {r.total} |",
        f"| **Cópias a unificar** | **{len(r.unificacoes)}** |",
        f"| Pessoas depois | {pessoas_depois} |",
        f"| Pares para revisão manual | {len(r.revisoes)} |",
        f"| Campos vazios completados em quem fica | {len(r.preenchimentos)} |",
        f"| Ignorados por nome inválido | {len(r.ignorados_nome)} |",
        f"| CPFs inválidos (tratados como vazios) | {r.cpfs_invalidos} |",
        "",
        f"Datas de nascimento ignoradas por serem de preenchimento: {datas}",
        "",
        "## Unificar, por motivo",
        "",
        *_tabela([{"motivo": m, "cópias": q} for m, q in por_motivo_une.most_common()]),
        "",
        "## Revisar, por motivo",
        "",
        *_tabela([{"motivo": m, "pares": q} for m, q in por_motivo_rev.most_common()]),
        "",
        "## Exemplos a unificar",
        "",
        *_tabela([asdict(u) for u in r.unificacoes]),
        "",
        "## Exemplos para revisão",
        "",
        *_tabela([asdict(v) for v in r.revisoes]),
        "",
    ]
    return "\n".join(linhas)


def gravar(r: Resultado, pasta: Path) -> list[Path]:
    pasta.mkdir(parents=True, exist_ok=True)
    arquivos = {
        "unificar.csv": ([asdict(u) for u in r.unificacoes], ["id_copia", "id_fica", "nome", "motivo"]),
        "revisar.csv": ([asdict(v) for v in r.revisoes], ["id_a", "id_b", "nome_a", "nome_b", "motivo"]),
        "completar.csv": ([asdict(p) for p in r.preenchimentos], ["id_fica", "campo", "valor", "vindo_de"]),
    }
    caminhos = []
    for nome, (linhas, colunas) in arquivos.items():
        _csv(pasta / nome, linhas, colunas)
        caminhos.append(pasta / nome)
    (pasta / "resumo.md").write_text(resumo(r), encoding="utf-8")
    caminhos.append(pasta / "resumo.md")
    return caminhos
