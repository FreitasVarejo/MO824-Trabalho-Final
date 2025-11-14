# Solvers C-SILSP

Este diretório contém os scripts para resolver as instâncias do problema C-SILSP (Capacitated Single-Item Lot Sizing Problem).

## Scripts

* `mip_csilsp.py`: Um solver exato baseado em Programação Inteira Mista (MIP).
* `grasp_csilsp.py`: Um solver heurístico baseado na meta-heurística GRASP (Greedy Randomized Adaptive Search Procedure).

## Execução

Os scripts são projetados para serem executados **a partir do diretório raiz** do projeto (a pasta `MO824-Trabalho-Final`).

Eles irão automaticamente:
1.  Buscar os arquivos de instância em `benchmark/instancias_csilsp/`.
2.  Resolver todas as instâncias encontradas.
3.  Salvar os resultados consolidados em um arquivo CSV (ex: `resultados_mip.csv`) dentro da própria pasta `benchmark/instancias_csilsp/`.

### Para rodar o solver MIP (Exato)

```bash
python solvers/mip_csilsp.py
````

### Para rodar o solver GRASP (Heurística)

```bash
python solvers/grasp_csilsp.py
```

## Dependências

  * `gurobipy` (necessário apenas para `mip_csilsp.py`).
