# Projeto Colônia — Missão Aurora Siger (FIAP)

Sistema integrado que simula o funcionamento inteligente de uma colônia em Marte. Continuação do projeto de pouso (MGPEB): os módulos já pousaram e agora formam a colônia, que precisa se organizar, gerar energia e tomar decisões sozinha.

Atividade integrativa da FIAP.

## O que o sistema faz

1. **Organiza os dados** da colônia em listas e estruturas hierárquicas (energia → solar / eólico / armazenamento).
2. **Toma decisões automáticas** com regras de lógica (ex.: se a energia está baixa e o consumo alto, ativa o modo economia).
3. **Prevê a geração de energia** usando regressão linear (vento → energia eólica).
4. **Analisa o uso de energia**, comparando geração, consumo e armazenamento.

## Arquivos do repositório

| Arquivo | O que é |
|---|---|
| `colonia.py` | O programa principal. Lê os dois `.md` e roda os 31 dias. |
| `dados_colonia.md` | Tabela com os 31 dias: energia, consumo, geração, vento e sol. |
| `modulos_colonia.md` | Os 5 sistemas da colônia, com prioridade e fontes de energia. |
| `calculo_consumo_geracao.md` | Explica, passo a passo, como cada número é calculado. |
| `assets/` | Imagens usadas na documentação (o gráfico da parábola). |

## Como rodar

Precisa só do Python 3 (nenhuma biblioteca extra).

```bash
git clone https://github.com/pietromaimone/PROJETO-COLONIA-FIAP.git
cd PROJETO-COLONIA-FIAP
python colonia.py
```

> No Linux e no macOS, use `python3` se o `python` não funcionar.

O `colonia.py` lê os arquivos `dados_colonia.md` e `modulos_colonia.md`, que precisam estar na mesma pasta.

## O que aparece na tela

- A hierarquia da colônia e a navegação entre os subsistemas.
- As regras de decisão testadas em alguns casos.
- As retas da regressão (vento → eólica e sol → solar).
- Os 31 dias, um por um, com a análise e a decisão de cada dia.
- Um resumo final: produção e consumo do mês, dias com falta de energia e as decisões tomadas.
