"""Gera um cadastro de pessoas FICTÍCIO com duplicatas e armadilhas conhecidas.

Todos os nomes, CPFs, e-mails e telefones são inventados (os CPFs passam no
cálculo do dígito, mas são aleatórios).

O arquivo sai com ; como separador, como o Excel em português salva.
ESPERADO diz, para cada pessoa colocada de propósito, o que o programa tem
que decidir. Os testes usam isso.

Uso: python samples/gerar_pessoas.py [arquivo.csv]
"""

import csv
import random
import sys
from datetime import date
from pathlib import Path

QT_BASE = 200
DATA_REPETIDA = date(1980, 1, 1)   # "data padrão" que o sistema antigo gravava

PRIMEIROS = ["ANA", "BEATRIZ", "CARLOS", "DANIELA", "EDUARDO", "FERNANDA", "GUSTAVO", "HELENA",
             "IGOR", "JULIANA", "KLEBER", "LETICIA", "MARCOS", "NATALIA", "OTAVIO", "PATRICIA",
             "RENATO", "SIMONE", "TATIANE", "VINICIUS", "WAGNER", "YARA"]
MEIOS = ["APARECIDA", "CRISTINA", "AUGUSTO", "HENRIQUE", "LUIZA", "MARIA", "PAULO", "REGINA",
         "ROBERTO", "SILVIA", "VITORIA", "JOSE"]
SOBRENOMES = ["ALVES", "BATISTA", "CAMPOS", "DUARTE", "ESTEVES", "FARIAS", "GARCIA", "MACHADO",
              "MENDES", "MOREIRA", "PINTO", "QUEIROZ", "RAMOS", "SAMPAIO", "TAVARES", "XAVIER"]

JUNTA, REVISAR, IGNORA = "junta", "revisar", "ignora"


def cpf_valido(rng: random.Random) -> str:
    base = [rng.randint(0, 9) for _ in range(9)]
    for tamanho in (9, 10):
        soma = sum(d * (tamanho + 1 - i) for i, d in enumerate(base))
        base.append((soma * 10) % 11 % 10)
    return "".join(map(str, base))


def _formatar_cpf(c: str) -> str:
    return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"


