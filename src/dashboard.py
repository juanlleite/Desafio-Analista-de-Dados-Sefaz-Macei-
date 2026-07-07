import streamlit as st
import polars as pl
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Sefaz - Despesas Públicas", layout="wide")

def carregar_dados_gold():
    """Lê a base analítica caso ela já tenha sido gerada."""
    caminho_gold = Path("dados_processados/finbra_gold.parquet")
    if not caminho_gold.exists():
        return None
    return pl.read_parquet(caminho_gold).to_pandas()

def main():
    # Estilização do cabeçalho Padrão Sefaz
    st.markdown("""
        <div style="background-color:#1f497d;padding:15px;border-radius:5px;margin-bottom:20px;">
            <h2 style="color:white;margin:0;">📊 Secretaria Municipal de Fazenda | Execução Orçamentária</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    **Entendendo os números:**
    - **Empenho**: É a promessa de pagamento. O governo reserva o dinheiro para um serviço ou obra.
    - **Pagamento**: É quando o fornecedor entrega o serviço e o dinheiro efetivamente sai da conta do governo.
    - **Taxa de Execução**: O quanto das promessas já viraram pagamentos reais.
    """)
    
    dados = carregar_dados_gold()
    
    if dados is None or dados.empty:
        st.warning("⚠️ Base de dados não encontrada. Execute os passos de extração, transformação e análise antes de abrir o painel.")
        return
        
    st.sidebar.header("Filtros")
    anos_disponiveis = sorted(dados["ano"].unique().tolist(), reverse=True)
    # Define 2024 como ano padrão (dados de 2025 estão incompletos)
    idx_padrao = anos_disponiveis.index(2024) if 2024 in anos_disponiveis else 0
    ano_selecionado = st.sidebar.selectbox("Ano", anos_disponiveis, index=idx_padrao)
    
    if ano_selecionado == 2025:
        st.sidebar.warning("⚠️ Atenção: Os dados de 2025 ainda estão sendo consolidados pelos municípios (incompletos).")
    
    # Limpa o nome da instituição para melhorar a exibição na UI
    dados["Capital_Limpa"] = dados["Instituição"].str.replace(r"Prefeitura Municipal d[eo] ", "", regex=True)
    
    capitais_disponiveis = sorted(dados["Capital_Limpa"].unique().tolist())
    capital_selecionada = st.sidebar.selectbox("Capital", capitais_disponiveis)
    
    nivel_selecionado = st.sidebar.radio("Nível de Análise", ["Função", "Subfunção"])
    
    # Aplica os filtros
    df_filtrado = dados[
        (dados["ano"] == ano_selecionado) & 
        (dados["Capital_Limpa"] == capital_selecionada) &
        (dados["Nivel"] == nivel_selecionado)
    ]
    
    if df_filtrado.empty:
        st.info("Não há registros para os filtros selecionados.")
        return
        
    # Métricas Globais
    total_empenhado = df_filtrado["Despesas_Empenhadas"].sum()
    total_pago = df_filtrado["Despesas_Pagas"].sum()
    taxa_execucao = (total_pago / total_empenhado * 100) if total_empenhado > 0 else 0
    
    # Cartões de Métrica customizados (Estilo Sefaz Dataviz)
    html_card = """
    <div style="background-color:{cor};padding:20px;border-radius:5px;color:white;box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
        <h5 style="margin:0;color:white;">| {titulo}</h5>
        <h3 style="margin:0;color:white;padding-top:10px;">{valor}</h3>
    </div>
    """
    
    col1, col2, col3 = st.columns(3)
    val_empenhado = f"R$ {total_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    val_pago = f"R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    val_taxa = f"{taxa_execucao:.1f}%"
    
    # Cores inspiradas no painel gerencial: Empenho (Azul), Pago (Verde), Taxa (Laranja)
    col1.markdown(html_card.format(cor="#1f497d", titulo="Total Empenhado", valor=val_empenhado), unsafe_allow_html=True)
    col2.markdown(html_card.format(cor="#00b050", titulo="Total Pago", valor=val_pago), unsafe_allow_html=True)
    col3.markdown(html_card.format(cor="#ed7d31", titulo="Taxa de Execução Geral", valor=val_taxa), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(f"Comparativo de {nivel_selecionado}s")
    
    # Preparação para o gráfico
    df_grafico = df_filtrado.melt(
        id_vars=["Conta"],
        value_vars=["Despesas_Empenhadas", "Despesas_Pagas"],
        var_name="Estágio",
        value_name="Valor"
    )
    
    # Limpa a nomenclatura das colunas para visualização
    df_grafico["Estágio"] = df_grafico["Estágio"].str.replace("_", " ")
    
    # Gráfico de barras horizontais (melhor leitura para nomes extensos)
    fig = px.bar(
        df_grafico,
        y="Conta",
        x="Valor",
        color="Estágio",
        barmode="group",
        orientation="h",
        color_discrete_map={"Despesas Empenhadas": "#1f497d", "Despesas Pagas": "#ed7d31"},
        labels={"Conta": nivel_selecionado, "Valor": "Valor (R$)"},
        height=600
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
