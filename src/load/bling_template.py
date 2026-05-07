import pandas as pd


class GeradorBling:

    def __init__(self):

        # ==========================================
        # ARQUIVOS
        # ==========================================

        self.arquivo_template = "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_bling.xlsx"
        self.arquivo_produtos = "/home/lucas-silva/auto_shopee/produtos_com_descricoes.xlsx"
        self.saida = "bling_teste.xlsx"

        # ==========================================
        # LIMITE TESTE
        # ==========================================

        self.LIMITE_TESTE = 20

        # ==========================================
        # LEITURA
        # ==========================================

        self.bling = pd.read_excel(self.arquivo_template)

        self.produtos = pd.read_excel(
            self.arquivo_produtos
        )

        # ==========================================
        # TESTE
        # ==========================================

        self.produtos = self.produtos.head(
            self.LIMITE_TESTE
        )

        self.bling_colunas = (
            self.bling.columns.tolist()
        )

    # ==========================================
    # VARIAÇÕES
    # ==========================================

    def montar_variacoes(self, item):

        variacoes = []

        for i in range(1, 6):

            nome = str(
                item.get(f"variacao_{i}_nome", "")
                or ""
            ).strip()

            valor = str(
                item.get(f"variacao_{i}_valor", "")
                or ""
            ).strip()

            if (
                nome
                and valor
                and nome.lower() != "nan"
                and valor.lower() != "nan"
            ):

                variacoes.append(
                    f"{nome}:{valor}"
                )

        return ";".join(variacoes)

    # ==========================================
    # IMAGENS
    # ==========================================

    def montar_imagens(self, item):

        urls = [
            str(item.get("Url_Imagem1.0", "") or ""),
            str(item.get("Url_Imagem2.0", "") or ""),
            str(item.get("Url_Imagem3.0", "") or ""),
            str(item.get("Url Imagem", "") or ""),
        ]

        urls = [
            u.strip()
            for u in urls
            if (
                u
                and u.lower() != "nan"
                and u.strip() != ""
            )
        ]

        return "|".join(urls)

    # ==========================================
    # LINHA BLING
    # ==========================================

    def criar_linha(self, item):

        linha = {
            col: ""
            for col in self.bling_colunas
        }

        tipo = str(
            item.get("Tipo", "")
        ).upper()

        # ==========================================
        # VARIAÇÕES
        # ==========================================

        descricao_variacao = (
            self.montar_variacoes(item)
        )

        # ==========================================
        # DESCRIÇÃO PRINCIPAL
        # ==========================================

        if tipo == "PAI":

            descricao_bling = str(
                item.get("nome_base", "")
                or item.get("Descrição", "")
            )

            codigo_pai = ""
            codigo_integracao = ""

        else:

            descricao_bling = (
                descricao_variacao
            )

            codigo_pai = item.get(
                "SKU_Pai",
                ""
            )

            codigo_integracao = item.get(
                "ID_Variacao",
                ""
            )

        # ==========================================
        # DESCRIÇÃO IA
        # ==========================================

        descricao_ia = item.get(
            "descricao_ia",
            ""
        )

        # ==========================================
        # MAPA
        # ==========================================

        mapa = {

            # ===== PRINCIPAIS =====

            "Código": item.get(
                "Sku",
                ""
            ),

            "Descrição": descricao_bling,

            "NCM": item.get(
                "NCM",
                ""
            ),

            "Origem": "0",

            # ===== PREÇOS =====

            "Preço": item.get(
                "Preço Final",
                ""
            ),

            "Preço de custo": item.get(
                "Valor_unitário",
                ""
            ),

            "Preço de compra": item.get(
                "Valor Unitário",
                ""
            ),

            # ===== STATUS =====

            "Situação": "Ativo",

            "Condição do produto": "Novo",

            # ===== ESTOQUE =====

            "Estoque": "0",

            "Estoque maximo": "1000",

            "Estoque minimo": "5",

            # ===== PESO =====

            "Peso líquido (Kg)": item.get(
                "Peso",
                ""
            ),

            "Peso bruto (Kg)": item.get(
                "Peso",
                ""
            ),

            # ===== DIMENSÕES =====

            "Largura do Produto": item.get(
                "Largura",
                ""
            ),

            "Altura do Produto": item.get(
                "Altura",
                ""
            ),

            "Profundidade do produto": item.get(
                "Comprimento",
                ""
            ),

            # ===== DESCRIÇÕES =====

            "Descrição do Produto no Fornecedor": (
                descricao_ia
            ),

            "Descrição Complementar": (
                descricao_ia
            ),

            "Descrição Curta": item.get(
                "Descrição",
                ""
            ),

            # ===== FORNECEDOR =====

            "Fornecedor": item.get(
                "Fornecedor",
                ""
            ),

            "Marca": item.get(
                "Marca",
                ""
            ),

            # ===== IMAGENS =====

            "URL Imagens Externas": (
                self.montar_imagens(item)
            ),

            # ===== VARIAÇÕES =====

            "Código Pai": codigo_pai,

            "Código Integração": (
                codigo_integracao
            ),

            "Clonar dados do pai": "",

            # ===== OUTROS =====

            "Departamento": item.get(
                "Categoria",
                ""
            ),

            "Categoria do produto": (
                "Materiais de Construção"
            ),
        }

        linha.update(mapa)

        return linha

    # ==========================================
    # GERA PLANILHA
    # ==========================================

    def gerar(self):

        linhas_bling = []

        # ==========================================
        # AGRUPA
        # ==========================================
        print(self.produtos.columns.tolist())
        
        grupos = self.produtos.groupby(
            "SKU_Pai"
        )

        total_grupos = len(grupos)

        for i, (sku_pai, grupo) in enumerate(
            grupos,
            start=1
        ):

            print(
                f"[{i}/{total_grupos}] "
                f"Grupo {sku_pai}"
            )

            # ==========================================
            # PAI
            # ==========================================

            primeiro = grupo.iloc[0].copy()

            pai = primeiro.copy()

            pai["Tipo"] = "PAI"

            pai["Sku"] = sku_pai

            linha_pai = self.criar_linha(
                pai
            )

            linhas_bling.append(
                linha_pai
            )

            # ==========================================
            # FILHOS
            # ==========================================

            for _, row in grupo.iterrows():

                filho = row.copy()

                filho["Tipo"] = "FILHO"

                linha_filho = (
                    self.criar_linha(
                        filho
                    )
                )

                linhas_bling.append(
                    linha_filho
                )

        # ==========================================
        # DATAFRAME
        # ==========================================

        df_final = pd.DataFrame(
            linhas_bling,
            columns=self.bling_colunas
        )

        # ==========================================
        # SALVA
        # ==========================================

        df_final.to_excel(
            self.saida,
            index=False
        )

        print("=" * 50)
        print(
            "PLANILHA BLING GERADA"
        )
        print("=" * 50)
        print(
            f"Arquivo: {self.saida}"
        )
        print(
            f"Linhas: {len(df_final)}"
        )
        print("=" * 50)


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":

    gerador = GeradorBling()

    gerador.gerar()
