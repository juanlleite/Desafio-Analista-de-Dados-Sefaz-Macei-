import zipfile
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def extrair_arquivos(origem: str, destino: str) -> None:
    """Extrai os arquivos finbra.csv dos zips e renomeia por ano."""
    caminho_origem = Path(origem)
    caminho_destino = Path(destino)
    
    # Garante que a pasta de destino exista
    caminho_destino.mkdir(parents=True, exist_ok=True)
    
    for arquivo_zip in caminho_origem.rglob("*.zip"):
        ano = arquivo_zip.parent.name
        
        try:
            with zipfile.ZipFile(arquivo_zip, "r") as zip_ref:
                # O Siconfi sempre entrega o arquivo interno como finbra.csv
                with zip_ref.open("finbra.csv") as source, \
                     open(caminho_destino / f"finbra_{ano}.csv", "wb") as target:
                    target.write(source.read())
            
            logging.info(f"Arquivo extraído com sucesso: finbra_{ano}.csv")
            
        except FileNotFoundError:
            logging.error(f"Arquivo zip não encontrado: {arquivo_zip}")
        except zipfile.BadZipFile:
            logging.error(f"Arquivo zip corrompido: {arquivo_zip}")
        except KeyError:
            logging.error(f"Arquivo finbra.csv não encontrado dentro do zip: {arquivo_zip}")

if __name__ == "__main__":
    extrair_arquivos("dados_compactos", "dados_processados/raw")
