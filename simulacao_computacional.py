# -*- coding: utf-8 -*-
# Simulacao computacional do SIFSM: SoC da bateria (integral numerica) e Monte Carlo
# Gera graficos em graficos_ou_imagens/
# Uso: python simulacao_computacional.py
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import codigo_fonte as sf

sf.inicializar_banco()
os.makedirs(sf.IMG_DIR, exist_ok=True)

# Grafico 1: SoC de cada modulo nas proximas 24 h (cenario normal x tempestade de poeira)
fig, ax = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
cenarios = (
    (1.0, "Cenario normal"),
    (0.3, "Tempestade de poeira (30% solar)"),
)
for k, (fator, titulo) in enumerate(cenarios):
    for m, p in sf.MODULOS.items():
        ult = sf.ultimas_leituras()[m]
        t, soc = sf.simular_soc(
            p["capacidade_kwh"], p["consumo_medio_kw"], p["geracao_pico_kw"],
            ult["bateria_pct"], int(ult["data_hora"][11:13]), fator_ger=fator,
        )
        ax[k].plot(t, soc, label=m)
    ax[k].axhline(sf.LIM["bat_critica"], color="r", ls="--", lw=1)
    ax[k].set_title(titulo)
    ax[k].set_xlabel("horas a partir da ultima leitura")
ax[0].set_ylabel("bateria (%)")
ax[0].legend()
fig.tight_layout()
fig.savefig(os.path.join(sf.IMG_DIR, "soc_cenarios.png"), dpi=140)
plt.close(fig)

# Grafico 2: histograma Monte Carlo do pior SoC do habitat
rng = np.random.default_rng(7)
p = sf.MODULOS["HAB-01"]
ult = sf.ultimas_leituras()["HAB-01"]
minimos = [
    sf.simular_soc(
        p["capacidade_kwh"], p["consumo_medio_kw"], p["geracao_pico_kw"],
        ult["bateria_pct"], int(ult["data_hora"][11:13]),
        fator_ger=rng.uniform(0.3, 1), ruido=0.05, rng=rng,
    )[1].min()
    for _ in range(300)
]
plt.figure(figsize=(6, 4))
plt.hist(minimos, bins=20, color="#ff4b0a")
plt.axvline(20, color="k", ls="--")
plt.xlabel("menor SoC em 24 h (%)")
plt.ylabel("cenarios")
plt.title("Monte Carlo - HAB-01 (300 cenarios)")
plt.tight_layout()
plt.savefig(os.path.join(sf.IMG_DIR, "monte_carlo_hab01.png"), dpi=140)
print("Graficos salvos em", sf.IMG_DIR)
