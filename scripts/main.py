import os
import sys

import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from src.extract.img_extract.url import Download

# email = EmailHandler(env.user, env.pwd)
# email.baixar_anexos(date.today())

# xml_proc = XMLProcessor("dados/nfes")
# lista_produtos = xml_proc.processar_todos(paralelo=True)

# manager = NotasManager(dados.fornecedores)

# df_produtos = manager.cria_dataframe(lista_produtos)

# manager.copiar_xmls("dados/nfes", "dados/processados")

# scraper = WebScraper(env.headers)
# df_enriquecido = scraper.enriquecer_dataframe(df_produtos, dados.fornecedores, paralelo=True)


# gtin = GTINValidator(df_enriquecido, dados.fornecedores_web_scraping)
# df = gtin.filter_priority()
# df = gtin.gerar_gtins_aleatorios(df)


# preco = PrecoVenda(df)
# df = preco.aplicar()

# marca = BrandDetector(df, dados.marcas_adicionais, dados.marca_variacoes)
# df = marca.aplicar()

# categoria = CategoryFiller(df)
# df = categoria.aplicar()

# variacao = VariationGrouper(df)
# df = variacao.aplicar()

# nome = BaseVariantExtractor()
# df = nome.aplicar(df)

# manager.salvar_excel(df)


# classifier = HeavyClassifier(df)
# df_pesados, df_restante = classifier.classify()
# classifier.save(restante_path="produtos_padrao.xlsx")
# classifier.save(pesados_path="grandes.xlsx")


grandes = pd.read_excel("/home/lucas-silva/auto_shopee/grandes.xlsx")
df = grandes[-1:]
print(df)
download = Download(df)
download.run()
