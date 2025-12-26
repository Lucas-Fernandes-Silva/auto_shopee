import pandas as pd


class DomainMapLoader:
    def __init__(self, path_excel):
        self.path_excel = path_excel

    def carregar(self):
        df_raw = pd.read_excel(self.path_excel)

        registros = []

        for dominio in df_raw.columns:
            for valor in df_raw[dominio]:
                if pd.notna(valor):
                    registros.append({
                        "dominio": dominio.upper().strip(),
                        "termo": str(valor).upper().strip()
                    })

        return pd.DataFrame(registros)
