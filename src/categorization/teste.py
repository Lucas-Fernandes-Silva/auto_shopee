import pandas as pd

from src.categorization.extratores.CorExtractor import CorExtractor
from src.categorization.extratores.medida.MedidaAxBExtractor import MedidaAxBExtractor
from src.categorization.extratores.medida.MedidaExtractor import MedidaExtractor
from src.categorization.pipeline.VariationPipeline import VariationPipeline
from src.transform.baseNome import aplicar_nomes  # seu baseNome.py refatorado

df = pd.DataFrame(
    [
        {
            "Descricao_Limpa": "AMANCO RALO LINEAR PVC 0,11X0,50CM SIFONADO BRANCO",
            "Dominio": "HIDRAULICA",
        },
        {
            "Descricao_Limpa": "TRAMONTINA BICO MANGUEIRA 3/4X1/2 PLASTICO P/ ENGATE",
            "Dominio": "HIDRAULICA",
        },
    ]
)

vp = VariationPipeline(
    dominio_extractors={
        "HIDRAULICA": [
            MedidaAxBExtractor(),
            MedidaExtractor(),
            CorExtractor(),
        ]
    },
    debug=True,  # pra ver Origem__...
)

df2 = vp.aplicar(df)
df3 = aplicar_nomes(df2)

print(df3[["Descricao_Limpa", "Medida", "Cor", "Nome_Produto_Base", "Nome_Variacao"]])

df3.to_excel("teste.xlsx", index=False)
