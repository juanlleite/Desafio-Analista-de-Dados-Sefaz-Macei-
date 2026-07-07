import streamlit as st
import polars as pl
import pandas as pd
import plotly.express as px
from pathlib import Path
from typing import Optional

# Configuração da página com barra lateral oculta por padrão
st.set_page_config(
    page_title="Secretaria de Fazenda | Execução Orçamentária", 
    layout="wide", 
    initial_sidebar_state="collapsed"
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
    # Injeção de CSS para customização estética institucional
    st.markdown("""
        <style>
        .stApp {
            background-color: #f8f9fa;
        }
        h1, h2, h3, h4, h5, h6, p {
            color: #212529 !important;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        /* Oculta os menus do Streamlit em inglês para manter o white-label */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Estilização dos títulos de seções */
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

    # Introdução de Abas (Visão Individual vs Comparativo entre Cidades)
    tab_individual, tab_comparativo = st.tabs(["📊 Visão por Capital", "🌍 Comparativo entre Capitais"])

    # ==================== ABA 1: VISÃO INDIVIDUAL ====================
    with tab_individual:
        # Filtros (Esquerda) e Métricas (Direita)
        col_filtros, col_kpis = st.columns([5, 7])

        with col_filtros:
            st.markdown('<div class="chart-title">Filtros de Consulta</div>', unsafe_allow_html=True)
            f_col1, f_col2, f_col3 = st.columns(3)
            
            anos_disponiveis = sorted(dados["ano"].unique().tolist(), reverse=True)
            idx_padrao = anos_disponiveis.index(2024) if 2024 in anos_disponiveis else 0
            
            with f_col1:
                ano_selecionado = st.selectbox("Exercício", anos_disponiveis, index=idx_padrao, key="sel_ano_ind")
            with f_col2:
                dados_ano = dados[dados["ano"] == ano_selecionado]
                capitais_disponiveis = sorted(dados_ano["Capital_Limpa"].unique().tolist())
                capital_selecionada = st.selectbox("Capital", capitais_disponiveis, key="sel_cap_ind")
            with f_col3:
                nivel_selecionado = st.selectbox("Nível", ["Função", "Subfunção"], key="sel_niv_ind")

        # Filtragem dos dados conforme seleção
        df_filtrado = dados[
            (dados["ano"] == ano_selecionado) & 
            (dados["Capital_Limpa"] == capital_selecionada) &
            (dados["Nivel"] == nivel_selecionado)
        ]

        # Alerta de dados parciais
        if ano_selecionado == 2025:
            st.warning("⚠️ **Aviso:** Os dados do exercício de 2025 ainda estão em fase de consolidação e podem estar incompletos.")

        # Tradutor de Negócio para Leigos (Data Literacy)
        with st.expander("ℹ️ Como interpretar as despesas públicas? (Clique para expandir)", expanded=False):
            st.markdown("""
            **Dicionário Orçamentário Simplificado:**
            - **Despesas Empenhadas**: É a reserva de dinheiro. O município assume o compromisso de pagar um fornecedor por um serviço contratado.
            - **Despesas Pagas**: É a saída real de caixa. Ocorre após o serviço ser entregue e atestado pelo órgão público.
            - **Restos a Pagar**: A diferença (espaço) entre o Empenhado e o Pago representa despesas contratadas no ano que ficaram pendentes para pagamento nos anos seguintes.
            - **Taxa de Execução**: Percentual das promessas (empenho) que efetivamente viraram pagamentos dentro do mesmo ano civil.
            """)

        # Subtítulo Dinâmico para Contextualização
        st.subheader(f"📋 Panorama de Execução Financeira — {capital_selecionada} ({ano_selecionado})")

        # Cálculo das Métricas Globais
        total_empenhado = df_filtrado["Despesas_Empenhadas"].sum() if not df_filtrado.empty else 0
        total_pago = df_filtrado["Despesas_Pagas"].sum() if not df_filtrado.empty else 0
        taxa_execucao = (total_pago / total_empenhado * 100) if total_empenhado > 0 else 0

        with col_kpis:
            st.markdown('<div class="chart-title">Indicadores Gerais</div>', unsafe_allow_html=True)
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            
            val_empenhado = formatar_brl(total_empenhado)
            val_pago = formatar_brl(total_pago)
            val_taxa = f"{taxa_execucao:.1f}%"
            
            html_card = """
            <div style="background-color:{cor}; padding:12px 15px; border-radius:6px; color:white; min-height:85px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; color:rgba(255,255,255,0.85); margin:0;">| {titulo}</div>
                <div style="font-size:1.15rem; font-weight:700; color:white; margin-top:5px; word-break:break-all;">{valor}</div>
            </div>
            """
            
            kpi_col1.markdown(html_card.format(cor="#1f497d", titulo="Total Empenhado", valor=val_empenhado), unsafe_allow_html=True)
            kpi_col2.markdown(html_card.format(cor="#00b050", titulo="Total Pago", valor=val_pago), unsafe_allow_html=True)
            kpi_col3.markdown(html_card.format(cor="#ed7d31", titulo="Eficiência de Execução", valor=val_taxa), unsafe_allow_html=True)

        st.markdown("<hr style='margin: 1.5rem 0; border: 0; border-top: 1px solid #e1e4e8;'>", unsafe_allow_html=True)

        # Gráfico de Distribuição e Análise Histórica
        col_chart_left, col_chart_right = st.columns([7, 5])

        with col_chart_left:
            st.markdown(f'<div class="chart-title">Distribuição Orçamentária por Área</div>', unsafe_allow_html=True)
            
            if df_filtrado.empty:
                st.info("Nenhum dado encontrado para os filtros selecionados.")
            else:
                # Ordena o DataFrame ascendente para que o Plotly renderize os maiores valores no topo da barra horizontal
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
                    height=500
                )
                
                # Formatação rica do Tooltip
                fig.update_traces(
                    hovertemplate="<b>%{y}</b><br>%{customdata[1]}: <b>%{customdata[0]}</b><extra></extra>"
                )
                
                fig.update_layout(
                    font=dict(color="#212529", family="Segoe UI, sans-serif"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=10, b=10),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.02, 
                        xanchor="right", 
                        x=1,
                        font=dict(color="#212529")
                    ),
                    xaxis=dict(gridcolor="#e9ecef", tickfont=dict(color="#212529")),
                    yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#212529"))
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_chart_right:
            st.markdown('<div class="chart-title">Evolução da Execução Orçamentária</div>', unsafe_allow_html=True)
            
            dados_historicos = dados[
                (dados["Capital_Limpa"] == capital_selecionada) & 
                (dados["Nivel"] == nivel_selecionado) &
                (dados["ano"] < 2025)
            ]
            
            if dados_historicos.empty:
                st.info("Dados históricos insuficientes para esta seleção.")
            else:
                df_evolucao_cap = dados_historicos.groupby("ano")[["Despesas_Empenhadas", "Despesas_Pagas"]].sum().reset_index()
                df_evolucao_cap["Taxa_Municipio"] = (df_evolucao_cap["Despesas_Pagas"] / df_evolucao_cap["Despesas_Empenhadas"] * 100)
                
                dados_nacionais = dados[(dados["Nivel"] == nivel_selecionado) & (dados["ano"] < 2025)]
                df_evolucao_nac = dados_nacionais.groupby("ano")[["Despesas_Empenhadas", "Despesas_Pagas"]].sum().reset_index()
                df_evolucao_nac["Taxa_Media_Nacional"] = (df_evolucao_nac["Despesas_Pagas"] / df_evolucao_nac["Despesas_Empenhadas"] * 100)
                
                df_historico_final = df_evolucao_cap.merge(df_evolucao_nac[["ano", "Taxa_Media_Nacional"]], on="ano")
                df_historico_final = df_historico_final.rename(columns={
                    "Taxa_Municipio": "Taxa do Município",
                    "Taxa_Media_Nacional": "Média Nacional"
                })
                
                fig_linha = px.line(
                    df_historico_final,
                    x="ano",
                    y=["Taxa do Município", "Média Nacional"],
                    labels={"ano": "Ano", "value": "Taxa de Execução (%)", "variable": "Legenda"},
                    color_discrete_map={"Taxa do Município": "#1f497d", "Média Nacional": "#ed7d31"},
                    height=220
                )
                
                fig_linha.update_layout(
                    font=dict(color="#212529", family="Segoe UI, sans-serif"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=10, b=10),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.02, 
                        xanchor="right", 
                        x=1,
                        font=dict(color="#212529")
                    ),
                    xaxis=dict(gridcolor="#e9ecef", tickmode="linear", tickfont=dict(color="#212529")),
                    yaxis=dict(gridcolor="#e9ecef", range=[0, 110], tickfont=dict(color="#212529"))
                )
                st.plotly_chart(fig_linha, use_container_width=True)

            # Tabela Detalhada com os dados orçamentários do exercício
            st.markdown(f'<div class="chart-title">Despesas Detalhadas ({ano_selecionado})</div>', unsafe_allow_html=True)
            if not df_filtrado.empty:
                df_tabela = df_filtrado[["Conta", "Despesas_Empenhadas", "Despesas_Pagas"]].copy()
                df_tabela.columns = [nivel_selecionado, "Empenhado (R$)", "Pago (R$)"]
                df_tabela["Empenhado (R$)"] = df_tabela["Empenhado (R$)"].map(formatar_brl)
                df_tabela["Pago (R$)"] = df_tabela["Pago (R$)"].map(formatar_brl)
                st.dataframe(df_tabela, use_container_width=True, hide_index=True, height=180)

    # ==================== ABA 2: COMPARATIVO GERAL ====================
    with tab_comparativo:
        st.markdown('<div class="chart-title">Comparação entre Capitais</div>', unsafe_allow_html=True)
        
        comp_col1, comp_col2, comp_col3 = st.columns(3)
        
        with comp_col1:
            ano_comp = st.selectbox("Exercício", anos_disponiveis, index=idx_padrao, key="sel_ano_comp")
        with comp_col2:
            nivel_comp = st.selectbox("Nível", ["Função", "Subfunção"], key="sel_niv_comp")
        with comp_col3:
            # Popula com as contas disponíveis para o nível
            contas_disponiveis = sorted(dados[dados["Nivel"] == nivel_comp]["Conta"].unique().tolist())
            conta_selecionada = st.selectbox("Área / Rubrica", contas_disponiveis, key="sel_cnt_comp")

        # Filtra os dados de todas as capitais para a área e ano selecionados
        df_comp = dados[
            (dados["ano"] == ano_comp) & 
            (dados["Nivel"] == nivel_comp) &
            (dados["Conta"] == conta_selecionada)
        ].copy()

        if df_comp.empty:
            st.info("Nenhum registro encontrado para comparação com os filtros selecionados.")
        else:
            # Calcula a taxa de execução de cada capital
            df_comp["Taxa_Execucao"] = (df_comp["Despesas_Pagas"] / df_comp["Despesas_Empenhadas"] * 100)
            df_comp = df_comp.sort_values(by="Taxa_Execucao", ascending=True) # Ascendente para barra horizontal Plotly

            # Formata valores para exibir nos tooltips
            df_comp["Empenhado_Formatado"] = df_comp["Despesas_Empenhadas"].map(formatar_brl)
            df_comp["Pago_Formatado"] = df_comp["Despesas_Pagas"].map(formatar_brl)
            df_comp["Taxa_Formatada"] = df_comp["Taxa_Execucao"].map(lambda x: f"{x:.1f}%")

            # Mapeia cores: Destaca a capital que foi selecionada na Aba 1 em rosa contrastante (#e61174), as demais em azul neutro
            cores = ["#e61174" if cap == capital_selecionada else "#b0c4de" for cap in df_comp["Capital_Limpa"]]

            fig_comp = px.bar(
                df_comp,
                y="Capital_Limpa",
                x="Taxa_Execucao",
                orientation="h",
                labels={"Capital_Limpa": "Capital", "Taxa_Execucao": "Taxa de Execução (%)"},
                custom_data=["Taxa_Formatada", "Empenhado_Formatado", "Pago_Formatado"],
                height=650
            )

            # Define as cores customizadas e formata tooltips
            fig_comp.update_traces(
                marker_color=cores,
                hovertemplate="<b>%{y}</b><br>Taxa de Execução: <b>%{customdata[0]}</b><br>Empenhado: %{customdata[1]}<br>Pago: %{customdata[2]}<extra></extra>"
            )

            fig_comp.update_layout(
                font=dict(color="#212529", family="Segoe UI, sans-serif"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=10, b=10),
                xaxis=dict(gridcolor="#e9ecef", tickfont=dict(color="#212529"), title="Taxa de Execução (%)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#212529"))
            )

            st.subheader(f"📈 Eficiência Orçamentária das Capitais em {conta_selecionada} ({ano_comp})")
            st.markdown(f"*(A capital selecionada na Aba 1, **{capital_selecionada}**, está destacada em **rosa** no gráfico abaixo)*")
            st.plotly_chart(fig_comp, use_container_width=True)

if __name__ == "__main__":
    main()
