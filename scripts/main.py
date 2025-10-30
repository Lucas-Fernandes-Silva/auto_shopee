from datetime import date

import dados.env as env
from src.extract.email_handler import EmailHandler
from src.extract.web_scraper import WebScraper
from src.extract.xml_processor import XMLProcessor
from src.load.notas_manager import NotasManager

email = EmailHandler(env.user, env.pwd)
email.baixar_anexos(date.today())

xml_proc = XMLProcessor("nfes")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager(env.fornecedores)

df_produtos = manager.cria_dataframe(lista_produtos)

manager.copiar_xmls("nfes", "nfes")

scraper = WebScraper(env.headers)
df_enriquecido = scraper.enriquecer_dataframe(
    df_produtos, env.fornecedores, paralelo=True
)

manager.salvar_excel(df_enriquecido)
