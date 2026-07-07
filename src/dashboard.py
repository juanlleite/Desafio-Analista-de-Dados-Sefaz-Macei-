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
    st.title("📊 Painel de Execução Orçamentária das Capitais")
    
    st.markdown("""
    **Entendendo os números:**
    - **Empenho**: É a promessa de pagamento. O governo reserva o dinheiro para um serviço ou obra.
    - **Pagamento**: É quando o fornecedor entrega o serviço e o dinheiro efetivamente sai da conta do governo.
    - **Taxa de Execução**: O quanto das promessas já viraram pagamentos reais. Uma taxa muito baixa pode indicar atrasos.
    """)
    
    dados = carregar_dados_gold()
    
    if dados is None or dados.empty:
        st.warning("⚠️ Base de dados não encontrada. Execute os passos de extração, transformação e análise antes de abrir o painel.")
        return
        
    st.sidebar.header("Filtros")
    anos_disponiveis = sorted(dados["ano"].unique().tolist(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Ano", anos_disponiveis)
    
    capitais_disponiveis = sorted(dados["Instituição"].unique().tolist())
    capital_selecionada = st.sidebar.selectbox("Capital", capitais_disponiveis)
    
    # Aplica os filtros
    df_filtrado = dados[(dados["ano"] == ano_selecionado) & (dados["Instituição"] == capital_selecionada)]
    
    if df_filtrado.empty:
        st.info("Não há registros para os filtros selecionados.")
        return
        
    # Métricas Globais
    total_empenhado = df_filtrado["Despesas_Empenhadas"].sum()
    total_pago = df_filtrado["Despesas_Pagas"].sum()
    taxa_execucao = (total_pago / total_empenhado * 100) if total_empenhado > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Empenhado", f"R$ {total_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col2.metric("Total Pago", f"R$ {total_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Taxa de Execução", f"{taxa_execucao:.1f}%")
    
    st.divider()
    st.subheader("Comparativo por Função (Grupos Funcionais)")
    
    # Preparação para o gráfico
    df_grafico = df_filtrado.melt(
        id_vars=["Grupo_Funcional"],
        value_vars=["Despesas_Empenhadas", "Despesas_Pagas"],
        var_name="Estágio",
        value_name="Valor"
    )
    
    # Limpa a nomenclatura das colunas para visualização
    df_grafico["Estágio"] = df_grafico["Estágio"].str.replace("_", " ")
    
    fig = px.bar(
        df_grafico,
        x="Grupo_Funcional",
        y="Valor",
        color="Estágio",
        barmode="group",
        labels={"Grupo_Funcional": "Função Governamental", "Valor": "Valor (R$)"},
        title=f"Despesas Empenhadas vs Pagas em {ano_selecionado}"
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
