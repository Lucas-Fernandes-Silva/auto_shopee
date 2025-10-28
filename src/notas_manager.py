import pandas as pd
import shutil
import os



class NotasManager:
    def __init__(self, fornecedores=None):
        self.fornecedores = fornecedores or []

    
    def cria_dataframe(self, lista_produtos):
        df = pd.DataFrame(lista_produtos)


        if 'Fornecedor' in df.columns:
            df = df[~df['Fornecedor'].isin(self.fornecedores[0])]


        if 'Data Emissão' in df.columns:
            df = df.sort_values(by='Data Emissão', ascending=False)


        if 'Codigo Produto' in df.columns:
            df = df.drop_duplicates(subset='Codigo Produto', keep='first')

        return df
    
    def copiar_xmls(self, pasta_origem, pasta_destino):

            os.makedirs(pasta_destino, exist_ok=True)
            for arquivo in os.listdir(pasta_origem):
                if arquivo.lower().endswith(".xml"):
                    shutil.copy(os.path.join(pasta_origem, arquivo), pasta_destino)


    def salvar_excel(self, df_produtos):
        df_produtos.to_excel('produtos.xlsx', index=False)