def gerar() -> tuple[list[dict], dict[int, tuple[str, str]]]:
    rng = random.Random(7)
    usados: set[str] = set()
    pessoas: list[dict] = []

    def novo_nome() -> str:
        while True:
            nome = f"{rng.choice(PRIMEIROS)} {rng.choice(MEIOS)} {rng.choice(SOBRENOMES)} {rng.choice(SOBRENOMES)}"
            if nome not in usados:
                usados.add(nome)
                return nome

    # ---------------------------------------------------------- cadastro "limpo"
    for i in range(1, QT_BASE + 1):
        nome = novo_nome()
        pessoas.append({
            "id": i,
            "nome": nome.title() if i % 3 == 0 else nome,   # caixa misturada não pode atrapalhar
            "cpf": _formatar_cpf(cpf_valido(rng)) if i % 5 != 0 else "",
            "nascimento": date(rng.randint(1960, 2000), rng.randint(1, 12), rng.randint(1, 28)).isoformat(),
            "email": f"{nome.split()[0].lower()}.{i}@exemplo.com" if i % 4 != 0 else "",
            "telefone": f"(11) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}" if i % 2 == 0 else "",
            "familia": f"F{i:03d}",
            "vinculos": rng.randint(2, 6),
        })
    # 20 pessoas com a "data padrão": repetida demais, não prova nada
    for p in pessoas[100:120]:
        p["nascimento"] = DATA_REPETIDA.isoformat()

    base = {p["id"]: p for p in pessoas}
    esperado: dict[int, tuple[str, str]] = {}
    proximo = [1001]

    def copia(id_base: int, decisao: str, motivo: str, **campos) -> None:
        b = base[id_base]
        nova = {"id": proximo[0], "nome": b["nome"], "cpf": "", "nascimento": "", "email": "",
                "telefone": "", "familia": f"X{proximo[0]}", "vinculos": 1} | campos
        pessoas.append(nova)
        esperado[nova["id"]] = (decisao, motivo)
        proximo[0] += 1

    # A) mesmo CPF; nome com acento, minúscula, espaço duplo, hífen
    for id_base, variante in [(1, "lower"), (2, "espaco"), (3, "hifen"), (4, "acento")]:
        nome = base[id_base]["nome"].upper()
        if variante == "lower":
            nome = nome.lower()
        elif variante == "espaco":
            nome = "  " + nome.replace(" ", "  ") + " "
        elif variante == "hifen":
            partes = nome.split()
            nome = " ".join(partes[:-2]) + f" {partes[-2]}-{partes[-1]}"
        else:
            nome = nome.replace("A", "Á", 1)
        copia(id_base, JUNTA, "mesmo CPF", nome=nome, cpf=base[id_base]["cpf"].replace(".", "").replace("-", ""),
              telefone="11 98888-0000")

    # B) sem CPF, mesmo nascimento; a cópia traz o e-mail que faltava (base 8 e 12 não têm e-mail)
    for id_base in (8, 12, 16):
        copia(id_base, JUNTA, "mesmo nascimento", nascimento=base[id_base]["nascimento"],
              email=f"copia{id_base}@exemplo.com")

    # C) homônimos com CPF diferente: nunca junta
    for id_base in (21, 22, 23):
        copia(id_base, REVISAR, "CPF diferente", cpf=_formatar_cpf(cpf_valido(rng)))

    # D) homônimos com nascimento diferente
    for id_base in (31, 32, 33):
        copia(id_base, REVISAR, "nascimento diferente", nascimento="2015-06-15")

    # E) sem dado nenhum, mas da mesma família (ex.: mãe de dois irmãos cadastrada duas vezes)
    for id_base in (41, 42, 43):
        copia(id_base, JUNTA, "mesma família", familia=base[id_base]["familia"])

    # F) sem dado nenhum, família diferente, tem vínculo: homônimo sem prova
    for id_base in (51, 52, 53):
        copia(id_base, REVISAR, "homônimo sem prova")

    # G) sem dado nenhum e sem vínculo: pode apagar, mas não copia nada dela
    #    (base 60, 64, 68 não têm e-mail: o da cópia NÃO pode ir para eles)
    for id_base in (60, 64, 68):
        copia(id_base, JUNTA, "cópia sem vínculo", vinculos=0, email=f"naocopiar{id_base}@exemplo.com")

    # H) mesma "data padrão": NÃO pode valer como prova (base 101..119 têm DATA_REPETIDA e alguns sem CPF)
    for id_base in (105, 110, 115):
        base[id_base]["cpf"] = ""
        copia(id_base, REVISAR, "homônimo sem prova", nascimento=DATA_REPETIDA.isoformat())

    # I) CPF inválido conta como vazio; junta pelo nascimento
    for id_base in (71, 72):
        copia(id_base, JUNTA, "mesmo nascimento", cpf="111.111.111-11", nascimento=base[id_base]["nascimento"])

    # J) grafia parecida: nunca junta sozinho
    for id_base in (81, 82, 83):
        partes = base[id_base]["nome"].upper().split()
        partes[1] = partes[1][:2] + partes[1][1] + partes[1][2:]   # letra dobrada no nome do meio
        nome = " ".join(partes)
        usados.add(nome)
        copia(id_base, REVISAR, "grafia parecida", nome=nome, nascimento=base[id_base]["nascimento"])

    # K) mesmo CPF com nome totalmente diferente: CPF digitado errado?
    for id_base in (91, 92):
        base[id_base]["cpf"] = base[id_base]["cpf"] or _formatar_cpf(cpf_valido(rng))
        copia(id_base, REVISAR, "mesmo CPF, nome diferente", nome=novo_nome(), cpf=base[id_base]["cpf"])

    # L) nome lixo
    for nome in ("NÃO DECLARADO", "nao informado", "X"):
        pessoas.append({"id": proximo[0], "nome": nome, "cpf": "", "nascimento": "", "email": "",
                        "telefone": "", "familia": "", "vinculos": 1})
        esperado[proximo[0]] = (IGNORA, "nome inválido")
        proximo[0] += 1

    return pessoas, esperado


def gravar_csv(caminho: str | Path = "samples/pessoas.csv") -> Path:
    pessoas, _ = gerar()
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(pessoas[0].keys()), delimiter=";")
        escritor.writeheader()
        escritor.writerows(pessoas)
    return caminho


if __name__ == "__main__":
    print(f"Cadastro gerado: {gravar_csv(sys.argv[1] if len(sys.argv) > 1 else 'samples/pessoas.csv')}")
