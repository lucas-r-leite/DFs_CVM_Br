from brfinance import CVMAsyncBackend
import pandas as pd
from datetime import datetime, date

cvm_httpclient = CVMAsyncBackend()

# Dict de códigos CVM para todas as empresas
cvm_codes = cvm_httpclient.get_cvm_codes()

# Dict de todas as categorias de busca disponíveis (Fato relevante, DFP, ITR, etc.)
categories = cvm_httpclient.get_consulta_externa_cvm_categories()

# Realizando busca por Empresa
ano = int(input("Qual o ano inicial para a pesquisa? "))
period = input("Você deseja buscar a partir do inicio o ano ou final?[inicio/final]")
if period=="inicio":
    start_date = date(ano, 1, 1)
elif period=="final":
    start_date = date(ano, 12, 31)
else:
    print("Entrada não reconhecida. Irei fazer a pesquisa pelo inicio do ano")
    start_date = date(ano, 1, 1)
end_dt = date.today()
cvm_codes_list = ['21067'] # Moura_Dubeux
category = ["EST_4"] # Códigos de categoria para DFP, ITR e fatos relevantes #, "EST_3", "IPE_4_-1_-1"
last_ref_date = False # Se "True" retorna apenas o último report no intervalo de datas

# Criar um dataframe vazio para armazenar os dados
df_concat = pd.DataFrame()

# Busca
search_result = cvm_httpclient.get_consulta_externa_cvm_results(
    cod_cvm=cvm_codes_list,
    start_date=start_date,
    end_date=end_dt,
    last_ref_date=last_ref_date,
    category=category
    )

# Filtrar dataframe de busca para DFP e Status Ativo
search_result = search_result[
    (search_result['categoria']=="DFP - Demonstrações Financeiras Padronizadas")]
search_result = search_result[search_result['status']=="Ativo"]
search_result = search_result[pd.to_numeric(search_result['numero_seq_documento'], errors='coerce').notnull()]

reports_list = [
    'Balanço Patrimonial Ativo',
    'Balanço Patrimonial Passivo',
    'Demonstração do Resultado',
    'Demonstração do Fluxo de Caixa'] # Se None retorna todos os demonstrativos disponíveis.

# Obter demonstrativos
for index, row in search_result.iterrows():
    empresa = f"{row['cod_cvm']} - {cvm_codes[row['cod_cvm']]}"

    reports = cvm_httpclient.get_report(row["numero_seq_documento"], row["codigo_tipo_instituicao"], reports_list=reports_list)

    for report in reports:
        print(report)
        reports[report]["cod_cvm"] = row["cod_cvm"]
        
        # Concatenar os dados de todos os anos em um único dataframe
        df_concat = pd.concat([df_concat, reports[report]], axis=0)


        # Salvar o dataframe no arquivo excel, repetindo as linhas das DFPs conforme os anos do filtro
df_concat.to_excel('Dados_CVM.xlsx', index=False)

# Criar pivot table
pivot_table = pd.pivot_table(df_concat, index=["Conta", "Descrição"], values=["Valor"], aggfunc=lambda x: "\n".join(str(i) for i in x))

# Salvar pivot table em um arquivo Excel
pivot_table.to_excel("pivot_table.xlsx")

# Carregar o arquivo pivot_table.xlsx em um DataFrame pandas
df_pivot = pd.read_excel('pivot_table.xlsx')

# Obter o número máximo de valores em uma única célula "Valor" em todo o DataFrame
max_values = int(df_pivot['Valor'].str.count('\n').max()) + 1
value_cols = [f'{i+ano}' for i in range(max_values)]
#ano = ano-max_values
#value_cols = [f'{ano+i}' for i in reversed(range(max_values))]
df_pivot[value_cols] = df_pivot['Valor'].str.split('\n', expand=True)

# Separar os valores da coluna "Valor" em colunas separadas
df_pivot[value_cols] = df_pivot['Valor'].str.split('\n', expand=True)

# Remover a coluna "Valor" original
df_pivot = df_pivot.drop(columns=['Valor'])

# Salvar o DataFrame atualizado em um arquivo Excel
df_pivot.to_excel('pivot_table_updated.xlsx', index=False)