from django import forms
from django.contrib.auth.models import Group, User

from .expressoes import ErroExpressao, para_decimal, variaveis_usadas
from .models import (Ambiente, BaseReferencia, Cliente, ComposicaoPropria, Cotacao, DocumentoEmpresa, Empresa,
                     ItemComposicaoPropria, ItemOrcamento, ModeloServico, Obra, Orcamento, Pergunta, RegraEtapa)
from .permissoes import PERFIS


class FormBase(forms.ModelForm):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        for f in self.fields.values():
            if isinstance(f, forms.DecimalField):
                f.localize = True
                f.widget = forms.TextInput(attrs={"inputmode": "decimal"})
                f.widget.is_localized = True


class EmpresaForm(FormBase):
    class Meta:
        model = Empresa
        fields = "__all__"


class DocumentoEmpresaForm(FormBase):
    class Meta:
        model = DocumentoEmpresa
        exclude = ["empresa", "sha256"]
        widgets = {"emissao": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                   "validade": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


class ClienteForm(FormBase):
    class Meta:
        model = Cliente
        fields = "__all__"


class ObraForm(FormBase):
    class Meta:
        model = Obra
        fields = ["cliente", "nome", "endereco", "municipio", "uf", "descricao"]


class AmbienteForm(FormBase):
    class Meta:
        model = Ambiente
        fields = ["nome", "comprimento", "largura", "pe_direito", "observacoes"]


class ImportarBaseForm(forms.Form):
    arquivo = forms.FileField(help_text="Pacote oficial SINAPI-AAAA-MM-formato-xlsx.zip ou a planilha SINAPI_Referência_AAAA_MM.xlsx.")
    uf = forms.CharField(max_length=2, initial="ES")
    regime = forms.ChoiceField(choices=BaseReferencia.REGIMES, initial="SD")


class CotacaoForm(FormBase):
    class Meta:
        model = Cotacao
        exclude = ["sha256", "criado_em"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                   "validade": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}


class ComposicaoPropriaForm(FormBase):
    class Meta:
        model = ComposicaoPropria
        fields = ["descricao", "unidade", "premissas", "justificativa", "memoria", "ativa"]


class ItemCPForm(FormBase):
    class Meta:
        model = ItemComposicaoPropria
        exclude = ["cp"]


class OrcamentoForm(FormBase):
    class Meta:
        model = Orcamento
        exclude = ["obra", "criado_em", "criado_por", "atualizado_em", "base"]


class NovoOrcamentoForm(FormBase):
    class Meta:
        model = Orcamento
        fields = ["titulo", "finalidade", "base", "premissas"]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["base"].queryset = BaseReferencia.objects.filter(status="confirmada")


def texto_para_variaveis(texto):
    """Formato: uma variável por linha → nome = valor | origem | observação. Origem: F, V, E, C ou M."""
    out = {}
    for n, linha in enumerate((texto or "").splitlines(), start=1):
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if "=" not in linha:
            raise forms.ValidationError(f"Linha {n}: use nome = valor | origem | observação")
        nome, resto = linha.split("=", 1)
        nome = nome.strip()
        if not nome.isidentifier():
            raise forms.ValidationError(f"Linha {n}: nome de variável inválido ({nome}).")
        partes = [p.strip() for p in resto.split("|")]
        valor = partes[0]
        origem = (partes[1] if len(partes) > 1 else "F").upper() or "F"
        if origem not in ("F", "V", "E", "C", "M"):
            raise forms.ValidationError(f"Linha {n}: origem deve ser F, V, E, C ou M.")
        try:
            para_decimal(valor)
        except ErroExpressao:
            pass  # texto permitido (raro); a fórmula acusará se não for número
        out[nome] = {"valor": valor, "origem": origem, "obs": partes[2] if len(partes) > 2 else ""}
    return out


def variaveis_para_texto(variaveis):
    linhas = []
    for nome, info in (variaveis or {}).items():
        if isinstance(info, dict):
            linhas.append(f"{nome} = {info.get('valor', '')} | {info.get('origem', 'F')} | {info.get('obs', '')}".rstrip(" |"))
        else:
            linhas.append(f"{nome} = {info}")
    return "\n".join(linhas)


class ItemOrcamentoForm(forms.Form):
    etapa = forms.CharField(max_length=200)
    ambiente = forms.ModelChoiceField(queryset=Ambiente.objects.none(), required=False)
    status = forms.ChoiceField(choices=ItemOrcamento.STATUS)
    tipo_ref = forms.ChoiceField(label="Tipo de referência", choices=ItemOrcamento.TIPOS_REF)
    codigo = forms.CharField(label="Código (base ou CP-xxx)", max_length=20, required=False)
    cotacao = forms.ModelChoiceField(queryset=Cotacao.objects.filter(descartada=False), required=False)
    complemento = forms.CharField(label="Complemento de escopo (texto próprio)", widget=forms.Textarea(attrs={"rows": 2}),
                                  required=False)
    formula = forms.CharField(label="Fórmula da quantidade", max_length=500,
                              help_text="Ex.: area  ·  comprimento * pe_direito - vaos  ·  max(a; b). Use vírgula decimal e ';' entre argumentos.")
    variaveis = forms.CharField(label="Variáveis (memória de cálculo)", widget=forms.Textarea(attrs={"rows": 4}), required=False,
                                help_text="Uma por linha: nome = valor | origem (F fornecido, V vistoria, E estimativa, C calculado, M medido) | observação")
    bdi_tipo = forms.ChoiceField(label="BDI", choices=ItemOrcamento.BDI_TIPOS)
    observacao = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)

    def __init__(self, *a, obra=None, **kw):
        super().__init__(*a, **kw)
        if obra is not None:
            self.fields["ambiente"].queryset = obra.ambientes.all()

    def clean_variaveis(self):
        return texto_para_variaveis(self.cleaned_data.get("variaveis"))

    def clean(self):
        cd = super().clean()
        try:
            usadas = variaveis_usadas(cd.get("formula", ""))
        except ErroExpressao as exc:
            self.add_error("formula", str(exc))
            return cd
        disponiveis = set((cd.get("variaveis") or {}).keys())
        amb = cd.get("ambiente")
        if amb:
            disponiveis |= set(amb.variaveis().keys())
        faltando = usadas - disponiveis
        if faltando:
            self.add_error("variaveis", f"Variáveis usadas na fórmula e não informadas: {', '.join(sorted(faltando))}")
        t = cd.get("tipo_ref")
        if t in ("composicao", "insumo", "cp") and not cd.get("codigo"):
            self.add_error("codigo", "Informe o código.")
        if t == "cotacao" and not cd.get("cotacao"):
            self.add_error("cotacao", "Selecione a cotação.")
        return cd


