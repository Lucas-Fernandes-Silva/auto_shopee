import re
import unicodedata

import pandas as pd


class Normalizer:
    @staticmethod
    def normalize(texto: str) -> str:
        if pd.isna(texto):
            return ""
        texto = str(texto).upper().strip()
        texto = "".join(
            c
            for c in unicodedata.normalize("NFD", texto)
            if unicodedata.category(c) != "Mn"
        )
        texto = re.sub(r"[^A-Z0-9 ]", "", texto)
        return re.sub(r"\s+", " ", texto).strip()
