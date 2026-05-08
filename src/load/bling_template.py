import pandas as pd


class GeradorBling:

    def __init__(self):

        # ==========================================
        # ARQUIVOS
        # ==========================================

        self.arquivo_template = (
            "/home/lucas-silva/auto_shopee/planilhas/input/colunas_produtos_bling.xlsx"
        )

        self.arquivo_produtos = (
            "/home/lucas-silva/auto_shopee/planilhas/outputs/Produtos.xlsx"
        )

        self.saida = "bling.xlsx"

        # ==========================================
        # LIMITE TESTE
        # ==========================================

        self.LIMITE_TESTE = 5000

        # ==========================================
        # LEITURA
        # ==========================================

        self.bling = pd.read_excel(
            self.arquivo_template
        )

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
                item.get(
                    f"variacao_{i}_nome",
                    ""
                ) or ""
            ).strip()

            valor = str(
                item.get(
                    f"variacao_{i}_valor",
                    ""
                ) or ""
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
            str(
                item.get(
                    "Url_Imagem1.0",
                    ""
                ) or ""
            ),

            str(
                item.get(
                    "Url_Imagem2.0",
                    ""
                ) or ""
            ),

            str(
                item.get(
                    "Url_Imagem3.0",
                    ""
                ) or ""
            ),

            str(
                item.get(
                    "Url Imagem",
                    ""
                ) or ""
            ),
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
    # GERA CÓDIGO PAI
    # ==========================================

    def gerar_codigo_pai(self, item):

        grupo_id = str(
            item.get(
                "grupo_id",
                ""
            ) or ""
        ).strip()

        return f"PAI-{grupo_id}"

    # ==========================================
    # LINHA BLING
    # ==========================================

    def criar_linha(self, item):

        linha = {
            col: ""
            for col in self.bling_colunas
        }

        tipo = str(
            item.get(
                "Tipo",
                ""
            ) or ""
        ).upper()

        # ==========================================
        # VARIAÇÕES
        # ==========================================

        descricao_variacao = (
            self.montar_variacoes(item)
        )

        # ==========================================
        # DESCRIÇÃO
        # ==========================================

        if tipo == "PAI":

            descricao_bling = str(
                item.get(
                    "nome_base",
                    ""
                )
                or item.get(
                    "Descrição",
                    ""
                )
                or item.get(
                    "descricao",
                    ""
                )
                or "PRODUTO SEM NOME"
            ).strip()

        elif tipo == "FILHO":

            descricao_bling = (
                descricao_variacao
            )

        else:

            descricao_bling = str(
                item.get(
                    "Descrição",
                    ""
                )
                or item.get(
                    "descricao",
                    ""
                )
                or "PRODUTO SEM NOME"
            ).strip()

        # ==========================================
        # DESCRIÇÃO IA
        # ==========================================

        descricao_ia = item.get(
            "descricao_ia",
            ""
        )

        # ==========================================
        # CÓDIGOS
        # ==========================================

        codigo_pai = self.gerar_codigo_pai(
            item
        )

        codigo_produto = str(
            item.get(
                "Codigo Produto",
                ""
            ) or ""
        ).strip()

        # ==========================================
        # MAPA
        # ==========================================

        mapa = {

            # ===== PRINCIPAIS =====

            "Código": (
                codigo_pai
                if tipo == "PAI"
                else codigo_produto
            ),

            "Unidade": item.get(
                "Unidade",
                ""
            ),

            "Descrição": (
                descricao_bling
            ),

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

            # ===== GTIN =====

            "GTIN/EAN": (
                ""
                if tipo == "PAI"
                else item.get(
                    "Código de Barras",
                    ""
                )
            ),

            "GTIN/EAN da embalagem": (
                ""
                if tipo == "PAI"
                else item.get(
                    "Código de Barras",
                    ""
                )
            ),

            # ===== STATUS =====

            "Situação": "Ativo",

            "Condição do produto": (
                "Novo"
            ),

            # ===== ESTOQUE =====

            "Estoque": "0",

            "Estoque maximo": "1000",

            "Estoque minimo": "5",

            # ===== PESOS =====

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

            "Descrição Curta": (
                descricao_ia
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
                self.montar_imagens(
                    item
                )
            ),

            # ===== VARIAÇÕES =====

            "Código Pai": (
                ""
                if tipo == "PAI"
                else codigo_pai
            ),

            "Código Integração": item.get(
                "grupo_id",
                ""
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

        grupos_processados = set()

        total = len(self.produtos)

        for i, (_, row) in enumerate(
            self.produtos.iterrows(),
            start=1
        ):

            print(f"[{i}/{total}]")

            grupo_id = str(
                row.get(
                    "grupo_id",
                    ""
                ) or ""
            ).strip()

            # ==========================================
            # PRODUTO ÚNICO
            # ==========================================

            if (
                not grupo_id
                or grupo_id.lower() == "nan"
            ):

                unico = row.copy()

                unico["Tipo"] = "UNICO"

                linha_unico = self.criar_linha(
                    unico
                )

                linhas_bling.append(
                    linha_unico
                )

                continue

            # ==========================================
            # CRIA PAI UMA VEZ
            # ==========================================

            if grupo_id not in grupos_processados:

                pai = row.copy()

                pai["Tipo"] = "PAI"

                linha_pai = self.criar_linha(
                    pai
                )

                linhas_bling.append(
                    linha_pai
                )

                grupos_processados.add(
                    grupo_id
                )

            # ==========================================
            # FILHO
            # ==========================================

            filho = row.copy()

            filho["Tipo"] = "FILHO"

            linha_filho = self.criar_linha(
                filho
            )

            linhas_bling.append(
                linha_filho
            )

        # ==========================================
        # DATAFRAME FINAL
        # ==========================================

        df_final = pd.DataFrame(
            linhas_bling,
            columns=self.bling_colunas
        )

        # ==========================================
        # EXPORTA
        # ==========================================

        df_final.to_excel(
            self.saida,
            index=False
        )

        print("=" * 50)
        print("PLANILHA BLING GERADA")
        print("=" * 50)
        print(f"Arquivo: {self.saida}")
        print(f"Linhas: {len(df_final)}")
        print("=" * 50)


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":

    gerador = GeradorBling()

    gerador.gerar()
