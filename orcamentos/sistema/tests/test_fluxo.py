"""Fluxo completo pelas views (sem IA): cadastro, importação, modelo de serviço, CP, BDI, versão, exportação."""
import io
import shutil
import subprocess
from decimal import Decimal as D

import openpyxl
import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse

from orc.models import (BaseReferencia, Cliente, ComposicaoPropria, ItemComposicaoPropria, ItemOrcamento, Obra,
                        Orcamento, RegistroAuditoria, VersaoOrcamento)

from .fabrica_sinapi import gerar

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(db):
    call_command("inicializar")
    from orc.models import Empresa
    Empresa.objects.create(razao_social="EMPRESA TESTE", cnpj="CNPJ-DE-TESTE")
    u = User.objects.create_user("orc", password="senha-muito-segura-1")
    u.groups.add(Group.objects.get(name="Orçamentista"))
    leitor = User.objects.create_user("leitor", password="senha-muito-segura-2")
    leitor.groups.add(Group.objects.get(name="Leitura"))
    return u, leitor


def _importar(client, tmp_path, nome="s.xlsx", **kw):
    caminho = gerar(tmp_path / nome, **kw)
    with open(caminho, "rb") as fh:
        r = client.post(reverse("base_importar"), {"arquivo": fh, "uf": "ES", "regime": "SD"})
    assert r.status_code == 302
    return BaseReferencia.objects.order_by("-id").first()


def test_exige_login(client):
    r = client.get(reverse("inicio"))
    assert r.status_code == 302 and "/entrar/" in r.url


def test_perfil_leitura_nao_altera(client, setup):
    _, leitor = setup
    client.force_login(leitor)
    assert client.get(reverse("obras")).status_code == 200
    assert client.post(reverse("cliente_novo"), {"nome": "X", "tipo": "escola", "uf": "ES"}).status_code == 403
    assert client.get(reverse("base_importar")).status_code == 403
    assert Cliente.objects.count() == 0


def test_importacao_previa_confirmacao_e_duplicidade(client, setup, tmp_path):
    u, _ = setup
    client.force_login(u)
    base = _importar(client, tmp_path)
    assert base.status == "previa" and base.competencia.month == 10
    assert base.insumos.get(codigo="11111").preco is None
    assert base.composicoes.get(codigo="104646").custo is None
    # não aparece na consulta antes de confirmar
    r = client.get(reverse("consulta"), {"q": "pintura"})
    assert r.context["base"] is None
    client.post(reverse("base_confirmar", args=[base.pk]))
    base.refresh_from_db()
    assert base.status == "confirmada"
    # mesmo arquivo de novo => recusado
    with open(tmp_path / "s.xlsx", "rb") as fh:
        client.post(reverse("base_importar"), {"arquivo": fh, "uf": "ES", "regime": "SD"})
    assert BaseReferencia.objects.count() == 1
    # consulta sem acento encontra descrição com acento
    r = client.get(reverse("consulta"), {"q": "latex standard", "base": base.pk})
    assert [c.codigo for c in r.context["resultados"]] == ["104642"]
    assert RegistroAuditoria.objects.filter(acao="base.confirmar").exists()


def test_importacao_recusada_nao_grava_dados(client, setup, tmp_path):
    u, _ = setup
    client.force_login(u)
    base = _importar(client, tmp_path, quebrar_cabecalho=True)
    assert base.status == "cancelada"
    assert base.insumos.count() == 0
    assert base.relatorio["erros"]


def _fluxo_ate_orcamento(client, tmp_path):
    base = _importar(client, tmp_path)
    client.post(reverse("base_confirmar", args=[base.pk]))
    client.post(reverse("cliente_novo"), {"nome": "EEEFM Escola Teste", "tipo": "escola", "uf": "ES", "municipio": "Vila Velha"})
    cli = Cliente.objects.get()
    client.post(reverse("obra_nova"), {"cliente": cli.pk, "nome": "Manutenção sala 1", "uf": "ES", "municipio": "Vila Velha"})
    obra = Obra.objects.get()
    client.post(reverse("ambiente_novo", args=[obra.pk]), {"nome": "Sala 1", "comprimento": "8,00", "largura": "6,00",
                                                         "pe_direito": "3,00"})
    client.post(reverse("orcamento_novo", args=[obra.pk]), {"titulo": "Pintura sala 1", "finalidade": "proposta",
                                                           "base": base.pk})
    orc = Orcamento.objects.get()
    r = client.post(reverse("orcamento_editar", args=[orc.pk]), {
        "titulo": orc.titulo, "finalidade": "proposta", "premissas": "", "modo_arredondamento": "ROUND_HALF_UP",
        "casas_preco": 2, "casas_quantidade": 2, "bdi_formula": "tcu", "bdi_ac": "3", "bdi_s": "1", "bdi_r": "1",
        "bdi_g": "0", "bdi_df": "1", "bdi_l": "8", "bdi_i": "10", "bdi_manual": "", "bdi_equip": "",
        "justificativa_bdi": "Teste"})
    assert r.status_code == 302, r.content
    orc.refresh_from_db()
    return base, obra, orc


