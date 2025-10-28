from src.email_handler import EmailHandler
from src.xml_processor import XMLProcessor
from src.web_scraper import WebScraper
from src.notas_manager import NotasManager
from datetime import date
import src.env as env
import pandas as pd
from src.logger import logger

email = EmailHandler(env.user, env.pwd)
email.baixar_anexos(date.today())

xml_proc = XMLProcessor("notas")
lista_produtos = xml_proc.processar_todos(paralelo=True)

manager = NotasManager(env.fornecedores)

df_produtos = manager.cria_dataframe(lista_produtos)

manager.copiar_xmls('notas', 'notas')

scraper = WebScraper(env.headers)
df_enriquecido = scraper.enriquecer_dataframe(df_produtos, env.fornecedores, paralelo=True)
df_enriquecido
manager.salvar_excel(df_enriquecido)

