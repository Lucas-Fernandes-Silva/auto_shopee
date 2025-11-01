import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# from datetime import date
from dados import dados, env

# from src.extract.email_handler import EmailHandler
from src.extract.web_scraper import WebScraper
from src.extract.xml_processor import XMLProcessor
from src.load.notas_manager import NotasManager
from src.transform.base_variation_extract import BaseVariantExtractor
from src.transform.brand_detector import BrandDetector
from src.transform.category_filter import CategoryFiller
from src.transform.variation_grouper import VariationGrouper
from src.utils.gtin_validator import GTINValidator
from src.utils.logger import logger

# email = EmailHandler(env.user, env.pwd)
# email.baixar_anexos(date.today())

xml_proc = XMLProcessor("dados/dados_exemplo")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager(dados.fornecedores)

df_produtos = manager.cria_dataframe(lista_produtos)

# manager.copiar_xmls("dados", "dados ")



scraper = WebScraper(env.headers)
df_enriquecido = scraper.enriquecer_dataframe(
    df_produtos, dados.fornecedores, paralelo=True
)

manager.salvar_excel(df_enriquecido)


gtin = GTINValidator(df_enriquecido, dados.fornecedores_web_scraping)
df = gtin.filter_priority()

marca = BrandDetector(df, dados.marcas_adicionais, dados.marca_variacoes)
df = marca.aplicar()

categoria = CategoryFiller(df)
df = categoria.aplicar()

variacao = VariationGrouper(df)
variacao.aplicar()

nome = BaseVariantExtractor()
nome.aplicar(df)

df.to_excel('teste.xlsx')
logger.info(type(df))
