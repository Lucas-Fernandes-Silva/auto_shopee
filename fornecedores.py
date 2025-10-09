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
                    if not any(f['CNPJ'] == fornecedor['CNPJ'] for f in fornecedores):
                        fornecedores.append(fornecedor)

            except ET.ParseError:
                print(f"Erro ao ler o XML: {arquivo}")
            except Exception as e:
                print(f"Erro inesperado em {arquivo}: {e}")

    return fornecedores


# Exemplo de uso
if __name__ == "__main__":
    pasta_origem = "notas/nfes/"  # coloque o caminho da pasta
    dados_fornecedores = extrair_fornecedores(pasta_origem)

    print(f"Foram encontrados {len(dados_fornecedores)} fornecedores únicos:\n")
    for f in dados_fornecedores:
        print(f)


df = pd.DataFrame(dados_fornecedores)
df.columns.tolist()

dados_fornecedores
colunas_bling = pd.read_csv('fornecedores.csv', sep=';').columns.tolist()


arquivo_csv = "contatos_bling_completo.csv"

def normalizar_cnpj(cnpj):
    return re.sub(r'\D', '', cnpj)

def formatar_cnpj(cnpj):
    cnpj_n = normalizar_cnpj(cnpj)
    return f"{cnpj_n[:2]}.{cnpj_n[2:5]}.{cnpj_n[5:8]}/{cnpj_n[8:12]}-{cnpj_n[12:]}"

def criar_linha(item):
    cnpj_formatado = formatar_cnpj(item.get("CNPJ", ""))
    return {
        "ID": "",
        "Código": "",
        "Nome": item.get("RazaoSocial", ""),
        "Fantasia": item.get("NomeFantasia", ""),
        "Endereço": item.get("Logradouro", ""),
        "Número": item.get("Numero", ""),
        "Complemento": "",
        "Bairro": item.get("Bairro", ""),
        "CEP": item.get("CEP", ""),
        "Cidade": item.get("Municipio", ""),
        "UF": item.get("UF", ""),
        "Contatos": "",
        "Fone": item.get("Telefone", ""),
        "Fax": "",
        "Celular": "",
        "E-mail": "",
        "Web Site": "",
        "Tipo pessoa": "Pessoa Jurídica",
        "CNPJ / CPF": cnpj_formatado,
        "IE / RG": item.get("IE", ""),
        "IE isento": "N",
        "Situação": "Ativo",
        "Observações": "",
        "Estado civil": "",
        "Profissão": "",
        "Sexo": "",
        "Data nascimento": "",
        "Naturalidade": "",
        "Nome pai": "",
        "CPF pai": "",
        "Nome mãe": "",
        "CPF mãe": "",
        "Segmento": "",
        "Vendedor": item.get("NomeFantasia", "") or item.get("RazaoSocial"),
        "Tipo contato": "Fornecedor",
        "E-mail para envio NFe": "",
        "Limite de crédito": "",
        "Cliente desde": "",
        "Próxima visita": "",
        "Condição de pagamento": "",
        "Regime tributário": ""
    }

# Carrega CSV existente
csv_existente = {}
if os.path.exists(arquivo_csv):
    with open(arquivo_csv, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cnpj_norm = normalizar_cnpj(row["CNPJ / CPF"])
            csv_existente[cnpj_norm] = row

# Adiciona ou atualiza
atualizados = 0
novos = 0

for item in dados_fornecedores: 
    cnpj_norm = normalizar_cnpj(item["CNPJ"])
    nova_linha = criar_linha(item)
    
    if cnpj_norm in csv_existente:
        linha_atual = csv_existente[cnpj_norm]
        mudou = False
        campos_verificar = ["Nome", "Fantasia", "Endereço", "Número", "Bairro", "CEP", "Cidade", "UF", "Fone", "IE / RG", "Vendedor", "Situação", "Tipo pessoa", "Tipo contato"]
        for campo in campos_verificar:
            if linha_atual.get(campo, "") != nova_linha[campo]:
                linha_atual[campo] = nova_linha[campo]
                mudou = True
        if mudou:
            atualizados += 1
    else:
        csv_existente[cnpj_norm] = nova_linha
        novos += 1

# Salva CSV final
with open(arquivo_csv, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=colunas_bling)
    writer.writeheader()
    for linha in csv_existente.values():
        writer.writerow(linha)

print(f"✅ {novos} novos contatos adicionados e {atualizados} contatos atualizados no '{arquivo_csv}'!")

