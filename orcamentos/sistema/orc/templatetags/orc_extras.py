from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _fmt(v, casas):
    if v in (None, ""):
        return "—"
    try:
        d = Decimal(str(v))
    except InvalidOperation:
        return str(v)
    txt = f"{d:,.{casas}f}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")


@register.filter
def moeda(v):
    return _fmt(v, 2)


@register.filter
def num(v, casas=2):
    return _fmt(v, int(casas))


@register.filter
def num4(v):
    if v in (None, ""):
        return "—"
    d = Decimal(str(v)).normalize()
    casas = max(2, -d.as_tuple().exponent) if d.as_tuple().exponent < 0 else 2
    return _fmt(v, min(casas, 8))


@register.filter
def get(d, k):
    try:
        return d.get(k)
    except AttributeError:
        return None
