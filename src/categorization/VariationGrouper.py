class ElectricVariationGrouper:
    CATEGORIA_ALVO = "TOMADAS INTERRUPTORES PINOS"

    def build_key(self, row) -> str | None:
        if row["Categoria"] != self.CATEGORIA_ALVO:
            return None

        return f"{row['Subgrupo']}|{row.get('Amperagem','')}|{row.get('Polos','')}"
