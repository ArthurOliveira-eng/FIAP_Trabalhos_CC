# SIFSM - Sistema Integrado de Futuro Sustentavel em Marte - FASE 7



| Nome  | RM |
| ------------- | ------------- |
| Arthur Apolônio De Oliveira  | RM: 571385  |


Prototipo para a colonia **Aurora Siger**. O sistema organiza os dados dos modulos,
classifica riscos com logica booleana, simula cenarios de energia, preve a descarga
das baterias e propoe um fluxo de agentes de IA com guardrails.

## Arquivos da entrega

| Arquivo | Conteudo |
|---|---|
| `codigo_fonte.py` | Sistema principal: menu, CRUD, regra booleana, estruturas de dados, simulacao, regressao e agentes |
| `script_banco.sql` | Criacao das tabelas `modulos` e `leituras` (SQLite, com notas para Oracle no cabecalho) |
| `dados_aurora_siger.csv` | Base simulada: 4 modulos x 6 leituras (a cada 4 h) |
| `circuito_logico.png` | Circuito logico de decisao (gerado pela opcao 6 do menu) |
| `simulacao_computacional.py` | Simulacao do estado de carga (integral numerica) e Monte Carlo, com graficos |
| `relatorio_tecnico.md` | Relatorio tecnico completo |
| `link_video.txt` | Link do video no YouTube (nao listado) |
| `graficos_ou_imagens/` | Graficos e exemplo de execucao (`exemplo_execucao.txt`) |

## Requisitos

Python 3.9 ou superior e `numpy`. Para gerar graficos, `matplotlib`.

```
pip install numpy matplotlib
```

Os modulos `sqlite3`, `csv`, `heapq` e `collections` ja vem com o Python.

## Como executar

```
python codigo_fonte.py --demo        # demonstracao automatica de todas as funcoes
python codigo_fonte.py               # menu interativo
python simulacao_computacional.py    # gera os graficos
```

O banco `aurora_siger.db` e criado na primeira execucao a partir do `.sql` e do `.csv`.
Para recomecar do zero, apague o arquivo `.db`.

## Menu

| Opcao | Funcao |
|---|---|
| 1 | Cadastrar |
| 2 | Consultar |
| 3 | Alterar |
| 4 | Excluir |
| 5 | Analisar sustentabilidade |
| 6 | Circuito logico |
| 7 | Monte Carlo |
| 8 | Regressao |
| 9 | Estruturas de dados |
| 10 | Agentes de IA |
| 11 | Analise final |
| 0 | Sair |
