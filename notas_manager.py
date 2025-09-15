import pandas as pd
import shutil, os
from logger import logger


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

    def separando_fornecedor(self, df, fornecedores):
        web = df.query(f'Fornecedor == {fornecedores[1]}')
        noweb = df.query(f'Fornecedor == {fornecedores[2]}')
        
        return {"web":web, "noweb":noweb}
    
    def salvar_excel(self,separado, caminho):
        for i in separado:
            separado[i].to_excel(f'{i}.xlsx', index=False)
            print(f"📁 Arquivo {i} gerado com sucesso!")

    def copiar_xmls(self, pasta_origem, pasta_destino):

            os.makedirs(pasta_destino, exist_ok=True)
            for arquivo in os.listdir(pasta_origem):
                if arquivo.lower().endswith(".xml"):
                    shutil.copy(os.path.join(pasta_origem, arquivo), pasta_destino)


