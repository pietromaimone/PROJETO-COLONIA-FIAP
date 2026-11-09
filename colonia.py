# MGPEB - MISSÃO AURORA SIGER
# SISTEMA INTEGRADO DA COLÔNIA
#
# Continuação do mgpeb.py (pouso dos 18 módulos). Os módulos já pousaram e
# formam a colônia. Este programa lê a base de dados da colônia nos arquivos:
#   dados_colonia.md     -> 31 dias de energia, consumo (total e por sistema), vento e sol
#   modulos_colonia.md  -> os 5 sistemas, suas prioridades e fontes de energia
#   (como os valores são calculados: calculo_consumo_geracao.md)
#
# E junta o que foi trabalhado na fase:
#   1. Organização dos dados (listas, chave-valor e hierarquia)
#   2. Regras de decisão (lógica booleana, igual à do pouso)
#   3. Previsão com regressão linear (vento -> energia eólica)
#   4. Análise do uso de energia (produção x consumo x armazenamento)
#
# Usa só a biblioteca padrão do Python (os .md ficam na mesma pasta):
#   python colonia.py

import os


# CONSTANTES DO SISTEMA (mesmo estilo do mgpeb.py)

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_DADOS = os.path.join(PASTA, "dados_colonia.md")
ARQ_SISTEMAS = os.path.join(PASTA, "modulos_colonia.md")

CAPACIDADE = 600  # kWh da bateria
ENERGIA_MIN = 50  # % mínimo de armazenamento para operar sem alerta
ENERGIA_CRITICA = 20  # % de armazenamento considerado crítico
CONSUMO_ALTO = 750  # kWh/dia a partir do qual o consumo é considerado alto
VENTO_TEMPESTADE = 25  # acima disso é tempestade severa (m/s), igual ao pouso

# Na tabela modulos_colonia.md, energia = 1 e laboratório = 5.
# True  -> prioridade 1 é a mais importante (energia é a última a ser cortada)
# False -> prioridade 5 é a mais importante (como nos módulos do mgpeb.py)
MENOR_NUMERO_MAIS_IMPORTANTE = True

VITAIS = ("Suporte médico", "Habitação")  # nunca podem ser desligados
SISTEMA_ENERGIA = "Energia"  # também nunca é desligado


# LEITURA DOS ARQUIVOS .md (tabelas)


def ler_tabela(caminho):
    """Lê a tabela de um .md e devolve uma lista de linhas (cada uma é uma
    lista de textos). Ignora o cabeçalho e a linha de separação.
    """
    linhas = []

    with open(caminho, encoding="utf-8") as arquivo:
        for texto in arquivo:
            texto = texto.strip()

            if not texto.startswith("|"):
                continue

            celulas = [c.strip() for c in texto.strip("|").split("|")]
            linhas.append(celulas)

    # linhas[0] = cabeçalho, linhas[1] = separador (---)
    return linhas[2:]


def carregar_dados():
    """Transforma a tabela de 31 dias em uma lista de dicionários."""
    dias = []

    for c in ler_tabela(ARQ_DADOS):
        dias.append(
            {
                "dia": int(c[0]),
                "energia_total": float(c[1]),
                "consumo_total": float(c[2]),
                "producao_total": float(c[3]),
                "producao_solar": float(c[4]),
                "producao_eolica": float(c[5]),
                "consumo_vida": float(c[6]),
                "vento": float(c[7]),
                "tempo_sol": float(c[8]),
                "armazenamento": float(c[9]),
                # consumo de cada sistema no dia (ver calculo_consumo_geracao.md)
                "consumo_sistemas": {
                    "Energia": float(c[10]),
                    "Habitação": float(c[11]),
                    "Suporte médico": float(c[12]),
                    "Logística": float(c[13]),
                    "Laboratório": float(c[14]),
                },
                "potencia_eolica": float(c[15]),
            }
        )

    return dias


