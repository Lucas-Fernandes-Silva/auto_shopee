import re
from collections import defaultdict

import pandas as pd
from rapidfuzz import fuzz
from tqdm import tqdm


class DomainClassifier:
    def __init__(
        self,
        df_dominios,
        fuzzy_threshold=85,
        peso_exato=2.0,
        peso_fuzzy=1.0,
        score_minimo=0.3,
        delta_minimo=0.15,
    ):
        self.fuzzy_threshold = fuzzy_threshold
        self.peso_exato = peso_exato
        self.peso_fuzzy = peso_fuzzy
        self.score_minimo = score_minimo
        self.delta_minimo = delta_minimo

        # 🔒 Domínios que NÃO podem ser classificados só por fuzzy
        self.dominios_sem_fuzzy = {"FIXADORES"}

        # Relatório de fallback / ambiguidade
        self.relatorios_fallback = []

        # Carrega termos por domínio
        self.dominios = defaultdict(list)
        for _, row in df_dominios.iterrows():
            dominio = row.get("dominio")
            termo = row.get("termo")

            if pd.isna(dominio) or pd.isna(termo):
                continue

            self.dominios[str(dominio).upper()].append(
                str(termo).upper()
            )

        self.total_termos = {
            dominio: len(termos)
            for dominio, termos in self.dominios.items()
        }

    def classificar(self, descricao):
        # ========= BLINDAGEM =========
        if descricao is None:
            return None, 0.0

        descricao = str(descricao).strip()
        if not descricao or descricao.lower() == "nan":
            return None, 0.0

        descricao_up = descricao.upper()

        pontuacao = defaultdict(float)
        matches_exatos = defaultdict(int)

        # =====================
        # 1. MATCH EXATO (REGEX)
        # =====================
        for dominio, termos in self.dominios.items():
            for termo in termos:
                if re.search(rf"\b{re.escape(termo)}\b", descricao_up):
                    pontuacao[dominio] += self.peso_exato
                    matches_exatos[dominio] += 1

        # =====================
        # 2. FUZZY (CONTROLADO)
        # =====================
        for dominio, termos in self.dominios.items():

            # 🚫 FIXADORES: fuzzy só se houve match exato
            if (
                dominio in self.dominios_sem_fuzzy
                and matches_exatos[dominio] == 0
            ):
                continue

            for termo in termos:
                score = fuzz.partial_ratio(termo, descricao_up)
                if score >= self.fuzzy_threshold:
                    pontuacao[dominio] += (
                        (score / 100) * self.peso_fuzzy
                    )

        if not pontuacao:
            self._registrar_fallback(
                descricao, None, 0.0, []
            )
            return None, 0.0

        # =====================
        # 3. RANKING
        # =====================
        ranking = sorted(
            pontuacao.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        dominio_top1, score_bruto_top1 = ranking[0]

        # 🔒 Segurança extra: FIXADORES sem match exato NÃO PASSA
        if (
            dominio_top1 == "FIXADORES"
            and matches_exatos["FIXADORES"] == 0
        ):
            self._registrar_fallback(
                descricao, None, 0.0, ranking[:3]
            )
            return None, 0.0

        normalizador = (
            self.total_termos.get(dominio_top1, 1)
            * self.peso_exato
        )

        score_top1 = min(score_bruto_top1 / normalizador, 1.0)

        # =====================
        # 4. AMBIGUIDADE
        # =====================
        ambiguidade = False
        delta = None

        if len(ranking) > 1:
            _, score_bruto_top2 = ranking[1]
            score_top2 = min(
                score_bruto_top2 / normalizador, 1.0
            )
            delta = round(score_top1 - score_top2, 3)

            if delta < self.delta_minimo:
                ambiguidade = True

        if score_top1 < self.score_minimo:
            ambiguidade = True

        if ambiguidade:
            self._registrar_fallback(
                descricao,
                dominio_top1,
                round(score_top1, 3),
                ranking[:3],
            )

        return dominio_top1, round(score_top1, 3)

    # =====================
    # RELATÓRIO
    # =====================
    def _registrar_fallback(
        self, descricao, dominio, score, ranking
    ):
        self.relatorios_fallback.append(
            {
                "descricao": descricao,
                "dominio_sugerido": dominio,
                "score": score,
                "ranking_dominios": ranking,
            }
        )

    def get_relatorio_fallback(self):
        if not self.relatorios_fallback:
            return pd.DataFrame()

        return pd.DataFrame(self.relatorios_fallback)

    # =====================
    # DATAFRAME
    # =====================
    def classificar_dataframe(
        self,
        df,
        coluna_descricao,
        col_dominio="Dominio",
        col_score="Score_Dominio",
    ):
        tqdm.pandas(desc="Classificando domínios")

        resultados = df[coluna_descricao].progress_apply(
            self.classificar
        )

        df[[col_dominio, col_score]] = pd.DataFrame(
            resultados.tolist(), index=df.index
        )

        return df
