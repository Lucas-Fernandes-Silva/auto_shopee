import os
import sys
from datetime import date

from src.extract.email_handler import EmailHandler

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from dados import dados, env
from src.extract.img_extract.url import Download
from src.extract.web_scraper import WebScraper
from src.extract.xml_processor import XMLProcessor
from src.load.notas_manager import NotasManager
from src.transform.base_variation_extract import BaseVariantExtractor
from src.transform.brand_detector import BrandDetector
from src.transform.category_filter import CategoryFiller
from src.transform.large_products import HeavyClassifier
from src.transform.market_price import PrecoVenda
from src.transform.TextNormalizer import TextNormalizer
from src.transform.variation_grouper import VariationGrouper
from src.utils.gtin_validator import GTINValidator

# email = EmailHandler(env.user, env.pwd)
# email.baixar_anexos(date.today())

xml_proc = XMLProcessor("dados/nfes")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager()

df_produtos = manager.cria_dataframe(lista_produtos)

manager.copiar_xmls("dados/nfes", "dados/processados")

scraper = WebScraper(env.headers)
df = scraper.enriquecer_dataframe(df_produtos)

gtin = GTINValidator(df, dados.fornecedores_web_scraping)
df = gtin.filter_priority()

gtin = GTINValidator(df, dados.fornecedores_web_scraping)
gtin.gerar_gtins_aleatorios(df)

preco = PrecoVenda(df)
df = preco.aplicar()

marca = BrandDetector(df)
df = marca.aplicar()

categoria = CategoryFiller(df)
df = categoria.aplicar()

text_normalizer = TextNormalizer()

df["Descricao_Limpa"] = df.apply(
    lambda r: text_normalizer.normalizar(r["Descrição"], r["Marca"]),
    axis=1
)

manager.salvar_excel(df, "Descrição_Norm")

# variacao = VariationGrouper(df_restante)
# df = variacao.aplicar()

# nome = BaseVariantExtractor()
# df = nome.aplicar(df)


# classifier = HeavyClassifier(df)
# df_pesados, df_restante = classifier.classify()

# download = Download(df_restante)
# df = download.run()

# manager = NotasManager()
# manager.salvar_excel(df, "download")
