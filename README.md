# Person Dedup

Ferramenta em Python que encontra **pessoas duplicadas num cadastro**, junta só quando há prova de que é a mesma pessoa e gera os **scripts SQL para aplicar no banco com segurança**.

Em sistema que passou por migração, a mesma pessoa aparece duas, três vezes: digitada com e sem acento, cadastrada de novo pela secretaria, trazida por duas cargas. O difícil não é achar os nomes repetidos. O difícil é **não juntar duas pessoas diferentes que têm o mesmo nome**. Juntar errado é muito pior do que deixar uma duplicata: o histórico, o financeiro e os contatos de uma pessoa passam para outra.

Por isso a regra deste projeto é: **na dúvida, não junta, manda para revisão com o motivo.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![pytest](https://img.shields.io/badge/testes-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)

## Como decide

1. **Normaliza o nome**: sem acento, sem diferença de maiúscula, sem pontuação, sem espaço duplo. `"  José  da Silva-Júnior "` vira `JOSE DA SILVA JUNIOR`.
2. **Agrupa** pelo nome normalizado e escolhe **quem fica**: quem tem CPF, depois quem tem mais vínculos, depois quem tem mais campos preenchidos.
3. **Compara cada cópia com quem fica**:

| Situação | Decisão |
|---|---|
| CPF dos dois é igual | ✅ junta |
| CPF dos dois é diferente | ⚠️ revisar (**nunca junta**) |
| Nascimento dos dois é igual | ✅ junta |
| Nascimento dos dois é diferente | ⚠️ revisar |
| São da mesma família (ex.: mãe de dois irmãos cadastrada duas vezes) | ✅ junta |
| A cópia não tem nenhum vínculo | ✅ junta (só apaga, não copia dados dela) |
| Nenhuma prova | ⚠️ revisar: homônimo sem prova |

4. **Aponta para revisão**, sem nunca juntar sozinho:
   - **mesmo CPF com nomes diferentes**: CPF digitado errado?
   - **grafia parecida**: `GABRIELA` × `GABRIELLA`.

### Armadilhas que ele trata

- **CPF inválido** (dígito verificador errado, `111.111.111-11`) conta como vazio, e não como prova.
- **"Data padrão" de nascimento**: sistema antigo costuma gravar `01/01/1900` ou `01/01/1980` quando não sabe a data. Data com ano até 1900, ou repetida em muita gente, **não vale como prova**. Sem essa regra, centenas de homônimos seriam juntados por "mesmo nascimento".
- **Nome lixo** (`NÃO DECLARADO`, `NAO INFORMADO`, `X`) fica de fora.
- **Quem fica recebe os campos vazios das cópias** (e-mail, telefone...), mas **nunca tem um dado sobrescrito**. Da cópia sem vínculo não se copia nada, porque não há prova de que é a mesma pessoa.

## Como usar

```bash
pip install -r requirements.txt

# 1. gera um cadastro fictício com duplicatas e armadilhas
python samples/gerar_pessoas.py

# 2. roda
python -m person_dedup config/exemplo.yaml --saida saida
```

```text
Pessoas: 235
Unificar: 15 · Revisar: 17 pares · Completar: 5 campos
```

### O que sai

| Arquivo | Para quê |
|---|---|
| `resumo.md` | números por motivo e exemplos ([ver exemplo](docs/exemplo_resumo.md)) |
| `unificar.csv` | cada cópia, quem fica e o motivo |
| `revisar.csv` | pares que precisam de olho humano, com o motivo |
| `completar.csv` | campos vazios que quem fica vai receber, e de qual cópia vieram |
| `sql/01_conferir_antes.sql` | **só SELECT**: confere que as cópias existem e quantas linhas serão repontadas |
| `sql/02_aplicar.sql` | backup → reponte das referências → completa campos → apaga cópias → confere. Dentro de transação, com o `COMMIT` comentado ([ver exemplo](docs/exemplo_02_aplicar.sql)) |
| `sql/03_desfazer.sql` | volta tudo a partir do backup |

Os CSVs saem com `;` e acentuação certa para abrir direto no Excel. Os scripts podem ser rodados de novo sem duplicar nada.

## Configuração

```yaml
fonte:
  csv: samples/pessoas.csv
  # ou direto do banco (senha vem do ambiente):
  # url: mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}/${DB_NAME}
  # sql: SELECT id_pessoa, nome, cpf, data_nasc FROM pessoa

colunas:                 # nome da coluna para cada campo
  id: id_pessoa
  nascimento: data_nasc

limite_data_repetida: 15 # data em 15+ pessoas = data padrão
limiar_grafia: 0.92      # semelhança para "grafia parecida"

sql:                     # opcional: gera os scripts
  tabela_pessoa: pessoa
  pk_pessoa: id_pessoa
  referencias:           # tudo que aponta para a pessoa
    - {tabela: matricula, coluna: id_responsavel, pk: id_matricula}
    - {tabela: contato,   coluna: id_pessoa,      pk: id_contato}
```

Os campos `familia` (grupo familiar) e `vinculos` (quantas coisas apontam para a pessoa) são opcionais. Com eles, a ferramenta consegue juntar mais casos com segurança.

## Testes

```bash
python -m pytest
```

O cadastro de exemplo tem um caso para cada regra (mesmo CPF com acento diferente, homônimo com CPF diferente, data padrão, CPF inválido, grafia parecida, nome lixo...). Os testes conferem que **cada caso tem a decisão e o motivo certos** e que **nenhum caso de revisão é juntado**.

## Estrutura

```text
person-dedup/
├── config/exemplo.yaml
├── docs/                      # exemplos de saída
├── person_dedup/
│   ├── normalize.py           # nome, CPF (com dígito), datas, e-mail, telefone
│   ├── matcher.py             # regras de decisão
│   ├── report.py              # CSVs e resumo
│   ├── sql_export.py          # scripts conferir / aplicar / desfazer
│   └── cli.py
├── samples/gerar_pessoas.py   # cadastro fictício com casos conhecidos
└── tests/
```

## Próximos passos

- [ ] Apelidos e abreviações (`MA.` = `MARIA`, `JR` = `JUNIOR`)
- [ ] Conferência de órfãos lendo as chaves estrangeiras do banco automaticamente
- [ ] Planilha de revisão em Excel com coluna para marcar "junta / não junta" e reimportar

---

Feito por [Henrique Souza](https://www.linkedin.com/in/henrique-souza99). Veja também o [Migration Validator](https://github.com/henriqSouza00/migration-validator).
