"""Modelo de dados do sistema de orçamentação.

Princípios:
- Valores monetários e coeficientes em Decimal (numeric no PostgreSQL). Nunca float.
- Dado ausente é NULL ("sem preço"), nunca zero.
- Bases importadas são imutáveis depois de confirmadas.
- Itens de orçamento guardam cópia (snapshot) dos dados de referência usados.
- Versões de orçamento são congeladas (JSON completo) e não podem ser editadas.
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

D = Decimal

# --------------------------------------------------------------------------------------------
# Cadastros
# --------------------------------------------------------------------------------------------


class Empresa(models.Model):
    razao_social = models.CharField("razão social", max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    nome_comercial = models.CharField("nome comercial", max_length=200, blank=True)
    cnpj = models.CharField("CNPJ", max_length=18)
    endereco = models.CharField("endereço", max_length=300, blank=True)
    municipio = models.CharField("município", max_length=100, blank=True)
    uf = models.CharField("UF", max_length=2, default="ES")
    telefone = models.CharField(max_length=40, blank=True)
    email = models.CharField("e-mail", max_length=120, blank=True)
    regime_tributario = models.CharField("regime tributário", max_length=60, blank=True,
                                         help_text="Simples Nacional, Lucro Presumido ou Lucro Real.")
    responsavel_tecnico = models.CharField("responsável técnico", max_length=200, blank=True)
    observacoes = models.TextField("observações", blank=True)

    class Meta:
        verbose_name = "empresa"

    def __str__(self):
        return self.razao_social


class DocumentoEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="documentos")
    tipo = models.CharField(max_length=120, help_text="Ex.: cartão CNPJ, CRF-FGTS, CND federal, CNDT.")
    numero = models.CharField("número/código", max_length=120, blank=True)
    emissao = models.DateField("emissão", null=True, blank=True)
    validade = models.DateField(null=True, blank=True)
    arquivo = models.FileField(upload_to="empresa/", blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    observacoes = models.TextField("observações", blank=True)

    class Meta:
        ordering = ["tipo"]

    @property
    def vencido(self):
        return bool(self.validade and self.validade < timezone.localdate())


class Cliente(models.Model):
    """Órgão, escola, prefeitura ou outro contratante."""
    TIPOS = [("escola", "Escola"), ("prefeitura", "Prefeitura/Secretaria"), ("estado", "Órgão estadual"),
             ("federal", "Órgão federal"), ("privado", "Privado"), ("outro", "Outro")]
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS, default="escola")
    documento = models.CharField("CNPJ/CPF", max_length=20, blank=True)
    municipio = models.CharField("município", max_length=100, blank=True)
    uf = models.CharField("UF", max_length=2, default="ES")
    contato = models.CharField(max_length=200, blank=True)
    telefone = models.CharField(max_length=40, blank=True)
    email = models.CharField("e-mail", max_length=120, blank=True)
    observacoes = models.TextField("observações", blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Obra(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="obras")
    nome = models.CharField(max_length=200)
    endereco = models.CharField("endereço", max_length=300, blank=True)
    municipio = models.CharField("município", max_length=100, blank=True)
    uf = models.CharField("UF", max_length=2, default="ES")
    descricao = models.TextField("descrição", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.nome} — {self.cliente}"


class Ambiente(models.Model):
    obra = models.ForeignKey(Obra, on_delete=models.CASCADE, related_name="ambientes")
    nome = models.CharField(max_length=120)
    comprimento = models.DecimalField("comprimento (m)", max_digits=10, decimal_places=3, null=True, blank=True)
    largura = models.DecimalField("largura (m)", max_digits=10, decimal_places=3, null=True, blank=True)
    pe_direito = models.DecimalField("pé-direito (m)", max_digits=10, decimal_places=3, null=True, blank=True)
    observacoes = models.TextField("observações", blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def variaveis(self):
        """Variáveis geométricas disponíveis para memória de cálculo (só as informadas)."""
        v = {}
        if self.comprimento is not None:
            v["comprimento"] = self.comprimento
        if self.largura is not None:
            v["largura"] = self.largura
        if self.pe_direito is not None:
            v["pe_direito"] = self.pe_direito
        if self.comprimento is not None and self.largura is not None:
            v["area_piso"] = self.comprimento * self.largura
            v["perimetro"] = 2 * (self.comprimento + self.largura)
        return v


# --------------------------------------------------------------------------------------------
# Bases de referência (importadas, imutáveis após confirmação)
# --------------------------------------------------------------------------------------------


class BaseReferencia(models.Model):
    FONTES = [("SINAPI", "SINAPI — CAIXA/IBGE")]
    REGIMES = [("SD", "Sem desoneração"), ("CD", "Com desoneração"), ("SE", "Sem encargos sociais")]
    STATUS = [("previa", "Prévia (não confirmada)"), ("confirmada", "Confirmada"), ("cancelada", "Cancelada")]

    fonte = models.CharField(max_length=20, choices=FONTES, default="SINAPI")
    uf = models.CharField("UF", max_length=2, default="ES")
    localidade = models.CharField(max_length=60, blank=True)
    competencia = models.DateField("competência (mês de referência)")
    regime = models.CharField("regime de encargos", max_length=2, choices=REGIMES)
    data_emissao = models.CharField("data de emissão (do arquivo)", max_length=20, blank=True)
    encargos_horista = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    encargos_mensalista = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    arquivo = models.FileField(upload_to="bases/", max_length=300)
    nome_arquivo = models.CharField(max_length=300)
    sha256 = models.CharField(max_length=64)
    leiaute = models.CharField("leiaute do importador", max_length=60)
    status = models.CharField(max_length=12, choices=STATUS, default="previa")
    relatorio = models.JSONField("relatório da importação", default=dict)
    importado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    importado_em = models.DateTimeField(auto_now_add=True)
    confirmado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name="+")
    confirmado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-competencia", "fonte", "uf", "regime"]
        constraints = [
            models.UniqueConstraint(fields=["fonte", "uf", "competencia", "regime"],
                                    condition=models.Q(status="confirmada"), name="base_unica_confirmada"),
        ]

    def __str__(self):
        return f"{self.fonte} {self.uf} {self.competencia:%m/%Y} {self.get_regime_display()}"

    @property
    def rotulo_curto(self):
        return f"{self.fonte}-{self.uf} {self.competencia:%m/%Y} {self.regime}"


class Insumo(models.Model):
    base = models.ForeignKey(BaseReferencia, on_delete=models.CASCADE, related_name="insumos")
    codigo = models.CharField(max_length=20)
    descricao = models.TextField("descrição")
    unidade = models.CharField(max_length=20)
    classificacao = models.CharField("classificação", max_length=60, blank=True)
    origem_preco = models.CharField("origem do preço", max_length=10, blank=True)
    preco = models.DecimalField("preço (R$)", max_digits=18, decimal_places=6, null=True, blank=True)
    linha = models.PositiveIntegerField("linha no arquivo", null=True)

    class Meta:
        unique_together = [("base", "codigo")]
        indexes = [models.Index(fields=["base", "codigo"])]

    def __str__(self):
        return f"{self.codigo} {self.descricao[:60]}"


class Composicao(models.Model):
    base = models.ForeignKey(BaseReferencia, on_delete=models.CASCADE, related_name="composicoes")
    codigo = models.CharField(max_length=20)
    descricao = models.TextField("descrição")
    unidade = models.CharField(max_length=20)
    grupo = models.CharField(max_length=120, blank=True)
    custo = models.DecimalField("custo (R$)", max_digits=18, decimal_places=6, null=True, blank=True)
    pct_atribuido_sp = models.DecimalField("%AS", max_digits=10, decimal_places=6, null=True, blank=True)
    situacao = models.CharField("situação", max_length=20, blank=True)
    linha = models.PositiveIntegerField("linha no arquivo", null=True)

    class Meta:
        unique_together = [("base", "codigo")]
        indexes = [models.Index(fields=["base", "codigo"])]

    def __str__(self):
        return f"{self.codigo} {self.descricao[:60]}"


class ComposicaoItem(models.Model):
    composicao = models.ForeignKey(Composicao, on_delete=models.CASCADE, related_name="itens")
    tipo = models.CharField(max_length=12)  # INSUMO | COMPOSICAO
    codigo = models.CharField(max_length=20)
    descricao = models.TextField("descrição")
    unidade = models.CharField(max_length=20)
    coeficiente = models.DecimalField(max_digits=20, decimal_places=8, null=True)
    situacao = models.CharField("situação", max_length=20, blank=True)
    ordem = models.PositiveIntegerField()

    class Meta:
        ordering = ["ordem"]


# --------------------------------------------------------------------------------------------
# Pesquisa de preços e composições próprias
# --------------------------------------------------------------------------------------------


class Cotacao(models.Model):
    fornecedor = models.CharField(max_length=200)
    cnpj_fornecedor = models.CharField("CNPJ do fornecedor", max_length=20, blank=True)
    data = models.DateField()
    validade = models.DateField(null=True, blank=True)
    especificacao = models.TextField("especificação")
    unidade = models.CharField(max_length=20)
    quantidade = models.DecimalField(max_digits=14, decimal_places=4, default=D("1"))
    preco_unitario = models.DecimalField("preço unitário (R$)", max_digits=18, decimal_places=4)
    frete = models.DecimalField("frete total (R$)", max_digits=18, decimal_places=2, default=D("0"))
    condicoes = models.TextField("tributos e condições comerciais", blank=True)
    prazo = models.CharField("prazo de entrega", max_length=120, blank=True)
    inclui_instalacao = models.BooleanField("o preço inclui instalação", default=False)
    arquivo = models.FileField("evidência", upload_to="cotacoes/", blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    descartada = models.BooleanField("descartada (outlier ou inadequada)", default=False)
    justificativa = models.TextField("justificativa de manutenção/descarte", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.fornecedor} — {self.especificacao[:50]} ({self.data:%d/%m/%Y})"

    @property
    def preco_com_frete(self):
        if not self.quantidade:
            return self.preco_unitario
        return self.preco_unitario + (self.frete / self.quantidade)


class ComposicaoPropria(models.Model):
    codigo = models.CharField(max_length=20, unique=True, editable=False)
    descricao = models.TextField("objeto/descrição")
    unidade = models.CharField(max_length=20)
    premissas = models.TextField(blank=True)
    justificativa = models.TextField(blank=True, help_text="Por que não há composição oficial adequada.")
    memoria = models.TextField("memória de cálculo / produtividade", blank=True)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "composição própria"
        verbose_name_plural = "composições próprias"

    def __str__(self):
        return f"{self.codigo} {self.descricao[:60]}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = ComposicaoPropria.objects.order_by("-id").first()
            n = (int(ultimo.codigo.split("-")[1]) + 1) if ultimo else 1
            self.codigo = f"CP-{n:03d}"
        super().save(*args, **kwargs)


class ItemComposicaoPropria(models.Model):
    TIPOS = [
        ("insumo_base", "Insumo de base oficial"),
        ("composicao_base", "Composição de base oficial"),
        ("cotacao", "Cotação de fornecedor"),
        ("mo_propria", "Mão de obra própria (custo horário + encargos)"),
        ("outro", "Outro custo (fonte descrita)"),
    ]
    cp = models.ForeignKey(ComposicaoPropria, on_delete=models.CASCADE, related_name="itens")
    tipo = models.CharField(max_length=20, choices=TIPOS)
    codigo_ref = models.CharField("código na base", max_length=20, blank=True)
    cotacao = models.ForeignKey(Cotacao, null=True, blank=True, on_delete=models.PROTECT)
    descricao = models.TextField("descrição/especificação")
    unidade = models.CharField(max_length=20)
    coeficiente = models.DecimalField(max_digits=20, decimal_places=8)
    preco_informado = models.DecimalField("preço unitário informado (R$)", max_digits=18, decimal_places=6,
                                          null=True, blank=True,
                                          help_text="Para 'outro' e para o custo horário sem encargos de 'mão de obra própria'.")
    encargos_pct = models.DecimalField("encargos sociais (%)", max_digits=8, decimal_places=4, null=True, blank=True,
                                       help_text="Somente para mão de obra própria. Bases oficiais já trazem encargos.")
    fonte = models.TextField("fonte do preço", blank=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "id"]

    def clean(self):
        if self.tipo in ("insumo_base", "composicao_base") and not self.codigo_ref:
            raise ValidationError("Informe o código na base oficial.")
        if self.tipo == "cotacao" and not self.cotacao_id:
            raise ValidationError("Selecione a cotação.")
        if self.tipo in ("mo_propria", "outro") and self.preco_informado is None:
            raise ValidationError("Informe o preço unitário.")
        if self.tipo == "mo_propria" and self.encargos_pct is None:
            raise ValidationError("Informe os encargos sociais (%) da mão de obra própria.")
        if self.tipo != "mo_propria" and self.encargos_pct:
            raise ValidationError("Encargos só podem ser aplicados à mão de obra própria (evita encargos em duplicidade).")
        if self.tipo in ("mo_propria", "outro") and not self.fonte:
            raise ValidationError("Descreva a fonte do preço.")


# --------------------------------------------------------------------------------------------
# Modelos de serviço com regras (decomposição sem IA)
# --------------------------------------------------------------------------------------------


class ModeloServico(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    descricao = models.TextField("descrição", blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "modelo de serviço"

    def __str__(self):
        return self.nome


class Pergunta(models.Model):
    TIPOS = [("numero", "Número"), ("escolha", "Escolha"), ("sim_nao", "Sim/Não"), ("texto", "Texto")]
    modelo = models.ForeignKey(ModeloServico, on_delete=models.CASCADE, related_name="perguntas")
    chave = models.SlugField(max_length=40, help_text="Nome da variável usada nas regras (ex.: area_parede).")
    texto = models.CharField(max_length=300)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    opcoes = models.TextField("opções", blank=True, help_text="Para 'escolha': uma por linha, no formato valor|rótulo.")
    unidade = models.CharField(max_length=20, blank=True)
    obrigatoria = models.BooleanField("obrigatória", default=True)
    ajuda = models.TextField(blank=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "id"]
        unique_together = [("modelo", "chave")]

    def lista_opcoes(self):
        out = []
        for linha in self.opcoes.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            valor, _, rotulo = linha.partition("|")
            out.append((valor.strip(), (rotulo or valor).strip()))
        return out


class RegraEtapa(models.Model):
    CLASSIFICACOES = [
        ("item", "Item de orçamento"),
        ("incluida", "Já incluída em outra composição"),
        ("operacional", "Tarefa operacional (sem item próprio)"),
        ("pendente", "Pendente de informação/vistoria"),
    ]
    STATUS = [("confirmado", "Confirmado"), ("condicional", "Condicional")]
    REFS = [("nenhuma", "Sem referência"), ("composicao", "Composição da base"), ("insumo", "Insumo da base"),
            ("cp", "Composição própria")]

    modelo = models.ForeignKey(ModeloServico, on_delete=models.CASCADE, related_name="regras")
    chave = models.SlugField(max_length=40, help_text="Identificador da etapa (usado em dependências e exclusões).")
    etapa = models.CharField(max_length=200)
    condicao = models.CharField("condição", max_length=500, blank=True,
                                help_text="Expressão com as chaves das perguntas. Vazio = sempre. Ex.: estado == 'ruim' and area_massa > 0")
    classificacao = models.CharField("classificação", max_length=12, choices=CLASSIFICACOES, default="item")
    status_sugerido = models.CharField(max_length=12, choices=STATUS, default="confirmado")
    tipo_ref = models.CharField("tipo de referência", max_length=12, choices=REFS, default="nenhuma")
    codigo_ref = models.CharField("código da referência", max_length=20, blank=True)
    formula_quantidade = models.CharField("fórmula da quantidade", max_length=300, blank=True,
                                          help_text="Expressão com as chaves das perguntas. Ex.: area_parede")
    complemento = models.CharField("complemento de escopo", max_length=300, blank=True)
    inclui = models.CharField("já inclui as etapas", max_length=300, blank=True,
                              help_text="Chaves separadas por vírgula. Se esta etapa entrar, aquelas são bloqueadas como duplicidade.")
    depende_de = models.CharField("depende das etapas", max_length=300, blank=True,
                                  help_text="Chaves separadas por vírgula.")
    observacao = models.TextField("observação/justificativa", blank=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "id"]
        unique_together = [("modelo", "chave")]

    @staticmethod
    def lista(txt):
        return [c.strip() for c in (txt or "").split(",") if c.strip()]


# --------------------------------------------------------------------------------------------
# Orçamento
# --------------------------------------------------------------------------------------------


class Orcamento(models.Model):
    FINALIDADES = [
        ("estimativa", "Estimativa preliminar"),
        ("proposta", "Proposta comercial da Mariani"),
        ("referencia", "Orçamento de referência"),
        ("manutencao", "Manutenção / serviço contratado"),
        ("revisao", "Revisão de orçamento"),
    ]
    MODOS = [("ROUND_HALF_UP", "Arredondar (meio para cima)"), ("ROUND_DOWN", "Truncar")]
    FORMULAS_BDI = [("tcu", "Componentes (AC, S, R, G, DF, L, I)"), ("manual", "Percentual informado")]

    obra = models.ForeignKey(Obra, on_delete=models.PROTECT, related_name="orcamentos")
    titulo = models.CharField("título", max_length=200)
    finalidade = models.CharField(max_length=12, choices=FINALIDADES, default="proposta")
    base = models.ForeignKey(BaseReferencia, on_delete=models.PROTECT, null=True, blank=True,
                             limit_choices_to={"status": "confirmada"}, related_name="orcamentos",
                             verbose_name="base de referência")
    premissas = models.TextField(blank=True)

    # Arredondamento
    modo_arredondamento = models.CharField(max_length=14, choices=MODOS, default="ROUND_HALF_UP")
    casas_preco = models.PositiveSmallIntegerField("casas decimais do preço unitário", default=2)
    casas_quantidade = models.PositiveSmallIntegerField("casas decimais da quantidade", default=2)

    # BDI principal (serviços)
    bdi_formula = models.CharField("forma do BDI", max_length=8, choices=FORMULAS_BDI, default="tcu")
    bdi_ac = models.DecimalField("administração central (%)", max_digits=7, decimal_places=4, default=D("0"))
    bdi_s = models.DecimalField("seguros (%)", max_digits=7, decimal_places=4, default=D("0"))
    bdi_r = models.DecimalField("riscos (%)", max_digits=7, decimal_places=4, default=D("0"))
    bdi_g = models.DecimalField("garantias (%)", max_digits=7, decimal_places=4, default=D("0"))
    bdi_df = models.DecimalField("despesas financeiras (%)", max_digits=7, decimal_places=4, default=D("0"))
    bdi_l = models.DecimalField("lucro (%)", max_digits=7, decimal_places=4, default=D("0"))
    bdi_i = models.DecimalField("tributos sobre o preço (%)", max_digits=7, decimal_places=4, default=D("0"),
                                help_text="PIS, COFINS, ISS, CPRB etc. conforme o regime da empresa.")
    bdi_manual = models.DecimalField("BDI informado (%)", max_digits=7, decimal_places=4, null=True, blank=True)
    # BDI diferenciado (fornecimento de equipamentos)
    bdi_equip = models.DecimalField("BDI de fornecimento de equipamentos (%)", max_digits=7, decimal_places=4,
                                    null=True, blank=True)
    justificativa_bdi = models.TextField("justificativa/fonte do BDI", blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-atualizado_em"]

    def __str__(self):
        return self.titulo


class ItemOrcamento(models.Model):
    STATUS = [("confirmado", "Confirmado"), ("condicional", "Condicional")]
    TIPOS_REF = [("composicao", "Composição da base"), ("insumo", "Insumo da base"), ("cp", "Composição própria"),
                 ("cotacao", "Cotação"), ("sem_ref", "Sem referência (pendente)")]
    BDI_TIPOS = [("servico", "BDI de serviços"), ("equipamento", "BDI de fornecimento de equipamentos")]

    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name="itens")
    ordem = models.PositiveIntegerField(default=0)
    numero = models.CharField("item", max_length=20, blank=True)
    etapa = models.CharField("etapa", max_length=200)
    ambiente = models.ForeignKey(Ambiente, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=12, choices=STATUS, default="confirmado")

    # Referência (snapshot no momento da inclusão/atualização)
    tipo_ref = models.CharField("tipo de referência", max_length=12, choices=TIPOS_REF)
    ref_base_rotulo = models.CharField("base", max_length=80, blank=True)
    ref_codigo = models.CharField("código", max_length=20, blank=True)
    ref_descricao = models.TextField("descrição oficial/original", blank=True)
    ref_unidade = models.CharField("unidade", max_length=20, blank=True)
    ref_data_base = models.CharField("data-base", max_length=10, blank=True)
    ref_regime = models.CharField("regime", max_length=2, blank=True)
    ref_detalhe = models.JSONField("detalhe da referência (analítico)", default=dict, blank=True)
    custo_unitario = models.DecimalField("custo unitário (R$)", max_digits=18, decimal_places=6, null=True, blank=True)
    fonte = models.TextField(blank=True)

    complemento = models.TextField("complemento de escopo", blank=True)
    bdi_tipo = models.CharField(max_length=12, choices=BDI_TIPOS, default="servico")

    # Memória de cálculo
    formula = models.CharField("fórmula da quantidade", max_length=500)
    variaveis = models.JSONField(default=dict, blank=True,
                                 help_text='{"nome": {"valor": "10,5", "origem": "F|V|E|C", "obs": ""}}')
    quantidade = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    observacao = models.TextField("observação", blank=True)

    origem_modelo = models.CharField("gerado pelo modelo", max_length=120, blank=True)
    chave_etapa = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["ordem", "id"]


class VersaoOrcamento(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.PROTECT, related_name="versoes")
    numero = models.PositiveIntegerField()
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    descricao = models.TextField("descrição da revisão")
    revisado_por = models.CharField("revisado por", max_length=200, blank=True)
    dados = models.JSONField()
    total_confirmado = models.DecimalField(max_digits=18, decimal_places=2)
    sha256 = models.CharField(max_length=64)

    class Meta:
        ordering = ["-numero"]
        unique_together = [("orcamento", "numero")]

    @property
    def rotulo(self):
        return f"R{self.numero:02d}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Versões de orçamento são imutáveis.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Versões de orçamento não podem ser excluídas.")


class AtualizacaoPrecos(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name="atualizacoes")
    base_anterior = models.ForeignKey(BaseReferencia, null=True, on_delete=models.PROTECT, related_name="+")
    base_nova = models.ForeignKey(BaseReferencia, on_delete=models.PROTECT, related_name="+")
    comparacao = models.JSONField()
    aplicado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    aplicado_em = models.DateTimeField(auto_now_add=True)


# --------------------------------------------------------------------------------------------
# Auditoria
# --------------------------------------------------------------------------------------------


class RegistroAuditoria(models.Model):
    quando = models.DateTimeField(default=timezone.now, db_index=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    acao = models.CharField(max_length=40)
    objeto_tipo = models.CharField(max_length=60)
    objeto_id = models.CharField(max_length=40, blank=True)
    descricao = models.TextField(blank=True)
    detalhes = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-quando"]
