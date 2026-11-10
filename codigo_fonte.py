# -*- coding: utf-8 -*-
# SCPRA - Sistema de Controle para Projeção de Recursos da Aurora
# Prototipo para a colonia Aurora Siger
#
# Execucao:
#   python codigo_fonte.py          menu interativo
#   python codigo_fonte.py --demo   demonstracao automatica
#   python codigo_fonte.py --web    painel web (http://127.0.0.1:8000, opcao --porta N)
# Dependencias: Python 3.9+, numpy (matplotlib so para gerar imagens)
import csv
import heapq
import json
import os
import re
import sqlite3
import sys
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "aurora_siger.db")
CSV_PATH = os.path.join(BASE, "dados_aurora_siger.csv")
SQL_PATH = os.path.join(BASE, "script_banco.sql")
IMG_DIR = os.path.join(BASE, "graficos_ou_imagens")

# Limites da regra booleana (valores didaticos)
LIM = {
    "bat_critica": 20.0,
    "bat_media": 40.0,
    "o2_min": 19.5,
    "temp_min": 18.0,
    "temp_max": 26.0,
}
CAMPOS = [
    "id_modulo",
    "data_hora",
    "consumo_kw",
    "geracao_kw",
    "temperatura_c",
    "o2_pct",
    "bateria_pct",
]

# Estruturas de dados
# Tabela hash (dict): busca O(1) dos parametros de cada modulo
MODULOS = {}
# Pilha (LIFO): ultimas operacoes do CRUD
HISTORICO = []
# Grafo (lista de adjacencia) da rede de energia
REDE = {
    "ENR-01": ["HAB-01", "EST-01"],
    "HAB-01": ["ENR-01", "REC-01"],
    "EST-01": ["ENR-01"],
    "REC-01": ["HAB-01"],
}


# 1. Banco de dados e CRUD

# Abre conexao com o banco
def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


