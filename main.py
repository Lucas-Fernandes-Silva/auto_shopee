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

arquivos = manager.separando_fornecedor(df_produtos, env.fornecedores)

manager.copiar_xmls('notas', 'notas/nfes')

manager.salvar_excel(arquivos)

teste = arquivos[0].copy()

sliced = teste[:1].copy()

scraper = WebScraper(env.headers)
enriquecer_df = scraper.enriquecer_dataframe(sliced, paralelo=True)

df_enriquecido = pd.DataFrame(enriquecer_df)
manager.salvar_enriquecido(df_enriquecido)