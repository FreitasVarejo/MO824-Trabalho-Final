import os
import random
import numpy as np

# --- Parâmetros de Geração ---

# 1. Horizonte de Planejamento (T)
HORIZONTES_T = [50, 100, 200, 500]

# 2. Aperto da Capacidade (tau = C_media / d_media)
APERTO_TAU = [1.5, 2.0, 5.0]

# 3. Variabilidade da Demanda (Coeficiente de Variação)
VAR_DEMANDA = [0.2, 0.8] # 0.2 = Baixa var, 0.8 = Alta var

# 4. Número de instâncias por combinação
N_INSTANCIAS = 10

# 5. Seed base para reprodutibilidade
BASE_SEED = 20251112 # Baseado na data da proposta

# --- Constantes Base ---
D_MEDIA_BASE = 100  # Demanda média base
P_CUSTO_RANGE = (10, 20) # Range do custo unitário de produção
H_CUSTO_RANGE = (1, 5)   # Range do custo unitário de estoque
S_H_RATIO_RANGE = (50, 150) # Range do multiplicador s_t = h_t * ratio

# Diretório de saída (relativo a este script)
BASE_OUTPUT_DIR = "instancias_csilsp"

def gerar_dados_instancia(T, tau, var_demanda, seed):
    """
    Gera os dados para uma única instância com base nos parâmetros.
    Retorna tuplas: (demandas, setups, producoes, estoques, capacidades)
    """

    # Cria um Gerador de Números Aleatórios (RNG) a partir do seed
    # Esta é a prática moderna do numpy para reprodutibilidade
    rng = np.random.default_rng(seed)

    # 1. Gerar Custos (s_t, p_t, h_t)
    # Gerar custos de produção e estoque independentemente
    # CORREÇÃO: O método mudou de 'randint' para 'integers' na nova API
    p_t = rng.integers(P_CUSTO_RANGE[0], P_CUSTO_RANGE[1], size=T, endpoint=True)
    h_t = rng.integers(H_CUSTO_RANGE[0], H_CUSTO_RANGE[1], size=T, endpoint=True)

    # Gerar custo de setup como um múltiplo do custo de estoque (estrutura de custos)
    # CORREÇÃO: O método mudou de 'randint' para 'integers' na nova API
    s_h_ratios = rng.integers(S_H_RATIO_RANGE[0], S_H_RATIO_RANGE[1], size=T, endpoint=True)
    s_t = h_t * s_h_ratios

    # 2. Gerar Demandas (d_t)
    d_std = D_MEDIA_BASE * var_demanda
    d_t = rng.normal(D_MEDIA_BASE, d_std, T)
    # Garantir que a demanda não seja negativa e tenha um valor mínimo
    d_t = np.clip(d_t, D_MEDIA_BASE * 0.1, None).astype(int)

    # 3. Gerar Capacidades (C_t)
    d_real_media = np.mean(d_t)
    C_media = d_real_media * tau

    # Adicionar alguma variabilidade à capacidade (ex: 20% da média)
    C_std = C_media * 0.2
    C_t = rng.normal(C_media, C_std, T)
    C_t = np.clip(C_t, 0, None).astype(int)

    # 4. Verificação de Factibilidade (Total Capacidade >= Total Demanda)
    total_demanda = np.sum(d_t)
    total_capacidade = np.sum(C_t)

    # Se a capacidade total for infactível, escala as capacidades
    # para garantir que a soma das capacidades seja 10% maior que a soma das demandas
    if total_capacidade < total_demanda:
        fator_escala = (total_demanda / total_capacidade) * 1.10
        C_t = (C_t * fator_escala).astype(int)

        # Garante que C_t individual não seja 0 se a média for > 0
        C_t[C_t == 0] = int(C_media * 0.1) if C_media > 0 else 1
        C_t = np.clip(C_t, 0, None).astype(int)


    return d_t, s_t, p_t, h_t, C_t

def salvar_instancia(filepath, T, d, s, p, h, C):
    """
    Salva os dados da instância em um arquivo de texto.
    Formato:
    Linha 1: T
    Linha 2: d_1 d_2 ... d_T
    Linha 3: s_1 s_2 ... s_T
    Linha 4: p_1 p_2 ... p_T
    Linha 5: h_1 h_2 ... h_T
    Linha 6: C_1 C_2 ... C_T
    """
    try:
        with open(filepath, 'w') as f:
            f.write(f"{T}\n")
            f.write(" ".join(map(str, d)) + "\n")
            f.write(" ".join(map(str, s)) + "\n")
            f.write(" ".join(map(str, p)) + "\n")
            f.write(" ".join(map(str, h)) + "\n")
            f.write(" ".join(map(str, C)) + "\n")
    except IOError as e:
        print(f"Erro ao salvar o arquivo {filepath}: {e}")

def main():
    """
    Loop principal para gerar todas as combinações de instâncias.
    """
    # Garante que o diretório base exista
    script_dir = os.path.dirname(__file__)
    base_output_path = os.path.join(script_dir, BASE_OUTPUT_DIR)
    os.makedirs(base_output_path, exist_ok=True)

    print(f"Gerador de Instâncias C-SILSP")
    print(f"Salvando instâncias em: {os.path.abspath(base_output_path)}\n")

    total_instancias = 0
    instance_seed_counter = 0 # Contador para garantir seeds únicos

    # Itera sobre todas as combinações de parâmetros
    for T in HORIZONTES_T:
        for tau in APERTO_TAU:
            for var in VAR_DEMANDA:

                # Cria um subdiretório para esta classe de instância
                nome_classe = f"T{T}_tau{tau}_var{var}"
                path_classe = os.path.join(base_output_path, nome_classe)
                os.makedirs(path_classe, exist_ok=True)

                print(f"Gerando classe: {nome_classe}...")

                # Gera N_INSTANCIAS para esta classe
                for i in range(1, N_INSTANCIAS + 1):
                    nome_arquivo = f"inst_{i:02d}.txt"
                    filepath_completo = os.path.join(path_classe, nome_arquivo)

                    # Cria um seed único e determinístico para esta instância
                    instance_seed = BASE_SEED + instance_seed_counter
                    instance_seed_counter += 1

                    # Gera os dados
                    d, s, p, h, C = gerar_dados_instancia(T, tau, var, instance_seed)

                    # Salva o arquivo
                    salvar_instancia(filepath_completo, T, d, s, p, h, C)
                    total_instancias += 1

    print(f"\nConcluído. Total de {total_instancias} instâncias geradas.")

if __name__ == "__main__":
    main()