def carregar_sistemas():
    """Transforma a tabela dos sistemas em um dicionário (chave = nome)."""
    sistemas = {}

    for c in ler_tabela(ARQ_SISTEMAS):
        sistemas[c[0]] = {
            "prioridade": int(c[1]),
            "solar": c[2].upper() == "OK",
            "eolico": c[3].upper() == "OK",
            "suporte_vida": c[4].upper() == "OK",
            "armazenamento": c[5].upper() == "OK",
        }

    return sistemas


# 1. ORGANIZAÇÃO DOS DADOS
#
# A colônia é uma hierarquia de dicionários (chave-valor dentro de chave-valor).
# Os dias ficam em uma lista; os sistemas, em um dicionário.

dias = carregar_dados()
sistemas = carregar_sistemas()

colonia = {
    "energia": {
        "solar": {"producao": 0.0},
        "eolico": {"producao": 0.0},
        "armazenamento": {"nivel": 0.0, "capacidade": CAPACIDADE},
    },
    "suporte_vida": {"consumo": 0.0},
    "clima": {"vento": 0.0, "tempo_sol": 0.0},
    "sistemas": sistemas,
}

# Pilha com o registro dos eventos (igual ao historico do mgpeb.py)
historico = []


def carregar_dia(d):
    """Coloca os dados de um dia na hierarquia da colônia."""
    colonia["energia"]["solar"]["producao"] = d["producao_solar"]
    colonia["energia"]["eolico"]["producao"] = d["producao_eolica"]
    colonia["energia"]["armazenamento"]["nivel"] = d["armazenamento"]
    colonia["suporte_vida"]["consumo"] = d["consumo_vida"]
    colonia["clima"]["vento"] = d["vento"]
    colonia["clima"]["tempo_sol"] = d["tempo_sol"]

    for nome in d["consumo_sistemas"]:
        sistemas[nome]["consumo"] = d["consumo_sistemas"][nome]


def navegar(caminho):
    """Acessa um subsistema pelo caminho. Ex.: 'energia/solar/producao'."""
    no = colonia

    for parte in caminho.split("/"):
        no = no[parte]

    return no


def mostrar_arvore(no, nivel):
    """Percorre a hierarquia e imprime cada subsistema com recuo."""
    for chave in no:
        valor = no[chave]

        if isinstance(valor, dict):
            print("  " * nivel + "- " + chave)
            mostrar_arvore(valor, nivel + 1)
        else:
            print("  " * nivel + "- %s: %s" % (chave, valor))


# ORDENAÇÃO: INSERTION SORT (o mesmo do mgpeb.py)


def criterio_corte(nome):
    """Quem é menos importante vem primeiro (será desligado primeiro)."""
    p = sistemas[nome]["prioridade"]

    if MENOR_NUMERO_MAIS_IMPORTANTE:
        return -p

    return p


def ordenar(lista, criterio):
    """Ordena a lista utilizando o algoritmo insertion sort."""
    for i in range(1, len(lista)):
        atual = lista[i]
        j = i - 1

        while j >= 0 and criterio(lista[j]) > criterio(atual):
            lista[j + 1] = lista[j]
            j = j - 1

        lista[j + 1] = atual


def ordem_de_corte():
    """Lista (estrutura linear) dos sistemas que podem ser desligados,
    do menos para o mais importante. Vitais e energia ficam de fora.
    """
    cortaveis = []

    for nome in sistemas:
        if nome not in VITAIS and nome != SISTEMA_ENERGIA:
            cortaveis.append(nome)

    ordenar(cortaveis, criterio_corte)

    return cortaveis


def sem_fonte(nome):
    """Sistema sem solar, sem eólica e sem armazenamento não tem de onde
    receber energia (como os sensores em falha do pouso).
    """
    s = sistemas[nome]
    return not (s["solar"] or s["eolico"] or s["armazenamento"])


