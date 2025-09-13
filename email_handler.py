
import os
import logging
from imap_tools import MailBox, AND 
from datetime import date, timedelta
from env import user, pwd

class EmailHandler:
    def __init__(self, email_user, email_pwd, pasta_notas="notas/", max_threads=5, log_file="processador.log"):
        self.email_user = email_user
        self.email_pwd = email_pwd
        self.save_folder = pasta_notas
        os.makedirs(self.save_folder, exist_ok=True)
        self.todos_produtos = []
        self.max_threads = max_threads

        # Configuração de logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        self.fornecedores_pesados = [
            'IND E COM DE TUBOS E CONEXOES FORT.COM',
            'VOTORANTIM CIMENTOS SA',
            'CABOQUINHO MATERIAIS PARA CONSTRUCAO'
        ]

    def baixar_anexos(self, data_inicio=date.today()):
        self.logger.info("🔹 Baixando anexos XML do e-mail…")
        with MailBox("imap.gmail.com").login(self.email_user, self.email_pwd, initial_folder="INBOX") as mailbox:
            list_mail = mailbox.fetch(criteria=AND(date_gte=(data_inicio - timedelta(7))))
            for email in list_mail:
                for anexo in email.attachments:
                    if anexo.filename.lower().endswith(".xml"):
                        file_path = os.path.join(self.save_folder, anexo.filename)
                        if not os.path.exists(file_path):
                            with open(file_path, "wb") as f:
                                f.write(anexo.payload)
                            self.logger.info(f"Arquivo salvo: {file_path}")


teste = EmailHandler(user, pwd)
teste.baixar_anexos()