class VersaoForm(forms.Form):
    descricao = forms.CharField(label="Descrição da revisão", widget=forms.Textarea(attrs={"rows": 3}))
    revisado_por = forms.CharField(label="Revisado por (nome)", max_length=200, required=False)


class ModeloServicoForm(FormBase):
    class Meta:
        model = ModeloServico
        fields = "__all__"


class PerguntaForm(FormBase):
    class Meta:
        model = Pergunta
        exclude = ["modelo"]


class RegraEtapaForm(FormBase):
    class Meta:
        model = RegraEtapa
        exclude = ["modelo"]

    def clean(self):
        cd = super().clean()
        for campo in ("condicao", "formula_quantidade"):
            if cd.get(campo):
                try:
                    variaveis_usadas(cd[campo])
                except ErroExpressao as exc:
                    self.add_error(campo, str(exc))
        if cd.get("tipo_ref") not in (None, "nenhuma") and not cd.get("codigo_ref"):
            self.add_error("codigo_ref", "Informe o código da referência.")
        return cd


class UsuarioForm(forms.ModelForm):
    perfil = forms.ChoiceField(choices=[(p, p) for p in PERFIS])
    senha = forms.CharField(widget=forms.PasswordInput, required=False,
                            help_text="Mínimo de 10 caracteres. Deixe em branco para manter a atual.")

    class Meta:
        model = User
        fields = ["username", "first_name", "email", "is_active"]

    def clean_senha(self):
        from django.contrib.auth.password_validation import validate_password
        s = self.cleaned_data.get("senha")
        if not s and not self.instance.pk:
            raise forms.ValidationError("Defina uma senha para o novo usuário.")
        if s:
            validate_password(s, self.instance)
        return s

    def save(self, commit=True):
        u = super().save(commit=False)
        if self.cleaned_data.get("senha"):
            u.set_password(self.cleaned_data["senha"])
        u.save()
        u.groups.set([Group.objects.get_or_create(name=self.cleaned_data["perfil"])[0]])
        return u
