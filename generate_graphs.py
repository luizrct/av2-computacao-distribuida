import os
import pandas as pd
import matplotlib.pyplot as plt

INPUT_FILE = "clean_results.csv"
OUTPUT_DIR = "graficos"

ORDEM_CARGAS = ["low", "medium", "high", "hybrid"]

PALETA_INSTANCIAS = ["#AEC6CF", "#FFB347", "#B39EB5"]  # azul, laranja, roxo pastel
PALETA_CARGAS = ["#77DD77", "#FDFD96", "#FF6961", "#CFCFC4"]  # verde, amarelo, vermelho, cinza pastel

def criar_pasta_saida():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def carregar_dados():
    df = pd.read_csv(INPUT_FILE)

    df["users"] = df["users"].astype(int)
    df["instances"] = df["instances"].astype(int)
    df["requests"] = df["requests"].astype(float)
    df["failures"] = df["failures"].astype(float)
    df["p95"] = df["p95"].astype(float)

    df["tempo_resposta_s"] = df["p95"] / 1000

    df["taxa_falhas_pct"] = df.apply(
        lambda row: (row["failures"] / row["requests"]) * 100
        if row["requests"] > 0 else 0,
        axis=1
    )

    # Forçar ordem das cargas
    df["scenario"] = pd.Categorical(
        df["scenario"],
        categories=ORDEM_CARGAS,
        ordered=True
    )

    return df

def obter_limite_y(df, coluna):
    valor_maximo = df[coluna].max()

    if pd.isna(valor_maximo) or valor_maximo == 0:
        return 1

    return valor_maximo * 1.10

def grafico_barras_agrupadas(
    df,
    eixo_x,
    eixo_y,
    barras,
    titulo,
    xlabel,
    ylabel,
    barrasLabel,
    output_file,
    ylim=None
):
    tabela = df.pivot_table(
        index=eixo_x,
        columns=barras,
        values=eixo_y,
        aggfunc="mean"
    ).sort_index()

    # garantir ordem das colunas quando for carga
    if barras == "scenario":
        tabela = tabela.reindex(columns=ORDEM_CARGAS)
        cores = PALETA_CARGAS[:len(tabela.columns)]
    else:
        tabela = tabela.reindex(columns=sorted(tabela.columns))
        cores = PALETA_INSTANCIAS[:len(tabela.columns)]

    ax = tabela.plot(
        kind="bar",
        figsize=(10, 6),
        width=0.8,
        color=cores
    )

    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(title=barrasLabel)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    if ylim is not None:
        ax.set_ylim(0, ylim)

    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, output_file), dpi=300)
    plt.close()


def gerar_estilo_1(df, ylim):
    for indice, carga in enumerate(ORDEM_CARGAS, start=1):
        dados = df[df["scenario"] == carga]
        if dados.empty:
            continue

        grafico_barras_agrupadas(
            df=dados,
            eixo_x="users",
            eixo_y="tempo_resposta_s",
            barras="instances",
            titulo=f"Tempo de resposta por número de usuários - Carga {carga}",
            xlabel="Usuários",
            ylabel="Tempo de resposta P95 (s)",
            barrasLabel="Instâncias",
            output_file=f"estilo_1_tempo_resposta_carga_{indice}_{carga}.png",
            ylim=ylim
        )


def gerar_estilo_2(df, ylim):
    for indice, carga in enumerate(ORDEM_CARGAS, start=1):
        dados = df[df["scenario"] == carga]
        if dados.empty:
            continue

        grafico_barras_agrupadas(
            df=dados,
            eixo_x="users",
            eixo_y="taxa_falhas_pct",
            barras="instances",
            titulo=f"Taxa de falhas por número de usuários - Carga {carga}",
            xlabel="Usuários",
            ylabel="Taxa de falhas (%)",
            barrasLabel="Instâncias",
            output_file=f"estilo_2_taxa_falhas_carga_{indice}_{carga}.png",
            ylim=ylim
        )


def gerar_estilo_3(df, ylim):
    for instancia in sorted(df["instances"].unique()):
        dados = df[df["instances"] == instancia]
        if dados.empty:
            continue

        grafico_barras_agrupadas(
            df=dados,
            eixo_x="users",
            eixo_y="tempo_resposta_s",
            barras="scenario",
            titulo=f"Tempo de resposta por tipo de carga - {instancia} instância(s)",
            xlabel="Usuários",
            ylabel="Tempo de resposta P95 (s)",
            barrasLabel="Carga",
            output_file=f"estilo_3_tempo_resposta_instancia_{instancia}.png",
            ylim=ylim
        )


def gerar_estilo_4(df, ylim):
    for instancia in sorted(df["instances"].unique()):
        dados = df[df["instances"] == instancia]
        if dados.empty:
            continue

        grafico_barras_agrupadas(
            df=dados,
            eixo_x="users",
            eixo_y="taxa_falhas_pct",
            barras="scenario",
            titulo=f"Taxa de falhas por tipo de carga - {instancia} instância(s)",
            xlabel="Usuários",
            ylabel="Taxa de falhas (%)",
            barrasLabel="Carga",
            output_file=f"estilo_4_taxa_falhas_instancia_{instancia}.png",
            ylim=ylim
        )


def main():
    criar_pasta_saida()
    df = carregar_dados()

    ylim_tempo = obter_limite_y(df, "tempo_resposta_s")
    ylim_falhas = obter_limite_y(df, "taxa_falhas_pct")

    gerar_estilo_1(df, ylim_tempo)
    gerar_estilo_2(df, ylim_falhas)
    gerar_estilo_3(df, ylim_tempo)
    gerar_estilo_4(df, ylim_falhas)

    print(f"Gráficos gerados em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()