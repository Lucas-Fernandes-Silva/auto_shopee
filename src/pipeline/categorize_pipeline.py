import pandas as pd

from src.categorization.DomainMapper import DomainMapper
from src.categorization.ElectricAttributeExtractor import ElectricAttributeExtractor
from src.categorization.VariationGrouper import ElectricVariationGrouper
from src.utils.normalizer import Normalizer


class CategorizationPipeline:
    def __init__(self, path_categorizados: str):
        self.mapper = DomainMapper(path_categorizados)
        self.electric_extractor = ElectricAttributeExtractor()
        self.variation_grouper = ElectricVariationGrouper()

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # normaliza descrição
        df["Descricao_Limpa"] = df["Descricao"].apply(Normalizer.normalize)

        # resolve dominio / categoria
        df[["Dominio", "Categoria_Principal", "Subcategoria"]] = df.apply(
            lambda r: pd.Series(self.mapper.resolve(r["Descricao_Limpa"])),
            axis=1,
        )

        # atributos elétricos
        electric_attrs = df.apply(
            lambda r: self.electric_extractor.extract(
                r["Descricao_Limpa"], r["Categoria_Principal"]
            ),
            axis=1,
        )

        electric_df = pd.json_normalize(electric_attrs.tolist())
        df = pd.concat([df, electric_df], axis=1)

        # chave de variação
        df["VariationKey"] = df.apply(
            lambda r: self.variation_grouper.get_group_key(r), # type: ignore
            axis=1,
        )

        return df


df = pd.read_csv("produtos.csv")

pipeline = CategorizationPipeline(path_categorizados="Categorizados.xlsx")

df_final = pipeline.run(df)

df_final.to_csv("produtos_categorizados.csv", index=False)
