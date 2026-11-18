"""Traducción local y gratuita con MarianMT (`Helsinki-NLP/opus-mt-{origen}-{destino}`).

El modelo se carga una vez por par de idiomas y queda en memoria (~300 MB cada uno).
"""
from functools import lru_cache


@lru_cache(maxsize=2)
def _modelo(origen: str, destino: str):
    import torch
    from transformers import MarianMTModel, MarianTokenizer

    nombre = f"Helsinki-NLP/opus-mt-{origen}-{destino}"
    disp = "mps" if torch.backends.mps.is_available() else "cpu"
    return MarianTokenizer.from_pretrained(nombre), MarianMTModel.from_pretrained(nombre).to(disp).eval(), disp


def traducir(textos: list[str], origen: str = "en", destino: str = "es", lote: int = 32) -> list[str]:
    import torch

    tok, modelo, disp = _modelo(origen, destino)
    salida = []
    with torch.no_grad():
        for i in range(0, len(textos), lote):
            x = tok(textos[i:i + lote], return_tensors="pt", padding=True, truncation=True).to(disp)
            salida += tok.batch_decode(modelo.generate(**x, max_new_tokens=128), skip_special_tokens=True)
    return salida