def suporte_vida_ok():
    """V: o suporte de vida de habitação e do médico está funcionando."""
    for nome in VITAIS:
        if not sistemas[nome]["suporte_vida"]:
            return False

    return True


# 2. REGRAS DE DECISÃO (lógica booleana, como no pouso)
#
# Variáveis, calculadas a cada dia:
#   V  = suporte de vida ok
#   E  = energia baixa        (armazenamento < ENERGIA_MIN %)
#   X  = energia crítica      (armazenamento < ENERGIA_CRITICA %)
#   K  = consumo alto         (consumo > CONSUMO_ALTO)
#   T  = tempestade severa    (vento > VENTO_TEMPESTADE)
#
# Em ordem de prioridade (a primeira regra verdadeira vence):
#   CRITICO     = ¬V
#   EMERGENCIA  = V · X · K
#   ECONOMIA    = V · E · K · ¬X
#   REDUZIR     = V · E · ¬K
#   PROTEGER    = V · ¬E · T


def critico(V):
    return bool(not V)


def emergencia(V, X, K):
    return bool(V and X and K)


def economia(V, E, K, X):
    return bool(V and E and K and (not X))


def reduzir(V, E, K):
    return bool(V and E and (not K))


def proteger(V, E, T):
    return bool(V and (not E) and T)


def decidir(energia, consumo, vida=True, vento=0):
    """Transforma os dados em UMA decisão clara.
    energia = armazenamento em %, consumo em kWh/dia.
    Retorna (mensagem, ação).
    """
    V = vida
    E = energia < ENERGIA_MIN
    X = energia < ENERGIA_CRITICA
    K = consumo > CONSUMO_ALTO
    T = vento > VENTO_TEMPESTADE

    if critico(V):
        return "CRÍTICO: religar suporte de vida", "critico"

    if emergencia(V, X, K):
        return "EMERGÊNCIA: desligar sistemas não essenciais", "emergencia"

    if economia(V, E, K, X):
        return "ALERTA: ativar modo economia", "economia"

    if reduzir(V, E, K):
        return "ALERTA: reduzir consumo", "reduzir"

    if proteger(V, E, T):
        return "ATENÇÃO: tempestade, proteger equipamentos externos", "proteger"

    return "OK: operação normal", "normal"


def aplicar(acao):
    """Devolve a lista de sistemas desligados pela ação.
    Suporte médico, habitação e energia nunca entram nessa lista.
    """
    cortaveis = ordem_de_corte()

    if acao == "emergencia":
        return cortaveis  # todos os não essenciais

    if acao == "economia":
        return cortaveis[:1]  # só o menos importante

    return []


def economia_kwh(desligados):
    """Quanto se economiza: soma o consumo do dia dos sistemas desligados."""
    total = 0

    for nome in desligados:
        total = total + sistemas[nome]["consumo"]

    return total


# 3. PREVISÃO: REGRESSÃO LINEAR SIMPLES (y = a·x + b)


def media(valores):
    soma = 0

    for v in valores:
        soma = soma + v

    return soma / len(valores)


def regressao_linear(x, y):
    """Ajusta a reta pelo método dos mínimos quadrados.
    Retorna (a, b, r2). O r2 mostra o quanto a reta explica os dados (1 = perfeito).
    """
    mx = media(x)
    my = media(y)

    cima = 0
    baixo = 0
    total = 0

    for i in range(len(x)):
        cima = cima + (x[i] - mx) * (y[i] - my)
        baixo = baixo + (x[i] - mx) ** 2
        total = total + (y[i] - my) ** 2

    a = cima / baixo
    b = my - a * mx

    erro = 0

    for i in range(len(x)):
        erro = erro + (y[i] - (a * x[i] + b)) ** 2

    r2 = 1 - erro / total

    return a, b, r2


def prever(a, b, x):
    """Usa a reta ajustada para estimar um valor."""
    return a * x + b