# Cria as tabelas e carrega o CSV se o banco estiver vazio
def inicializar_banco():
    con = conectar()
    try:
        with open(SQL_PATH, encoding="utf-8") as f:
            con.executescript(f.read())
        if con.execute("SELECT COUNT(*) FROM leituras").fetchone()[0] == 0:
            with open(CSV_PATH, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    con.execute(
                        "INSERT INTO leituras (%s) VALUES (?,?,?,?,?,?,?)"
                        % ",".join(CAMPOS),
                        [r[c] for c in CAMPOS],
                    )
            print("[BANCO] Dados carregados de dados_aurora_siger.csv")
        con.commit()
    except (OSError, sqlite3.Error) as e:
        print("[ERRO] Falha ao preparar o banco:", e)
        raise
    finally:
        con.close()
    carregar_modulos()


# Le a tabela modulos para o dict MODULOS
def carregar_modulos():
    MODULOS.clear()
    con = conectar()
    try:
        for r in con.execute("SELECT * FROM modulos"):
            MODULOS[r["id_modulo"]] = dict(r)
    finally:
        con.close()


# Levanta ValueError se algum campo estiver fora da faixa fisica
def validar_leitura(d):
    if d["id_modulo"] not in MODULOS:
        raise ValueError("Modulo inexistente: %s" % d["id_modulo"])
    if d["consumo_kw"] < 0 or d["geracao_kw"] < 0:
        raise ValueError("Consumo e geracao nao podem ser negativos.")
    if not (0 <= d["o2_pct"] <= 100 and 0 <= d["bateria_pct"] <= 100):
        raise ValueError("O2 e bateria devem estar entre 0 e 100 %.")
    if not (-100 <= d["temperatura_c"] <= 100):
        raise ValueError("Temperatura fora da faixa plausivel.")


# C - Create
def criar_leitura(d):
    con = conectar()
    try:
        validar_leitura(d)
        cur = con.execute(
            "INSERT INTO leituras (%s) VALUES (?,?,?,?,?,?,?)" % ",".join(CAMPOS),
            [d[c] for c in CAMPOS],
        )
        con.commit()
    except (ValueError, KeyError, sqlite3.Error) as e:
        print("[ERRO] Nao foi possivel cadastrar:", e)
        return None
    else:
        HISTORICO.append(("CADASTRO", cur.lastrowid))
        print("[OK] Leitura %d cadastrada." % cur.lastrowid)
        return cur.lastrowid
    finally:
        con.close()


# R - Read
def listar_leituras(modulo=None):
    con = conectar()
    try:
        sql = "SELECT * FROM leituras"
        args = []
        if modulo:
            sql += " WHERE id_modulo = ?"
            args.append(modulo)
        return [
            dict(r)
            for r in con.execute(sql + " ORDER BY data_hora, id_leitura", args)
        ]
    finally:
        con.close()


# U - Update
def atualizar_leitura(id_leitura, campo, valor):
    # Lista branca evita SQL injection
    if campo not in CAMPOS:
        print("[ERRO] Campo invalido.")
        return False
    con = conectar()
    try:
        cur = con.execute(
            "UPDATE leituras SET %s = ? WHERE id_leitura = ?" % campo,
            (valor, id_leitura),
        )
        con.commit()
    except sqlite3.Error as e:
        print("[ERRO] Falha ao alterar:", e)
        return False
    else:
        if cur.rowcount == 0:
            print("[AVISO] Leitura %s nao encontrada." % id_leitura)
            return False
        HISTORICO.append(("ALTERACAO", id_leitura))
        print("[OK] Leitura %s alterada (%s = %s)." % (id_leitura, campo, valor))
        return True
    finally:
        con.close()


# D - Delete
def excluir_leitura(id_leitura):
    con = conectar()
    try:
        cur = con.execute("DELETE FROM leituras WHERE id_leitura = ?", (id_leitura,))
        con.commit()
    except sqlite3.Error as e:
        print("[ERRO] Falha ao excluir:", e)
        return False
    else:
        if cur.rowcount == 0:
            print("[AVISO] Leitura %s nao encontrada." % id_leitura)
            return False
        HISTORICO.append(("EXCLUSAO", id_leitura))
        print("[OK] Leitura %s excluida." % id_leitura)
        return True
    finally:
        con.close()


# Imprime as leituras em tabela
# Interface de terminal (cores ANSI; desligam sozinhas se a saida nao for um terminal)
if os.name == "nt":
    os.system("")  # habilita sequencias ANSI no Windows
_COR = (sys.stdout.isatty() or bool(os.environ.get("FORCE_COLOR"))) and not os.environ.get("NO_COLOR")
NIVEL_COR = {"CRITICO": "1;97;41", "ATENCAO": "1;30;43", "NORMAL": "1;30;42"}


def _c(txt, cod):
    return "\033[%sm%s\033[0m" % (cod, txt) if _COR else txt


def titulo(txt):
    print("\n" + _c("▌ " + txt.upper(), "1;38;5;202"))
    print(_c("─" * (len(txt) + 2), "90"))


def imprimir_leituras(lista):
    """Tabela com bordas; bateria e status coloridos conforme a regra booleana."""
    cab = ["ID", "MÓDULO", "DATA/HORA", "CONS", "GER", "TEMP", "O2%", "BAT%", "STATUS"]
    larg = [4, 7, 16, 6, 6, 6, 6, 6, 9]

    def borda(e, m, d):
        return _c(e + m.join("─" * (w + 2) for w in larg) + d, "90")

    def cel(txt, w, alin="<", cor=None):
        t = "{:{a}{w}}".format(txt, a=alin, w=w)
        return " " + (_c(t, cor) if cor else t) + " "

    sep = _c("│", "90")
    print(borda("┌", "┬", "┐"))
    print(sep + sep.join(cel(c, w, "^", "1") for c, w in zip(cab, larg)) + sep)
    print(borda("├", "┼", "┤"))
    for l in lista:
        nivel = classificar_risco(l)
        bat = l["bateria_pct"]
        cor_bat = "1;31" if bat < LIM["bat_critica"] else "33" if bat < LIM["bat_media"] else None
        celulas = [
            cel(l["id_leitura"], larg[0], ">"), cel(l["id_modulo"], larg[1]),
            cel(l["data_hora"], larg[2]), cel("%.1f" % l["consumo_kw"], larg[3], ">"),
            cel("%.1f" % l["geracao_kw"], larg[4], ">"), cel("%.1f" % l["temperatura_c"], larg[5], ">"),
            cel("%.1f" % l["o2_pct"], larg[6], ">"), cel("%.1f" % bat, larg[7], ">", cor_bat),
            cel(nivel, larg[8], "^", NIVEL_COR[nivel]),
        ]
        print(sep + sep.join(celulas) + sep)
    print(borda("└", "┴", "┘"))
    print(_c("  %d registro(s)" % len(lista), "90"))


# Controle de acesso por perfil (privilegio minimo): C=Create R=Read U=Update D=Delete
PERFIS = {
    "Operador": {"HAB-01": "CR", "EST-01": "R", "ENR-01": "R", "REC-01": "CR"},
    "Engenheiro": {m: "CRU" for m in ("HAB-01", "EST-01", "ENR-01", "REC-01")},
    "Comandante": {m: "CRUD" for m in ("HAB-01", "EST-01", "ENR-01", "REC-01")},
}
NOME_ACAO = {"C": "cadastrar", "R": "consultar", "U": "alterar", "D": "excluir"}


def pode(perfil, modulo, acao):
    return acao in PERFIS.get(perfil, {}).get(modulo, "")


def matriz_permissoes(perfil):
    titulo("Perfil e acesso: " + perfil)
    print("  %-8s" % "MÓDULO" + "".join("%-8s" % a for a in ("Create", "Read", "Update", "Delete")))
    for m, perm in PERFIS[perfil].items():
        marcas = "".join(
            _c("■".ljust(8), "1") if a in perm else _c("□".ljust(8), "90") for a in "CRUD"
        )
        print("  %-8s%s" % (m, marcas))


def obter_leitura(id_leitura):
    con = conectar()
    try:
        r = con.execute("SELECT * FROM leituras WHERE id_leitura = ?", (id_leitura,)).fetchone()
        return dict(r) if r else None
    finally:
        con.close()


# 2. Logica booleana e circuito logico

# Converte uma leitura nas 5 entradas booleanas (A a E do circuito)
def sinais(l):
    return {
        "A": l["bateria_pct"] < LIM["bat_critica"],
        "B": l["o2_pct"] < LIM["o2_min"],
        "C": l["consumo_kw"] > l["geracao_kw"],
        "D": l["bateria_pct"] < LIM["bat_media"],
        "E": not (LIM["temp_min"] <= l["temperatura_c"] <= LIM["temp_max"]),
    }


# CRITICO = A ou B | ATENCAO = (C e D) ou E | senao NORMAL
def classificar_risco(l):
    s = sinais(l)
    if s["A"] or s["B"]:
        return "CRITICO"
    if (s["C"] and s["D"]) or s["E"]:
        return "ATENCAO"
    return "NORMAL"


# Imprime as tabelas-verdade dos dois circuitos
def tabela_verdade():
    print("\nCircuito 1 (CRITICO):  Y1 = A + B      | A=bateria<20%  B=O2<19,5%")
    print(" A B | Y1")
    for a in (0, 1):
        for b in (0, 1):
            print(" %d %d |  %d" % (a, b, a or b))
    print(
        "\nCircuito 2 (ATENCAO):  Y2 = (C . D) + E | "
        "C=consumo>geracao D=bateria<40% E=temp fora"
    )
    print(" C D E | Y2")
    for c in (0, 1):
        for d in (0, 1):
            for e in (0, 1):
                print(" %d %d %d |  %d" % (c, d, e, (c and d) or e))
    print("\nEquivalente em Arduino/Tinkercad: 5 entradas (comparadores/sensores),")
    print("portas OR e AND (CI 74HC32 e 74HC08) e 2 LEDs (vermelho = Y1, amarelo = Y2).")


# Gera circuito_logico.png (precisa de matplotlib)
def gerar_circuito_png():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("[AVISO] matplotlib ausente: imagem do circuito nao gerada.")
        return
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.axis("off")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7)
    ent = {"A": 6.2, "B": 5.2, "C": 3.6, "D": 2.6, "E": 1.2}
    nomes = {
        "A": "A: bateria < 20%",
        "B": "B: O2 < 19,5%",
        "C": "C: consumo > geracao",
        "D": "D: bateria < 40%",
        "E": "E: temperatura fora",
    }
    for k, y in ent.items():
        ax.text(0, y, nomes[k], ha="left", va="center", fontsize=8)

    # Desenha uma porta logica
    def porta(x, y, rot, cor):
        ax.add_patch(plt.Rectangle((x, y - 0.6), 1.6, 1.2, fc=cor, ec="k"))
        ax.text(x + 0.8, y, rot, ha="center", va="center", fontweight="bold")

    # Desenha um fio
    def fio(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], "k", lw=1)

    # Circuito 1: Y1 = A + B
    porta(5, 5.7, "OR", "#ffb199")
    fio(2.9, 6.2, 5, 5.9)
    fio(2.9, 5.2, 5, 5.5)
    fio(6.6, 5.7, 9.5, 5.7)
    ax.text(9.6, 5.7, "Y1 = CRITICO (LED vermelho)", va="center",
            fontsize=9, color="#c1380a")

    # Circuito 2: Y2 = (C . D) + E
    porta(5, 3.1, "AND", "#e8ff7a")
    fio(3.2, 3.6, 5, 3.3)
    fio(3.2, 2.6, 5, 2.9)
    porta(7.8, 2.1, "OR", "#ffb199")
    fio(6.6, 3.1, 7.2, 3.1)
    fio(7.2, 3.1, 7.2, 2.4)
    fio(7.2, 2.4, 7.8, 2.4)
    fio(2.9, 1.2, 7.2, 1.2)
    fio(7.2, 1.2, 7.2, 1.8)
    fio(7.2, 1.8, 7.8, 1.8)
    fio(9.4, 2.1, 9.8, 2.1)
    ax.text(9.9, 2.1, "Y2 = ATENCAO (LED amarelo)", va="center",
            fontsize=9, color="#8a7a00")

    ax.set_title("SCPRA - circuito logico de decisao de risco", fontsize=11)
    os.makedirs(IMG_DIR, exist_ok=True)
    fig.savefig(os.path.join(BASE, "circuito_logico.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("[OK] circuito_logico.png gerado.")


# 3. Estruturas de dados (heap, grafo, pilha, hash)

# Ultima leitura de cada modulo, usando dict (hash) como indice
def ultimas_leituras():
    ult = {}
    for l in listar_leituras():
        ult[l["id_modulo"]] = l
    return ult


# Fila de prioridade (heap): CRITICO sai antes de ATENCAO, empate pela menor bateria
def fila_de_alertas():
    heap = []
    for mod, l in ultimas_leituras().items():
        nivel = classificar_risco(l)
        if nivel != "NORMAL":
            prio = 0 if nivel == "CRITICO" else 1
            heapq.heappush(heap, (prio, l["bateria_pct"], mod, nivel))
    return heap


# BFS no grafo: caminho da usina ate o modulo, evitando um modulo em falha
def rota_energia(destino, falha=None):
    fila, vistos = deque([["ENR-01"]]), {"ENR-01"}
    while fila:
        caminho = fila.popleft()
        if caminho[-1] == destino:
            return caminho
        for viz in REDE[caminho[-1]]:
            if viz not in vistos and viz != falha:
                vistos.add(viz)
                fila.append(caminho + [viz])
    return None


# Mostra um exemplo de cada estrutura
def mostrar_estruturas():
    print("\n[HASH] Parametros do modulo EST-01 (busca O(1)):", MODULOS.get("EST-01"))
    print("[GRAFO] Rota de energia ENR-01 -> REC-01:",
          " -> ".join(rota_energia("REC-01")))
    for falha in ("HAB-01", "EST-01"):
        sem = [m for m in REDE if m != falha and rota_energia(m, falha) is None]
        print("[GRAFO] Se %s falhar, ficam sem energia: %s" % (falha, sem or "nenhum"))
    print("[PILHA] Ultimas operacoes (topo primeiro):",
          list(reversed(HISTORICO))[:5] or "vazia")
    print("[HEAP] Alertas por prioridade:")
    heap = fila_de_alertas()
    while heap:
        p, bat, mod, nivel = heapq.heappop(heap)
        print("   %-8s %s (bateria %.1f%%)" % (nivel, mod, bat))


# 4. Simulacao computacional e integracao numerica (estado de carga)

# SoC(t) = SoC0 + 100/cap * integral de (P_ger - P_cons) dt, pela regra do trapezio
def simular_soc(cap, cons_kw, ger_pico_kw, soc0, hora_ini=0, horas=24, dt=0.25,
                fator_ger=1.0, ruido=0.0, rng=None):
    t = np.arange(0, horas + dt, dt)
    hr = (t + hora_ini) % 24
    ger = ger_pico_kw * fator_ger * np.clip(np.sin(np.pi * (hr - 6) / 12), 0, None)
    if rng is not None:
        cons = cons_kw * (1 + ruido * rng.standard_normal(len(t)))
    else:
        cons = cons_kw * np.ones_like(t)
    p = ger - cons
    soc = [soc0]
    for i in range(1, len(t)):
        # Energia do passo em kWh
        energia = (p[i] + p[i - 1]) / 2 * dt
        soc.append(min(100.0, max(0.0, soc[-1] + 100 * energia / cap)))
    return t, np.array(soc)


# Cenarios aleatorios: tempestade de poeira reduz a geracao solar (30% a 100%)
def monte_carlo(id_mod, n=300, seed=7):
    m = MODULOS[id_mod]
    ult = ultimas_leituras()[id_mod]
    hora = int(ult["data_hora"][11:13])
    rng = np.random.default_rng(seed)
    minimos = []
    for _ in range(n):
        _, soc = simular_soc(
            m["capacidade_kwh"], m["consumo_medio_kw"], m["geracao_pico_kw"],
            ult["bateria_pct"], hora, 24, 0.25, rng.uniform(0.3, 1.0), 0.05, rng,
        )
        minimos.append(soc.min())
    arr = np.array(minimos)
    return {
        "prob_critico": float((arr < LIM["bat_critica"]).mean()),
        "min_medio": float(arr.mean()),
        "p5": float(np.percentile(arr, 5)),
        "soc_inicial": ult["bateria_pct"],
    }


# 5. Modelo linear simples (regressao: bateria x tempo)

# Ajusta SoC = a*t + b nas ultimas n leituras (t em horas) e estima o tempo ate 20%
def regressao_bateria(id_mod, n=4):
    ls = listar_leituras(id_mod)[-n:]
    if len(ls) < 3:
        return None
    x = np.arange(len(ls)) * 4.0
    y = np.array([l["bateria_pct"] for l in ls])
    a, b = np.polyfit(x, y, 1)
    res = ((y - (a * x + b)) ** 2).sum()
    tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - res / tot if tot > 0 else 1.0
    atual = float(y[-1])
    if atual <= LIM["bat_critica"]:
        horas = 0.0
    elif a < 0:
        horas = (LIM["bat_critica"] - atual) / a
    else:
        horas = None
    return {"a": float(a), "b": float(b), "r2": float(r2),
            "atual": atual, "horas": horas}


# 6. IA por agentes (simulada): handoffs, guardrails, RAG e tracing

# Base de conhecimento minima (RAG simulado por palavra-chave)
PROCEDIMENTOS = {
    "bateria": "Reduzir cargas nao essenciais e priorizar o modulo critico na rede.",
    "oxigenio": "Verificar a Reciclagem de Ar (REC-01) e inspecionar vedacao do modulo.",
    "temperatura": "Revisar o controle termico e a isolacao do modulo.",
}


# Guardrail de entrada: bloqueia pedidos com dados pessoais
def guardrail_entrada(texto):
    if re.search(r"\b(cpf|rg|senha|nome do tripulante)\b", texto.lower()):
        raise PermissionError(
            "Guardrail de privacidade: dados pessoais nao sao processados."
        )


# Agente 1: le as ultimas leituras
def agente_sensores(ctx):
    ctx["leituras"] = ultimas_leituras()
    ctx["trace"].append("AgenteSensores: leu %d modulos" % len(ctx["leituras"]))


# Agente 2: classifica o risco com a regra booleana
def agente_risco(ctx):
    ctx["risco"] = {m: classificar_risco(l) for m, l in ctx["leituras"].items()}
    ctx["trace"].append("AgenteRisco: classificou com regra booleana " + str(ctx["risco"]))


# Agente 3: sugere acoes (guardrail de saida: so sugere, humano confirma)
def agente_recomendacao(ctx):
    ctx["recs"] = []
    for m, nivel in ctx["risco"].items():
        if nivel == "NORMAL":
            continue
        s = sinais(ctx["leituras"][m])
        if s["A"] or s["D"]:
            chave = "bateria"
        elif s["B"]:
            chave = "oxigenio"
        else:
            chave = "temperatura"
        ctx["recs"].append(
            "%s [%s]: %s (REQUER CONFIRMACAO HUMANA)" % (m, nivel, PROCEDIMENTOS[chave])
        )
    ctx["trace"].append("AgenteRecomendacao: consultou procedimentos (RAG simulado)")


# Orquestra o fluxo Sensores -> Risco -> Recomendacao
def orquestrar(pergunta="Analisar sustentabilidade da colonia"):
    ctx = {"trace": []}
    try:
        guardrail_entrada(pergunta)
    except PermissionError as e:
        print("[BLOQUEADO]", e)
        return None
    fluxo = (
        (agente_sensores, "AgenteRisco"),
        (agente_risco, "AgenteRecomendacao"),
        (agente_recomendacao, None),
    )
    for ag, prox in fluxo:
        ag(ctx)
        if prox:
            ctx["trace"].append("HANDOFF -> " + prox)
    return ctx


# 7. Analise integrada e relatorio final

# Analise de sustentabilidade: risco, alertas, regressao, Monte Carlo e recomendacoes
def analisar_colonia():
    print("\n=== ANALISE DE SUSTENTABILIDADE DA COLONIA ===")
    ctx = orquestrar()
    for m, nivel in ctx["risco"].items():
        print("  %-7s -> %s" % (m, nivel))
    print("\nFila de alertas (heap):")
    heap = fila_de_alertas()
    primeiro = None
    while heap:
        p, bat, mod, nivel = heapq.heappop(heap)
        primeiro = primeiro or mod
        print("  %-8s %s (bateria %.1f%%)" % (nivel, mod, bat))
    for m in MODULOS:
        r = regressao_bateria(m)
        if r and r["a"] < 0:
            if r["horas"] == 0:
                h = "ja abaixo do limite"
            else:
                h = "~%.1f h ate 20%%" % r["horas"]
            print("Regressao %s: %.2f %%/h, R2=%.2f, %s" % (m, r["a"], r["r2"], h))
    for alvo in (m for m in MODULOS if m != "ENR-01"):
        mc = monte_carlo(alvo)
        print("Monte Carlo %s: P(bateria<20%% em 24 h) = %.0f%% | pior caso (P5) = %.1f%%"
              % (alvo, 100 * mc["prob_critico"], mc["p5"]))
    print("\nRecomendacoes tecnicas:")
    for r in ctx["recs"]:
        print("  -", r)
    print("\nTrace:", " | ".join(ctx["trace"]))


# Resumo final com contagem de riscos e limitacoes
def analise_final():
    ls = listar_leituras()
    cont = {"NORMAL": 0, "ATENCAO": 0, "CRITICO": 0}
    for l in ls:
        cont[classificar_risco(l)] += 1
    print("\n=== ANALISE FINAL ===")
    print("Leituras: %d | NORMAL: %d | ATENCAO: %d | CRITICO: %d" % (len(ls), *cont.values()))
    print("Consumo medio da colonia: %.1f kW" % np.mean([l["consumo_kw"] for l in ls]))
    print("Limitacoes: dados simulados; limites didaticos; regressao com poucos pontos;")
    print("  modelo solar simplificado (sem poeira detalhada); agentes sao simulados (sem LLM real).")
    print("Impacto: decisoes sao sugestoes com confirmacao humana; sem dados pessoais; baixo custo")
    print("  computacional (CPU local, borda) reduz energia e depende menos de data centers.")


# 8. Menu e demonstracao

# Le um numero dentro do intervalo, repetindo ate ser valido
def ler_numero(msg, minimo, maximo):
    while True:
        try:
            v = float(input(msg).replace(",", "."))
        except ValueError:
            print("Valor invalido: digite um numero.")
        else:
            if minimo <= v <= maximo:
                return v
            print("Digite um valor entre %s e %s." % (minimo, maximo))


# Cadastro guiado pelo teclado
def cadastrar_interativo():
    mod = input("Modulo (%s): " % ", ".join(MODULOS)).strip().upper()
    d = {
        "id_modulo": mod,
        "data_hora": input("Data/hora (AAAA-MM-DD HH:MM): ").strip(),
        "consumo_kw": ler_numero("Consumo (kW): ", 0, 1000),
        "geracao_kw": ler_numero("Geracao (kW): ", 0, 1000),
        "temperatura_c": ler_numero("Temperatura (C): ", -100, 100),
        "o2_pct": ler_numero("O2 (%): ", 0, 100),
        "bateria_pct": ler_numero("Bateria (%): ", 0, 100),
    }
    criar_leitura(d)


# Menu principal
def menu():
    opcoes = {
        "1": "Cadastrar leitura",
        "2": "Consultar leituras",
        "3": "Alterar leitura",
        "4": "Excluir leitura",
        "5": "Analisar sustentabilidade da colonia",
        "6": "Circuito logico (tabela-verdade + imagem)",
        "7": "Simulacao Monte Carlo",
        "8": "Modelo linear (regressao)",
        "9": "Estruturas de dados",
        "10": "Fluxo de agentes de IA",
        "11": "Analise final e limitacoes",
        "0": "Sair",
    }
    while True:
        print("\n===== SCPRA - Aurora Siger =====")
        for k, v in opcoes.items():
            print(" %2s) %s" % (k, v))
        op = input("Escolha: ").strip()
        try:
            if op == "1":
                cadastrar_interativo()
            elif op == "2":
                modulo = input("Modulo (Enter = todos): ").strip().upper() or None
                imprimir_leituras(listar_leituras(modulo))
            elif op == "3":
                atualizar_leitura(
                    int(ler_numero("ID: ", 1, 10**6)),
                    input("Campo (%s): " % ", ".join(CAMPOS[2:])).strip(),
                    ler_numero("Novo valor: ", -1000, 1000),
                )
            elif op == "4":
                excluir_leitura(int(ler_numero("ID: ", 1, 10**6)))
            elif op == "5":
                analisar_colonia()
            elif op == "6":
                tabela_verdade()
                gerar_circuito_png()
            elif op == "7":
                mod = input("Modulo (ex.: HAB-01): ").strip().upper()
                if mod in MODULOS:
                    print(monte_carlo(mod))
                else:
                    print("Modulo inexistente.")
            elif op == "8":
                mod = input("Modulo (ex.: EST-01): ").strip().upper()
                print(regressao_bateria(mod) if mod in MODULOS else "Modulo inexistente.")
            elif op == "9":
                mostrar_estruturas()
            elif op == "10":
                c = orquestrar(input("Pergunta ao sistema: ") or "Analisar colonia")
                if c:
                    print("\n".join(c["trace"] + c["recs"]))
            elif op == "11":
                analise_final()
            elif op == "0":
                print("Ate logo!")
                break
            else:
                print("Opcao invalida.")
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            break


# Demonstracao automatica de todas as funcoes
# 9. Painel web (API JSON + interface_web.html), somente biblioteca padrao
HTML_PATH = os.path.join(BASE, "interface_web.html")
FORMATO_DATA = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")


def validar_entrada(d):
    """Valida tipos e formato antes das regras fisicas de validar_leitura()."""
    if not isinstance(d, dict):
        raise ValueError("Corpo da requisição inválido.")
    for c in CAMPOS[2:]:
        if isinstance(d.get(c), bool) or not isinstance(d.get(c), (int, float)):
            raise ValueError("O campo %s deve ser numérico." % c)
    if not FORMATO_DATA.fullmatch(str(d.get("data_hora", ""))):
        raise ValueError("data_hora deve seguir AAAA-MM-DD HH:MM.")
    validar_leitura(d)


def exigir(perfil, modulo, acao):
    if not pode(perfil, modulo, acao):
        raise PermissionError("O perfil %s não pode %s no módulo %s." % (perfil, NOME_ACAO[acao], modulo))


class ApiSCPRA(BaseHTTPRequestHandler):
    server_version = "SCPRA/1.0"

    def log_message(self, fmt, *args):
        print(_c(" %-6s " % self.command, "1;7") + " %s  ->  %s" % (self.path, args[1] if len(args) > 1 else ""))

    def _enviar(self, codigo, obj=None, tipo="application/json; charset=utf-8", bruto=None):
        corpo = bruto if bruto is not None else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 10000:
            raise ValueError("Corpo da requisição grande demais.")
        return json.loads(self.rfile.read(n) or b"{}")

    def _tratar(self, metodo):
        perfil = self.headers.get("X-Perfil", "Operador")
        url = urlparse(self.path)
        p = [x for x in url.path.split("/") if x]
        try:
            if perfil not in PERFIS:
                raise PermissionError("Perfil desconhecido.")
            if p[:1] != ["api"]:
                if metodo == "GET" and not p:
                    with open(HTML_PATH, "rb") as f:
                        return self._enviar(200, tipo="text/html; charset=utf-8", bruto=f.read())
                raise LookupError("Rota inexistente.")
            rota = p[1:2]
            if metodo == "GET" and rota == ["leituras"]:
                return self._enviar(200, listar_leituras(parse_qs(url.query).get("modulo", [None])[0]))
            if metodo == "GET" and rota == ["modulos"]:
                return self._enviar(200, list(MODULOS.values()))
            if metodo == "GET" and rota == ["permissoes"]:
                return self._enviar(200, PERFIS)
            if metodo == "POST" and p == ["api", "leituras"]:
                d = self._corpo()
                exigir(perfil, d.get("id_modulo"), "C")
                validar_entrada(d)
                novo = criar_leitura({c: d[c] for c in CAMPOS})
                if novo is None:
                    raise ValueError("Não foi possível cadastrar a leitura.")
                return self._enviar(201, obter_leitura(novo))
            if metodo in ("PUT", "DELETE") and rota == ["leituras"] and len(p) == 3:
                id_l = int(p[2])
                atual = obter_leitura(id_l)
                if atual is None:
                    raise LookupError("Leitura %d não encontrada." % id_l)
                if metodo == "DELETE":
                    exigir(perfil, atual["id_modulo"], "D")
                    excluir_leitura(id_l)
                    return self._enviar(200, {"ok": True})
                d = self._corpo()
                if not d or set(d) - set(CAMPOS):
                    raise ValueError("Informe apenas campos válidos: " + ", ".join(CAMPOS))
                novo = {**atual, **d}
                exigir(perfil, atual["id_modulo"], "U")
                exigir(perfil, novo["id_modulo"], "U")
                validar_entrada(novo)
                for campo, valor in d.items():
                    atualizar_leitura(id_l, campo, valor)
                return self._enviar(200, obter_leitura(id_l))
            if metodo == "GET" and rota in (["regressao"], ["simulacao"]):
                q = parse_qs(url.query)
                mod = q.get("modulo", [""])[0]
                if mod not in MODULOS:
                    raise ValueError("Módulo inexistente.")
                if rota == ["regressao"]:
                    pts = [[i * 4.0, l["bateria_pct"]] for i, l in enumerate(listar_leituras(mod)[-4:])]
                    return self._enviar(200, {"modelo": regressao_bateria(mod), "pontos": pts})
                fator = float(q.get("fator", ["1"])[0])
                if not 0 < fator <= 1.5:
                    raise ValueError("fator deve estar entre 0 e 1,5.")
                m, ult = MODULOS[mod], ultimas_leituras()[mod]
                t, soc = simular_soc(m["capacidade_kwh"], m["consumo_medio_kw"], m["geracao_pico_kw"],
                                     ult["bateria_pct"], int(ult["data_hora"][11:13]), fator_ger=fator)
                return self._enviar(200, {"t": t.tolist(), "soc": [round(x, 2) for x in soc.tolist()],
                                          "mc": monte_carlo(mod)})
            if metodo == "GET" and rota == ["estruturas"]:
                heap, alertas = fila_de_alertas(), []
                while heap:
                    _, bat, m, nivel = heapq.heappop(heap)
                    alertas.append({"modulo": m, "nivel": nivel, "bateria": bat})
                return self._enviar(200, {
                    "hash": MODULOS, "alertas": alertas,
                    "rotas": {m: rota_energia(m) for m in REDE},
                    "falhas": {f: [m for m in REDE if m != f and rota_energia(m, f) is None] for f in REDE if f != "ENR-01"},
                    "pilha": list(reversed(HISTORICO))[:8]})
            raise LookupError("Rota inexistente.")
        except PermissionError as e:
            self._enviar(403, {"erro": str(e)})
        except LookupError as e:
            self._enviar(404, {"erro": str(e)})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
            self._enviar(422, {"erro": str(e) if not isinstance(e, KeyError) else "Campo ausente: %s" % e})
        except Exception as e:  # ultimo recurso: nunca derruba o servidor
            print(_c("[ERRO] %r" % e, "1;31"))
            self._enviar(500, {"erro": "Erro interno do servidor."})

    def do_GET(self): self._tratar("GET")
    def do_POST(self): self._tratar("POST")
    def do_PUT(self): self._tratar("PUT")
    def do_DELETE(self): self._tratar("DELETE")


def servir(porta=8000):
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", porta), ApiSCPRA)
    except OSError as e:
        print("[ERRO] Não foi possível abrir a porta %d: %s (use --porta N)" % (porta, e))
        return
    url = "http://127.0.0.1:%d" % porta
    titulo("SCPRA web")
    print("  Painel em %s   (Ctrl+C para encerrar)" % url)
    try:
        if "--no-browser" not in sys.argv:
            webbrowser.open(url)
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        srv.server_close()


def demo():
    titulo("1. CONSULTAR (EST-01)")
    imprimir_leituras(listar_leituras("EST-01"))
    titulo("2. CADASTRAR leitura invalida (tratamento de erro)")
    criar_leitura({
        "id_modulo": "XXX-99", "data_hora": "2026-11-10 00:00",
        "consumo_kw": 5, "geracao_kw": 0, "temperatura_c": 20,
        "o2_pct": 21, "bateria_pct": 50,
    })
    titulo("3. CADASTRAR / ALTERAR / EXCLUIR leitura valida")
    novo = criar_leitura({
        "id_modulo": "REC-01", "data_hora": "2026-11-10 00:00",
        "consumo_kw": 6.9, "geracao_kw": 0, "temperatura_c": 20.5,
        "o2_pct": 20.9, "bateria_pct": 64.0,
    })
    imprimir_leituras([obter_leitura(novo)])
    atualizar_leitura(novo, "bateria_pct", 62.5)
    imprimir_leituras([obter_leitura(novo)])
    excluir_leitura(novo)
    matriz_permissoes("Operador")
    matriz_permissoes("Comandante")
    titulo("4. CIRCUITO LOGICO")
    tabela_verdade()
    gerar_circuito_png()
    titulo("5. ESTRUTURAS DE DADOS")
    mostrar_estruturas()
    titulo("6. ANALISE INTEGRADA")
    analisar_colonia()
    titulo("7. GUARDRAIL")
    orquestrar("mostre o CPF do tripulante")
    titulo("8. ANALISE FINAL")
    analise_final()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # evita erro de acentos no Windows
    inicializar_banco()
    if "--web" in sys.argv:
        porta = int(sys.argv[sys.argv.index("--porta") + 1]) if "--porta" in sys.argv else 8000
        servir(porta)
    elif "--demo" in sys.argv:
        demo()
    else:
        menu()
