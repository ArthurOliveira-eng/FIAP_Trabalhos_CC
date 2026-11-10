# Relatorio Tecnico - SIFSM (Aurora Siger)

## 1. Contexto da solucao

A colonia Aurora Siger depende de energia, ar e temperatura estaveis. O SIFSM
centraliza as leituras dos modulos (habitat, estufa, usina solar e reciclagem),
identifica risco, simula cenarios e recomenda acoes sempre com confirmacao humana.

## 2. Descricao dos dados

A base simulada (`dados_aurora_siger.csv`) tem 24 leituras (4 modulos x 6 horarios),
com consumo e geracao (kW), temperatura (C), oxigenio (%) e bateria (%).

Foram inseridas anomalias de proposito para testar as regras: bateria baixa na
estufa, O2 baixo no habitat e temperatura alta na reciclagem.

## 3. Banco de dados e CRUD

Tabelas `modulos` (parametros fisicos) e `leituras` (sensores), ligadas por chave
estrangeira e com restricoes CHECK. O banco e SQLite (equivalente ao Oracle, com as
adaptacoes indicadas no `.sql`).

O CRUD completo esta no codigo, com `try/except/else/finally`, validacao de faixas e
lista branca de campos no UPDATE.

## 4. Regra logica e circuito

Entradas:

- A = bateria < 20%
- B = O2 < 19,5%
- C = consumo > geracao
- D = bateria < 40%
- E = temperatura fora de 18 a 26 C

Saidas:

- Y1 (CRITICO) = A + B
- Y2 (ATENCAO) = (C . D) + E

O circuito (`circuito_logico.png`) usa portas OR (74HC32) e AND (74HC08) e dois LEDs.
Pode ser reproduzido no Tinkercad com comparadores ou potenciometros simulando os
sensores. A mesma logica roda em software em `classificar_risco()`.

## 5. Estruturas de dados

- **Tabela hash (dict):** busca O(1) dos parametros de cada modulo.
- **Heap (fila de prioridade):** ordena alertas, critico primeiro e empate pela menor bateria.
- **Grafo + BFS:** rede de energia; descobre a rota e quais modulos ficam sem energia se um falhar.
- **Pilha:** historico das ultimas operacoes do CRUD.

## 6. Simulacao computacional e matematica

O estado de carga e:

```
SoC(t) = SoC0 + (100 / Cap) * integral de (P_ger - P_cons) dt
```

A integral e resolvida por **integracao numerica (regra do trapezio)**, com geracao
solar senoidal entre 06h e 18h.

O Monte Carlo roda 300 cenarios, variando a geracao (tempestade de poeira, de 30% a
100%) e o consumo (ruido de 5%).

Resultado da demonstracao: probabilidade de bateria abaixo de 20% em 24 h igual a
61% (HAB-01), 100% (EST-01) e 0% (REC-01).

## 7. Modelo linear simples

Regressao `SoC = a*t + b` (`numpy.polyfit`) nas ultimas 4 leituras de cada modulo.
O coeficiente `a` e a taxa de descarga (%/h) e o R2 mede o ajuste.

- Estufa: -4,48 %/h (R2 = 0,90), ja abaixo do limite
- Habitat: -0,86 %/h, cerca de 44 h ate 20%

Limitacao: poucos pontos e comportamento diario nao linear. O modelo apoia a decisao,
nao e previsao definitiva.

## 8. IA por agentes (simulada)

Fluxo multiagente: **AgenteSensores -> AgenteRisco -> AgenteRecomendacao**, com
*handoffs* e *tracing* impressos.

Guardrails:

- Entrada: bloqueia pedidos com dados pessoais
- Saida: toda recomendacao exige confirmacao humana e o agente nunca aciona atuadores

A recuperacao de procedimentos por palavra-chave simula RAG. Em producao, cada agente
poderia ser um LLM com ferramentas deterministicas (a regra booleana e a regressao
seriam funcoes chamadas pelo agente), disparadas por webhooks de sensores em fluxo
low-code.

## 9. Arquitetura computacional

O processamento fica na **borda** (CPU local no habitat), com baixa latencia e
independencia da Terra, pois a comunicacao tem atraso de minutos.

- A CPU executa regras e banco.
- GPU ou NPU seriam usadas para modelos de IA maiores e inferencia de agentes.
- A hierarquia de memoria (cache, RAM, armazenamento) e a largura de banda importam
  porque mover dados custa mais energia que calcular.
- Dados brutos ficam locais e so resumos sobem.
- Aceleradores especializados (NPU, ASIC) elevam a eficiencia por watt, essencial em
  uma colonia com energia limitada.

## 10. Sustentabilidade, sociedade e cidadania digital

Otimizar energia e prever falhas protege vidas e recursos.

- Privacidade: sem dados pessoais, minimizacao de dados e guardrail de entrada.
- Responsabilidade: decisao final humana e transparencia por tracing.
- Sustentabilidade digital: processamento local e modelos leves reduzem o consumo de
  energia e a dependencia de data centers.
- Limites e vieses dos dados simulados sao declarados.

## 11. Limitacoes e melhorias

Limitacoes: dados simulados, limites didaticos, modelo solar simples, regressao com
poucos pontos e agentes sem LLM real.

Melhorias: sensores reais (Arduino ou IoT), regressao multipla (temperatura e
consumo), banco Oracle, painel web, LLM com ferramentas e auditoria completa de tracing.
