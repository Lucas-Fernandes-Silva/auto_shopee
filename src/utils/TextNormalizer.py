import re

import pandas as pd

from dados import dados


class TextNormalizer:
    def __init__(self):
        self.marca_variacoes = dados.marca_variacoes or {}
        self.mapa_abreviacoes = dados.mapa_abreviacoes or {}

        self.mapa_abreviacoes = {
            k: v for k, v in self.mapa_abreviacoes.items() if str(k).upper() != "EMB"
        }

        self.regex_marcas = self._preparar_marcas()
        self.regex_abreviacoes = self._preparar_abreviacoes()

    # =========================
    # Preparação de regex
    # =========================
    def _preparar_marcas(self):
        regex_marcas = []

        for marca, variacoes in self.marca_variacoes.items():
            todas = {marca, *variacoes}

            for v in sorted(todas, key=len, reverse=True):
                padrao = rf"\b{re.escape(v)}\b"
                regex_marcas.append((re.compile(padrao, re.IGNORECASE), marca.upper()))

        return regex_marcas

    def _preparar_abreviacoes(self):
        return {
            re.compile(rf"\b{re.escape(k)}\b", re.IGNORECASE): v.upper()
            for k, v in self.mapa_abreviacoes.items()
        }

    # =========================
    # Limpeza base
    # =========================
    def _remover_codigos(self, texto):
        return re.sub(r"\b\d{5,}\b", "", texto)

    def _limpar_caracteres(self, texto):
        # mantém letras, números, espaço, / + - X vírgula e parênteses
        return re.sub(r"[^\w\s\+\-\/X,x\(\),]", "", texto)

    def _normalizar_fracao_mista(self, texto: str) -> str:
        # Ex.: 1.1/2 -> 1 1/2
        return re.sub(r"\b(\d+)\s*([.,\-])\s*(\d+/\d+)\b", r"\1 \3", texto)

    def _normalizar_decimais(self, texto):
        # Ex.: 4.5 -> 4,5
        return re.sub(r"(?<=\d)\.(?=\d)", ",", texto)

    def _normalizar_simbolos(self, texto):
        return (
            texto.replace("×", " X ")
            .replace("x", " X ")
            .replace("+", " + ")
            .replace("-", " ")
            .replace("—", " ")
            .replace("=", " ")
            .replace("(", " ")
            .replace(")", " ")
        )

    def _remover_pontos_nao_decimais(self, texto):
        # remove apenas pontos que sobraram e não são decimais
        return re.sub(r"\.(?!\d)|(?<!\d)\.", " ", texto)

    def _remover_ruidos(self, texto):
        texto = re.sub(r"\bC\/\b", "C/ ", texto)
        texto = re.sub(r"\bP\/\b", "PARA ", texto)
        texto = re.sub(r"\bR\/\b", "ROLO ", texto)
        texto = re.sub(r"\bRL\/\b", "ROLO ", texto)

        return texto

    # =========================
    # Abreviações contextuais
    # =========================
    def _resolver_emb(self, texto, dominio=None, segmento=None):
        contexto_embutir = [
            r"\bCENTRINHO\b",
            r"\bQUADRO\b",
            r"\bQDC\b",
            r"\bDISTRIBUICAO\b",
            r"\bDISTRIBUIÇÃO\b",
            r"\bDISJ\b",
            r"\bDISJUNTOR(?:ES)?\b",
            r"\bDIN\b",
            r"\bTRILHO\b",
            r"\bBARRAMENTO\b",
            r"\bSOBREPOR\b",
            r"\bEMBUT(?:IR)?\b",
        ]

        eh_embutir = bool(re.search("|".join(contexto_embutir), texto, re.IGNORECASE))

        if dominio:
            dominio_norm = str(dominio).upper()
            if dominio_norm in {"ELETRICA", "ELÉTRICA"}:
                eh_embutir = True

        if segmento:
            segmento_norm = str(segmento).upper()
            if segmento_norm in {"CENTRINHO", "DISJUNTORES", "QUADRO", "QDC"}:
                eh_embutir = True

        substituto = "EMBUTIR" if eh_embutir else "EMBALAGEM"
        return re.sub(r"\bEMB\b", substituto, texto, flags=re.IGNORECASE)

    def _padronizar_abreviacoes_contextuais(self, texto, dominio=None, segmento=None):
        texto = self._resolver_emb(texto, dominio=dominio, segmento=segmento)
        return texto

    def _padronizar_abreviacoes(self, texto):
        for regex, valor in self.regex_abreviacoes.items():
            texto = regex.sub(valor, texto)
        return texto

    # =========================
    # Pipeline principal
    # =========================
    def normalizar(self, descricao, dominio=None, segmento=None):
        if pd.isna(descricao):
            return descricao

        t = str(descricao).upper()

        # ordem importante
        t = self._normalizar_fracao_mista(t)
        t = self._normalizar_decimais(t)
        t = self._normalizar_simbolos(t)
        t = self._remover_pontos_nao_decimais(t)

        t = self._remover_codigos(t)
        t = self._limpar_caracteres(t)
        t = self._remover_ruidos(t)

        # primeiro resolve ambiguidades
        t = self._padronizar_abreviacoes_contextuais(
            t,
        )

        # depois aplica o mapa genérico
        t = self._padronizar_abreviacoes(t)

        return re.sub(r"\s+", " ", t).strip()
