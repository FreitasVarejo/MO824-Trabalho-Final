#!/usr/bin/env python3
import os
import sys
import time
import random
import csv
import grasp_csilsp as grasp_lib # Importa seu script original como uma biblioteca

# Pega o caminho da instância do argumento da linha de comando
if len(sys.argv) < 2:
    print(f"Erro: Forneça o caminho para o arquivo da instância.", file=sys.stderr)
    sys.exit(1)

instance_path = os.path.abspath(sys.argv[1])
if not os.path.exists(instance_path):
    print(f"Erro: Arquivo não encontrado: {instance_path}", file=sys.stderr)
    sys.exit(1)

# --- Define os caminhos base (como no seu script original) ---
# Assume que este script está no diretório raiz do projeto (MO824-Trabalho-Final)
script_dir = os.path.dirname(os.path.abspath(__file__)) # <--- Renomeado
project_root = os.path.dirname(script_dir) # <--- CORRIGIDO: Sobe um nível

base_inst_dir = os.path.join(project_root, "benchmark", "instancias_csilsp") # <--- CORRIGIDO
benchmark_dir = os.path.join(project_root, "benchmark") # <--- NOVO

log_output_dir = "grasp_logs" # O mesmo nome de diretório do seu script
log_dir = os.path.join(benchmark_dir, log_output_dir) # <--- CORRIGIDO

# --- Parâmetros do GRASP (como no seu script original) ---
MAX_ITER = 200
ALPHA = 0.3
L_MAX = 10
TIME_LIMIT = 1800  # 30 minutos

# Cria diretórios de log se não existirem
os.makedirs(log_dir, exist_ok=True)

# -----------------------------------------------------------------
# Lógica principal (adaptada de 'run_grasp_on_all_instances')
# -----------------------------------------------------------------
try:
    # 1. Carrega a instância
    T, d, s, p, h, C = grasp_lib.load_instance(instance_path)

    # 2. Parseia os metadados
    T_class, tau_class, var_class = grasp_lib.parse_class_from_path(instance_path, base_inst_dir)
    classe_name = os.path.relpath(os.path.dirname(instance_path), base_inst_dir)
    fname = os.path.basename(instance_path)

    # 3. Roda o GRASP
    t0 = time.time()
    # seed aleatória para garantir diversidade na execução paralela
    y, X, I, cost, log_conv = grasp_lib.grasp(
        d=d, C=C, s=s, p=p, h=h,
        max_iter=MAX_ITER,
        alpha=ALPHA,
        L_max=L_MAX,
        seed=random.randint(1, 10**9),
        time_limit=TIME_LIMIT
    )
    t1 = time.time()
    elapsed = t1 - t0
    factivel = cost < grasp_lib.BIGM / 2

    # 4. Salva o LOG de convergência (sem conflitos)
    log_class_dir = os.path.join(log_dir, classe_name)
    os.makedirs(log_class_dir, exist_ok=True)
    log_fname = fname.replace(".txt", "_log.csv")
    log_path = os.path.join(log_class_dir, log_fname)

    try:
        with open(log_path, "w", newline="") as f_log:
            writer_log = csv.writer(f_log)
            writer_log.writerow(["tempo_seg", "custo"]) # Header
            writer_log.writerows(log_conv)
    except IOError as e:
        print(f"ERRO ao salvar log {log_path}: {e}", file=sys.stderr)

    # 5. Prepara a linha de resumo
    # (classe, arquivo, T, tau, var, custo_grasp, factivel_grasp, tempo_seg)
    # IMPORTANTE: Usamos 'print' para enviar ao stdout, sem header.
    # Usamos um 'csv.writer' para garantir formatação correta (ex: vírgulas)

    writer = csv.writer(sys.stdout)
    writer.writerow([
        classe_name,
        fname,
        T,
        tau_class,
        var_class,
        cost,
        int(factivel),
        elapsed
    ])

    # Imprime um log no stderr para vermos o progresso no terminal
    print(f"[OK] {fname} | Custo={cost:.2f} | Tempo={elapsed:.2f}s", file=sys.stderr)


except Exception as e:
    print(f"Falha ao processar {instance_path}: {e}", file=sys.stderr)
    sys.exit(1)
