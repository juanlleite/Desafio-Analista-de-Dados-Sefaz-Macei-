import streamlit as st
import polars as pl
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from typing import Optional

# Configuração da página
st.set_page_config(
    page_title="Sefaz | Painel Orçamentário", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

def carregar_dados_gold() -> Optional[pd.DataFrame]:
    """Carrega os dados consolidados da camada Gold em formato Pandas."""
    try:
        caminho_gold = Path("dados_processados/finbra_gold.parquet")
        if not caminho_gold.exists():
            return None
        return pl.read_parquet(caminho_gold).to_pandas()
    except Exception as e:
        st.error(f"Erro técnico ao ler base de dados: {e}")
        return None

def formatar_brl(valor: float) -> str:
    """Formata valor float para moeda brasileira (R$)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def main() -> None:
    # Injeção de CSS minificado para carregar Plus Jakarta Sans e JetBrains Mono (Tema High-Tech Light)
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">', unsafe_allow_html=True)
    
    css = """
    .stApp {
        background-color: #f4f4f5;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0.2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, .stSelectbox {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e4e4e7 !important;
    }
    section[data-testid="stSidebar"] label {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: #71717a !important;
        margin-bottom: 6px !important;
        margin-top: 12px !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid #e4e4e7 !important;
        background-color: #fafafa !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .chart-title {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #18181b !important;
        border-left: 3px solid #18181b;
        padding-left: 8px;
        margin-bottom: 8px;
        margin-top: 10px;
    }
    .content-card {
        background-color: #ffffff;
        border: 1px solid #e4e4e7;
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.01);
        margin-bottom: 12px;
    }
    
    /* Transformação dos Radios em Botões Segmentados tipo Pill (Padrão Aether) */
    div[role="radiogroup"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    div[role="radiogroup"] label {
        background-color: #ffffff !important;
        border: 1px solid #e4e4e7 !important;
        padding: 6px 14px !important;
        border-radius: 9999px !important; /* Visual de Pill */
        cursor: pointer !important;
        margin: 0 !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
    }
    div[role="radiogroup"] label:hover {
        border-color: #a1a1aa !important;
        background-color: #fafafa !important;
    }
    div[role="radiogroup"] label:has(input:checked) {
        background-color: #1f497d !important; /* Azul institucional */
        border-color: #1f497d !important;
    }
    div[role="radiogroup"] label:has(input:checked) * {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    /* Força os filhos diretos e descendentes do label a não terem deslocamento e centralizarem */
    div[role="radiogroup"] label * {
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[role="radiogroup"] label p {
        font-size: 0.8rem !important;
        font-weight: 500 !important;
    }
    div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    div[role="radiogroup"] label > div:nth-child(2) {
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    
    /* Rótulos e valores de telemetria baseados em JetBrains Mono */
    .kpi-title {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        color: #71717a !important;
        letter-spacing: 0.08em !important;
    }
    .kpi-value {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #18181b !important;
    }
    """
    css_minificado = "".join([line.strip() for line in css.split("\n")])
    st.markdown(f"<style>{css_minificado}</style>", unsafe_allow_html=True)

    dados = carregar_dados_gold()
    
    if dados is None or dados.empty:
        st.warning("⚠️ Base de dados não encontrada. Execute as etapas de extração, transformação e análise antes de abrir o painel.")
        return

    # Limpeza do nome da instituição para exibição amigável
    dados["Capital_Limpa"] = dados["Instituição"].str.replace(r"Prefeitura Municipal d[eo] ", "", regex=True)

    # ==================== MENU LATERAL (SIDEBAR) REFINADO ====================
    st.sidebar.markdown("""
        <div style="padding-bottom: 12px; border-bottom: 1px solid #e4e4e7; margin-bottom: 15px;">
            <h3 style="color:#18181b; margin:0; font-weight:700; font-size:1.1rem; font-family:'Plus Jakarta Sans', sans-serif;">🏛️ Sefaz Maceió</h3>
            <p style="color:#71717a; margin:2px 0 0 0; font-size:0.75rem; font-family:'Plus Jakarta Sans', sans-serif;">Painel de Execução Orçamentária</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<div style='font-family:\"JetBrains Mono\", monospace; font-size:0.7rem; font-weight:700; text-transform:uppercase; color:#71717a; margin-bottom:5px;'>Navegação</div>", unsafe_allow_html=True)
    navegacao = st.sidebar.radio(
        "Selecione a Visualização",
        ["📊 Visão por Capital", "🌍 Comparativo Geral"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("<hr style='margin:15px 0; border:0; border-top:1px solid #e4e4e7;'>", unsafe_allow_html=True)

    # Carrega anos disponíveis para os filtros
    anos_disponiveis = sorted(dados["ano"].unique().tolist(), reverse=True)
    idx_padrao = anos_disponiveis.index(2024) if 2024 in anos_disponiveis else 0

    if navegacao == "📊 Visão por Capital":
        st.sidebar.markdown("<div style='font-size:0.7rem; font-weight:700; text-transform:uppercase; color:#71717a; margin-bottom:5px;'>Filtros</div>", unsafe_allow_html=True)
        ano_selecionado = st.sidebar.radio("Exercício", anos_disponiveis, index=idx_padrao, horizontal=True)
        
        # Filtra capitais válidas para o ano selecionado
        dados_ano = dados[dados["ano"] == ano_selecionado]
        capitais_disponiveis = sorted(dados_ano["Capital_Limpa"].unique().tolist())
        capital_selecionada = st.sidebar.selectbox("Capital", capitais_disponiveis)
        
        nivel_selecionado = st.sidebar.radio("Nível", ["Função", "Subfunção"], horizontal=True)

        # Filtragem dos dados conforme seleção
        df_filtrado = dados[
            (dados["ano"] == ano_selecionado) & 
            (dados["Capital_Limpa"] == capital_selecionada) &
            (dados["Nivel"] == nivel_selecionado)
        ]

        # Cabeçalho da Página super compacto
        st.markdown(f"<h3 style='margin:0 0 10px 0; font-weight:700; color:#18181b; font-family:\"Plus Jakarta Sans\", sans-serif; font-size:1.35rem;'>📋 Panorama Orçamentário — {capital_selecionada} ({ano_selecionado})</h3>", unsafe_allow_html=True)

        if ano_selecionado == 2025:
            st.warning("⚠️ **Aviso:** Os dados de 2025 ainda estão em fase de consolidação no Siconfi.")

        # Dicionário explicativo (Data Literacy) compacto
        with st.expander("ℹ️ Entendendo os dados (Clique para expandir)", expanded=False):
            st.markdown("""
            **Guia rápido:**
            - **Despesas Empenhadas**: Reserva formal de dinheiro para o contrato.
            - **Despesas Pagas**: Saída física de caixa após a entrega do serviço.
            - **Restos a Pagar**: Diferença entre Empenhado e Pago (promessa que ficou para pagar depois).
            - **Eficiência**: Percentual de empenhos quitados no mesmo ano civil.
            """)

        # Indicadores Financeiros centralizados e horizontais (Exigência do Usuário)
        total_empenhado = df_filtrado["Despesas_Empenhadas"].sum() if not df_filtrado.empty else 0
        total_pago = df_filtrado["Despesas_Pagas"].sum() if not df_filtrado.empty else 0
        taxa_execucao = (total_pago / total_empenhado * 100) if total_empenhado > 0 else 0
        
        val_empenhado = formatar_brl(total_empenhado)
        val_pago = formatar_brl(total_pago)
        val_taxa = f"{taxa_execucao:.1f}%"

        st.markdown('<div class="chart-title">Indicadores Financeiros</div>', unsafe_allow_html=True)
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        html_card = """
        <div style="background-color:#ffffff; padding:12px 18px; border-radius:12px; border:1px solid #e4e4e7; border-left:5px solid {cor}; box-shadow: 0 1px 2px rgba(0,0,0,0.01);">
            <div class="kpi-title">| {titulo}</div>
            <div class="kpi-value">{valor}</div>
        </div>
        """
        
        with kpi_col1:
            st.markdown(html_card.format(cor="#1f497d", titulo="Total Empenhado", valor=val_empenhado), unsafe_allow_html=True)
        with kpi_col2:
            st.markdown(html_card.format(cor="#00b050", titulo="Total Pago", valor=val_pago), unsafe_allow_html=True)
        with kpi_col3:
            st.markdown(html_card.format(cor="#ed7d31", titulo="Taxa de Execução Geral", valor=val_taxa), unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

        # Corpo do Painel: Gráfico de Distribuição Orçamentária ocupando largura total
        st.markdown('<div class="chart-title">Distribuição Orçamentária por Área</div>', unsafe_allow_html=True)
        if df_filtrado.empty:
            st.info("Nenhum dado encontrado para os filtros selecionados.")
        else:
            st.markdown('<div class="content-card">', unsafe_allow_html=True)
            df_ordenado = df_filtrado.sort_values(by="Despesas_Empenhadas", ascending=True)
            df_grafico = df_ordenado.melt(
                id_vars=["Conta"],
                value_vars=["Despesas_Empenhadas", "Despesas_Pagas"],
                var_name="Estágio",
                value_name="Valor"
            )
            df_grafico["Estágio"] = df_grafico["Estágio"].str.replace("_", " ")
            df_grafico["Valor_Formatado"] = df_grafico["Valor"].map(formatar_brl)
            
            fig = px.bar(
                df_grafico,
                y="Conta",
                x="Valor",
                color="Estágio",
                barmode="group",
                orientation="h",
                color_discrete_map={"Despesas Empenhadas": "#1f497d", "Despesas Pagas": "#ed7d31"},
                labels={"Conta": nivel_selecionado, "Valor": "Valor"},
                custom_data=["Valor_Formatado", "Estágio"],
                height=320 
            )
            fig.update_traces(
                hovertemplate="<b>%{y}</b><br>%{customdata[1]}: <b>%{customdata[0]}</b><extra></extra>"
            )
            fig.update_layout(
                font=dict(color="#18181b", family="Plus Jakarta Sans, sans-serif"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=5, b=5),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.02, 
                    xanchor="right", 
                    x=1,
                    font=dict(color="#71717a", size=9)
                ),
                xaxis=dict(gridcolor="#e4e4e7", tickfont=dict(color="#71717a")),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#18181b"))
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Seção inferior dividida em duas colunas para Histórico e Tabela Detalhada
        col_bottom_left, col_bottom_right = st.columns([5, 7])

        with col_bottom_left:
            st.markdown('<div class="chart-title">Evolução Histórica da Execução</div>', unsafe_allow_html=True)
            dados_historicos = dados[
                (dados["Capital_Limpa"] == capital_selecionada) & 
                (dados["Nivel"] == nivel_selecionado) &
                (dados["ano"] < 2025)
            ]
            
            if dados_historicos.empty:
                st.info("Histórico indisponível.")
            else:
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                df_evolucao_cap = dados_historicos.groupby("ano")[["Despesas_Empenhadas", "Despesas_Pagas"]].sum().reset_index()
                df_evolucao_cap["Taxa_Municipio"] = np.where(
                    df_evolucao_cap["Despesas_Empenhadas"] > 0,
                    (df_evolucao_cap["Despesas_Pagas"] / df_evolucao_cap["Despesas_Empenhadas"] * 100),
                    0.0
                )
                
                dados_nacionais = dados[(dados["Nivel"] == nivel_selecionado) & (dados["ano"] < 2025)]
                df_evolucao_nac = dados_nacionais.groupby("ano")[["Despesas_Empenhadas", "Despesas_Pagas"]].sum().reset_index()
                df_evolucao_nac["Taxa_Media_Nacional"] = np.where(
                    df_evolucao_nac["Despesas_Empenhadas"] > 0,
                    (df_evolucao_nac["Despesas_Pagas"] / df_evolucao_nac["Despesas_Empenhadas"] * 100),
                    0.0
                )
                
                df_historico_final = df_evolucao_cap.merge(df_evolucao_nac[["ano", "Taxa_Media_Nacional"]], on="ano")
                df_historico_final = df_historico_final.rename(columns={
                    "Taxa_Municipio": "Taxa do Município",
                    "Taxa_Media_Nacional": "Média Nacional"
                })
                
                fig_linha = px.line(
                    df_historico_final,
                    x="ano",
                    y=["Taxa do Município", "Média Nacional"],
                    labels={"ano": "Ano", "value": "Taxa (%)", "variable": "Legenda"},
                    color_discrete_map={"Taxa do Município": "#1f497d", "Média Nacional": "#ed7d31"},
                    height=230
                )
                fig_linha.update_layout(
                    font=dict(color="#18181b", family="Plus Jakarta Sans, sans-serif"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=5, b=5),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.02, 
                        xanchor="right", 
                        x=1,
                        font=dict(color="#71717a", size=8)
                    ),
                    xaxis=dict(gridcolor="#e4e4e7", tickmode="linear", tickfont=dict(color="#71717a")),
                    yaxis=dict(gridcolor="#e4e4e7", range=[0, 110], tickfont=dict(color="#71717a"))
                )
                st.plotly_chart(fig_linha, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with col_bottom_right:
            st.markdown(f'<div class="chart-title">Despesas Detalhadas ({ano_selecionado})</div>', unsafe_allow_html=True)
            if not df_filtrado.empty:
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                df_tabela = df_filtrado[["Conta", "Despesas_Empenhadas", "Despesas_Pagas"]].copy()
                df_tabela.columns = [nivel_selecionado, "Empenhado (R$)", "Pago (R$)"]
                df_tabela["Empenhado (R$)"] = df_tabela["Empenhado (R$)"].map(formatar_brl)
                df_tabela["Pago (R$)"] = df_tabela["Pago (R$)"].map(formatar_brl)
                st.dataframe(df_tabela, use_container_width=True, hide_index=True, height=230)
                st.markdown('</div>', unsafe_allow_html=True)

    # ==================== ABA 2: COMPARATIVO GERAL ====================
    elif navegacao == "🌍 Comparativo Geral":
        st.sidebar.markdown("<div style='font-size:0.7rem; font-weight:700; text-transform:uppercase; color:#71717a; margin-bottom:5px;'>Filtros</div>", unsafe_allow_html=True)
        ano_comp = st.sidebar.radio("Exercício", anos_disponiveis, index=idx_padrao, horizontal=True, key="rad_ano_comp")
        nivel_comp = st.sidebar.radio("Nível", ["Função", "Subfunção"], horizontal=True, key="rad_niv_comp")
        
        contas_disponiveis = sorted(dados[dados["Nivel"] == nivel_comp]["Conta"].unique().tolist())
        conta_selecionada = st.sidebar.selectbox("Área / Rubrica", contas_disponiveis)

        st.markdown(f"<h3 style='margin:0 0 10px 0; font-weight:700; color:#18181b; font-family:\"Plus Jakarta Sans\", sans-serif; font-size:1.35rem;'>🌍 Eficiência Orçamentária entre Capitais</h3>", unsafe_allow_html=True)

        df_comp = dados[
            (dados["ano"] == ano_comp) & 
            (dados["Nivel"] == nivel_comp) &
            (dados["Conta"] == conta_selecionada)
        ].copy()

        if df_comp.empty:
            st.info("Nenhum registro encontrado para os filtros selecionados.")
        else:
            df_comp["Taxa_Execucao"] = np.where(
                df_comp["Despesas_Empenhadas"] > 0,
                (df_comp["Despesas_Pagas"] / df_comp["Despesas_Empenhadas"] * 100),
                0.0
            )
            df_comp = df_comp.sort_values(by="Taxa_Execucao", ascending=True)

            # Cálculos dos destaques para os KPIs
            media_nacional = df_comp["Taxa_Execucao"].mean()
            maior_row = df_comp.loc[df_comp["Taxa_Execucao"].idxmax()]
            menor_row = df_comp.loc[df_comp["Taxa_Execucao"].idxmin()]

            val_media = f"{media_nacional:.1f}%"
            val_maior = f"{maior_row['Capital_Limpa']} ({maior_row['Taxa_Execucao']:.1f}%)"
            val_menor = f"{menor_row['Capital_Limpa']} ({menor_row['Taxa_Execucao']:.1f}%)"

            # KPIs da Rubrica no topo
            st.markdown('<div class="chart-title">Destaques Comparativos da Rubrica</div>', unsafe_allow_html=True)
            kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
            
            html_card_kpi = """
            <div style="background-color:#ffffff; padding:12px 18px; border-radius:12px; border:1px solid #e4e4e7; border-left:5px solid {cor}; box-shadow: 0 1px 2px rgba(0,0,0,0.01);">
                <div class="kpi-title">| {titulo}</div>
                <div class="kpi-value">{valor}</div>
            </div>
            """
            with kpi_c1:
                st.markdown(html_card_kpi.format(cor="#1f497d", titulo="Média de Execução Nacional", valor=val_media), unsafe_allow_html=True)
            with kpi_c2:
                st.markdown(html_card_kpi.format(cor="#00b050", titulo="Maior Eficiência", valor=val_maior), unsafe_allow_html=True)
            with kpi_c3:
                st.markdown(html_card_kpi.format(cor="#ed7d31", titulo="Menor Eficiência", valor=val_menor), unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)

            # Grid de duas colunas: Gráfico na esquerda e Tabela na direita
            col_comp_left, col_comp_right = st.columns([7, 5])

            with col_comp_left:
                st.markdown('<div class="chart-title">Ranking de Eficiência das Capitais</div>', unsafe_allow_html=True)
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                
                df_comp["Empenhado_Formatado"] = df_comp["Despesas_Empenhadas"].map(formatar_brl)
                df_comp["Pago_Formatado"] = df_comp["Despesas_Pagas"].map(formatar_brl)
                df_comp["Taxa_Formatada"] = df_comp["Taxa_Execucao"].map(lambda x: f"{x:.1f}%")

                cores = ["#e61174" if cap == "Maceió - AL" else "#cbd5e1" for cap in df_comp["Capital_Limpa"]]

                fig_comp = px.bar(
                    df_comp,
                    y="Capital_Limpa",
                    x="Taxa_Execucao",
                    orientation="h",
                    labels={"Capital_Limpa": "Capital", "Taxa_Execucao": "Taxa de Execução (%)"},
                    custom_data=["Taxa_Formatada", "Empenhado_Formatado", "Pago_Formatado"],
                    height=580
                )
                fig_comp.update_traces(
                    marker_color=cores,
                    hovertemplate="<b>%{y}</b><br>Taxa: <b>%{customdata[0]}</b><br>Empenhado: %{customdata[1]}<br>Pago: %{customdata[2]}<extra></extra>"
                )
                fig_comp.update_layout(
                    font=dict(color="#18181b", family="Plus Jakarta Sans, sans-serif"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=5, b=5),
                    xaxis=dict(gridcolor="#e4e4e7", tickfont=dict(color="#71717a"), title="Taxa (%)"),
                    yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#18181b"))
                )
                st.plotly_chart(fig_comp, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_comp_right:
                st.markdown('<div class="chart-title">Tabela Comparativa Completa</div>', unsafe_allow_html=True)
                st.markdown('<div class="content-card">', unsafe_allow_html=True)
                
                # Prepara tabela de detalhes ordenada do melhor para o pior
                df_comp_tabela = df_comp.sort_values(by="Taxa_Execucao", ascending=False)[
                    ["Capital_Limpa", "Despesas_Empenhadas", "Despesas_Pagas", "Taxa_Execucao"]
                ].copy()
                df_comp_tabela.columns = ["Capital", "Empenhado (R$)", "Pago (R$)", "Taxa (%)"]
                df_comp_tabela["Empenhado (R$)"] = df_comp_tabela["Empenhado (R$)"].map(formatar_brl)
                df_comp_tabela["Pago (R$)"] = df_comp_tabela["Pago (R$)"].map(formatar_brl)
                df_comp_tabela["Taxa (%)"] = df_comp_tabela["Taxa (%)"].map(lambda x: f"{x:.1f}%")
                
                st.dataframe(df_comp_tabela, use_container_width=True, hide_index=True, height=580)
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
