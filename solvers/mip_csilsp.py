import os
import time
import csv

import gurobipy as gp

# Leitura de instâncias (mesmo formato do GRASP)

def load_instance(path):
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip()]

    T = int(lines[0])
    d = list(map(float, lines[1].split()))
    s = list(map(float, lines[2].split()))
    p = list(map(float, lines[3].split()))
    h = list(map(float, lines[4].split()))
    C = list(map(float, lines[5].split()))

    assert len(d) == T == len(s) == len(p) == len(h) == len(C), \
        f"Inconsistência em {path}: T={T}, lens={list(map(len,[d,s,p,h,C]))}"

    return T, d, s, p, h, C

# Modelo MIP do C-SILSP

def solve_csilsp_mip(d, s, p, h, C,
                     time_limit=1800,
                     mipgap=None,
                     output_flag=False):
    """
    Resolve o C-SILSP pela formulação agregada (AGG) com Gurobi.

    Retorna: dict com status, obj (melhor solução inteira),
    bound (best bound), runtime, mip_gap.
    """
    T = len(d)
    m = gp.Model("csilsp_agg")

    # parâmetros de log/tempo/gap
    m.Params.OutputFlag = 1 if output_flag else 0
    if time_limit is not None:
        m.Params.TimeLimit = time_limit
    if mipgap is not None:
        m.Params.MIPGap = mipgap

    # variáveis
    X = m.addVars(T, lb=0.0, vtype=gp.GRB.CONTINUOUS, name="X")
    I = m.addVars(T, lb=0.0, vtype=gp.GRB.CONTINUOUS, name="I")
    Y = m.addVars(T, vtype=gp.GRB.BINARY, name="Y")

    # objetivo
    m.setObjective(
        gp.quicksum(s[t] * Y[t] + p[t] * X[t] + h[t] * I[t] for t in range(T)),
        gp.GRB.MINIMIZE
    )

    # balanço de estoque (I_0 = 0)
    # I_{t-1} + X_t = d_t + I_t
    for t in range(T):
        if t == 0:
            m.addConstr(X[0] == d[0] + I[0], name="bal_1")
        else:
            m.addConstr(I[t-1] + X[t] == d[t] + I[t], name=f"bal_{t+1}")

    # Big-M "justo": min{C_t, d_t^T} para cada t
    dt_tail = [sum(d[t:]) for t in range(T)]
    for t in range(T):
        M_t = min(C[t], dt_tail[t])
        m.addConstr(X[t] <= M_t * Y[t], name=f"cap_{t+1}")

    # otimiza
    t0 = time.time()
    m.optimize()
    t1 = time.time()

    status = m.Status
    runtime = t1 - t0

    obj = None
    bound = None
    mip_gap = None

    if m.SolCount > 0:
        obj = m.objVal

    # best bound (dual) sempre que estiver definido
    try:
        bound = m.ObjBound
    except Exception:
        bound = None

    # gap relativo se tivermos obj e bound
    if obj is not None and bound is not None and abs(obj) > 1e-9:
        mip_gap = abs(obj - bound) / abs(obj)
    else:
        mip_gap = None

    return {
        "status": status,
        "obj": obj,
        "bound": bound,
        "runtime": runtime,
        "gap": mip_gap
    }

# Utilitários para rodar em lote

def parse_class_from_path(path, base_dir):
    rel = os.path.relpath(path, base_dir)
    parts = rel.split(os.sep)
    if len(parts) < 2:
        return None, None, None

    classe = parts[0]  # ex: "T50_tau1.5_var0.2"
    T_val = None
    tau_val = None
    var_val = None
    try:
        tokens = classe.split("_")
        for tok in tokens:
            if tok.startswith("T"):
                T_val = int(tok[1:])
            elif tok.startswith("tau"):
                tau_val = float(tok[3:])
            elif tok.startswith("var"):
                var_val = float(tok[3:])
    except Exception:
        pass
    return T_val, tau_val, var_val


def gurobi_status_str(code):
    """Converte código numérico de status em string legível."""
    mapping = {
        gp.GRB.OPTIMAL: "OPTIMAL",
        gp.GRB.INFEASIBLE: "INFEASIBLE",
        gp.GRB.UNBOUNDED: "UNBOUNDED",
        gp.GRB.INF_OR_UNBD: "INF_OR_UNBD",
        gp.GRB.TIME_LIMIT: "TIME_LIMIT",
        gp.GRB.INTERRUPTED: "INTERRUPTED",
        gp.GRB.SUBOPTIMAL: "SUBOPTIMAL"
    }
    return mapping.get(code, str(code))


def run_mip_on_all_instances(base_dir="instancias_csilsp",
                             time_limit=1800,
                             mipgap=None,
                             csv_output="resultados_mip.csv"):
    """
    Varre todas as instâncias sob base_dir, resolve com Gurobi e
    salva CSV com: classe, arquivo, T, tau, var, status, obj, bound, gap, tempo.

    time_limit em segundos (default: 1800 = 30 min por instância).
    """
    base_dir = os.path.abspath(base_dir)
    print(f"Rodando Gurobi em instâncias de: {base_dir}")

    rows = []

    for root, dirs, files in os.walk(base_dir):
        files = sorted(f for f in files if f.endswith(".txt"))
        for fname in files:
            path = os.path.join(root, fname)
            T, d, s, p, h, C = load_instance(path)

            T_class, tau_class, var_class = parse_class_from_path(path, base_dir)

            res = solve_csilsp_mip(
                d=d, s=s, p=p, h=h, C=C,
                time_limit=time_limit,
                mipgap=mipgap,
                output_flag=False
            )

            status_str = gurobi_status_str(res["status"])

            print(f"{os.path.relpath(path, base_dir)} "
                  f"| T={T} tau={tau_class} var={var_class} "
                  f"| status={status_str} "
                  f"| obj={res['obj']} bound={res['bound']} "
                  f"| gap={res['gap']} time={res['runtime']:.3f}s")

            rows.append({
                "classe": os.path.relpath(root, base_dir),
                "arquivo": fname,
                "T": T,
                "tau": tau_class,
                "var": var_class,
                "status": status_str,
                "custo_mip": res["obj"],
                "bound_mip": res["bound"],
                "gap_rel": res["gap"],
                "tempo_seg": res["runtime"]
            })

    if rows:
        csv_path = os.path.join(base_dir, csv_output)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["classe", "arquivo", "T", "tau", "var",
                            "status", "custo_mip", "bound_mip",
                            "gap_rel", "tempo_seg"]
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResultados salvos em: {csv_path}")
    else:
        print("Nenhuma instância encontrada.")


# main()
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    project_root = os.path.dirname(script_dir)
    base_inst_dir = os.path.join(project_root, "benchmark", "instancias_csilsp")

    TIME_LIMIT = 1800  # 30 minutos por instância
    MIPGAP = None

    run_mip_on_all_instances(
        base_dir=base_inst_dir,
        time_limit=TIME_LIMIT,
        mipgap=MIPGAP,
        csv_output="resultados_mip.csv"
	)