RESPOSTAS = {"p_area_parede": "30", "p_tipo_servico": "repintura", "p_estado": "regular", "p_area_massa": "4,5",
             "p_demaos_massa": "1", "p_fundo": "nao", "p_linha_tinta": "standard", "p_altura": "3",
             "p_area_raspagem": "0", "p_comprimento_parede": "10", "p_faixa_protecao": "1", "p_ocupado": "sim"}


def test_fluxo_aceite_completo(client, setup, tmp_path):
    u, _ = setup
    client.force_login(u)
    base, obra, orc = _fluxo_ate_orcamento(client, tmp_path)
    amb = obra.ambientes.get()
    modelo_id = __import__("orc.models", fromlist=["ModeloServico"]).ModeloServico.objects.get().pk
    url = reverse("aplicar_modelo", args=[orc.pk])
    # visualizar
    r = client.post(url, {"modelo": modelo_id, "ambiente": amb.pk, "acao": "visualizar", **RESPOSTAS})
    sug = {s["regra"].chave: s for s in r.context["sugestoes"]}
    assert sug["pintura_standard"]["ativa"] and sug["pintura_standard"]["quantidade"] == D("30")
    assert not sug["pintura_premium"]["ativa"]
    assert sug["massa_1"]["quantidade"] == D("4.5")  # área medida, não 30
    assert sug["lixamento"]["regra"].classificacao == "incluida" and not sug["lixamento"]["criavel"]
    assert sug["protecao_piso"]["quantidade"] == D("10")  # faixa de piso, não área de parede
    assert not sug["raspagem"]["ativa"]
    # confirmar todas as criáveis
    escolhidas = [k for k, s in sug.items() if s["criavel"]]
    r = client.post(url, {"modelo": modelo_id, "ambiente": amb.pk, "acao": "confirmar", "etapa": escolhidas, **RESPOSTAS})
    assert r.status_code == 302
    itens = {i.chave_etapa: i for i in orc.itens.all()}
    assert set(itens) == {"pintura_standard", "massa_1", "protecao_piso"}
    assert itens["pintura_standard"].custo_unitario == D("13.51")
    assert itens["protecao_piso"].tipo_ref == "sem_ref" and itens["protecao_piso"].custo_unitario is None
    assert itens["massa_1"].status == "condicional"

    # composição própria para a proteção de piso
    cp = ComposicaoPropria.objects.create(descricao="Proteção de piso com lona plástica", unidade="M2",
                                          justificativa="Sem composição oficial específica identificada")
    ItemComposicaoPropria.objects.create(cp=cp, tipo="insumo_base", codigo_ref="35692", descricao="insumo base",
                                         unidade="L", coeficiente=D("0.1"))
    ItemComposicaoPropria.objects.create(cp=cp, tipo="mo_propria", descricao="Servente", unidade="H",
                                         coeficiente=D("0.05"), preco_informado=D("10"), encargos_pct=D("100"),
                                         fonte="Folha Mariani (teste)")
    it = itens["protecao_piso"]
    r = client.post(reverse("item_editar", args=[orc.pk, it.pk]), {
        "etapa": it.etapa, "ambiente": amb.pk, "status": "confirmado", "tipo_ref": "cp", "codigo": cp.codigo,
        "complemento": "lona", "formula": it.formula, "variaveis": "comprimento_parede = 10 | V\nfaixa_protecao = 1 | E",
        "bdi_tipo": "servico", "observacao": ""})
    assert r.status_code == 302, r.context["form"].errors if r.context else r
    it.refresh_from_db()
    # CP = TRUNC(0,1×20;2) + TRUNC(0,05×10×2;2) = 2,00 + 1,00
    assert it.custo_unitario == D("3.00") and it.tipo_ref == "cp"

    # item manual usando dimensões do ambiente (área de piso)
    r = client.post(reverse("item_novo", args=[orc.pk]), {
        "etapa": "Fundo no teto (exemplo)", "ambiente": amb.pk, "status": "condicional", "tipo_ref": "composicao",
        "codigo": "88485", "complemento": "", "formula": "area_piso", "variaveis": "", "bdi_tipo": "servico",
        "observacao": ""})
    assert r.status_code == 302
    # duplicidade: mesma composição no mesmo ambiente
    client.post(reverse("item_novo", args=[orc.pk]), {
        "etapa": "Pintura repetida", "ambiente": amb.pk, "status": "confirmado", "tipo_ref": "composicao",
        "codigo": "104642", "formula": "1", "variaveis": "", "bdi_tipo": "servico"})

    from orc.calculo import calcular_orcamento
    dados = calcular_orcamento(orc)
    assert dados["bdi"]["servicos"] == "27.26"
    por_etapa = {i["etapa"]: i for i in dados["itens"]}
    p = por_etapa["Pintura látex acrílica standard — duas demãos"]
    # 13,51 × 1,2726 = 17,192826 → 17,19 ; 30 × 17,19 = 515,70 ; custo 30 × 13,51 = 405,30
    assert (p["preco_unitario"], p["preco_total"], p["custo_total"]) == ("17.19", "515.70", "405.30")
    assert any("duplicidade" in a["mensagem"].lower() for a in dados["alertas"])
    # confirmado: pintura 515,70 + proteção (10 × TRUNC... 3,00×1,2726=3,8178→3,82 ; 38,20) + repetida 17,19
    assert dados["totais"]["confirmado"]["preco"] == str(D("515.70") + D("38.20") + D("17.19"))
    # condicionais fora do total: massa 4,5 × (16,27×1,2726=20,705…→20,71)=93,195→93,20 ; fundo 48 × (5,47×1,2726=6,961…→6,96)=334,08
    assert dados["totais"]["condicional"]["preco"] == str(D("93.20") + D("334.08"))

    # versão
    r = client.post(reverse("versao_nova", args=[orc.pk]), {"descricao": "Primeira emissão", "revisado_por": "Fulano"})
    v = VersaoOrcamento.objects.get()
    assert v.rotulo == "R00" and v.total_confirmado == D("571.09")
    with pytest.raises(ValidationError):
        v.descricao = "alterada"
        v.save()

    # exportações
    rx = client.get(reverse("exportar_versao", args=[orc.pk, v.pk, "xlsx"]))
    wb = openpyxl.load_workbook(io.BytesIO(rx.content))
    ws = wb["Orçamento"]
    assert ws["C6"].value == "='BDI'!C10"
    assert str(ws["M11"].value).startswith("=IF(")
    rp = client.get(reverse("exportar_versao", args=[orc.pk, v.pk, "pdf"]))
    assert rp.content[:4] == b"%PDF"
    if shutil.which("soffice"):
        _confere_xlsx_recalculado(rx.content, tmp_path, D("571.09"))

    # Atualização explícita de preços para nova competência
    base2 = _importar(client, tmp_path, nome="nov.xlsx", competencia="11/2026", composicoes=[
        ("Pintura Interna", 104642, "PINTURA LÁTEX ACRÍLICA STANDARD, APLICAÇÃO MANUAL EM PAREDES, DUAS DEMÃOS. AF_04/2023", "M2", {"ES": (14.00, 0)}),
        ("Pintura Interna", 88485, "FUNDO SELADOR ACRÍLICO, APLICAÇÃO MANUAL EM PAREDE, UMA DEMÃO. AF_04/2023", "M2", {"ES": (5.47, 0)}),
    ])
    client.post(reverse("base_confirmar", args=[base2.pk]))
    r = client.get(reverse("atualizar_precos", args=[orc.pk]), {"base": base2.pk})
    sit = {l["item"].ref_codigo: l["situacao"] for l in r.context["linhas"]}
    assert sit["104642"] == "alterado" and "não encontrado" in sit["88495"]
    client.post(reverse("atualizar_precos", args=[orc.pk]), {"base": base2.pk, "acao": "aplicar"})
    orc.refresh_from_db()
    assert orc.base == base2
    assert orc.versoes.count() == 2  # R00 já igual ao estado anterior => só gera R01 da atualização
    v0 = orc.versoes.get(numero=0)
    assert v0.total_confirmado == D("571.09")  # versão antiga preservada
    assert ItemOrcamento.objects.get(orcamento=orc, chave_etapa="pintura_standard").custo_unitario == D("14.00")


def _confere_xlsx_recalculado(conteudo, tmp_path, total_esperado):
    """Recalcula o XLSX no LibreOffice e confere o total com o cálculo do sistema."""
    origem = tmp_path / "orc.xlsx"
    origem.write_bytes(conteudo)
    saida = tmp_path / "recalc"
    saida.mkdir()
    subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", str(saida), str(origem)],
                   check=True, capture_output=True, timeout=180)
    wb = openpyxl.load_workbook(saida / "orc.xlsx", data_only=True)
    ws = wb["Orçamento"]
    valores = {ws.cell(r, 12).value: ws.cell(r, 13).value for r in range(1, ws.max_row + 1)}
    assert D(str(valores["PREÇO TOTAL CONFIRMADO"])).quantize(D("0.01")) == total_esperado
    assert D(str(wb["BDI"]["C10"].value)).quantize(D("0.01")) == D("27.26")
