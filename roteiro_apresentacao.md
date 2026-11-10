# Roteiro de apresentação (vídeo de 6 minutos)

O vídeo precisa ter no mínimo 5 minutos. Este roteiro soma cerca de 6 min 15 s e deixa folga: se
algum trecho sair mais rápido, ainda passa de 5 minutos. O `graficos_ou_imagens/exemplo_execucao.txt`
já tem a saída da demonstração, então não precisa gerar outra; use-o só como apoio.

## Antes de gravar

1. Apague o `aurora_siger.db` para começar com os dados originais.
2. Rode `python codigo_fonte.py --web` e deixe o painel aberto no navegador.
3. Deixe em outras abas: o circuito montado no Tinkercad (guia em `tinkercad/guia_tinkercad.md`),
   o `circuito_logico.png` e o `script_banco.sql`.
4. Deixe um terminal aberto na pasta do projeto para a opção 10 (agentes) e o `--demo`.
5. Grave a tela com o microfone, publique no YouTube como **não listado** e cole o link em `link_video.txt`.

## Roteiro com tempos

| Tempo | O que mostrar | O que falar |
|---|---|---|
| 0:00 a 0:30 | Painel, tela inicial | Nome do projeto (Sistema de Controle para Projeção de Recursos da Aurora), seu nome e RM. A colônia Aurora Siger depende de energia, ar e temperatura estáveis, e a comunicação com a Terra tem atraso de minutos. O sistema centraliza as leituras, classifica o risco e sugere ações. |
| 0:30 a 1:30 | `script_banco.sql`, depois painel em Leituras | Duas tabelas, `modulos` e `leituras`, ligadas por chave estrangeira, com restrições CHECK. No painel: consultar, filtrar por módulo, abrir Nova leitura. Na etapa Sensores, digitar bateria 120 e mostrar "Fora da faixa" bloqueando o avanço; corrigir para 62,5, avançar e salvar. Mostrar o Operador com botões de alterar e excluir desativados na EST-01 (privilégio mínimo). |
| 1:30 a 2:30 | Regra no painel (Circuito lógico), `circuito_logico.png`, Tinkercad | Cinco entradas: A bateria menor que 20%, B O₂ menor que 19,5%, C consumo maior que geração, D bateria menor que 40%, E temperatura fora de 18 a 26 °C. Y1 = A + B é crítico e Y2 = (C · D) + E é atenção. No Tinkercad, ajustar os potenciômetros para os casos do guia: HAB-01 acende o vermelho, REC-01 acende o amarelo, ENR-01 acende o verde. Dizer que a mesma regra está em `classificar_risco()`. |
| 2:30 a 3:15 | Painel em Estruturas de dados (ou opção 9 do terminal) | Tabela hash para buscar os parâmetros do módulo em O(1). Heap para ordenar os alertas, crítico primeiro. Grafo com busca em largura para a rede de energia: se o HAB-01 falhar, o REC-01 fica sem energia. Pilha para o histórico das operações. |
| 3:15 a 4:15 | Painel em Simulação e Modelo linear | Estado de carga por integração numérica, regra do trapézio, com geração solar entre 6h e 18h. Monte Carlo com 300 cenários e tempestade de poeira: probabilidade de bateria abaixo de 20% em 24 h de 61% no HAB-01, 100% na EST-01 e 0% na REC-01. Regressão linear: a estufa descarrega a 4,48 %/h (R² 0,90) e o habitat chega ao limite em cerca de 44 h. Ser honesto: o R² da REC-01 é baixo (0,11), então o modelo apoia a decisão, não é previsão definitiva. |
| 4:15 a 5:00 | Terminal, opção 10 (fluxo de agentes) | AgenteSensores, AgenteRisco e AgenteRecomendação, com handoffs e tracing impressos. Guardrail de entrada bloqueando pedido com dados pessoais. Toda recomendação exige confirmação humana e o agente nunca aciona atuadores. Deixar claro que os agentes são simulados, sem LLM real, e que a busca de procedimentos por palavra-chave simula RAG. |
| 5:00 a 5:40 | Relatório, seções 9 e 10 | Processamento na borda, no próprio habitat, por causa do atraso da Terra. CPU para regras e banco; GPU ou NPU para modelos de IA maiores; a hierarquia de memória importa porque mover dado custa mais energia que calcular. Sustentabilidade e cidadania digital: sem dados pessoais, decisão final humana, tracing para transparência, modelos leves. |
| 5:40 a 6:15 | Opção 11 do terminal ou relatório, seção 11 | Limitações: dados simulados, limites didáticos, poucos pontos na regressão, modelo solar simplificado, agentes sem LLM real. Melhorias: sensores reais (Arduino ou IoT), regressão múltipla, banco Oracle, LLM com ferramentas. Agradecer e encerrar. |

## Dicas

- Fale um pouco mais devagar nas demonstrações; é o que garante passar dos 5 minutos sem enrolar.
- Se o tempo apertar numa gravação, a ordem do que dá para encurtar é: estruturas de dados, depois arquitetura.
- Cada tópico do roadmap aparece ao menos uma vez: dados e banco, CRUD, circuitos, estruturas, simulação,
  modelo de decisão, IA multiagente, arquitetura e sustentabilidade.
- Antes de publicar, confira o áudio e se o link não listado abre numa janela anônima.
