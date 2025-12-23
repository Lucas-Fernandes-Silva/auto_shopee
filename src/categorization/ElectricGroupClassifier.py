class ElectricGroupClassifier:
    CATEGORIA_ALVO = "TOMADAS INTERRUPTORES PINOS"

    def classify(self, descricao: str, categoria: str) -> str | None:
        if categoria != self.CATEGORIA_ALVO:
            return None

        texto = descricao.upper()

        if "PROLONGADOR" in texto or "EXTENSAO" in texto:
            return "PROLONGADOR"

        if "PLUG" in texto and "MACHO" in texto:
            return "PLUG MACHO"

        if "INTERRUPTOR" in texto:
            return "INTERRUPTOR"

        if "TOMADA" in texto:
            return "TOMADA"

        return "OUTROS"
