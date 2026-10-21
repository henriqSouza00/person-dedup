"""O cadastro de exemplo tem casos conhecidos; cada um precisa ter a decisão certa."""

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "samples"))

import gerar_pessoas  # noqa: E402
from person_dedup import matcher, normalize, sql_export  # noqa: E402

PESSOAS, ESPERADO = gerar_pessoas.gerar()


@pytest.fixture(scope="module")
def resultado():
    linhas = [{k: str(v) for k, v in p.items()} for p in PESSOAS]   # como viria do CSV
    return matcher.deduplicar(linhas, limite_data_repetida=15)


def _casos(decisao):
    return {i: m for i, (d, m) in ESPERADO.items() if d == decisao}


def test_junta_com_o_motivo_certo(resultado):
    unificadas = {u.id_copia: u.motivo for u in resultado.unificacoes}
    for id_copia, motivo in _casos("junta").items():
        assert unificadas.get(id_copia) == motivo, f"pessoa {id_copia}"


def test_nunca_junta_o_que_e_para_revisar(resultado):
    unificadas = {u.id_copia for u in resultado.unificacoes} | {u.id_fica for u in resultado.unificacoes}
    assert not unificadas & set(_casos("revisar"))


def test_vai_para_revisao_com_o_motivo_certo(resultado):
    motivos = {}
    for r in resultado.revisoes:
        motivos.setdefault(r.id_a, []).append(r.motivo)
        motivos.setdefault(r.id_b, []).append(r.motivo)
    for id_copia, motivo in _casos("revisar").items():
        assert any(motivo in m for m in motivos.get(id_copia, [])), f"pessoa {id_copia}"


def test_ignora_nome_lixo(resultado):
    ignorados = {p.id for p in resultado.ignorados_nome}
    assert set(_casos("ignora")) <= ignorados


def test_completa_campo_vazio_sem_copiar_da_copia_sem_vinculo(resultado):
    completados = {(p.id_fica, p.campo): p.valor for p in resultado.preenchimentos}
    assert completados[(8, "email")] == "copia8@exemplo.com"
    for id_base in (60, 64, 68):          # cópia sem vínculo: só apaga, não copia
        assert (id_base, "email") not in completados


def test_data_padrao_nao_prova(resultado):
    assert gerar_pessoas.DATA_REPETIDA in resultado.datas_preenchimento


def test_cpf_invalido(resultado):
    assert resultado.cpfs_invalidos == 2


@pytest.mark.parametrize("entrada, saida", [
    ("  José  da Silva-Júnior ", "JOSE DA SILVA JUNIOR"),
    ("maria  aparecida", "MARIA APARECIDA"),
    ("ÂNGELA D'ÁVILA", "ANGELA D AVILA"),
])
def test_normaliza_nome(entrada, saida):
    assert normalize.nome(entrada) == saida


@pytest.mark.parametrize("entrada, saida", [
    ("529.982.247-25", "52998224725"),   # válido
    ("529.982.247-24", None),            # dígito errado
    ("111.111.111-11", None),            # todos iguais
    ("123", None),
])
def test_cpf(entrada, saida):
    assert normalize.cpf(entrada) == saida


def test_sql_gerado(resultado):
    cfg = sql_export.ConfigSql(
        tabela_pessoa="pessoa", pk_pessoa="id", colunas={"email": "email"},
        referencias=[sql_export.Referencia("matricula", "id_responsavel", "id_matricula")],
        sufixo="teste",
    )
    aplicar = sql_export.aplicar(resultado, cfg)
    assert aplicar.index("CREATE TABLE IF NOT EXISTS bkp_pessoa_teste") < aplicar.index("DELETE p FROM pessoa")
    assert "-- COMMIT;" in aplicar and "\nCOMMIT;" not in aplicar
    assert "UPDATE matricula x JOIN dedup_mapa_teste" in aplicar
    assert "bkp_matricula_teste" in sql_export.desfazer(resultado, cfg)
    assert "DELETE" not in sql_export.conferir(resultado, cfg)
