import duckdb
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def gerar_base_analitica(caminho_silver: str, caminho_gold: str) -> None:
    """Calcula taxas de execução orçamentária por função usando DuckDB."""
    silver_path = Path(caminho_silver)
    gold_path = Path(caminho_gold)
    
    # Valida a existência do arquivo silver
    if not silver_path.exists():
        logging.error(f"Arquivo Silver não encontrado: {silver_path}. Execute o pipeline anterior.")
        return
        
    gold_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extrai os 2 primeiros caracteres (Função), pivota e calcula a taxa de execução
    query = f"""
    COPY (
        WITH base AS (
            SELECT 
                Instituição,
                "Cod.IBGE" AS Cod_IBGE,
                UF,
                População,
                substring(Conta, 1, 2) AS Grupo_Funcional,
                ano,
                Coluna,
                Valor
            FROM read_parquet('{silver_path}')
        ),
        pivotada AS (
            PIVOT base
            ON Coluna IN ('Despesas Empenhadas', 'Despesas Pagas')
            USING SUM(Valor)
            GROUP BY Instituição, Cod_IBGE, UF, População, Grupo_Funcional, ano
        )
        SELECT 
            Instituição,
            Cod_IBGE,
            UF,
            População,
            Grupo_Funcional,
            ano,
            COALESCE("Despesas Empenhadas", 0) AS Despesas_Empenhadas,
            COALESCE("Despesas Pagas", 0) AS Despesas_Pagas,
            (COALESCE("Despesas Pagas", 0) / NULLIF(COALESCE("Despesas Empenhadas", 0), 0)) * 100 AS Taxa_de_Execucao
        FROM pivotada
    ) TO '{gold_path}' (FORMAT PARQUET, COMPRESSION 'SNAPPY');
    """
    
    try:
        duckdb.sql(query)
        logging.info(f"Base analítica Gold gerada com sucesso: {gold_path}")
    except Exception as e:
        logging.error(f"Erro ao gerar a base Gold com DuckDB: {e}")

if __name__ == "__main__":
    gerar_base_analitica(
        "dados_processados/finbra_silver.parquet",
        "dados_processados/finbra_gold.parquet"
    )
