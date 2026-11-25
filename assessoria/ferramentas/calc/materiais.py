"""
Acesso à base de materiais (assessoria/referencias/materiais/materiais.json) para cálculos.

Regra central: um material só vira Superficie por banda se tiver alfa_por_banda com relatório de
ensaio identificado. Para materiais com apenas NRC, a aproximação plana é permitida só com
`aproximar_por_nrc=True`, e a fonte fica marcada como ESTIMATIVA [E] (pré-dimensionamento).
Materiais sem nenhum dado acústico geram erro — não há base para cálculo.

    import sys; sys.path.insert(0, "assessoria/ferramentas/calc")
    import materiais as mt
    forro = mt.superficie("lady-inovawall-28mm", 20.0, aproximar_por_nrc=True, bandas=(500, 1000))
"""
from __future__ import annotations

import json
from pathlib import Path

from acustica import Superficie

BASE = Path(__file__).resolve().parents[2] / "referencias" / "materiais" / "materiais.json"


class DadoInsuficiente(ValueError):
    """O material não tem dado acústico suficiente para o cálculo pedido."""


def carregar() -> dict:
    return {m["id"]: m for m in json.loads(BASE.read_text(encoding="utf-8"))["materiais"]}


def listar() -> list[str]:
    linhas = []
    for m in carregar().values():
        nrc = (m.get("nrc") or {}).get("valor")
        dado = "α por banda" if m.get("alfa_por_banda") else (f"NRC {nrc}" if nrc is not None else "SEM DADO ACÚSTICO")
        linhas.append(f"{m['id']}: {m['linha']} — {dado} — {m['uso_em_calculo'][:80]}…")
    return linhas


def superficie(material_id: str, area_m2: float, aproximar_por_nrc: bool = False,
               bandas: tuple[int, ...] = (500, 1000)) -> Superficie:
    m = carregar().get(material_id)
    if m is None:
        raise KeyError(f"material '{material_id}' não está na base")
    fonte = f"{m['fabricante']} — {m['fonte']['arquivo']} ({m['fonte']['paginas']})"
    if m.get("alfa_por_banda"):
        alfa = {int(k): v for k, v in m["alfa_por_banda"]["valores"].items()}
        return Superficie(m["id"], area_m2, alfa, fonte + f"; ensaio: {m['alfa_por_banda'].get('relatorio')}")
    nrc = (m.get("nrc") or {}).get("valor")
    if nrc is None:
        raise DadoInsuficiente(f"{material_id}: sem α nem NRC no catálogo — {m['uso_em_calculo']}")
    if not aproximar_por_nrc:
        raise DadoInsuficiente(f"{material_id}: só há NRC {nrc} (número único). Use aproximar_por_nrc=True "
                               f"para estimativa [E] de pré-dimensionamento, ou obtenha α por banda.")
    if any(b < 250 or b > 2000 for b in bandas):
        raise DadoInsuficiente("NRC representa 250–2000 Hz; não extrapolar para outras bandas.")
    return Superficie(m["id"], area_m2, {b: nrc for b in bandas},
                      f"ESTIMATIVA [E]: α≈NRC {nrc} (plano, sem ensaio por banda) — {fonte}")
