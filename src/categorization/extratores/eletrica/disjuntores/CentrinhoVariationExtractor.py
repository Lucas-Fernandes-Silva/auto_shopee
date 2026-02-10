import re


class CentrinhoVariationExtractor:

    # capacidade numérica (02, 04, 08, 12)
    PADRAO_CAP_NUMERICA = re.compile(r"\b(0?[2348]|12)\b")

    # padrão NEMA / DIN (1/2, 3/4, 6/8)
    PADRAO_NEMA_DIN = re.compile(r"\b(1/2|3/4|6/8)\b")

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Capacidade_Centrinho": None}

        desc = descricao.lower()

        # 1️⃣ prioridade: padrão NEMA / DIN
        match_nema = self.PADRAO_NEMA_DIN.search(desc)
        if match_nema:
            return {"Capacidade_Centrinho": match_nema.group(1) + '"'}

        # 2️⃣ capacidade numérica
        match_num = self.PADRAO_CAP_NUMERICA.search(desc)
        if match_num:
            valor = match_num.group(1)

            # normaliza para dois dígitos
            valor = valor.zfill(2)

            return {"Capacidade_Centrinho": valor}

        return {"Capacidade_Centrinho": None}
