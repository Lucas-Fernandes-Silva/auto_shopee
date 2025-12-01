import os
import sys
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from dados import dados, env
from src.extract.email_handler import EmailHandler
from src.extract.img_extract.url import Download
from src.extract.web_scraper import WebScraper
from src.extract.xml_processor import XMLProcessor
from src.load.notas_manager import NotasManager

# from src.transform.base_variation_extract import BaseVariantExtractor
from src.transform.brand_detector import BrandDetector
from src.transform.category_filter import CategoryFiller
from src.transform.large_products import HeavyClassifier
from src.transform.market_price import PrecoVenda

# from src.transform.variation_grouper import VariationGrouper
from src.utils.gtin_validator import GTINValidator

email = EmailHandler(env.user, env.pwd)
email.baixar_anexos(date.today())

xml_proc = XMLProcessor("dados/nfes")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager(dados.fornecedores)

df_produtos = manager.cria_dataframe(lista_produtos)

manager.copiar_xmls("dados/nfes", "dados/processados")

scraper = WebScraper(env.headers)
df = scraper.enriquecer_dataframe(df_produtos, dados.fornecedores, paralelo=True)

gtin = GTINValidator(df, dados.fornecedores_web_scraping)
df = gtin.filter_priority()

gtin = GTINValidator(df, dados.fornecedores_web_scraping)
gtin.gerar_gtins_aleatorios(df)

preco = PrecoVenda(df)
df = preco.aplicar()

marca = BrandDetector(df, dados.marcas_adicionais, dados.marca_variacoes)
df = marca.aplicar()

categoria = CategoryFiller(df)
df = categoria.aplicar()

# variacao = VariationGrouper(df)
# df = variacao.aplicar()

# nome = BaseVariantExtractor()
# df = nome.aplicar(df)

manager.salvar_excel(df, 'categorias')


classifier = HeavyClassifier(df)
df_pesados, df_restante, df_custo_baixo = classifier.classify()
classifier.save(restante_path="produtos_padrao.xlsx")
classifier.save(pesados_path="grandes.xlsx")

download = Download(df_restante)
df = download.run()

manager.salvar_excel(df, 'download')


classifier = HeavyClassifier(df)
df_pesados, df_restante, df_custo_baixo = classifier.classify()
classifier.save(restante_path="produtos_padrao.xlsx")
classifier.save(pesados_path="grandes.xlsx")
