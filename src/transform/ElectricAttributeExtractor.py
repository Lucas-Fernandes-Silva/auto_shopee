import re
import pandas as pd


class ElectricAttributeExtractor:
    def __init__(
        self,
        categoria_alvo="TOMADAS INTERRUPTORES PINOS",
        linhas_eletricas=None,
    ):
        self.categoria_alvo = categoria_alvo.upper()
        self.linhas_eletricas = {l.upper() for l in (linhas_eletricas or set())}

    def _categoria_valida(self, categoria):
        return categoria and categoria.upper().strip() == self.categoria_alvo

    def _regex(self, pattern, texto):
        m = re.search(pattern, texto)
        return m.group(0) if m else None

    # ---------- Extratores ----------
    def extrair_linha(self, texto):
        for linha in self.linhas_eletricas:
            if re.search(rf"\b{re.escape(linha)}\b", texto):
                return linha
        return None

    def extrair_formato_placa(self, texto):
        return self._regex(r"\b\dX\d\b", texto)

    def extrair_formato_metragem(self, texto):
        return self._regex(r"\b\d{1,2}M\b", texto)

    def extrair_cor(self, texto):
        for cor in ["BRANCO", "PRETO", "CINZA", "MARROM"]:
            if cor in texto:
                return cor
        return None

    def extrair_funcao(self, texto):
        m = re.search(r"\((.*?)\)", texto)
        if m:
            return m.group(1).strip()

        for p in [
            r"\bTOMADA\s?\d{1,2}A\b",
            r"\b\dS\b",
            r"\b\dP\+T\b",
        ]:
            m = re.search(p, texto)
            if m:
                return m.group(0)

        return None

    def extrair_amperagem(self, texto):
        return self._regex(r"\b\d{1,2}A\b", texto)

    def extrair_polos(self, texto):
        return self._regex(r"\b\dP\+?T?\b", texto)

    # ---------- Delegação ----------
    def extrair_por_grupo(self, texto, grupo):
        if grupo in {"CONJUNTO", "MODULO", "PLACA"}:
            return {
                "linha": self.extrair_linha(texto),
                "formato": self.extrair_formato_placa(texto),
                "cor": self.extrair_cor(texto),
                "funcao": self.extrair_funcao(texto),
                "amperagem": None,
                "polos": None,
            }

        if grupo == "PROLONGADOR":
            return {
                "linha": None,
                "formato": self.extrair_formato_metragem(texto),
                "cor": None,
                "funcao": None,
                "amperagem": self.extrair_amperagem(texto),
                "polos": None,
            }

        if grupo == "PLUG_MACHO":
            return {
                "linha": None,
                "formato": None,
                "cor": None,
                "funcao": None,
                "amperagem": self.extrair_amperagem(texto),
                "polos": self.extrair_polos(texto),
            }

        if grupo in {"CANALETA", "BARRA", "SOBREPOR"}:
            return {
                "linha": None,
                "formato": self.extrair_formato_metragem(texto),
                "cor": None,
                "funcao": None,
                "amperagem": None,
                "polos": None,
            }

        return {
            "linha": None,
            "formato": None,
            "cor": None,
            "funcao": None,
            "amperagem": None,
            "polos": None,
        }

    # ---------- Público ----------
    def extrair(self, descricao_limpa, categoria, grupo_eletrico):
        if not self._categoria_valida(categoria):
            return {}

        if pd.isna(descricao_limpa):
            return {}

        return self.extrair_por_grupo(descricao_limpa.upper(), grupo_eletrico)


linhas_eletricas = { "STYLUS", "MILL", "PETRA", "STECK", "INTERNEED", "FAME", "ARIA", "LIZ", "LUX", "FC", }

extrator_eletrico = ElectricAttributeExtractor(
    linhas_eletricas=linhas_eletricas
)

df = pd.read_excel('/home/lucas-silva/auto_shopee/planilhas/outputs/Descrição_Norm.xlsx')

atributos = df.apply(
    lambda r: extrator_eletrico.extrair(
        r["Descricao_Limpa"],
        r["Categoria"],
        r["grupo_eletrico"],
    ),
    axis=1,
)

df = pd.concat([df, atributos.apply(pd.Series)], axis=1)

