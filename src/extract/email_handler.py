import os
from datetime import timedelta

from imap_tools.mailbox import MailBox
from imap_tools.query import AND

from src.utils.logger import logger


class EmailHandler:
    def __init__(self, email_user, email_pwd, save_folder="nfes/"):
        self.email_user = email_user
        self.email_pwd = email_pwd
        self.save_folder = save_folder
        os.makedirs(self.save_folder, exist_ok=True)

    def baixar_anexos(self, data_inicio):
        logger.info("🔹 Baixando anexos XML do e-mail…")
        with MailBox("imap.gmail.com").login(
            self.email_user, self.email_pwd, initial_folder="INBOX"
        ) as mailbox:
            list_mail = mailbox.fetch(
                criteria=AND(date_gte=(data_inicio - timedelta(7)))
            )
            for email in list_mail:
                for anexo in email.attachments:
                    if anexo.filename.lower().endswith(".xml"):
                        file_path = os.path.join(self.save_folder, anexo.filename)
                        if not os.path.exists(file_path):
                            with open(file_path, "wb") as f:
                                f.write(anexo.payload)
                            logger.info(f"Arquivo salvo: {file_path}")
