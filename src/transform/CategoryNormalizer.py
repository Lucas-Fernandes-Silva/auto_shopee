import re

import pandas as pd

from src.utils.logger import logger


class CategoryNormalizer:
    """
    Resolve Categoria_Normalizada a partir da Descricao_Limpa
    com fallback controlado para a categoria do fornecedor.
    """

    def __init__(self):
        # Ordem importa: específico → genérico
        self.regras = [
            (
                "ABRASIVOS",
                [
                    r"\bDISCO\b",
                    r"\bREBOLO\b",
                    r"\bFLAP\b",
                    r"\bDESBASTE\b",
                    r"\bDIAMANTAD",
                    r"\bLIXA\b",
                    r"\bSPEED\b",
                    r"\bSPED\b",
                ],
            ),
            (
                "BROCAS",
                [
                    r"\bBROCA\b",
                ],
            ),
            (
                "ELETRICA",
                [
                    r"\bTOMADA\b",
                    r"\bINTERRUPTOR\b",
                    r"\bDISJUNTOR\b",
                    r"\bCHUVEIRO\b",
                    r"\bRESISTENCIA\b",
                    r"\bCAIXA DE LUZ\b",
                    r"\bCENTRO DISJUNTOR\b",
                ],
            ),
            (
                "HIDRAULICA",
                [
                    r"\bCONEX",
                    r"\bTUBO\b",
                    r"\bJOELHO\b",
                    r"\bTEE\b",
                    r"\bTE\b",
                    r"\bCURVA\b",
                    r"\bRALO\b",
                    r"\bVALVULA\b",
                    r"\bREGISTRO\b",
                    r"\bFILTRO\b",
                    r"\bVEDA ROSCA\b",
                ],
            ),
            (
                "FITAS_ADESIVOS",
                [
                    r"\bFITA\b",
                    r"\bSILICONE\b",
                    r"\bCOLA\b",
                    r"\bADESIVO\b",
                ],
            ),
            (
                "AUTOMOTIVA",
                [
                    r"\bAUTOMOTIV",
                    r"\bBATERIA\b",
                    r"\bCATALISADOR\b",
                    r"\bBOINA\b",
                    r"\bMASSA\b",
                ],
            ),
            (
                "COBERTURA",
                [
                    r"\bCALHA\b",
                    r"\bRUFO\b",
                    r"\bTELHA\b",
                ],
            ),
            (
                "FERRAGENS_GERAIS",
                [
                    r"\bCADEADO\b",
                    r"\bRATOEIRA\b",
                    r"\bCANETA\b",
                    r"\bTRAVA\b",
                    r"\bSUPORTE\b",
                ],
            ),
        ]

    def resolver(self, descricao_limpa, categoria_fornecedor=None):
        if pd.isna(descricao_limpa):
            return categoria_fornecedor

        texto = descricao_limpa.upper()

        for categoria, padroes in self.regras:
            for p in padroes:
                if re.search(p, texto):
                    return categoria

        # fallback controlado
        return categoria_fornecedor


normalizador = CategoryNormalizer()

df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx")

df["Categoria_Normalizada"] = df.apply(
    lambda r: normalizador.resolver(
        r["Descricao_Limpa"],
        r["Categoria"],
    ),  # type: ignore
    axis=1,
)  # type: ignore

logger.info(df["Categoria_Normalizada"].value_counts())
