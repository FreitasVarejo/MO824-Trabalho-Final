# Diretório de Benchmark (MO824 - C-SILSP)

Este diretório contém o gerador de instâncias (`gerador_instancias.py`) e as próprias instâncias (`instancias_csilsp/`) usadas para avaliar os _solvers_ (PLIM e GRASP) do projeto.

## 1. Estrutura dos Diretórios de Instâncias

As instâncias estão localizadas em `benchmark/instancias_csilsp/`. Elas são organizadas em subdiretórios com a seguinte nomenclatura:

`T<T>_tau<tau>_var<var>/`

Onde:

- **T**: Horizonte de planejamento (número de períodos). Ex: `T50`, `T100`.
- **tau**: Nível de "aperto" da capacidade. É a razão entre a capacidade média e a demanda média (`C_media / d_media`). Ex: `tau1.5` (capacidade restrita), `tau5.0` (capacidade frouxa).
- **var**: Coeficiente de variabilidade da demanda. Ex: `var0.2` (baixa variabilidade), `var0.8` (alta variabilidade).

Dentro de cada um desses diretórios, existem 10 arquivos de instância, nomeados de `inst_01.txt` a `inst_10.txt`.

## 2. Formato do Arquivo de Instância (`.txt`)

Cada arquivo de instância é um arquivo de texto simples contendo 6 linhas. Os valores em cada linha são separados por espaços.

O formato é o seguinte:

- **Linha 1:** `T` (Um único inteiro indicando o horizonte de planejamento).
- **Linha 2:** `d_1 d_2 ... d_T` (Valores inteiros das demandas para cada período `t`).
- **Linha 3:** `s_1 s_2 ... s_T` (Valores inteiros dos custos de setup (fixos) para cada período `t`).
- **Linha 4:** `p_1 p_2 ... p_T` (Valores inteiros dos custos unitários de produção para cada período `t`).
- **Linha 5:** `h_1 h_2 ... h_T` (Valores inteiros dos custos unitários de estoque para cada período `t`).
- **Linha 6:** `C_1 C_2 ... C_T` (Valores inteiros das capacidades de produção para cada período `t`).
