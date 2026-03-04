from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ExtractionResult:
    """
    Resultado padronizado retornado pelos extractors.

    values:
        Campos estruturados extraídos da descrição.
        Exemplo:
        {"Medida": "0.11cmX0.50cm", "Cor": "BRANCO"}

    consumed:
        Trechos da descrição que foram utilizados para gerar os valores.
        Esses tokens podem ser removidos ao gerar o Nome_Produto_Base.

        Exemplo:
        ["0,11X0,50CM", "BRANCO"]

    meta:
        Informações extras opcionais para debug ou auditoria.
    """

    values: Dict[str, str] = field(default_factory=dict)

    consumed: List[str] = field(default_factory=list)

    meta: Dict[str, str] = field(default_factory=dict)

    def is_empty(self) -> bool:
        """Verifica se não houve extração."""
        return not self.values

    def merge(self, other: "ExtractionResult"):
        """
        Combina resultados de dois extractors.

        - valores novos sobrescrevem valores antigos
        - tokens consumidos são unidos
        """

        if not isinstance(other, ExtractionResult):
            return

        self.values.update(other.values)

        for token in other.consumed:
            if token not in self.consumed:
                self.consumed.append(token)

        self.meta.update(other.meta)
