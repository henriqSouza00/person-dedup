"""Decide quem é a mesma pessoa.

Regra de ouro: na dúvida, NÃO junta. Juntar duas pessoas diferentes é muito
pior do que deixar uma duplicata para alguém revisar.

1. Agrupa por nome normalizado (sem acento, caixa, pontuação e espaço duplo).
2. Em cada grupo escolhe quem FICA: tem CPF > mais vínculos > mais campos preenchidos > menor id.
3. Compara cada outra pessoa do grupo com quem fica:
   - CPF dos dois e igual ............ junta
   - CPF dos dois e diferente ........ revisar (nunca junta)
   - nascimento dos dois e igual ..... junta
   - nascimento dos dois e diferente . revisar
   - mesma família ................... junta
   - cópia sem nenhum vínculo ........ junta (só apaga, não copia dados dela)
   - senão ........................... revisar (homônimo sem prova)
4. À parte, aponta para revisão: mesmo CPF com nomes diferentes e grafias
   muito parecidas (GABRIELA × GABRIELLA). Esses nunca juntam sozinhos.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher

from person_dedup import normalize

JUNTA = "junta"
REVISAR = "revisar"


@dataclass
class Pessoa:
    id: int
    nome_original: str
    nome: str
    cpf: str | None
    nascimento: date | None
    email: str | None
    telefone: str | None
    familias: set[str] = field(default_factory=set)
    vinculos: int | None = None

    def preenchidos(self) -> int:
        return sum(v is not None for v in (self.cpf, self.nascimento, self.email, self.telefone))


@dataclass
class Unificacao:
    id_copia: int
    id_fica: int
    nome: str
    motivo: str


@dataclass
class Revisao:
    id_a: int
    id_b: int
    nome_a: str
    nome_b: str
    motivo: str


@dataclass
class Preenchimento:
    id_fica: int
    campo: str
    valor: str
    vindo_de: int


@dataclass
class Resultado:
    total: int
    ignorados_nome: list[Pessoa]
    cpfs_invalidos: int
    datas_preenchimento: set[date]
    unificacoes: list[Unificacao]
    revisoes: list[Revisao]
    preenchimentos: list[Preenchimento]


CAMPOS_COMPLETAR = ("cpf", "nascimento", "email", "telefone")
MOTIVO_SEM_VINCULO = "cópia sem vínculo"


def carregar(linhas: list[dict], limite_data_repetida: int) -> tuple[list[Pessoa], int, set[date]]:
    """Converte as linhas brutas em Pessoa já normalizada."""
    datas = [normalize.data(l.get("nascimento")) for l in linhas]
    falsas = normalize.datas_de_preenchimento(datas, limite_data_repetida)
    pessoas, cpfs_invalidos = [], 0
    for linha, nasc in zip(linhas, datas):
        cpf = normalize.cpf(linha.get("cpf"))
        if linha.get("cpf") and not cpf:
            cpfs_invalidos += 1
        familias = {f.strip() for f in str(linha.get("familia") or "").split(";") if f.strip()}
        vinculos = linha.get("vinculos")
        pessoas.append(Pessoa(
            id=int(linha["id"]),
            nome_original=linha.get("nome") or "",
            nome=normalize.nome(linha.get("nome")),
            cpf=cpf,
            nascimento=None if nasc in falsas else nasc,
            email=normalize.email(linha.get("email")),
            telefone=normalize.telefone(linha.get("telefone")),
            familias=familias,
            vinculos=None if vinculos in (None, "") else int(vinculos),
        ))
    return pessoas, cpfs_invalidos, falsas


def escolher_quem_fica(grupo: list[Pessoa]) -> Pessoa:
    return min(grupo, key=lambda p: (p.cpf is None, -(p.vinculos or 0), -p.preenchidos(), p.id))


def decidir(fica: Pessoa, copia: Pessoa) -> tuple[str, str]:
    if fica.cpf and copia.cpf:
        return (JUNTA, "mesmo CPF") if fica.cpf == copia.cpf else (REVISAR, "CPF diferente")
    if fica.nascimento and copia.nascimento:
        if fica.nascimento == copia.nascimento:
            return JUNTA, "mesmo nascimento"
        return REVISAR, "nascimento diferente"
    if fica.familias & copia.familias:
        return JUNTA, "mesma família"
    if copia.vinculos == 0:
        return JUNTA, MOTIVO_SEM_VINCULO
    return REVISAR, "homônimo sem prova"


def _completar(fica: Pessoa, copias: list[tuple[Pessoa, str]]) -> list[Preenchimento]:
    """Quem fica recebe os campos VAZIOS das cópias. Nunca sobrescreve."""
    preenchimentos = []
    for campo in CAMPOS_COMPLETAR:
        if getattr(fica, campo) is not None:
            continue
        for copia, motivo in copias:
            valor = getattr(copia, campo)
            if valor is not None and motivo != MOTIVO_SEM_VINCULO:
                setattr(fica, campo, valor)
                preenchimentos.append(Preenchimento(fica.id, campo, str(valor), copia.id))
                break
    return preenchimentos


def _grafias_parecidas(nomes: dict[str, Pessoa], limiar: float) -> list[Revisao]:
    """Nomes diferentes com mesmo primeiro e último nome e escrita quase igual."""
    por_ponta = defaultdict(list)
    for nome in nomes:
        partes = nome.split()
        por_ponta[(partes[0], partes[-1])].append(nome)

    revisoes = []
    for candidatos in por_ponta.values():
        for i, a in enumerate(candidatos):
            for b in candidatos[i + 1:]:
                if SequenceMatcher(None, a, b).ratio() >= limiar:
                    pa, pb = nomes[a], nomes[b]
                    revisoes.append(Revisao(pa.id, pb.id, pa.nome_original, pb.nome_original,
                                            "grafia parecida"))
    return revisoes


def deduplicar(linhas: list[dict], limite_data_repetida: int = 15,
               limiar_grafia: float = 0.92) -> Resultado:
    pessoas, cpfs_invalidos, falsas = carregar(linhas, limite_data_repetida)

    validas = [p for p in pessoas if normalize.nome_valido(p.nome)]
    ignorados = [p for p in pessoas if not normalize.nome_valido(p.nome)]

    grupos: dict[str, list[Pessoa]] = defaultdict(list)
    for p in validas:
        grupos[p.nome].append(p)

    unificacoes, revisoes, preenchimentos = [], [], []
    representantes: dict[str, Pessoa] = {}

    for nome, grupo in grupos.items():
        fica = escolher_quem_fica(grupo)
        representantes[nome] = fica
        juntadas = []
        for copia in grupo:
            if copia is fica:
                continue
            decisao, motivo = decidir(fica, copia)
            if decisao == JUNTA:
                unificacoes.append(Unificacao(copia.id, fica.id, fica.nome_original, motivo))
                juntadas.append((copia, motivo))
            else:
                revisoes.append(Revisao(fica.id, copia.id, fica.nome_original,
                                        copia.nome_original, motivo))
        preenchimentos += _completar(fica, juntadas)

    # Mesmo CPF em nomes diferentes: pode ser erro de digitação ou CPF errado
    por_cpf = defaultdict(list)
    for p in validas:
        if p.cpf:
            por_cpf[p.cpf].append(p)
    for mesmos in por_cpf.values():
        nomes = {p.nome for p in mesmos}
        if len(nomes) > 1:
            a, *outros = sorted(mesmos, key=lambda p: p.id)
            for b in outros:
                if b.nome != a.nome:
                    revisoes.append(Revisao(a.id, b.id, a.nome_original, b.nome_original,
                                            "mesmo CPF, nome diferente"))

    revisoes += _grafias_parecidas(representantes, limiar_grafia)

    # O mesmo par pode cair em duas regras: junta os motivos numa linha só
    por_par: dict[tuple[int, int], Revisao] = {}
    for r in revisoes:
        par = (min(r.id_a, r.id_b), max(r.id_a, r.id_b))
        if par in por_par:
            por_par[par].motivo += f" + {r.motivo}"
        else:
            por_par[par] = r
    revisoes = list(por_par.values())

    return Resultado(len(pessoas), ignorados, cpfs_invalidos, falsas,
                     unificacoes, revisoes, preenchimentos)
