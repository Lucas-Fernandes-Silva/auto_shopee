import re
from collections import defaultdict

import pandas as pd
from src.utils.logger import logger

class DomainClassifier:
    def __init__(self, df_dominios):

        # organiza termos por domínio
        self.dominios = defaultdict(list)
        for _, row in df_dominios.iterrows():
            self.dominios[row["dominio"]].append(row["termo"])

    def classificar(self, descricao):
        if pd.isna(descricao):
            return None

        palavras = descricao.upper().split()
        tamanho = len(palavras)
        logger.info(palavras)

        pontuacao = defaultdict(int)

        # percorre janelas
        for i in range(tamanho):
            janela = " ".join(palavras[i : i + tamanho])

            for dominio, termos in self.dominios.items():
                matches = 0
                for termo in termos:
                    if re.search(rf"\b{re.escape(termo)}\b", janela):
                        matches += 1

                if matches >= 1:
                    pontuacao[dominio] += matches

        if not pontuacao:
            return None

        return max(pontuacao.items(), key=lambda x: x[1])[0]
