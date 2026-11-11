# SCPRA · Sistema de Controle para Projeção de Recursos da Aurora

Protótipo para a colônia **Aurora Siger**. O sistema organiza os dados dos módulos, classifica riscos com lógica booleana, simula cenários de energia, estima a descarga das baterias e propõe um fluxo de agentes de IA com guardrails. Pode ser usado pelo terminal ou por um painel web.

## Integrantes

| Nome  | RM |
| ------------- | ------------- |
| Arthur Apolônio De Oliveira  | RM: 571385  |

## Funcionalidades

| Área | O que o sistema faz |
|---|---|
| Banco de dados e CRUD | Cadastra, consulta, altera e exclui leituras de sensores (SQLite), com validação e tratamento de erros |
| Lógica booleana | Classifica cada módulo como NORMAL, ATENÇÃO ou CRÍTICO e exibe o circuito lógico equivalente |
| Estruturas de dados | Tabela hash, fila de prioridade (heap), grafo com BFS e pilha de histórico |
| Simulação | Estado de carga da bateria por integração numérica e Monte Carlo (300 cenários) |
| Modelo linear | Regressão simples da bateria no tempo, com R² e estimativa de horas até o limite crítico |
| IA por agentes | Fluxo AgenteSensores, AgenteRisco e AgenteRecomendação, com handoffs, tracing, RAG simulado e guardrails |
| Painel web | CRUD, perfis de acesso e as telas de simulação, modelo linear, circuito lógico e estruturas de dados |

## Estrutura da pasta

```
SCPRA/
├── codigo_fonte.py              # sistema principal (menu, CRUD, regras, simulação, API do painel)
├── interface_web.html           # painel web (usado pelo --web)
├── script_banco.sql             # criação das tabelas modulos e leituras
├── dados_aurora_siger.csv       # base simulada: 4 módulos x 6 leituras
├── simulacao_computacional.py   # simulação e gráficos
├── circuito_logico.png          # circuito lógico de decisão
├── tinkercad/                   # guia de montagem e sketch Arduino do circuito
├── relatorio_tecnico.md         # relatório técnico
├── link_video.txt               # link do vídeo (YouTube, não listado)
├── README.md
└── graficos_ou_imagens/         # gráficos, exemplo de execução e capturas de tela do CRUD
```

O arquivo `aurora_siger.db` é criado automaticamente na primeira execução.

## Requisitos

Python 3.9 ou superior e `numpy`. O `matplotlib` só é necessário para gerar gráficos e a imagem do circuito.

```
python -m pip install numpy matplotlib
```

`sqlite3`, `csv`, `heapq`, `json` e `http.server` já vêm com o Python. No Mac e no Linux, use `python3` no lugar de `python`.

## Como executar

Abra um terminal dentro da pasta `SCPRA` e use um dos comandos:

| Comando | Resultado |
|---|---|
| `python codigo_fonte.py --demo` | Demonstração automática de todas as funções |
| `python codigo_fonte.py` | Menu interativo no terminal |
| `python codigo_fonte.py --web` | Painel web em http://127.0.0.1:8000 (opções `--porta N` e `--no-browser`) |
| `python simulacao_computacional.py` | Gera os gráficos em `graficos_ou_imagens/` |

Para recomeçar com os dados originais, apague o arquivo `aurora_siger.db`.

## Menu do terminal

| Opção | Função |
|---|---|
| 1 | Cadastrar leitura |
| 2 | Consultar leituras |
| 3 | Alterar leitura |
| 4 | Excluir leitura |
| 5 | Analisar sustentabilidade da colônia |
| 6 | Circuito lógico (tabela-verdade e imagem) |
| 7 | Simulação Monte Carlo |
| 8 | Modelo linear (regressão) |
| 9 | Estruturas de dados |
| 10 | Fluxo de agentes de IA |
| 11 | Análise final e limitações |
| 0 | Sair |

## Regra de decisão

Entradas: **A** bateria < 20%, **B** O₂ < 19,5%, **C** consumo > geração, **D** bateria < 40%, **E** temperatura fora de 18 a 26 °C.

- **CRÍTICO:** `Y1 = A + B`
- **ATENÇÃO:** `Y2 = (C · D) + E`

## Painel web

O painel funciona de duas formas:

- **Com `--web`:** usa o banco SQLite real. A API do `codigo_fonte.py` valida os dados e as permissões de cada perfil (Operador, Engenheiro e Comandante), e calcula simulação, regressão e estruturas de dados.
- **Aberto direto no navegador:** usa dados de demonstração em memória, com a mesma lógica, e nada é salvo.

Capturas de tela das telas de Leituras (CRUD) estão em `graficos_ou_imagens/tela_leituras_crud.png` e `tela_nova_leitura_cadastro.png`.

## Onde encontrar cada item

| Critério | Onde ver |
|---|---|
| Dados, banco e CRUD | `script_banco.sql`, `codigo_fonte.py` (opções 1 a 4), painel: Leituras |
| Capturas de tela do CRUD web | `graficos_ou_imagens/tela_leituras_crud.png` (consultar/alterar/excluir) e `tela_nova_leitura_cadastro.png` (cadastrar) |
| Circuitos lógicos | `circuito_logico.png`, `tinkercad/`, opção 6, painel: Circuito lógico |
| Estruturas de dados | opção 9, painel: Estruturas de dados |
| Simulação e integração matemática | `simulacao_computacional.py`, opção 7, painel: Simulação |
| Modelo linear | opção 8, painel: Modelo linear |
| IA multiagentes | opção 10, seção 8 do relatório |
| Arquitetura computacional | seção 9 do relatório |
| Sustentabilidade e cidadania digital | seção 10 do relatório, painel: Perfis e acesso |
| Execução | `graficos_ou_imagens/exemplo_execucao.txt`, o roteiro em `roteiro_apresentacao.md` e o vídeo em `link_video.txt` |

## Limitações

Os dados são simulados e os limites são didáticos. A regressão usa poucos pontos e o modelo solar é simplificado. Os agentes de IA são simulados, sem modelo de linguagem real. O circuito do Tinkercad está documentado em `tinkercad/` (guia de ligação e sketch Arduino), mas a montagem no site precisa ser feita e testada por quem for entregar. Mais detalhes no `relatorio_tecnico.md`.
