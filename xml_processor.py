from concurrent.futures import ProcessPoolExecutor
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from logger import logger

class XMLProcessor:
    def __init__(self, pasta_xml, fornecedores_bloqueados=None):
        self.pasta_xml = pasta_xml
        self.fornecedores_bloqueados = fornecedores_bloqueados or []

    def processar_todos(self, paralelo=True):
        arquivos = self._listar_arquivos_xml()

        if paralelo:

            with ProcessPoolExecutor() as executor:
                resultados = list(executor.map(self._processar_arquivo, arquivos))
        else:
            resultados = [self._processar_arquivo(a) for a in arquivos]


        produtos = [p for lista in resultados for p in lista]
        return produtos


    def _listar_arquivos_xml(self):
        return [
            os.path.join(self.pasta_xml, nome)
            for nome in os.listdir(self.pasta_xml)
            if nome.lower().endswith(".xml")
        ]


    def _processar_arquivo(self, caminho_arquivo):

        try:
            tree = ET.parse(caminho_arquivo)
            root = tree.getroot()
            ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}

            cnpj_emitente = root.find(".//ns:emit/ns:CNPJ", ns)
            if cnpj_emitente is None:
                print(f"⚠️ CNPJ não encontrado em {caminho_arquivo}")
                return []

            produtos = self._extrair_dados(root, ns)
            return produtos

        except Exception as e:
            print(f"Erro ao processar {caminho_arquivo}: {e}")
            return []
        

    def _extrair_dados(self, root, ns):
        produtos = []

        data_str = root.find(".//ns:ide/ns:dhEmi", ns).text
        data_emissao = datetime.fromisoformat(data_str).replace(tzinfo=None)

        natOp = root.find(".//ns:ide/ns:natOp", ns)
        if natOp is not None and natOp.text.strip().upper() == 'BONIFICACAO, DOACAO OU BRINDE':
            return [] 

        for det in root.findall(".//ns:det", ns):   
            produto = {}

            temp_codigo = det.find("./ns:prod/ns:cProd", ns).text
            if "-" not in temp_codigo:
                produto['Codigo Produto'] = temp_codigo
            produto['Descrição'] = det.find("./ns:prod/ns:xProd", ns).text
            produto['Valor_unitário'] = det.find("./ns:prod/ns:vUnCom", ns).text
            cEAN = det.find("./ns:prod/ns:cEAN", ns).text 
            produto['Código de Barras'] = cEAN
            produto['Sku'] = cEAN
            if produto['Sku'] == 'SEM GTIN':
                produto['Sku'] = produto['Descrição']
            produto['Fornecedor'] = root.find(".//ns:emit/ns:xNome", ns).text
            produto['Data Emissão'] = data_emissao
            produto['NCM'] = det.find("./ns:prod/ns:NCM", ns).text
            logger.info(produto)

            produtos.append(produto)
        return produtos
