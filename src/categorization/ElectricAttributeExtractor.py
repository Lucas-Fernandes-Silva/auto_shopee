import re


class ElectricAttributeExtractor:
    CATEGORIA_ALVO = "TOMADAS INTERRUPTORES PINOS"

    def extract(self, descricao: str, categoria: str) -> dict:
        if categoria != self.CATEGORIA_ALVO:
            return {}

        texto = descricao.upper()
        attrs = {}

        amp = re.search(r"\b(10|20)A\b", texto)
        if amp:
            attrs["Amperagem"] = amp.group(1)

        polos = re.search(r"\b(\dP\+?T?)\b", texto)
        if polos:
            attrs["Polos"] = polos.group(1)

        return attrs
