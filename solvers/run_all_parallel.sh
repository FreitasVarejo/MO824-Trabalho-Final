#!/bin/bash

# Este script executa o GRASP em paralelo em todas as instâncias.
# Ele é seguro para interrupção (Ctrl+C).

# --- 1. Como ver seus cores ---
# O comando 'nproc' informa quantos cores lógicos (threads) você tem.
N_CORES=$(nproc)
echo "-------------------------------------------------------------"
echo "Máquina detectada com $N_CORES cores lógicos."
echo "Usando $N_CORES processos paralelos."
echo "-------------------------------------------------------------"

# --- 2. Configuração ---
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR") # <--- NOVO: Define o root do projeto

INST_DIR="$PROJECT_ROOT/benchmark/instancias_csilsp" # <--- CORRIGIDO
BENCHMARK_DIR="$PROJECT_ROOT/benchmark" # <--- NOVO: Define o diretório de benchmark

CSV_RESULT_FILE="$BENCHMARK_DIR/resultados_grasp.csv" # <--- CORRIGIDO
LOG_DIR="$BENCHMARK_DIR/grasp_logs" # <--- CORRIGIDO
RUNNER_SCRIPT="$SCRIPT_DIR/run_single_instance.py" # <--- Este já estava certo

# Limpa execuções anteriores (Opcional, mas recomendado)
rm -f "$CSV_RESULT_FILE"
rm -rf "$LOG_DIR"
echo "Resultados anteriores limpos."

# --- 3. Cria o cabeçalho do CSV de resumo ---
echo "classe,arquivo,T,tau,var,custo_grasp,factivel_grasp,tempo_seg" > "$CSV_RESULT_FILE"

# --- 4. Execução paralela ---
# O "pulo do gato" está aqui.
# 1. 'find' lista todos os arquivos .txt
# 2. 'xargs' pega essa lista e:
#    -P $N_CORES: Roda em paralelo usando todos os seus cores.
#    -n 1: Passa 1 arquivo de cada vez para o comando.
# 3. 'python3 $RUNNER_SCRIPT' é o comando executado para cada arquivo.
# 4. '>> "$CSV_RESULT_FILE"' anexa a saída (a linha de resumo) ao CSV,
#    em tempo real, assim que cada instância termina.

echo "Iniciando execuções... (Pressione Ctrl+C para parar)"

find "$INST_DIR" -name "*.txt" | xargs -P $N_CORES -n 1 python3 "$RUNNER_SCRIPT" >> "$CSV_RESULT_FILE"

echo "-------------------------------------------------------------"
echo "Execução finalizada!"
echo "Logs de convergência (TTT) salvos em: $LOG_DIR"
echo "Resumo final salvo em: $CSV_RESULT_FILE"
echo "-------------------------------------------------------------"
