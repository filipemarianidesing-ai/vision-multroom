"""Avaliador seguro de expressões (memória de cálculo e regras de modelos de serviço).

- Somente aritmética Decimal, comparações, and/or/not, textos entre aspas e as funções min, max, arred.
- Nada de atributos, índices, importações ou chamadas arbitrárias.
- Números aceitam vírgula decimal ("10,5"). Argumentos de função são separados por ponto e vírgula:
  max(a; 2,5)  ·  arred(area * 1,1; 2)
"""
import ast
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_DEC_VIRGULA = re.compile(r"(?<=\d),(?=\d)")


class ErroExpressao(ValueError):
    pass


def para_decimal(valor):
    """Converte texto/numero em Decimal exato. Vazio -> None. Aceita '1.234,56' e '1234.56'."""
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, bool):
        raise ErroExpressao("Valor lógico não é número.")
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, float):
        return Decimal(repr(valor))
    txt = str(valor).strip().replace(" ", "")
    if txt == "":
        return None
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    try:
        return Decimal(txt)
    except InvalidOperation as exc:
        raise ErroExpressao(f"Número inválido: {valor!r}") from exc


def _preparar(expr):
    expr = (expr or "").strip()
    if not expr:
        raise ErroExpressao("Expressão vazia.")
    expr = _DEC_VIRGULA.sub(".", expr)
    expr = expr.replace(";", ",")
    return expr


def _arred(x, casas=Decimal(0)):
    casas = int(casas)
    return x.quantize(Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP)


_FUNCOES = {
    "min": lambda *a: min(a),
    "max": lambda *a: max(a),
    "arred": _arred,
}
_NOMES_LOGICOS = {"verdadeiro": True, "falso": False, "sim": True, "nao": False, "True": True, "False": False}


def variaveis_usadas(expr):
    try:
        arvore = ast.parse(_preparar(expr), mode="eval")
    except SyntaxError as exc:
        raise ErroExpressao(f"Sintaxe inválida: {exc.msg}") from exc
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Name) and no.id not in _FUNCOES and no.id not in _NOMES_LOGICOS:
            nomes.add(no.id)
    return nomes


def avaliar(expr, variaveis=None):
    """Avalia a expressão. Variáveis numéricas devem ser Decimal; textos ficam como str; booleanos como bool."""
    variaveis = variaveis or {}
    fonte = _preparar(expr)
    try:
        arvore = ast.parse(fonte, mode="eval")
    except SyntaxError as exc:
        raise ErroExpressao(f"Sintaxe inválida: {exc.msg}") from exc

    def ev(no):
        if isinstance(no, ast.Expression):
            return ev(no.body)
        if isinstance(no, ast.Constant):
            if isinstance(no.value, bool):
                return no.value
            if isinstance(no.value, (int, float)):
                return Decimal(ast.get_source_segment(fonte, no))
            if isinstance(no.value, str):
                return no.value
            raise ErroExpressao("Constante não permitida.")
        if isinstance(no, ast.Name):
            if no.id in _NOMES_LOGICOS:
                return _NOMES_LOGICOS[no.id]
            if no.id not in variaveis:
                raise ErroExpressao(f"Variável não informada: {no.id}")
            v = variaveis[no.id]
            if v is None:
                raise ErroExpressao(f"Variável sem valor: {no.id}")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                v = para_decimal(v)
            return v
        if isinstance(no, ast.UnaryOp):
            v = ev(no.operand)
            if isinstance(no.op, ast.USub):
                return -_num(v)
            if isinstance(no.op, ast.UAdd):
                return +_num(v)
            if isinstance(no.op, ast.Not):
                return not v
        if isinstance(no, ast.BinOp):
            a, b = _num(ev(no.left)), _num(ev(no.right))
            if isinstance(no.op, ast.Add):
                return a + b
            if isinstance(no.op, ast.Sub):
                return a - b
            if isinstance(no.op, ast.Mult):
                return a * b
            if isinstance(no.op, ast.Div):
                if b == 0:
                    raise ErroExpressao("Divisão por zero.")
                return a / b
            raise ErroExpressao("Operador não permitido.")
        if isinstance(no, ast.BoolOp):
            if isinstance(no.op, ast.And):
                return all(bool(ev(v)) for v in no.values)
            return any(bool(ev(v)) for v in no.values)
        if isinstance(no, ast.Compare):
            esquerda = ev(no.left)
            for op, comp in zip(no.ops, no.comparators):
                direita = ev(comp)
                ok = _comparar(op, esquerda, direita)
                if not ok:
                    return False
                esquerda = direita
            return True
        if isinstance(no, ast.Call):
            if not isinstance(no.func, ast.Name) or no.func.id not in _FUNCOES or no.keywords:
                raise ErroExpressao("Função não permitida (use min, max ou arred).")
            args = [_num(ev(a)) for a in no.args]
            if not args:
                raise ErroExpressao("Função sem argumentos.")
            return _FUNCOES[no.func.id](*args)
        raise ErroExpressao(f"Elemento não permitido na expressão: {type(no).__name__}")

    return ev(arvore)


def _num(v):
    if isinstance(v, bool) or not isinstance(v, Decimal):
        raise ErroExpressao(f"Esperado número, recebido {v!r}.")
    return v


def _comparar(op, a, b):
    if isinstance(a, Decimal) != isinstance(b, Decimal) and not (isinstance(a, bool) and isinstance(b, bool)):
        if isinstance(op, (ast.Eq, ast.NotEq)):
            return isinstance(op, ast.NotEq)
        raise ErroExpressao(f"Comparação entre tipos diferentes: {a!r} e {b!r}.")
    if isinstance(op, ast.Eq):
        return a == b
    if isinstance(op, ast.NotEq):
        return a != b
    if isinstance(op, ast.Lt):
        return a < b
    if isinstance(op, ast.LtE):
        return a <= b
    if isinstance(op, ast.Gt):
        return a > b
    if isinstance(op, ast.GtE):
        return a >= b
    raise ErroExpressao("Comparação não permitida.")
