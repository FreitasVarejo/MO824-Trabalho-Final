import os
import math
import time
import random
import csv

BIGM = 1e15
PENALTY = 1e6


# ============================================================
# 1. Leitura de instâncias
# ============================================================

def load_instance(path):
    """
    Formato da instância (arquivo .txt):
    Linha 1: T
    Linha 2: d_1 ... d_T    (demanda)
    Linha 3: s_1 ... s_T    (custo de setup)
    Linha 4: p_1 ... p_T    (custo de produção)
    Linha 5: h_1 ... h_T    (custo de estoque)
    Linha 6: C_1 ... C_T    (capacidade)
    """
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


# ============================================================
# 2. Decoder: dado y -> X, I, custo
# ============================================================

def decode_solution(y, d, C, s, p, h,
                    bigM=BIGM,
                    penalty=PENALTY):
    """
    Dada uma configuração de setups y[t] (0/1), calcula:
    - X[t]: produção em cada período
    - I[t]: estoque ao final de cada período
    - custo total (setup + produção + estoque)

    Estratégia:
    - backward: acumula demanda R de trás pra frente;
      se y[t] = 1, produz min(C[t], R).
    - forward: calcula estoques via balanço.
    - se não conseguir atender toda a demanda ou faltar estoque,
      retorna custo penalizado.
    """
    T = len(d)
    X = [0.0] * T

    # Demanda restante
    R = 0.0
    for t in range(T - 1, -1, -1):
        R += d[t]
        if y[t] == 1:
            x_t = min(C[t], R)
            X[t] = x_t
            R -= x_t

    # Se sobrou demanda, inviável
    if R > 1e-6:
        return None, None, bigM + R * penalty

    # Balanço de estoque
    I = [0.0] * T
    inv = 0.0
    for t in range(T):
        inv = inv + X[t] - d[t]
        if inv < -1e-6:
            # falta de estoque em algum período
            return None, None, bigM + abs(inv) * penalty
        I[t] = inv

    # Cálculo do custo
    cost = 0.0
    for t in range(T):
        cost += s[t] * y[t] + p[t] * X[t] + h[t] * I[t]

    return X, I, cost


# ============================================================
# 3. Construção gulosa-aleatória (fase GRASP)
# ============================================================

def greedy_randomized_construction(d, C, s, p, h,
                                   alpha=0.3,
                                   L_max=10):
    """
    Constrói um vetor de setups y[t] escolhendo lotes (t..t+L-1)
    com base em custo médio aproximado e RCL, usando o parâmetro alpha.

    - alpha = 0 -> totalmente guloso
    - alpha = 1 -> totalmente aleatório dentro dos candidatos
    """
    T = len(d)
    y = [0] * T
    t = 0

    while t < T:
        candidates = []

        # Tenta lotes que cobrem de t até t+L-1
        for L in range(1, L_max + 1):
            end = t + L - 1
            if end >= T:
                break

            dem = sum(d[t:end+1])
            # CORREÇÃO: tudo é produzido em t na aproximação
            cap = C[t]
            if cap + 1e-6 < dem:
                # não há capacidade suficiente para produzir esse lote em t
                continue

            # custo aproximado: produz tudo em t
            setup_cost = s[t]
            prod_cost = sum(p[k] * d[k] for k in range(t, end + 1))

            # custo de estoque aproximado:
            # demanda futura é produzida em t e estocada até consumo
            hold_cost = 0.0
            cum = 0.0
            for k in range(t + 1, end + 1):
                cum += d[k]
                hold_cost += h[k] * cum

            avg_cost = (setup_cost + prod_cost + hold_cost) / (dem + 1e-9)
            candidates.append((L, avg_cost))

        if not candidates:
            # Se não há nenhum lote viável "grande", força setup em t
            y[t] = 1
            t += 1
            continue

        c_min = min(c for _, c in candidates)
        c_max = max(c for _, c in candidates)
        thresh = c_min + alpha * (c_max - c_min + 1e-9)

        # RCL: candidatos com custo <= limiar
        RCL = [L for L, c in candidates if c <= thresh]

        L_chosen = random.choice(RCL)
        y[t] = 1
        t = t + L_chosen

    return y


# ============================================================
# 4. Busca local
# ============================================================

def local_search(y, d, C, s, p, h,
                 time_limit=None,
                 start_time=None):
    """
    Hill-climbing com vizinhança de flip:
    - tenta inverter y[t] (0->1 ou 1->0),
    - aceita qualquer movimento que melhora,
    - até atingir ótimo local ou estourar o time_limit.
    """
    T = len(d)
    _, _, best_cost = decode_solution(y, d, C, s, p, h)
    improved = True

    if start_time is None:
        start_time = time.time()

    while improved:
        # checa limite de tempo
        if time_limit is not None and (time.time() - start_time) >= time_limit:
            break

        improved = False
        for t in range(T):
            # checa limite de tempo dentro do laço também
            if time_limit is not None and (time.time() - start_time) >= time_limit:
                break

            y[t] ^= 1  # flip 0<->1
            _, _, cost = decode_solution(y, d, C, s, p, h)
            if cost < best_cost:
                best_cost = cost
                improved = True
                break  # recomeça vizinhança
            else:
                y[t] ^= 1  # desfaz flip

    return y, best_cost


