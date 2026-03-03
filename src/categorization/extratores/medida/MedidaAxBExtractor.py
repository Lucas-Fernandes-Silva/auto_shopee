import re


class MedidaAxBExtractor:
    # NUM pode ser:
    # - decimal/inteiro: 50 | 4,5 | 0,11 | 4.5
    # - fração: 3/4 | 1/2
    # - misto padrão: 1 1/2
    # - misto "zoado": 1,1/2 | 1.1/2 | 1-1/2  (vamos normalizar depois)
    TOKEN_NUM = r"(?:\d+\s+\d+/\d+|\d+[.,-]\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
    TOKEN_UN = r"(?:mm|cm|m|\"|pol|')"

    # AxB (sem \b perto do X pra não quebrar 0,11X0,70)
    PADRAO_AXB = re.compile(
        rf"({TOKEN_NUM})\s*({TOKEN_UN})?\s*[xX×]\s*({TOKEN_NUM})\s*({TOKEN_UN})?",
        re.IGNORECASE
    )

    # AxBxC
    PADRAO_AXBXC = re.compile(
        rf"({TOKEN_NUM})\s*({TOKEN_UN})?\s*[xX×]\s*({TOKEN_NUM})\s*({TOKEN_UN})?\s*[xX×]\s*({TOKEN_NUM})\s*({TOKEN_UN})?",
        re.IGNORECASE
    )

    PADRAO_FRACAO_OU_MISTO = re.compile(r"^\s*(?:\d+\s+\d+/\d+|\d+/\d+|\d+[.,-]\d+/\d+)\s*$")

    def _norm_un(self, un: str | None) -> str | None:
        if not un:
            return None
        u = un.strip().lower()
        return '"' if u in ("pol", '"', "'") else u

    def _norm_num(self, s: str) -> str:
        s = s.strip()
        s = re.sub(r"\s+", " ", s)

        # corrige misto zoado: 1,1/2 / 1.1/2 / 1-1/2  -> 1 1/2
        s = re.sub(r"^(\d+)\s*[.,-]\s*(\d+/\d+)$", r"\1 \2", s)

        # se for fração/misto, mantém; se for decimal normal, troca vírgula por ponto
        if "/" in s:
            return s
        return s.replace(",", ".")

    def _is_fracao_ou_misto(self, s: str) -> bool:
        return self.PADRAO_FRACAO_OU_MISTO.match(s.strip()) is not None

    def _aplicar_unidade_em_falta(self, nums: list[str], uns: list[str | None]) -> list[str]:
        """
        Regras:
        - Se só o último tem unidade (ex: 0,11X0,70CM), aplica a mesma unidade pros anteriores.
        - Se algum token for fração/misto e não houver unidade, assume polegada (").
        - Se houver mistura (ex: um lado mm e outro sem), aplica a unidade existente ao que falta.
        """
        # 1) se existe alguma unidade explícita, tenta propagar
        # (prioriza unidade do último valor, pq é bem comum em catálogos)
        un_preferida = None
        for u in reversed(uns):
            if u:
                un_preferida = u
                break

        if un_preferida:
            uns = [u or un_preferida for u in uns]

        # 2) fração/misto sem unidade -> polegada (se ainda estiver None)
        uns = [u if u is not None else ('"' if self._is_fracao_ou_misto(n) else None) for n, u in zip(nums, uns)]

        # 3) monta com unidade (se houver)
        partes = []
        for n, u in zip(nums, uns):
            partes.append(f"{n}{u or ''}")
        return partes

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str) or not descricao.strip():
            return {}

        texto = descricao.lower()

        # 1) tenta AxBxC primeiro
        m3 = self.PADRAO_AXBXC.search(texto)
        if m3:
            a_raw, ua_raw, b_raw, ub_raw, c_raw, uc_raw = m3.group(1), m3.group(2), m3.group(3), m3.group(4), m3.group(5), m3.group(6)

            nums = [self._norm_num(a_raw), self._norm_num(b_raw), self._norm_num(c_raw)]
            uns = [self._norm_un(ua_raw), self._norm_un(ub_raw), self._norm_un(uc_raw)]

            partes = self._aplicar_unidade_em_falta(nums, uns)
            return {"Medida": "X".join(partes)}

        # 2) AxB
        m2 = self.PADRAO_AXB.search(texto)
        if not m2:
            return {}

        a_raw, ua_raw, b_raw, ub_raw = m2.group(1), m2.group(2), m2.group(3), m2.group(4)

        nums = [self._norm_num(a_raw), self._norm_num(b_raw)]
        uns = [self._norm_un(ua_raw), self._norm_un(ub_raw)]

        partes = self._aplicar_unidade_em_falta(nums, uns)
        return {"Medida": "X".join(partes)}
