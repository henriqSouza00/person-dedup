"""Linha de comando: python -m person_dedup config.yaml"""

import argparse
import sys
from pathlib import Path

from person_dedup import config, matcher, report, sql_export


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="person_dedup",
        description="Encontra pessoas duplicadas, junta só com prova e gera os scripts SQL.",
    )
    parser.add_argument("config", help="arquivo YAML")
    parser.add_argument("--saida", default="saida", help="pasta dos arquivos gerados")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cfg = config.carregar(args.config)
    resultado = matcher.deduplicar(
        config.ler_pessoas(cfg), cfg.limite_data_repetida, cfg.limiar_grafia
    )

    pasta = Path(args.saida)
    gerados = report.gravar(resultado, pasta)
    if cfg.sql:
        gerados += sql_export.gravar(resultado, cfg.sql, pasta / "sql")

    print(f"Pessoas: {resultado.total}")
    print(f"Unificar: {len(resultado.unificacoes)} · Revisar: {len(resultado.revisoes)} pares"
          f" · Completar: {len(resultado.preenchimentos)} campos")
    print("Arquivos:")
    for caminho in gerados:
        print(f"  {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
