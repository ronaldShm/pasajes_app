"""Detector automático de aerolínea basado en contenido del documento."""
from typing import Optional
from extractors.base import BaseExtractor
from extractors.latam import LATAMExtractor
from extractors.sky import SKYExtractor
from extractors.jetsmart import JetSMARTExtractor


class AirlineDetector:
    def __init__(self):
        self.extractors: list[BaseExtractor] = [
            LATAMExtractor(),
            SKYExtractor(),
            JetSMARTExtractor(),
        ]

    def detect(self, text: str) -> Optional[BaseExtractor]:
        for extractor in self.extractors:
            if extractor.detect(text):
                return extractor
        return None

    def get_airline_name(self, text: str) -> str:
        extractor = self.detect(text)
        if extractor:
            if isinstance(extractor, LATAMExtractor):
                return "LATAM"
            elif isinstance(extractor, SKYExtractor):
                return "SKY"
            elif isinstance(extractor, JetSMARTExtractor):
                return "JetSMART"
        return "Desconocida"
