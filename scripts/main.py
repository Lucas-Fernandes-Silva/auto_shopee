import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import date

from dados import dados, env
from src.extract.email_handler import EmailHandler
from src.extract.web_scraper import WebScraper
from src.extract.xml_processor import XMLProcessor
from src.load.notas_manager import NotasManager
from src.transform.base_variation_extract import BaseVariantExtractor
from src.transform.brand_detector import BrandDetector
from src.transform.category_filter import CategoryFiller
from src.transform.large_products import HeavyClassifier
from src.transform.market_price import PrecoVenda
from src.transform.variation_grouper import VariationGrouper
from src.utils.gtin_validator import GTINValidator

email = EmailHandler(env.user, env.pwd)
email.baixar_anexos(date.today())

xml_proc = XMLProcessor("dados/nfes")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager(dados.fornecedores)

df_produtos = manager.cria_dataframe(lista_produtos)

manager.copiar_xmls("dados/nfes", "dados/processados")

scraper = WebScraper(env.headers)
df_enriquecido = scraper.enriquecer_dataframe(
    df_produtos, dados.fornecedores, paralelo=True
)


gtin = GTINValidator(df_enriquecido, dados.fornecedores_web_scraping)
df = gtin.filter_priority()
df = gtin.gerar_gtins_aleatorios(df)


preco = PrecoVenda(df)
df = preco.aplicar()

marca = BrandDetector(df, dados.marcas_adicionais, dados.marca_variacoes)
df = marca.aplicar()

categoria = CategoryFiller(df)
df = categoria.aplicar()

variacao = VariationGrouper(df)
df = variacao.aplicar()

nome = BaseVariantExtractor()
df = nome.aplicar(df)

manager.salvar_excel(df)


col = "Descrição"

heavy_keywords = [
    r"\bTELHA\b", r"\bCUMEEIRA\b",
    r"\bPORTA\b", r"GABINETE", r"\bVASO\b", r"LAVAT[ÓO]RIO", r"\bPIA\b", r"\bTANQUE\b",
    r"CAIXA D'?[ÁA]GUA", r"CANTON", r"EXTENSOR", r"BACIA", r"VIAPLUS", r"VEDAPREN",
    r"TUBO", r"CONEX[ÃA]O", r"CANAL", r"LONA", r"TECPLUS", r"SIKATOP", r"CORRENTE",
    r"CIMENTO", r"ARGAMASSA", r"MASSA CORRIDA", r"MASSA ACR[IÍ]LICA",
    r"TINTA", r"VEDATOP", r"\bCALHA\b", r"ELETRODUTO", r"VAR[ÃA]O",
    r"\bPÁ\b", r"\bENXADA\b", r"CAVADEIRA", r"\bFORCADO\b", r"R[EÉ]GUA ALUM[IÍ]NIO",
    r"CARRINHO", r"\bESCADA\b", r"VARAL DE CH[ÃA]O", r"MANTA", r"DAGUA", r"COLUNA",
    r"\bLAV\b", r"TELA"
]

exclude_keywords = [
    "PARAFUSO P/ TELHA", "PARAF", "FECH", "SOLDA", "LIGACAO", "VALV", "ANEL", "SERRA", "BOCAL",
    "ABRAC", "CADEADO ", "GRELHA", "TORN", "DESEMP", "RALINHO", "PINO", "BOLSA", "ADAP",
    "PLASTICO", "TRAVA", "BOLSA", "LIMA", "RALINHO", "FITA", "CABO FLEX", "CABO REDE",
    "PATCH CORD", "COAXIAL", "CABO PP", "BATEDOR", "BALDE", "ABRAC", "SELATRINCA",
    "FIXADOR", "PILHA", "FRISO", "MOVEIS", "REFIL", "VIDRO", "PRATELEIRA", "FRANC",
    "PRESSURIZADOR", "FILTRO", "PENEIRA", "LUVA", "CALCO", "DISCO", "SUP", "BATEADOR",
    "MISTURADOR", "SAIDA", "CABECEIRA", "PNEU P/ CARRINHO"
]

# Instancia a classe
classifier = HeavyClassifier(
    df=df,
    column=col,
    heavy_keywords=heavy_keywords,
    exclude_keywords=exclude_keywords
)

df_pesados, df_restante = classifier.classify()

print("Itens pesados:", len(df_pesados))
print("Itens restantes:", len(df_restante))

classifier.save(restante_path="grandes.xlsx")
