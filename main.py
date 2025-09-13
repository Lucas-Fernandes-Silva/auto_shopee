from email_handler import EmailHandler
from xml_processor import XMLProcessor
from web_scraper import WebScraper
from notas_manager import NotasManager
from datetime import date
from env import user, pwd, headers

email = EmailHandler(user, pwd)
email.baixar_anexos(date.today())

xml_proc = XMLProcessor("notas/nfes")
produtos = xml_proc.processar_xmls()

scraper = WebScraper(headers)
produtos = scraper.processar_produtos()

manager = NotasManager(produtos)
manager.filtrar_fornecedores(['Fornecedor pesado 1', 'Fornecedor pesado 2'])
manager.salvar_excel("produtos.xlsx")

