import datetime
import xml.etree.ElementTree as ET
import os 
import shutil
from processo import ProcessadorNotas

class XMLProcessor:
       def __init__(self, pasta_notas):
           self.pasta_notas = pasta_notas
           
       def extrai_dados(self, caminho_arquivo):
        produtos = []
        tree = ET.parse(caminho_arquivo)
        root = tree.getroot()
        ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
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
            produto['Código de Barras'] = det.find("./ns:prod/ns:cEAN", ns).text 
            produto['Sku'] = produto['Código de Barras']
            if produto['Sku'] == 'SEM GTIN':
                produto['Sku'] = produto['Descrição']
            produto['Fornecedor'] = root.find(".//ns:emit/ns:xNome", ns).text
            produto['Data Emissão'] = data_emissao
            produtos.append(produto)
        return produtos

def processar_xmls(self):
    ProcessadorNotas.logger.info("🔹 Processando XMLs da pasta…")
    for arquivo in os.listdir(self.save_folder):
        if arquivo.lower().endswith(".xml"):
            caminho_arquivo = os.path.join(self.save_folder, arquivo)
            try:
                tree = ET.parse(caminho_arquivo)
                root = tree.getroot()
                ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}

                cnpj_emitente = root.find(".//ns:emit/ns:CNPJ", ns)
                if cnpj_emitente is None:
                    self.logger.warning(f"CNPJ não encontrado em {arquivo}")
                    continue

                produtos_xml = self.extrai_dados(caminho_arquivo)
                ProcessadorNotas.todos_produtos.extend(produtos_xml)

                pasta_destino = os.path.join("notas/nfes")
                os.makedirs(pasta_destino, exist_ok=True)
                shutil.copy(caminho_arquivo, pasta_destino)

            except Exception as e:
                ProcessadorNotas.logger.error(f"{arquivo}: {e}")

