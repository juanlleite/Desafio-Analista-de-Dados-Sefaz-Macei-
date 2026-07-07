import streamlit as st
import polars as pl
import plotly.express as px
from pathlib import Path

# Configuração da página com barra lateral oculta por padrão
st.set_page_config(
    page_title="Secretaria de Fazenda | Execução Orçamentária", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

def carregar_dados_gold():
    """Carrega os dados consolidados da camada Gold."""
    caminho_gold = Path("dados_processados/finbra_gold.parquet")
    if not caminho_gold.exists():
        return None
    return pl.read_parquet(caminho_gold).to_pandas()

def main():
    # Injeção de CSS para forçar o tema claro e estilização dos componentes
    st.markdown("""
        <style>
        .stApp {
            background-color: #f8f9fa;
        }
        h1, h2, h3, h4, h5, h6, p, span, label {
            color: #212529 !important;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        /* Estiliza os containers de filtros */
        div[data-testid="column"] {
            background-color: transparent;
        }
        /* Ajusta o espaçamento do título do gráfico */
        .chart-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1f497d !important;
            border-left: 4px solid #1f497d;
            padding-left: 8px;
            margin-bottom: 15px;
            margin-top: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Cabeçalho Institucional
    st.markdown("""
        <div style="background-color:#1f497d; padding:15px 25px; border-radius:6px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <div style="color:white; font-size:1.5rem; font-weight:700; font-family:'Segoe UI', sans-serif; display:flex; align-items:center; gap:10px;">
                🏛️ Secretaria Municipal de Fazenda
            </div>
            <div style="color:rgba(255,255,255,0.9); font-size:1.05rem; font-weight:400; font-family:'Segoe UI', sans-serif;">
                Execução Orçamentária das Capitais
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    dados = carregar_dados_gold()
    
    if dados is None or dados.empty:
        st.warning("⚠️ Base de dados não encontrada. Execute as etapas de extração, transformação e análise antes de abrir o painel.")
        return

    # Limpeza do nome da instituição para exibição amigável
    dados["Capital_Limpa"] = dados["Instituição"].str.replace(r"Prefeitura Municipal d[eo] ", "", regex=True)

    # Primeira Linha: Filtros (Esquerda) e Métricas (Direita)
    col_filtros, col_kpis = st.columns([5, 7])

    with col_filtros:
        st.markdown('<div class="chart-title">Filtros de Consulta</div>', unsafe_allow_html=True)
        
        # Filtros dispostos horizontalmente
        f_col1, f_col2, f_col3 = st.columns(3)
        
        anos_disponiveis = sorted(dados["ano"].unique().tolist(), reverse=True)
        idx_padrao = anos_disponiveis.index(2024) if 2024 in anos_disponiveis else 0
        
        with f_col1:
            ano_selecionado = st.selectbox("Exercício", anos_disponiveis, index=idx_padrao)
        with f_col2:
            capitais_disponiveis = sorted(dados["Capital_Limpa"].unique().tolist())
            capital_selecionada = st.selectbox("Capital", capitais_disponiveis)
        with f_col3:
            nivel_selecionado = st.selectbox("Nível", ["Função", "Subfunção"])

    # Filtragem dos dados conforme seleção
    df_filtrado = dados[
        (dados["ano"] == ano_selecionado) & 
        (dados["Capital_Limpa"] == capital_selecionada) &
        (dados["Nivel"] == nivel_selecionado)
    ]

    # Alerta de dados parciais para o ano de 2025
    if ano_selecionado == 2025:
        st.warning("⚠️ **Aviso:** Os dados do exercício de 2025 ainda estão em fase de consolidação e podem estar incompletos.")

    # Cálculo das Métricas Globais
    total_empenhado = df_filtrado["Despesas_Empenhadas"].sum() if not df_filtrado.empty else 0
    total_pago = df_filtrado["Despesas_Pagas"].sum() if not df_filtrado.empty else 0
    taxa_execucao = (total_pago / total_empenhado * 100) if total_empenhado > 0 else 0

    with col_kpis:
        st.markdown('<div class="chart-title">Indicadores de Desempenho</div>', unsafe_allow_html=True)
        
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        val_empenhado = f"R$ {total_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        val_pago = f"R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        val_taxa = f"{taxa_execucao:.1f}%"
        
        html_card = """
        <div style="background-color:{cor}; padding:12px 15px; border-radius:6px; color:white; min-height:85px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display:flex; flex-direction:column; justify-content:center;">
            <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; color:rgba(255,255,255,0.85); margin:0;">| {titulo}</div>
            <div style="font-size:1.15rem; font-weight:700; color:white; margin-top:5px; word-break:break-all;">{valor}</div>
        </div>
        """
        
        kpi_col1.markdown(html_card.format(cor="#1f497d", titulo="Total Empenhado", valor=val_empenhado), unsafe_allow_html=True)
        kpi_col2.markdown(html_card.format(cor="#00b050", titulo="Total Pago", valor=val_pago), unsafe_allow_html=True)
        kpi_col3.markdown(html_card.format(cor="#ed7d31", titulo="Execução Financeira", valor=val_taxa), unsafe_allow_html=True)

    st.markdown("<hr style='margin: 1.5rem 0; border: 0; border-top: 1px solid #e1e4e8;'>", unsafe_allow_html=True)

    # Segunda Linha: Gráfico de Distribuição (Esquerda) e Análise Histórica (Direita)
    col_chart_left, col_chart_right = st.columns([7, 5])

    with col_chart_left:
        st.markdown(f'<div class="chart-title">Distribuição por {nivel_selecionado}</div>', unsafe_allow_html=True)
        
        if df_filtrado.empty:
            st.info("Nenhum dado encontrado para os filtros selecionados.")
        else:
            df_grafico = df_filtrado.melt(
                id_vars=["Conta"],
                value_vars=["Despesas_Empenhadas", "Despesas_Pagas"],
                var_name="Estágio",
                value_name="Valor"
            )
            df_grafico["Estágio"] = df_grafico["Estágio"].str.replace("_", " ")
            
            fig = px.bar(
                df_grafico,
                y="Conta",
                x="Valor",
                color="Estágio",
                barmode="group",
                orientation="h",
                color_discrete_map={"Despesas Empenhadas": "#1f497d", "Despesas Pagas": "#ed7d31"},
                labels={"Conta": nivel_selecionado, "Valor": "Valor (R$)"},
                height=500
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(gridcolor="#e9ecef"),
                yaxis=dict(categoryorder="total ascending", gridcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_chart_right:
        st.markdown('<div class="chart-title">Evolução Histórica da Execução Orçamentária</div>', unsafe_allow_html=True)
        
        # Filtra os dados históricos do município (2020 a 2024 para evitar distorção de 2025)
        dados_historicos = dados[
            (dados["Capital_Limpa"] == capital_selecionada) & 
            (dados["Nivel"] == nivel_selecionado) &
            (dados["ano"] < 2025)
        ]
        
        if dados_historicos.empty:
            st.info("Dados históricos insuficientes para esta seleção.")
        else:
            # Agrupa os valores anuais do município
            df_evolucao_cap = dados_historicos.groupby("ano")[["Despesas_Empenhadas", "Despesas_Pagas"]].sum().reset_index()
            df_evolucao_cap["Taxa_Municipio"] = (df_evolucao_cap["Despesas_Pagas"] / df_evolucao_cap["Despesas_Empenhadas"] * 100)
            
            # Calcula a média nacional das capitais no mesmo período
            dados_nacionais = dados[(dados["Nivel"] == nivel_selecionado) & (dados["ano"] < 2025)]
            df_evolucao_nac = dados_nacionais.groupby("ano")[["Despesas_Empenhadas", "Despesas_Pagas"]].sum().reset_index()
            df_evolucao_nac["Taxa_Media_Nacional"] = (df_evolucao_nac["Despesas_Pagas"] / df_evolucao_nac["Despesas_Empenhadas"] * 100)
            
            # Consolida dados históricos
            df_historico_final = df_evolucao_cap.merge(df_evolucao_nac[["ano", "Taxa_Media_Nacional"]], on="ano")
            
            fig_linha = px.line(
                df_historico_final,
                x="ano",
                y=["Taxa_Municipio", "Taxa_Media_Nacional"],
                labels={"ano": "Ano", "value": "Taxa de Execução (%)", "variable": "Legenda"},
                color_discrete_map={"Taxa_Municipio": "#1f497d", "Taxa_Media_Nacional": "#ed7d31"},
                height=220
            )
            
            fig_linha.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(gridcolor="#e9ecef", tickmode="linear"),
                yaxis=dict(gridcolor="#e9ecef", range=[0, 110])
            )
            
            st.plotly_chart(fig_linha, use_container_width=True)

        # Tabela Detalhada com os dados orçamentários do exercício
        st.markdown(f'<div class="chart-title">Despesas Detalhadas ({ano_selecionado})</div>', unsafe_allow_html=True)
        if not df_filtrado.empty:
            df_tabela = df_filtrado[["Conta", "Despesas_Empenhadas", "Despesas_Pagas"]].copy()
            df_tabela.columns = [nivel_selecionado, "Empenhado (R$)", "Pago (R$)"]
            st.dataframe(df_tabela, use_container_width=True, hide_index=True, height=180)

if __name__ == "__main__":
    main()
