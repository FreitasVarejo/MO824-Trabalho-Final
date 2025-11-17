import pandas as pd
import matplotlib.pyplot as plt

ARQ_MIP = "resultados_mip.csv"
ARQ_GRASP = "resultados_grasp.csv"

mip = pd.read_csv(ARQ_MIP)
grasp = pd.read_csv(ARQ_GRASP)

mip_ok = mip[mip["status"] == "OPTIMAL"].copy()

chaves = ["classe", "arquivo", "T", "tau", "var"]
df = pd.merge(
    mip_ok,
    grasp,
    on=chaves,
    how="inner",
    suffixes=("_mip", "_grasp")
)

if "factivel" in df.columns:
    df = df[df["factivel"] == True].copy()

df["desvio_grasp_rel"] = (df["custo_grasp"] - df["custo_mip"]) / df["custo_mip"]

df["desvio_grasp_pct"] = 100 * df["desvio_grasp_rel"]

agrupado = df.groupby("T").agg(
    gap_mip_medio = ("gap_rel", "mean"),
    desvio_grasp_medio = ("desvio_grasp_rel", "mean"),
    desvio_grasp_pct_medio = ("desvio_grasp_pct", "mean"),
    tempo_mip_medio = ("tempo_seg_mip", "mean"),
    tempo_grasp_medio = ("tempo_seg_grasp", "mean"),
    n_instancias = ("arquivo", "count")
).reset_index()

print("\n=== Resumo por T ===")
print(agrupado.to_string(index=False))

agrupado.to_csv("analise_escalabilidade_por_T.csv", index=False)
print("\nArquivo 'analise_escalabilidade_por_T.csv' gerado.")

# Qualidade: desvio médio do GRASP vs T
plt.figure()
plt.plot(agrupado["T"], agrupado["desvio_grasp_pct_medio"], marker="o")
plt.xlabel("T")
plt.ylabel("Desvio médio do GRASP em relação ao MIP (%)")
plt.title("Escalabilidade de qualidade – GRASP vs MIP")
plt.grid(True)
plt.savefig("escala_qualidade_grasp.png", bbox_inches="tight")

# Tempo: MIP vs GRASP
plt.figure()
plt.plot(agrupado["T"], agrupado["tempo_mip_medio"]/60, marker="o", label="MIP (min)")
plt.plot(agrupado["T"], agrupado["tempo_grasp_medio"]/60, marker="o", label="GRASP (min)")
plt.xlabel("T")
plt.ylabel("Tempo médio (minutos)")
plt.title("Escalabilidade de tempo – MIP vs GRASP")
plt.legend()
plt.grid(True)
plt.savefig("escala_tempo_mip_grasp.png", bbox_inches="tight")