# ============================================================
# 5. Loop principal do GRASP
# ============================================================

def grasp(d, C, s, p, h,
          max_iter=200,
          alpha=0.3,
          L_max=10,
          seed=None,
          time_limit=None):
    """
    Executa o GRASP:
    - max_iter iterações (máximo)
    - cada iteração: construção gulosa-aleatória + busca local
    - se time_limit (segundos) for dado, respeita limite por instância
    - retorna melhor solução encontrada (y, X, I, custo)
    """
    if seed is not None:
        random.seed(seed)

    T = len(d)
    start_time = time.time()

    # solução trivial: setup em todos os períodos (fallback factível, se existir)
    y_trivial = [1] * T
    _, _, cost_trivial = decode_solution(y_trivial, d, C, s, p, h)
    best_y = y_trivial[:]
    best_cost = cost_trivial

    for it in range(max_iter):
        # checa limite de tempo
        if time_limit is not None and (time.time() - start_time) >= time_limit:
            break

        y = greedy_randomized_construction(d, C, s, p, h,
                                           alpha=alpha,
                                           L_max=min(L_max, T))

        # joga fora construções claramente infactíveis
        _, _, cost_init = decode_solution(y, d, C, s, p, h)
        if cost_init >= BIGM / 2:
            continue

        y, cost = local_search(y, d, C, s, p, h,
                               time_limit=time_limit,
                               start_time=start_time)

        if cost < best_cost:
            best_cost = cost
            best_y = y[:]

    X, I, _ = decode_solution(best_y, d, C, s, p, h)
    return best_y, X, I, best_cost


# ============================================================
# 6. Runner: aplicar GRASP em todas as instâncias
# ============================================================

def parse_class_from_path(path, base_dir):
    """
    Extrai T, tau, var a partir do caminho da instância.
    Exemplo de diretório:
      instancias_csilsp/T50_tau1.5_var0.2/inst_01.txt
    """
    rel = os.path.relpath(path, base_dir)
    parts = rel.split(os.sep)
    if len(parts) < 2:
        return None, None, None

    classe = parts[0]  # ex: "T50_tau1.5_var0.2"
    # T50_tau1.5_var0.2 -> T=50, tau=1.5, var=0.2
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


def run_grasp_on_all_instances(base_dir="instancias_csilsp",
                               max_iter=200,
                               alpha=0.3,
                               L_max=10,
                               seed=42,
                               time_limit=1800,
                               csv_output="resultados_grasp.csv"):
    """
    Varre todas as instâncias sob base_dir, aplica GRASP e
    salva um CSV com: classe, arquivo, T, tau, var, custo, tempo, flag de factibilidade.
    time_limit é em segundos (default: 1800 = 30 min por instância).
    """
    base_dir = os.path.abspath(base_dir)
    print(f"Rodando GRASP em instâncias de: {base_dir}")
    random.seed(seed)

    rows = []
    for root, dirs, files in os.walk(base_dir):
        files = sorted(f for f in files if f.endswith(".txt"))
        for fname in files:
            path = os.path.join(root, fname)
            T, d, s, p, h, C = load_instance(path)

            T_class, tau_class, var_class = parse_class_from_path(path, base_dir)

            t0 = time.time()
            y, X, I, cost = grasp(
                d=d, C=C, s=s, p=p, h=h,
                max_iter=max_iter,
                alpha=alpha,
                L_max=L_max,
                seed=random.randint(1, 10**9),
                time_limit=time_limit
            )
            t1 = time.time()
            elapsed = t1 - t0

            factivel = cost < BIGM / 2

            print(f"{os.path.relpath(path, base_dir)} "
                  f"| T={T} tau={tau_class} var={var_class} "
                  f"| cost={cost:.2f} factivel={factivel} time={elapsed:.3f}s")

            rows.append({
                "classe": os.path.relpath(root, base_dir),
                "arquivo": fname,
                "T": T,
                "tau": tau_class,
                "var": var_class,
                "custo_grasp": cost,
                "factivel_grasp": int(factivel),
                "tempo_seg": elapsed
            })

    # Salva CSV
    if rows:
        csv_path = os.path.join(base_dir, csv_output)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["classe", "arquivo", "T", "tau", "var",
                            "custo_grasp", "factivel_grasp", "tempo_seg"]
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResultados salvos em: {csv_path}")
    else:
        print("Nenhuma instância encontrada.")


# ============================================================
# 7. main()
# ============================================================

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_inst_dir = os.path.join(script_dir, "instancias_csilsp")

    # Parâmetros do GRASP
    MAX_ITER = 200
    ALPHA = 0.3
    L_MAX = 10
    SEED = 2025
    TIME_LIMIT = 1800  # 30 minutos por instância

    run_grasp_on_all_instances(
        base_dir=base_inst_dir,
        max_iter=MAX_ITER,
        alpha=ALPHA,
        L_max=L_MAX,
        seed=SEED,
        time_limit=TIME_LIMIT,
        csv_output="resultados_grasp.csv"
    )
