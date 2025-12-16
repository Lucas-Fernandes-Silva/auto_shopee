import re

import pandas as pd


class ElectricAttributeExtractor:
    def __init__(self, linhas_conhecidas=None, cores_conhecidas=None):
        self.linhas_conhecidas = linhas_conhecidas or set()
        self.cores_conhecidas = cores_conhecidas or {
            "BRANCO", "PRETO", "CINZA"
        }

    # -------------------------
    # Linha / modelo
    # -------------------------
    def extrair_linha(self, texto):
        for linha in self.linhas_conhecidas:
            if linha in texto:
                return linha
        return None

    # -------------------------
    # Formato da placa (4X2, 4X4)
    # -------------------------
    def extrair_formato(self, texto):
        match = re.search(r"\b\dX\d\b", texto)
        return match.group(0) if match else None

    # -------------------------
    # Cor (define grupo, não variação)
    # -------------------------
    def extrair_cor(self, texto):
        for cor in self.cores_conhecidas:
            if cor in texto:
                return cor
        return None

    # -------------------------
    # Função elétrica (VARIAÇÃO)
    # -------------------------
    def extrair_funcao(self, texto):
        # conteúdo entre parênteses
        match = re.search(r"\((.*?)\)", texto)
        if match:
            return match.group(1).strip()

        # fallback sem parênteses
        padroes = [
            r"\bTOMADA\s?\d{1,2}A\b",
            r"\b\dS\b",
            r"\b\dP\+T\b",
        ]

        for p in padroes:
            m = re.search(p, texto)
            if m:
                return m.group(0)

        return None

    # -------------------------
    # Extrator completo
    # -------------------------
    def extrair(self, descricao_limpa):
        if pd.isna(descricao_limpa):
            return {}

        t = descricao_limpa.upper()

        return {
            "linha": self.extrair_linha(t),
            "formato": self.extrair_formato(t),
            "cor": self.extrair_cor(t),
            "funcao": self.extrair_funcao(t),
        }


