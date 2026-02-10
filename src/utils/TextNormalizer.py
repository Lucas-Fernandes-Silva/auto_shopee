import re

import pandas as pd

from dados import dados
from src.utils.normalizer import Normalizer


class TextNormalizer:
    def __init__(self):
        self.marca_variacoes = dados.marca_variacoes or {}
        self.mapa_abreviacoes = dados.mapa_abreviacoes or {}

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
                regex_marcas.append(
                    (re.compile(padrao, re.IGNORECASE), marca.upper())
                )

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
        # remove códigos longos (SKU, códigos internos)
        return re.sub(r"\b\d{5,}\b", "", texto)

    def _limpar_caracteres(self, texto):
        # mantém letras, números e símbolos técnicos
        return re.sub(r"[^\w\s\+\-\(\)\/X,]", "", texto)

    # =========================
    # Normalizações específicas
    # =========================
    def _normalizar_decimais(self, texto):
        # 1.50 -> 1,50
        return re.sub(r"(?<=\d)\.(?=\d)", ",", texto)

    def _normalizar_simbolos(self, texto):
        return (
            texto.replace("×", "X")
            .replace("+", " ")
            .replace("-", "")
            .replace("—", "")
            .replace("(", " ")
            .replace(")", " ")
        )

    def _remover_pontos_nao_decimais(self, texto):
        # remove pontos de abreviações (EX: ACR. -> ACR)
        return texto.replace(".", " ")

    # =========================
    # Ruídos
    # =========================
    def _remover_ruidos(self, texto):
        texto = re.sub(r"\bC\/\b", "COM", texto)
        texto = re.sub(r"\bP\/\b", "PARA", texto)
        return texto

    # =========================
    # Marca
    # =========================
    def _normalizar_marca_na_descricao(self, texto, marca):
        if not marca or marca == "GENÉRICO":
            return texto

        texto_norm = Normalizer.normalize(texto)
        marca_norm = Normalizer.normalize(marca)

        # se já contém a marca canônica, não faz nada
        if marca_norm in texto_norm:
            return texto

        # remove qualquer variação da marca
        for regex, marca_padrao in self.regex_marcas:
            if marca_padrao == marca.upper():
                texto = regex.sub("", texto)

        # insere a marca no início
        return f"{marca.upper()} {texto}".strip()

    # =========================
    # Abreviações
    # =========================
    def _padronizar_abreviacoes(self, texto):
        for regex, valor in self.regex_abreviacoes.items():
            texto = regex.sub(valor, texto)
        return texto

    # =========================
    # Método público
    # =========================
    def normalizar(self, descricao, marca=None):
        if pd.isna(descricao):
            return descricao

        t = str(descricao).upper()

        # 🔥 ORDEM IMPORTANTE
        t = self._normalizar_decimais(t)          # 1.50 -> 1,50
        t = self._normalizar_simbolos(t)           # símbolos
        t = self._remover_pontos_nao_decimais(t)   # ACR. -> ACR

        t = self._remover_codigos(t)
        t = self._limpar_caracteres(t)
        t = self._remover_ruidos(t)
        t = self._padronizar_abreviacoes(t)

        if marca:
            t = self._normalizar_marca_na_descricao(t, marca)

        return re.sub(r"\s+", " ", t).strip()
