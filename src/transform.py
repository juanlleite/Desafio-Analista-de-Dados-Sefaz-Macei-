import polars as pl
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def processar_dados(caminho_raw: str, caminho_saida: str) -> None:
    """Processa e limpa os arquivos CSV extraídos, gerando um Parquet."""
    path_raw = Path(caminho_raw)
    
    arquivos_csv = list(path_raw.glob("*.csv"))
    if not arquivos_csv:
        logging.warning("Nenhum arquivo CSV encontrado para processamento.")
        return

    frames = []
    for arquivo in arquivos_csv:
        # Extrai o ano do nome do arquivo (ex: finbra_2020.csv -> 2020)
        ano = int(arquivo.stem.split("_")[-1])
        
        df_lazy = pl.read_csv(
            str(arquivo),
            separator=';',
            encoding='ISO-8859-1',
            skip_rows=3,
            ignore_errors=True
        ).lazy()
        
        df_lazy = df_lazy.with_columns(
            pl.col("Valor").str.replace(",", ".").cast(pl.Float64),
            pl.lit(ano).alias("ano")
        )
        
        # Trata strings nulas e limpa a coluna Conta
        df_lazy = df_lazy.with_columns(
            pl.col(pl.Utf8).fill_null("")
        )
        
        # Filtra os totais agregados para evitar contagem dupla e ignora as rubricas FU
        df_lazy = df_lazy.filter(
            ~pl.col("Conta").is_in(["Despesas Exceto Intraorçamentárias", "Despesas Intraorçamentárias"]) &
            ~pl.col("Conta").str.contains(r"^FU.*")
        )
        
        frames.append(df_lazy)
    
    # Processamento lazy e concatenação vertical
    df_silver = pl.concat(frames, how="vertical").collect()
    
    caminho_output = Path(caminho_saida)
    caminho_output.parent.mkdir(parents=True, exist_ok=True)
    
    df_silver.write_parquet(caminho_output, compression="snappy")
    logging.info(f"Silver layer salva com sucesso: {caminho_output}")

if __name__ == "__main__":
    processar_dados("dados_processados/raw", "dados_processados/finbra_silver.parquet")
