from datetime import date

import dados.env as env
from extract.email_handler import EmailHandler
from extract.web_scraper import WebScraper
from extract.xml_processor import XMLProcessor
from load.notas_manager import NotasManager

email = EmailHandler(env.user, env.pwd)
email.baixar_anexos(date.today())

xml_proc = XMLProcessor("dados")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager(env.fornecedores)

df_produtos = manager.cria_dataframe(lista_produtos)

manager.copiar_xmls("dados", "dados")

scraper = WebScraper(env.headers)
df_enriquecido = scraper.enriquecer_dataframe(
    df_produtos, env.fornecedores, paralelo=True
)

manager.salvar_excel(df_enriquecido)
