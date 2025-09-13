import pandas as pd


class NotasManager:
    def __init__(self,produtos):
        self.produtos = pd.DataFrame(produtos)

    def filtra_fornecedor(self, fornecedores_pesado):
        self.produtos = self.produtos[~self.produtos['Fornecedor'].isin(self.fornecedores_pesados)]


    def organizar_dataframe(self):
        self.produtos = pd.DataFrame(self.todos_produtos)
        self.produtos = self.produtos.sort_values(by="Data Emissão", ascending=False)
        self.produtos = self.produtos.drop_duplicates(subset='Codigo Produto', keep='first')
        
    def salvar_excel(self, nome):
        self.produtos.to_excel(nome, index=False)
        self.logger.info(f"📁 Arquivo {nome} gerado com sucesso!")

