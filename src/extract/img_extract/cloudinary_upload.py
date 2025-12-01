import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import cloudinary
import cloudinary.uploader
import pandas as pd
from PIL import Image, ImageOps
from tqdm import tqdm


class ImageOptimizerUploader:
    def __init__(
        self,
        cloudinary_config_path="/home/lucas-silva/auto_shopee/src/extract/img_extract/json_files/cloudinary_config.json",
        qualidade=85,
        tamanho_padrao=(1000, 1000),
    ):
        self.cloudinary_config_path = cloudinary_config_path
        self.qualidade = qualidade
        self.tamanho_padrao = tamanho_padrao

        self.project_dir = "/home/lucas-silva/auto_shopee"
        self.input_folder = f"{self.project_dir}/src/extract/img_extract/imagens"
        self.optimized_folder = f"{self.project_dir}/src/extract/img_extract/imagens_otimizadas"
        os.makedirs(self.optimized_folder, exist_ok=True)

        self._load_cloudinary_config()
        self.resultados = []

    def _load_cloudinary_config(self):
        with open(self.cloudinary_config_path, "r", encoding="utf-8") as f:
            secrets = json.load(f)

        cloudinary.config(
            cloud_name=secrets["cloud_name"],
            api_key=secrets["api_key"],
            api_secret=secrets["api_secret"],
        )

    def _carregar_resultados_existentes(self, output_csv_path):
        """
        Lê o CSV existente (se houver) e retorna:
        - set com nomes de arquivos já processados
        - lista de resultados já salvos
        """
        if output_csv_path and os.path.exists(output_csv_path):
            df_existente = pd.read_csv(output_csv_path)
            # garante que tenha as colunas esperadas
            if {"arquivo", "url_cloudinary"}.issubset(df_existente.columns):
                processados = set(df_existente["arquivo"].astype(str))
                resultados_existentes = df_existente.to_dict("records")
                return processados, resultados_existentes

        return set(), []

    def processar_imagens(self, output_csv_path=None, max_workers=4):
        # Carrega o que já foi processado antes
        arquivos_processados, resultados_existentes = self._carregar_resultados_existentes(
            output_csv_path
        )
        self.resultados = resultados_existentes

        # Lista todos os arquivos da pasta de entrada
        todos_arquivos = [
            f
            for f in os.listdir(self.input_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]

        # Filtra apenas os que ainda não foram processados
        novos_arquivos = [f for f in todos_arquivos if f not in arquivos_processados]

        if not novos_arquivos:
            print("✅ Nenhuma nova imagem para processar. Tudo já está no CSV.")
            return

        print(f"🔎 Encontradas {len(todos_arquivos)} imagens, "
              f"{len(arquivos_processados)} já processadas, "
              f"{len(novos_arquivos)} novas para processar.")

        resultados_novos = []

        # Multithreading para processar as novas imagens
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._processar_imagem, file): file
                for file in novos_arquivos
            }

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Processando imagens",
                unit="img",
            ):
                try:
                    result = future.result()
                    if result:
                        resultados_novos.append(result)
                except Exception as e:
                    file = futures[future]
                    print(f"❌ Erro inesperado na thread para {file}: {e}")

        # Junta resultados antigos + novos
        self.resultados.extend(resultados_novos)

        # Salva CSV apenas uma vez no final
        if output_csv_path:
            df = pd.DataFrame(self.resultados)
            df.to_csv(output_csv_path, index=False)
            print(f"💾 CSV atualizado em: {output_csv_path}")

    def _processar_imagem(self, file):
        """
        Processa UMA imagem e retorna um dict:
        {"arquivo": file, "url_cloudinary": url}
        Em caso de erro, retorna None.
        """
        try:
            caminho = os.path.join(self.input_folder, file)
            otimizado_path = os.path.join(self.optimized_folder, file)

            # Abrir
            img = Image.open(caminho).convert("RGB")

            # Redimensionar
            img_otimizada = ImageOps.pad(
                img,
                self.tamanho_padrao,
                color=(255, 255, 255),
                method=Image.Resampling.LANCZOS,
            )

            # Salvar temporário
            img_otimizada.save(
                otimizado_path, optimize=True, quality=self.qualidade
            )

            # Upload
            upload_result = cloudinary.uploader.upload(
                otimizado_path,
                folder="imagens_otimizadas_marketplace",
                use_filename=True,
                unique_filename=False,
            )

            url_otimizada = upload_result["secure_url"].replace(
                "/upload/", "/upload/f_auto,q_auto/"
            )

            return {"arquivo": file, "url_cloudinary": url_otimizada}

        except Exception as e:
            print(f"❌ Erro ao processar {file}: {e}")
            return None


# Exemplo de uso
processor = ImageOptimizerUploader()

processor.processar_imagens(
    output_csv_path="/home/lucas-silva/auto_shopee/planilhas/input/urls_cloudinary.csv",
    max_workers=8,  # ajusta conforme a máquina/conexão
)
