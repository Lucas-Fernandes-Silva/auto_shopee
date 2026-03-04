import re


class MedidaAxBExtractor:
    
    NUM = r"(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)"
    UNIDADE = r"(?:mm|cm|m|\"|pol)?"

    PADRAO_2D = re.compile(
        rf"\b({NUM})\s*({UNIDADE})?\s*[xX×]\s*({NUM})\s*({UNIDADE})?",
        re.IGNORECASE,
    )

    PADRAO_3D = re.compile(
        rf"\b({NUM})\s*({UNIDADE})?\s*[xX×]\s*({NUM})\s*({UNIDADE})?\s*[xX×]\s*({NUM})\s*({UNIDADE})?",
        re.IGNORECASE,
    )

    def _norm_num(self, s: str) -> str:
        """Normaliza números mantendo frações."""
        s = s.strip()

        if "/" in s:
            return s

        return s.replace(",", ".")

    def _norm_un(self, un: str | None) -> str | None:
        if not un:
            return None

        u = un.strip().lower()

        if u in ("pol", '"'):
            return '"'

        return u

    def extrair(self, descricao: str) -> dict:
        if not isinstance(descricao, str):
            return {}

        texto = descricao.lower()

        # ---------- AxBxC ----------
        m3 = self.PADRAO_3D.search(texto)

        if m3:
            a, ua, b, ub, c, uc = (
                m3.group(1),
                m3.group(2),
                m3.group(3),
                m3.group(4),
                m3.group(5),
                m3.group(6),
            )

            nums = [
                self._norm_num(a),
                self._norm_num(b),
                self._norm_num(c),
            ]

            uns = [
                self._norm_un(ua),
                self._norm_un(ub),
                self._norm_un(uc),
            ]

            unidade = next((u for u in reversed(uns) if u), None)

            partes = [
                f"{n}{u or unidade or ''}" for n, u in zip(nums, uns)
            ]

            return {"Medida": "X".join(partes)}

        # ---------- AxB ----------
        m2 = self.PADRAO_2D.search(texto)

        if not m2:
            return {}

        a, ua, b, ub = m2.group(1), m2.group(2), m2.group(3), m2.group(4)

        nums = [
            self._norm_num(a),
            self._norm_num(b),
        ]

        uns = [
            self._norm_un(ua),
            self._norm_un(ub),
        ]

        unidade = next((u for u in reversed(uns) if u), None)

        partes = [
            f"{n}{u or unidade or ''}" for n, u in zip(nums, uns)
        ]

        return {"Medida": "X".join(partes)}
