# Deduplicação de pessoas

Gerado em 21/10/2026 13:05

## Resumo

| | Quantidade |
|---|---|
| Pessoas no cadastro | 235 |
| **Cópias a unificar** | **15** |
| Pessoas depois | 220 |
| Pares para revisão manual | 17 |
| Campos vazios completados em quem fica | 5 |
| Ignorados por nome inválido | 3 |
| CPFs inválidos (tratados como vazios) | 2 |

Datas de nascimento ignoradas por serem de preenchimento: 01/01/1980

## Unificar, por motivo

| motivo | cópias |
|---|---|
| mesmo nascimento | 5 |
| mesmo CPF | 4 |
| mesma família | 3 |
| cópia sem vínculo | 3 |

## Revisar, por motivo

| motivo | pares |
|---|---|
| homônimo sem prova | 6 |
| CPF diferente | 3 |
| nascimento diferente | 3 |
| grafia parecida | 3 |
| mesmo CPF, nome diferente | 2 |

## Exemplos a unificar

| id_copia | id_fica | nome | motivo |
|---|---|---|---|
| 1001 | 1 | KLEBER AUGUSTO RAMOS BATISTA | mesmo CPF |
| 1002 | 2 | HELENA CRISTINA SAMPAIO BATISTA | mesmo CPF |
| 1003 | 3 | Eduardo Roberto Duarte Moreira | mesmo CPF |
| 1004 | 4 | GUSTAVO REGINA SAMPAIO PINTO | mesmo CPF |
| 1005 | 8 | GUSTAVO LUIZA ESTEVES MACHADO | mesmo nascimento |
| 1006 | 12 | Vinicius Aparecida Duarte Alves | mesmo nascimento |
| 1007 | 16 | GUSTAVO ROBERTO XAVIER QUEIROZ | mesmo nascimento |
| 1014 | 41 | YARA REGINA MOREIRA MOREIRA | mesma família |
| 1015 | 42 | Renato Regina Mendes Ramos | mesma família |
| 1016 | 43 | LETICIA HENRIQUE XAVIER XAVIER | mesma família |
| 1020 | 60 | Marcos Maria Moreira Sampaio | cópia sem vínculo |
| 1021 | 64 | OTAVIO MARIA CAMPOS GARCIA | cópia sem vínculo |
| 1022 | 68 | WAGNER REGINA BATISTA DUARTE | cópia sem vínculo |
| 1026 | 71 | JULIANA CRISTINA GARCIA BATISTA | mesmo nascimento |
| 1027 | 72 | Marcos Jose Mendes Sampaio | mesmo nascimento |

## Exemplos para revisão

| id_a | id_b | nome_a | nome_b | motivo |
|---|---|---|---|---|
| 21 | 1008 | Renato Paulo Esteves Esteves | Renato Paulo Esteves Esteves | CPF diferente |
| 22 | 1009 | SIMONE APARECIDA PINTO XAVIER | SIMONE APARECIDA PINTO XAVIER | CPF diferente |
| 23 | 1010 | VINICIUS ROBERTO GARCIA MENDES | VINICIUS ROBERTO GARCIA MENDES | CPF diferente |
| 31 | 1011 | ANA LUIZA BATISTA ALVES | ANA LUIZA BATISTA ALVES | nascimento diferente |
| 32 | 1012 | MARCOS ROBERTO MOREIRA GARCIA | MARCOS ROBERTO MOREIRA GARCIA | nascimento diferente |
| 33 | 1013 | Beatriz Cristina Ramos Moreira | Beatriz Cristina Ramos Moreira | nascimento diferente |
| 51 | 1017 | Carlos Luiza Machado Ramos | Carlos Luiza Machado Ramos | homônimo sem prova |
| 52 | 1018 | MARCOS ROBERTO TAVARES TAVARES | MARCOS ROBERTO TAVARES TAVARES | homônimo sem prova |
| 53 | 1019 | BEATRIZ VITORIA MOREIRA ESTEVES | BEATRIZ VITORIA MOREIRA ESTEVES | homônimo sem prova |
| 105 | 1023 | Ana Augusto Mendes Ramos | Ana Augusto Mendes Ramos | homônimo sem prova |
| 110 | 1024 | TATIANE LUIZA DUARTE MACHADO | TATIANE LUIZA DUARTE MACHADO | homônimo sem prova |
| 115 | 1025 | VINICIUS CRISTINA MOREIRA GARCIA | VINICIUS CRISTINA MOREIRA GARCIA | homônimo sem prova |
| 91 | 1031 | HELENA CRISTINA MENDES MACHADO | TATIANE SILVIA CAMPOS SAMPAIO | mesmo CPF, nome diferente |
| 92 | 1032 | CARLOS ROBERTO ALVES FARIAS | YARA CRISTINA TAVARES ESTEVES | mesmo CPF, nome diferente |
| 81 | 1028 | Eduardo Regina Moreira Farias | EDUARDO REEGINA MOREIRA FARIAS | grafia parecida |

*Mostrando 15 de 17. Lista completa no CSV.*
