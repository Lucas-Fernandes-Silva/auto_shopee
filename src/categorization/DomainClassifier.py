import re
from collections import defaultdict

import pandas as pd


class DomainClassifier:
    def __init__(self, df_dominios, window_size=6, min_matches=2):

        self.window_size = window_size
        self.min_matches = min_matches

        # organiza termos por domínio
        self.dominios = defaultdict(list)
        for _, row in df_dominios.iterrows():
            self.dominios[row["dominio"]].append(row["termo"])

    def classificar(self, descricao):
        if pd.isna(descricao):
            return None

        palavras = descricao.upper().split()
        tamanho = len(palavras)

        pontuacao = defaultdict(int)

        # percorre janelas
        for i in range(tamanho):
            janela = " ".join(palavras[i : i + self.window_size])

            for dominio, termos in self.dominios.items():
                matches = 0
                for termo in termos:
                    if re.search(rf"\b{re.escape(termo)}\b", janela):
                        matches += 1

                if matches >= self.min_matches:
                    pontuacao[dominio] += matches

        if not pontuacao:
            return None

        return max(pontuacao, key=pontuacao.get) # type: ignore
