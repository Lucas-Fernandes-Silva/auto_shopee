from email_handler import EmailHandler
from xml_processor import XMLProcessor
from web_scraper import WebScraper
from notas_manager import NotasManager
from datetime import date
import env
import pandas as pd
from logger import logger

email = EmailHandler(env.user, env.pwd)
email.baixar_anexos(date.today())

xml_proc = XMLProcessor("notas/nfes")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager(env.fornecedores)

df_produtos = manager.cria_dataframe(lista_produtos)

manager.copiar_xmls('notas', 'notas/nfes')

scraper = WebScraper(env.headers)
df_enriquecido = scraper.enriquecer_dataframe(df_produtos, env.fornecedores, paralelo=True)
manager.salvar_excel(df_enriquecido)