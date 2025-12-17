import re

import pandas as pd

from src.transform.ElectricAttributeExtractor import ElectricAttributeExtractor


class ElectricGroupClassifier:
    def __init__(self, categoria_alvo="TOMADAS INTERRUPTORES PINOS"):
        self.categoria_alvo = categoria_alvo.upper()

        # ⚠️ ORDEM IMPORTA (específico → genérico)
        self.grupos = [
            (
                "CONJUNTO",
                [
                    r"\bCONJUNTO\b",
                    r"\bCJ\b",
                ],
            ),
            (
                "PLACA",
                [
                    r"\bPLACA\b",
                ],
            ),
            (
                "MODULO",
                [
                    r"\bMODULO\b",
                    r"\bMÓDULO\b",
                ],
            ),
            (
                "PLUG",
                [r"\bPLUG\b.*\bMACHO\b", r"\bPLUG\b"],
            ),
            (
                "PINO FEMÊA",
                [
                    r"\bPROLONGADOR\b",
                    r"\bEXTENSAO\b",
                    r"\bEXTENSÃO\b",
                    r"\bFEMEA\b",
                    r"\bFÊMEA\b",
                    r"\bTOMADA\b.*\bFEMEA\b",
                    r"\bPINO\b.*\bFEMEA\b",
                ],
            ),
            (
                "CANALETA",
                [
                    r"\bSISTEMA\b" r"\bCANALETA\b",
                ],
            ),
            (
                "BARRA",
                [
                    r"\bTOMADA EM BARRA\b",
                    r"\bBARRA\b",
                ],
            ),
            (
                "SOBREPOR",
                [
                    r"\bSOBREPOR\b",
                    r"\bBOX\b",
                    r"\bCAIXA SOBREPOR\b",
                ],
            ),
        ]

    def classificar(self, descricao, categoria):
        if pd.isna(descricao) or not categoria:
            return None

        if str(categoria).upper().strip() != self.categoria_alvo:
            return None

        texto = descricao.upper()

        for grupo, padroes in self.grupos:
            for p in padroes:
                if re.search(p, texto):
                    return grupo

        return "OUTROS"


classificador = ElectricGroupClassifier(categoria_alvo="TOMADAS INTERRUPTORES PINOS")

df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx")

df["Grupo_Eletrico"] = df.apply(
    lambda r: classificador.classificar(
        r["Descricao_Limpa"],  # use a descrição já normalizada
        r["Categoria"],
    ),  # type: ignore
    axis=1,
)  # type: ignore


linhas_eletricas = {
    "STYLUS",
    "MILL",
    "PETRA",
    "STECK",
    "INTERNEED",
    "FAME",
    "ARIA",
    "LIZ",
    "LUX",
    "FC",
}


extrator_eletrico = ElectricAttributeExtractor(linhas_eletricas=linhas_eletricas)

atributos = df.apply(
    lambda r: extrator_eletrico.extrair(
        r["Descricao_Limpa"],
        r["Categoria"],
        r["Grupo_Eletrico"],
    ),
    axis=1,
)

df = pd.concat([df, atributos.apply(pd.Series)], axis=1)

df.to_excel("Eletricos.xlsx", index=False)