# Listas de treino. A turbina tem um teto (720 kWh/dia), então a reta só é
# ajustada nos dias em que a turbina NÃO estava no limite nem desligada.
teto_eolica = max(d["producao_eolica"] for d in dias)

vento_treino = []
eolica_treino = []

for d in dias:
    if d["vento"] <= VENTO_TEMPESTADE and d["producao_eolica"] < teto_eolica:
        vento_treino.append(d["vento"])
        eolica_treino.append(d["producao_eolica"])

sol_treino = [d["tempo_sol"] for d in dias]
solar_treino = [d["producao_solar"] for d in dias]

a_eol, b_eol, r2_eol = regressao_linear(vento_treino, eolica_treino)
a_sol, b_sol, r2_sol = regressao_linear(sol_treino, solar_treino)


def energia_eolica(vento):
    """Energia eólica prevista (kWh/dia) para um vento (m/s).
    Tempestade desliga as turbinas; o equipamento tem um limite máximo.
    """
    if vento > VENTO_TEMPESTADE:
        return 0.0

    return max(0.0, min(prever(a_eol, b_eol, vento), teto_eolica))


def energia_solar(horas_sol):
    """Energia solar prevista (kWh/dia) para as horas de sol."""
    return max(0.0, prever(a_sol, b_sol, horas_sol))


# 4. ANÁLISE DO USO DE ENERGIA


def analisar_energia(geracao, consumo, reserva=None):
    """Compara geração, consumo e reserva e gera uma ação simples."""
    if consumo > geracao:
        msg = "ALERTA: consumo maior que geração"

        if reserva is not None and reserva > 0:
            msg = msg + " (cobrindo com o armazenamento)"

        return msg

    if geracao > consumo:
        return "SUGESTÃO: armazenar energia excedente"

    return "OK: geração igual ao consumo"


def nomes(lista):
    return ", ".join(lista) if lista else "nenhum"


# PROGRAMA PRINCIPAL

print("=== 1. ORGANIZAÇÃO DOS DADOS ===")
print("Arquivos lidos: %d dias de dados e %d sistemas" % (len(dias), len(sistemas)))

carregar_dia(dias[0])
print("\nHierarquia da colônia (dia 1):")
mostrar_arvore(colonia, 0)

print("\nNavegando: energia/solar/producao =", navegar("energia/solar/producao"))
print("Navegando: clima/vento =", navegar("clima/vento"))
print("Navegando: sistemas/Laboratório/prioridade =", navegar("sistemas/Laboratório/prioridade"))

print("\nSistemas (prioridade, fontes de energia):")

for nome in sistemas:
    s = sistemas[nome]
    fontes = []

    if s["solar"]:
        fontes.append("solar")
    if s["eolico"]:
        fontes.append("eólica")
    if s["armazenamento"]:
        fontes.append("armazenamento")

    linha = "  %-15s prioridade %d | consumo dia 1: %3d kWh | fontes: %s" % (
        nome,
        s["prioridade"],
        s["consumo"],
        nomes(fontes),
    )

    if sem_fonte(nome):
        linha = linha + "  <- ALERTA: sem fonte de energia"

    print(linha)

print("\nSuporte de vida ok (V):", suporte_vida_ok())
print("Ordem de corte (menos importante primeiro):", ordem_de_corte())


print("\n=== 2. REGRAS DE DECISÃO ===")

testes = [
    # (armazenamento %, consumo kWh, suporte de vida, vento)
    (40, 800, True, 10),
    (40, 600, True, 10),
    (15, 800, True, 10),
    (80, 600, True, 10),
    (80, 600, True, 28),
    (60, 600, False, 10),
]

for energia, consumo, vida, vento in testes:
    msg, acao = decidir(energia, consumo, vida, vento)
    print(
        "armazenamento=%d%%, consumo=%d, vida=%s, vento=%d -> %s"
        % (energia, consumo, vida, vento, msg)
    )


print("\n=== 3. PREVISÃO POR REGRESSÃO ===")

