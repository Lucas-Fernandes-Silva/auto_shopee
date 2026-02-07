import re


class FormatoLampadaExtractor:
    PADRAO_BULBO = re.compile(r"alta|bulbo|a60", re.IGNORECASE)
    PADRAO_globo = re.compile(r"globo", re.IGNORECASE)
    PADRAO_bolinha = re.compile(r"bolinha", re.IGNORECASE)
    PADRAO_TUBULAR = re.compile(r"tubular|t8|t5|tuboled", re.IGNORECASE)
    PADRAO_compacta = re.compile(r"comp", re.IGNORECASE)
    PADRAO_PAR = re.compile(r"par\s*(20|30|38)", re.IGNORECASE)

    def extrair(self, descricao: str) -> dict:
        if not descricao:
            return {"Formato": None}

        desc = descricao.lower()

        if self.PADRAO_TUBULAR.search(desc):
            return {"Formato": "TUBULAR"}
        if self.PADRAO_compacta.search(desc):
            return {"Formato": "compacta"}
        if self.PADRAO_PAR.search(desc):
            return {"Formato": "PAR"}
        if self.PADRAO_bolinha.search(desc):
            return {"Formato": "bolinha"}
        if self.PADRAO_globo.search(desc):
            return {"Formato": "globo"}
        if self.PADRAO_BULBO.search(desc):
            return {"Formato": "BULBO"}

        return {"Formato": None}
