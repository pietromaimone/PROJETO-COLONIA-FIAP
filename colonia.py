
import os

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_DADOS = os.path.join(PASTA, "dados_colonia.md")
ARQ_SISTEMAS = os.path.join(PASTA, "modulos_colonia.md")

CAPACIDADE = 600  # kWh da bateria
ENERGIA_MIN = 50  # % mínimo de armazenamento para operar sem alerta
ENERGIA_CRITICA = 20  # % de armazenamento considerado crítico
CONSUMO_ALTO = 750  # kWh/dia a partir do qual o consumo é considerado alto
VENTO_TEMPESTADE = 25  # acima disso é tempestade severa (m/s), igual ao pouso

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

# Pilha 
historico = []


def carregar_dia(d):
   
    colonia["energia"]["solar"]["producao"] = d["producao_solar"]
    colonia["energia"]["eolico"]["producao"] = d["producao_eolica"]
    colonia["energia"]["armazenamento"]["nivel"] = d["armazenamento"]
    colonia["suporte_vida"]["consumo"] = d["consumo_vida"]
    colonia["clima"]["vento"] = d["vento"]
    colonia["clima"]["tempo_sol"] = d["tempo_sol"]

    for nome in d["consumo_sistemas"]:
        sistemas[nome]["consumo"] = d["consumo_sistemas"][nome]


def navegar(caminho):
    
    no = colonia

    for parte in caminho.split("/"):
        no = no[parte]

    return no


def mostrar_arvore(no, nivel):

    for chave in no:
        valor = no[chave]

        if isinstance(valor, dict):
            print("  " * nivel + "- " + chave)
            mostrar_arvore(valor, nivel + 1)
        else:
            print("  " * nivel + "- %s: %s" % (chave, valor))


# ORDENAÇÃO: INSERTION SORT

def criterio_corte(nome):
   
    p = sistemas[nome]["prioridade"]

    if MENOR_NUMERO_MAIS_IMPORTANTE:
        return -p

    return p


def ordenar(lista, criterio):
    
    for i in range(1, len(lista)):
        atual = lista[i]
        j = i - 1

        while j >= 0 and criterio(lista[j]) > criterio(atual):
            lista[j + 1] = lista[j]
            j = j - 1

        lista[j + 1] = atual


def ordem_de_corte():
 
    cortaveis = []

    for nome in sistemas:
        if nome not in VITAIS and nome != SISTEMA_ENERGIA:
            cortaveis.append(nome)

    ordenar(cortaveis, criterio_corte)

    return cortaveis


def sem_fonte(nome):
  
    s = sistemas[nome]
    return not (s["solar"] or s["eolico"] or s["armazenamento"])


def suporte_vida_ok():

    for nome in VITAIS:
        if not sistemas[nome]["suporte_vida"]:
            return False

    return True


# 2. REGRAS DE DECISÃO

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
        return cortaveis  
        
    if acao == "economia":
        return cortaveis[:1]  

    return []


def economia_kwh(desligados):
   
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
   
    return a * x + b



vento_medido = [6, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 7, 8, 9, 10, 6]
eolica_medida = [348, 433, 465, 496, 551, 528, 612, 585, 648, 677, 705, 410, 489, 560, 606, 372]


sol_medido = [8, 8, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 9, 10, 11, 8]
solar_medida = [112, 101, 124, 117, 138, 129, 141, 151, 140, 153, 156, 164, 126, 127, 149, 110]

teto_eolica = max(d["producao_eolica"] for d in dias)  

a_eol, b_eol, r2_eol = regressao_linear(vento_medido, eolica_medida)
a_sol, b_sol, r2_sol = regressao_linear(sol_medido, solar_medida)


def energia_eolica(vento):
  
    if vento > VENTO_TEMPESTADE:
        return 0.0

    return max(0.0, min(prever(a_eol, b_eol, vento), teto_eolica))


def energia_solar(horas_sol):
    
    return max(0.0, prever(a_sol, b_sol, horas_sol))


# 4. ANÁLISE DO USO DE ENERGIA


def analisar_energia(geracao, consumo, reserva=None):
 
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


# MODO INTERATIVO

def modo_interativo():

    print("\n=== MODO INTERATIVO ===")
    print("Digite os dados de um dia e veja a decisão. Enter vazio para sair.\n")

    while True:
        txt = input("Armazenamento em % (0 a 100): ").strip().replace(",", ".")

        if txt == "":
            print("Saindo do modo interativo.")
            break

        try:
            arm = float(txt)
            consumo = float(input("Consumo total (kWh): ").replace(",", "."))
            vento = float(input("Vento (m/s): ").replace(",", "."))
        except ValueError:
            print("  Valor inválido, tente de novo.\n")
            continue

        msg, acao = decidir(arm, consumo, True, vento)
        print("  Decisão:", msg)

        desligados = aplicar(acao)
        if desligados:
            print("  Desligar:", nomes(desligados))

        print()


# PROGRAMA MAIN

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

print("Vento -> energia eólica (%d medições reais)" % len(vento_medido))
print("Reta: eólica = %.2f * vento %+.2f  (r2 = %.3f)" % (a_eol, b_eol, r2_eol))

for v in (8, 11, 14, 28):
    print("Entrada: vento = %d -> previsão de energia eólica ≈ %.0f kWh" % (v, energia_eolica(v)))

print("\nTempo de sol -> energia solar (%d medições reais)" % len(sol_medido))
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



print("\n=== CONCLUSÃO ===")

dias_de_corte = contagem.get("emergencia", 0) + contagem.get("economia", 0) + contagem.get("reduzir", 0)

print(
    "Nos %d dias, a colônia operou normal em %d e precisou agir em %d."
    % (len(dias), contagem.get("normal", 0), dias_de_corte)
)
print(
    "O consumo (%d kWh) ficou perto da geração (%d kWh) no mês, então a colônia"
    % (total_cons, total_prod)
)
print("vive no limite: depende da bateria para atravessar os dias ruins.")
print(
    "O pior momento foi o dia %d, quando a bateria zerou (%d kWh) por causa da"
    % (pior["dia"], pior["armazenamento"])
)
print(
    "tempestade, e o sistema entrou em emergência (%d dia(s)) cortando Logística"
    % contagem.get("emergencia", 0)
)
print("e Laboratório para proteger o suporte à vida, que nunca foi desligado.")
print(
    "Conclusão: o sistema de decisão deu conta, mas a margem é pequena — mais"
)
print("painéis ou uma bateria maior deixariam a colônia mais segura.")


# acessa o modo interativo:  python colonia.py -i
import sys

if "-i" in sys.argv or "--interativo" in sys.argv:
    modo_interativo()
