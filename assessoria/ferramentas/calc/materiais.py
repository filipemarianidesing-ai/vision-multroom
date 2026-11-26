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


# ----------------------------------------------------------------------------- referências de mercado
REF_MERCADO = BASE.with_name("referencias-mercado-vicoustic.json")
OITAVAS = {125: (100, 125, 160), 250: (200, 250, 315), 500: (400, 500, 630),
           1000: (800, 1000, 1250), 2000: (1600, 2000, 2500), 4000: (3150, 4000, 5000)}


def referencias() -> dict:
    """Produtos de referência (benchmark) com curvas declaradas em terços de oitava."""
    d = json.loads(REF_MERCADO.read_text(encoding="utf-8"))
    return {i["id"]: i for i in d["catalogo_curvas"]}


def curva_referencia(ref_id: str, modelo: str | None = None, tipo: str = "absorcao") -> dict[int, float]:
    """Curva em terços de oitava {Hz: valor} de um produto de referência."""
    it = referencias()[ref_id]
    cs = [c for c in it["curvas"] if c["tipo"] == tipo and (modelo is None or (c["modelo"] or "").startswith(modelo))]
    if not cs:
        raise KeyError(f"{ref_id}: sem curva '{tipo}'" + (f" para o modelo '{modelo}'" if modelo else ""))
    if len(cs) > 1 and modelo is None:
        raise ValueError(f"{ref_id}: várias curvas {[c['modelo'] for c in cs]} — informe 'modelo'")
    return {int(k): v for k, v in cs[0]["valores_terco_oitava"].items()}


def para_oitavas(curva_terco: dict[int, float]) -> dict[int, float]:
    """Média aritmética dos três terços de cada oitava (125–4000 Hz), arredondada a 0,01."""
    return {b: round(sum(curva_terco[f] for f in fs) / 3, 2) for b, fs in OITAVAS.items()}


def superficie_referencia(ref_id: str, area_m2: float, modelo: str | None = None,
                          aceitar_declarado: bool = False) -> Superficie:
    """Superfície com α por oitava de um produto de REFERÊNCIA (valores declarados pelo fabricante, ensaio não
    identificado). Exige aceitar_declarado=True e marca a fonte como [S-declarado]: serve para comparar construções
    e pré-dimensionar; o material fabricado pela Mariani precisa de ensaio próprio."""
    if not aceitar_declarado:
        raise DadoInsuficiente(f"{ref_id}: valores declarados pelo fabricante sem norma/laboratório/montagem. "
                               "Use aceitar_declarado=True para referência de pré-dimensionamento.")
    it = referencias()[ref_id]
    alfa = para_oitavas(curva_referencia(ref_id, modelo))
    rotulo = f"{it['produto']}" + (f" — {modelo}" if modelo else "")
    return Superficie(ref_id, area_m2, alfa,
                      f"[S-declarado] referência de mercado {rotulo}; {it['fonte']['arquivo']} ({it['fonte']['paginas']}); "
                      f"ensaio não identificado — não é desempenho do material Mariani")
