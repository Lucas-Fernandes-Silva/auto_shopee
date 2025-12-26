import pandas as pd

from src.categorization.DomainClassifier import DomainClassifier
from src.categorization.DomainMapLoader import DomainMapLoader
from src.categorization.ElectricAttributeExtractor import ElectricAttributeExtractor
from src.categorization.ElectricGroupClassifier import ElectricGroupClassifier


class CategorizationPipeline:
    def __init__(
        self,
        domain_classifier,
        electric_group_classifier=None,
        electric_attribute_extractor=None,
    ):
        self.domain_classifier = domain_classifier
        self.electric_group_classifier = electric_group_classifier
        self.electric_attribute_extractor = electric_attribute_extractor

    def processar_linha(self, row):
        descricao = row.get("Descricao_Limpa")
        categoria = row.get("Categoria")

        resultado = {}

        # -------------------------
        # 1. DOMÍNIO
        # -------------------------
        dominio = self.domain_classifier.classificar(descricao)
        resultado["Dominio"] = dominio

        # -------------------------
        # 2. ELÉTRICA
        # -------------------------
        if dominio == "ELÉTRICA" and self.electric_group_classifier:
            grupo = self.electric_group_classifier.classify(descricao, categoria)
            resultado["Grupo_Eletrico"] = grupo

            if self.electric_attribute_extractor:
                atributos = self.electric_attribute_extractor.extrair(
                    descricao_limpa=descricao,
                    categoria=categoria,
                    grupo_eletrico=grupo,
                )
                resultado.update(atributos)

        # -------------------------
        # 3. FUTUROS DOMÍNIOS
        # -------------------------
        # if dominio == "HIDRAULICA":
        #     ...

        return pd.Series(resultado)

    def aplicar(self, df: pd.DataFrame):
        atributos = df.apply(self.processar_linha, axis=1)
        return pd.concat([df, atributos], axis=1)


# ---- Domínio
loader = DomainMapLoader("/home/lucas-silva/auto_shopee/planilhas/outputs/Categorizados.xlsx")
df_dominios = loader.carregar()
domain_classifier = DomainClassifier(df_dominios)

# ---- Elétrica
electric_group_classifier = ElectricGroupClassifier()
electric_attribute_extractor = ElectricAttributeExtractor(
    linhas_eletricas={
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
)

# ---- Pipeline
pipeline = CategorizationPipeline(
    domain_classifier=domain_classifier,
    electric_group_classifier=electric_group_classifier,
    electric_attribute_extractor=electric_attribute_extractor,
)

# ---- Executar
df = pd.read_excel("/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx")
df_final = pipeline.aplicar(df)

df_final.to_excel("Produtos_Classificados.xlsx", index=False)
