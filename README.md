# Painel de Execução Orçamentária | Sefaz Maceió

Este projeto faz parte do Desafio Técnico para Analista de Dados da Sefaz Maceió. Ele automatiza a extração, transformação, carga e visualização de dados do **Siconfi** referentes às despesas das 26 capitais brasileiras (2020 a 2025).

A solução foi projetada pensando em alta performance e clareza de negócio, resolvendo inconsistências dos dados brutos e utilizando uma paleta de cores institucional.

## 🚀 Tecnologias Utilizadas
- **Polars**: Para processamento e limpeza dos dados brutos em massa de forma muito rápida (*lazy evaluation*).
- **DuckDB**: Como motor SQL analítico direto em cima de arquivos Parquet, poupando memória RAM.
- **Streamlit**: Para prototipação ágil do Dashboard Gerencial.
- **Plotly**: Para gráficos responsivos e visualmente atraentes.

## ⚙️ Como Instalar e Rodar o Projeto

### Pré-requisitos
Ter o [Python 3.10+](https://www.python.org/downloads/) instalado na sua máquina. (Recomendamos 3.12).

### 1. Preparando o Ambiente
No seu terminal, clone o repositório e crie um ambiente virtual:
```bash
# Crie um ambiente virtual (recomendado)
python -m venv .venv

# Ative o ambiente virtual
# No Windows:
.venv\Scripts\activate
# No Linux/Mac:
source .venv/bin/activate

# Instale as dependências com versões travadas
pip install -r requirements.txt
```

### 2. Executando o Pipeline de Dados
Antes de visualizar o painel, você precisa descompactar os dados brutos e prepará-los. O pipeline foi dividido em scripts modulares:

```bash
# 1. Extrai os arquivos .csv dos .zip compactados
python src/extract.py

# 2. Limpa os dados, formata tipos e categoriza (Função/Subfunção) gerando a camada Silver
python src/transform.py

# 3. Calcula as métricas de Execução via SQL, criando a camada Gold
python src/analyze.py
```
> Obs: Os arquivos pesados Parquet resultantes não são versionados para não sobrecarregar o git. A geração deles dura poucos segundos ao rodar os scripts acima.

### 3. Abrindo o Dashboard
Com o `finbra_gold.parquet` gerado, basta rodar o servidor do Streamlit:
```bash
streamlit run src/dashboard.py
```
Uma página abrirá automaticamente no seu navegador. 

## 💡 Destaques da Solução
- **Tratamento de Contagem Dupla**: Foi implementada uma lógica de regex no `transform.py` para separar rigorosamente "Funções" de "Subfunções", garantindo que a soma dos agrupamentos seja exata.
- **Aviso de Dados Incompletos (2025)**: Conforme nota do projeto, a seleção padrão é 2024. Se o gestor selecionar 2025, um aviso de "dados incompletos" saltará na tela.
- **UI/UX Focado no Gestor**: As métricas superiores adotam as cores clássicas de controle orçamentário (Verde para sucesso de Pagamento, Azul para Empenho e Laranja para a Taxa).