print("Vento -> energia eólica (%d dias de treino)" % len(vento_treino))
print("Reta: eólica = %.2f * vento %+.2f  (r2 = %.3f)" % (a_eol, b_eol, r2_eol))

for v in (8, 11, 14, 28):
    print("Entrada: vento = %d -> previsão de energia eólica ≈ %.0f kWh" % (v, energia_eolica(v)))

print("\nTempo de sol -> energia solar (%d dias de treino)" % len(sol_treino))
print("Reta: solar = %.2f * horas %+.2f  (r2 = %.3f)" % (a_sol, b_sol, r2_sol))

for h in (6, 10, 12):
    print("Entrada: sol = %d h -> previsão de energia solar ≈ %.0f kWh" % (h, energia_solar(h)))

erro = 0

for d in dias:
    previsto = energia_eolica(d["vento"]) + energia_solar(d["tempo_sol"])
    erro = erro + abs(previsto - d["producao_total"])

print("\nErro médio da previsão de produção total nos 31 dias: %.1f kWh" % (erro / len(dias)))


print("\n=== 4. ANÁLISE DO USO DE ENERGIA ===")

for geracao, consumo in ((40, 70), (80, 30), (50, 50)):
    print(
        "geração=%d, consumo=%d -> %s"
        % (geracao, consumo, analisar_energia(geracao, consumo))
    )


print("\n=== 5. SISTEMA INTEGRADO: 31 DIAS ===")
print("Cada dia: dados -> análise -> decisão -> corte (se houver)\n")

contagem = {}
total_prod = 0
total_cons = 0
total_economia = 0
dias_deficit = 0
dias_excesso = 0
pior = dias[0]

for d in dias:

    carregar_dia(d)

    solar = navegar("energia/solar/producao")
    eolica = navegar("energia/eolico/producao")
    nivel = navegar("energia/armazenamento/nivel")
    vento = navegar("clima/vento")

    geracao = solar + eolica
    consumo = d["consumo_total"]
    percentual = nivel / CAPACIDADE * 100

    analise = analisar_energia(geracao, consumo, nivel)
    msg, acao = decidir(percentual, consumo, suporte_vida_ok(), vento)
    desligados = aplicar(acao)
    economizado = economia_kwh(desligados)

    print(
        "Dia %2d | vento %4.1f m/s | sol %4.1f h | prod %4d kWh | cons %4d kWh | armaz %3d kWh (%3d%%)"
        % (d["dia"], vento, d["tempo_sol"], geracao, consumo, nivel, percentual)
    )
    print("        %s" % analise)
    print("        %s" % msg)

    if len(desligados) > 0:
        print("        Desligados: %s (economiza ≈ %d kWh)" % (nomes(desligados), economizado))

    historico.append("Dia %d: %s" % (d["dia"], acao))

    contagem[acao] = contagem.get(acao, 0) + 1
    total_prod = total_prod + geracao
    total_cons = total_cons + consumo
    total_economia = total_economia + economizado

    if consumo > geracao:
        dias_deficit = dias_deficit + 1
    else:
        dias_excesso = dias_excesso + 1

    if nivel < pior["armazenamento"]:
        pior = d


print("\n=== RESULTADO FINAL ===")

print("Produção total no mês: %d kWh" % total_prod)
print("Consumo total no mês : %d kWh" % total_cons)
print("Dias com consumo maior que a produção: %d" % dias_deficit)
print("Dias com produção maior que o consumo: %d" % dias_excesso)
print("Menor armazenamento: %d kWh (dia %d)" % (pior["armazenamento"], pior["dia"]))
print("Economia estimada com os cortes: %d kWh" % total_economia)

print("\nDecisões tomadas:")

for acao in contagem:
    print("  %-11s %d dia(s)" % (acao, contagem[acao]))

print("\nÚltimos 3 eventos da pilha (do mais recente para o mais antigo):")

for _ in range(min(3, len(historico))):
    print("  ", historico.pop())
