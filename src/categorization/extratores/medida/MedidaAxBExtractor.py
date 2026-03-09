import re


class MedidaAxBExtractor:
    NUM = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
    UNIDADE = r"(?:mm|cm|m|\"|pol|')"

    PADRAO_3D = re.compile(
        rf"({NUM})\s*({UNIDADE})?\s*[xX×]\s*({NUM})\s*({UNIDADE})?\s*[xX×]\s*({NUM})\s*({UNIDADE})?",
        re.IGNORECASE,
    )

    PADRAO_2D = re.compile(
        rf"({NUM})\s*({UNIDADE})?\s*[xX×-]\s*({NUM})\s*({UNIDADE})?",
        re.IGNORECASE,
    )

    def _norm_num(self, s: str) -> str:
        s = s.strip()
        # mantém fração/misto intacto
        if "/" in s:
            s = re.sub(r"\s+", " ", s)  # normaliza espaços no "1 1/2"
            return s
        # decimal: vírgula -> ponto
        return s.replace(",", ".")

    def _norm_un(self, un: str | None) -> str | None:
        if not un:
            return None
        u = un.strip().lower()
        if u in ("pol", '"', "'"):
            return '"'
        return u

    def _assumir_polegada_se_fracao(
        self, nums: list[str], uns: list[str | None]
    ) -> list[str | None]:
        # Se tiver "/" e não tiver unidade explícita, assume polegada (")
        for i, n in enumerate(nums):
            if "/" in n and (uns[i] is None):
                uns[i] = '"'
        # se algum lado virou polegada, aplica pros outros que não têm unidade
        if any(u == '"' for u in uns):
            uns = [u or '"' for u in uns]
        return uns

    def _propagar_unidade_final(self, uns: list[str | None]) -> list[str | None]:
        # Se só o último tem unidade (muito comum), aplica nos anteriores
        unidade = next((u for u in reversed(uns) if u), None)
        if unidade:
            return [u or unidade for u in uns]
        return uns

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {}

        texto = descricao.lower()

        # --- AxBxC primeiro ---
        m3 = self.PADRAO_3D.search(texto)
        if m3:
            nums = [
                self._norm_num(m3.group(1)),
                self._norm_num(m3.group(3)),
                self._norm_num(m3.group(5)),
            ]
            uns = [
                self._norm_un(m3.group(2)),
                self._norm_un(m3.group(4)),
                self._norm_un(m3.group(6)),
            ]

            uns = self._assumir_polegada_se_fracao(nums, uns)
            uns = self._propagar_unidade_final(uns)

            partes = [f"{n}{u or ''}" for n, u in zip(nums, uns)]
            return {"Medida": "X".join(partes)}

        # --- AxB ---
        m2 = self.PADRAO_2D.search(texto)
        if not m2:
            return {}

        nums = [self._norm_num(m2.group(1)), self._norm_num(m2.group(3))]
        uns = [self._norm_un(m2.group(2)), self._norm_un(m2.group(4))]

        uns = self._assumir_polegada_se_fracao(nums, uns)
        uns = self._propagar_unidade_final(uns)

        partes = [f"{n}{u or ''}" for n, u in zip(nums, uns)]
        return {"Medida": "X".join(partes)}
