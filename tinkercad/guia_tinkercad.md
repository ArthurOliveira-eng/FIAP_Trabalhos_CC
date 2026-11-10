# Circuito no Tinkercad (Circuits)

Monta os sensores e a regra de risco do SCPRA com um Arduino Uno. A lógica é a mesma
de `classificar_risco()` no `codigo_fonte.py` e do `circuito_logico.png`.

## Componentes

| Qtd | Componente | Função |
|---|---|---|
| 1 | Arduino Uno R3 | Lê os sensores e aplica a regra |
| 4 | Potenciômetro | Simulam bateria (A0), O₂ (A1), consumo (A3) e geração (A4) |
| 1 | Sensor de temperatura TMP36 | Temperatura do módulo (A2) |
| 3 | LED (vermelho, amarelo, verde) | Y1 crítico, Y2 atenção, normal |
| 3 | Resistor 220 Ω | Um por LED |

## Ligações

| Peça | Ligação |
|---|---|
| Potenciômetros (4) | Pino 1 em 5V, pino 3 em GND, pino do meio em A0 (bateria), A1 (O₂), A3 (consumo) e A4 (geração) |
| TMP36 | Esquerdo em 5V, meio em A2, direito em GND (lado reto virado para você) |
| LED vermelho | D8 → resistor 220 Ω → anodo; catodo em GND |
| LED amarelo | D9 → resistor 220 Ω → anodo; catodo em GND |
| LED verde | D10 → resistor 220 Ω → anodo; catodo em GND |

## Passo a passo

1. No Tinkercad, abra **Circuits** e crie um novo circuito.
2. Coloque as peças da tabela e faça as ligações.
3. Clique em **Código**, escolha **Texto**, apague o exemplo e cole o conteúdo de `circuito_tinkercad.ino`.
4. Abra o **Monitor Serial**, clique em **Iniciar simulação** e mexa nos potenciômetros e no TMP36.

## Escalas dos sensores

| Entrada | Faixa lida |
|---|---|
| Bateria (A0) | 0 a 100 % |
| O₂ (A1) | 15 a 25 % |
| Consumo (A3) e geração (A4) | 0 a 20 kW |
| Temperatura (A2) | O TMP36 do Tinkercad tem o valor definido em °C direto na peça |

## Testes com os dados da colônia (última leitura de cada módulo)

Posição do cursor do potenciômetro = valor ÷ faixa.

| Módulo | Bateria | O₂ | Temp. | Consumo | Geração | LEDs esperados |
|---|---|---|---|---|---|---|
| HAB-01 | 57,6 % (cursor em 58 %) | 19,2 % (42 %) | 21 °C | 9,6 kW (48 %) | 0 kW (0 %) | Vermelho |
| EST-01 | 17,8 % (18 %) | 20,9 % (59 %) | 24,4 °C | 15,5 kW (78 %) | 0 kW (0 %) | Vermelho e amarelo |
| ENR-01 | 98,8 % (99 %) | 20,9 % (59 %) | 21,8 °C | 2,6 kW (13 %) | 0 kW (0 %) | Verde |
| REC-01 | 69,3 % (69 %) | 20,9 % (59 %) | 27,2 °C | 6,6 kW (33 %) | 0 kW (0 %) | Amarelo |

O LED amarelo mostra Y2 sozinho, como no circuito lógico. No EST-01 a bateria baixa também
satisfaz C·D, então o amarelo acende junto com o vermelho. No terminal e no painel o
status final dá prioridade ao crítico.

## Versão só com portas lógicas (opcional)

O `circuito_logico.png` usa 74HC32 (OR) e 74HC08 (AND). Se esses CIs aparecerem na lista de
componentes do seu Tinkercad, dá para montar Y1 = A + B e Y2 = (C·D) + E ligando as saídas
dos comparadores às portas. Se não aparecerem, use a versão com Arduino acima.
