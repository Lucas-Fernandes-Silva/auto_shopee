from pathlib import Path
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.categorization.pipeline.RemovedorComercial import aplicar_limpeza_nome_base
from src.utils.TextNormalizer import TextNormalizer


INPUT_XLSX = Path("/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx")
OUTPUT_XLSX = Path(
    "/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm_Normalizada.xlsx"
)


def normalizar_descricao_linha(row: pd.Series, normalizer: TextNormalizer) -> str:
    descricao = row.get("Descrição")
    dominio = row.get("Dominio")
    segmento = row.get("Segmento")

    kwargs = {}
    if pd.notna(dominio):
        kwargs["dominio"] = dominio
    if pd.notna(segmento):
        kwargs["segmento"] = segmento

    return normalizer.normalizar(descricao, **kwargs)


def main() -> None:
    df = pd.read_excel(INPUT_XLSX, dtype=str)

    if "Descrição" not in df.columns:
        raise ValueError("A planilha precisa ter a coluna 'Descrição'.")

    normalizer = TextNormalizer()

    df["Descricao_Limpa"] = df.apply(
        lambda row: normalizar_descricao_linha(row, normalizer),
        axis=1,
    )

    df = aplicar_limpeza_nome_base(df)
    df.to_excel(OUTPUT_XLSX, index=False)

    print(f"Arquivo gerado em: {OUTPUT_XLSX}")
    print(f"Linhas processadas: {len(df)}")


if __name__ == "__main__":
    main()
