import os
import xml.etree.ElementTree as ET
import csv
import re
import pandas as pd


def extrair_fornecedores(pasta_origem):
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    fornecedores = []

    for arquivo in os.listdir(pasta_origem):
        if arquivo.lower().endswith(".xml"):
            caminho_arquivo = os.path.join(pasta_origem, arquivo)
            try:
                tree = ET.parse(caminho_arquivo)
                root = tree.getroot()

                emitente = root.find('.//nfe:emit', ns)
                if emitente is not None:
                    fornecedor = {
                        'CNPJ': emitente.findtext('nfe:CNPJ', default='', namespaces=ns),
                        'RazaoSocial': emitente.findtext('nfe:xNome', default='', namespaces=ns),
                        'NomeFantasia': emitente.findtext('nfe:xFant', default='', namespaces=ns),
                        'Logradouro': emitente.findtext('nfe:enderEmit/nfe:xLgr', default='', namespaces=ns),
                        'Numero': emitente.findtext('nfe:enderEmit/nfe:nro', default='', namespaces=ns),
                        'Bairro': emitente.findtext('nfe:enderEmit/nfe:xBairro', default='', namespaces=ns),
                        'Municipio': emitente.findtext('nfe:enderEmit/nfe:xMun', default='', namespaces=ns),
                        'UF': emitente.findtext('nfe:enderEmit/nfe:UF', default='', namespaces=ns),
                        'CEP': emitente.findtext('nfe:enderEmit/nfe:CEP', default='', namespaces=ns),
                        'Telefone': emitente.findtext('nfe:enderEmit/nfe:fone', default='', namespaces=ns),
                        'IE': emitente.findtext('nfe:IE', default='', namespaces=ns),
                    }

                    # Verifica se o fornecedor já existe na lista (pelo CNPJ)
                    if not any(f['RazaoSocial'] == fornecedor['RazaoSocial'] for f in fornecedores):
                        fornecedores.append(fornecedor)

            except ET.ParseError:
                print(f"Erro ao ler o XML: {arquivo}")
            except Exception as e:
                print(f"Erro inesperado em {arquivo}: {e}")

    return fornecedores


if __name__ == "__main__":
    pasta_origem = "notas/nfes/"
    dados_fornecedores = extrair_fornecedores(pasta_origem)

df = pd.DataFrame(dados_fornecedores)


colunas_bling = pd.read_csv('fornecedores.csv', sep=';').columns.tolist()

arquivo_csv = "contatos_bling_completo.csv"

def normalizar_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)

def formatar_cnpj(cnpj):
    cnpj_n = normalizar_cnpj(cnpj)
    return f"{cnpj_n[:2]}.{cnpj_n[2:5]}.{cnpj_n[5:8]}/{cnpj_n[8:12]}-{cnpj_n[12:]}"

def criar_linha(item, colunas_bling):
    linha = {col: "" for col in colunas_bling}

    cnpj_formatado = formatar_cnpj(item.get("CNPJ", ""))

    mapa = {
        "Nome": item.get("RazaoSocial", ""),
        "Fantasia": item.get("NomeFantasia", ""),
        "Endereço": item.get("Logradouro", ""),
        "Número": item.get("Numero", ""),
        "Bairro": item.get("Bairro", ""),
        "CEP": item.get("CEP", ""),
        "Cidade": item.get("Municipio", ""),
        "UF": item.get("UF", ""),
        "Fone": item.get("Telefone", ""),
        "Tipo pessoa": "Pessoa Jurídica",
        "CNPJ / CPF": cnpj_formatado,
        "IE / RG": item.get("IE", ""),
        "IE isento": "N",
        "Situação": "Ativo",
        "Vendedor": item.get("NomeFantasia", "") or item.get("RazaoSocial"),
        "Tipo contato": "Fornecedor",
    }

    linha.update(mapa)
    return linha


linhas_bling = [criar_linha(row, colunas_bling) for _, row in df.iterrows()]
bling_df = pd.DataFrame(linhas_bling, columns=colunas_bling)
bling_df.to_csv("fornecedores_bling.csv", sep=";", index=False, encoding="utf-8-sig")

