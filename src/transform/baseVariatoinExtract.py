import itertools
import re
from collections import Counter

import numpy as np
from rapidfuzz import fuzz
from tqdm import tqdm

from utils.normalizer import Normalizer


class BaseVariantExtractor:
    @staticmethod
    def similaridade_media(strings):
        pares = list(itertools.combinations(strings, 2))
        if not pares:
            return 1.0
        return np.mean([fuzz.token_set_ratio(a, b) / 100 for a, b in pares])

    @staticmethod
    def parte_comum(strings, sensibilidade=0.7):
        token_lists = [Normalizer.normalize(s).split() for s in strings if s]
        if not token_lists:
            return ""
        todas = {
            p
            for tokens in token_lists
            for p in tokens
            if not re.match(r"^\d+[Xx/]\d+$", p)
        }
        contagem = Counter(
            {
                p: sum(
                    fuzz.ratio(p, t) / 100 >= sensibilidade
                    for tokens in token_lists
                    for t in tokens
                )
                for p in todas
            }
        )
        limite = max(1, int(len(strings) * 0.8))
        comuns = [w for w, c in contagem.items() if c >= limite]
        base = " ".join(
            [
                t
                for t in token_lists[0]
                if any(fuzz.ratio(t, w) / 100 >= sensibilidade for w in comuns)
            ]
        )
        return re.sub(r"\b\d+([Xx/]\d+)?\b", "", base).strip()

    def aplicar(self, df):
        df["Base"], df["Variante"] = "", ""
        for gid, grupo in tqdm(
            df.groupby("ID_Variacao", group_keys=False), desc="Gerando bases"
        ):
            chaves = grupo["Chave"].tolist()
            media = self.similaridade_media(chaves)
            sens = 0.85 if media >= 0.9 else 0.75 if media >= 0.8 else 0.65
            comum = self.parte_comum(chaves, sens) or Normalizer.normalize(
                grupo["Descrição"].iloc[0]
            )
            df.loc[grupo.index, "Base"] = comum
            df.loc[grupo.index, "Variante"] = grupo["Chave"].map(
                lambda x: x.replace(comum, "").strip()
            )
        return df
