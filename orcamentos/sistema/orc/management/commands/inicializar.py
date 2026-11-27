"""Cria perfis de acesso e o modelo de serviço inicial "Pintura de parede (interna)". Idempotente.

Os códigos SINAPI usados nas regras foram conferidos no arquivo oficial SINAPI-2026-10-formato-xlsx.zip
(planilha SINAPI_Referência_2026_10.xlsx, aba CSD/Analítico). Em outra competência, o sistema avisa se o código não existir.
"""
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from orc.models import ModeloServico, Pergunta, RegraEtapa
from orc.permissoes import PERFIS

PERGUNTAS = [
    ("area_parede", "Área de parede a pintar (superfície, já descontados os vãos conforme critério adotado)", "numero", "", "m²", True,
     "Não converta metros lineares ou área de piso em área de parede sem as dimensões."),
    ("tipo_servico", "Tipo de serviço", "escolha", "repintura|Repintura sobre pintura existente\nnova|Pintura nova (reboco/massa novos)", "", True, ""),
    ("estado", "Estado da superfície (vistoria)", "escolha",
     "bom|Bom — sem descascamento\nregular|Regular — pequenas falhas localizadas\nruim|Ruim — descascando, mofo, umidade ou trincas", "", True, ""),
    ("area_massa", "Área que precisa de massa (medida em vistoria; 0 se nenhuma)", "numero", "", "m²", True,
     "Não presuma emassamento integral em repintura."),
    ("demaos_massa", "Demãos de massa", "escolha", "1|Uma demão\n2|Duas demãos", "", False, "Só se houver área de massa."),
    ("fundo", "Aplicar fundo selador?", "sim_nao", "", "", True, "Em geral sobre reboco ou massa novos; conferir especificação e fabricante."),
    ("linha_tinta", "Linha da tinta látex acrílica", "escolha", "economica|Econômica\nstandard|Standard\npremium|Premium", "", True, ""),
    ("altura", "Altura máxima de trabalho", "numero", "", "m", True, ""),
    ("area_raspagem", "Área com pintura solta a raspar (0 se nenhuma)", "numero", "", "m²", True, ""),
    ("comprimento_parede", "Comprimento de parede para proteção de piso (opcional)", "numero", "", "m", False,
     "Proteção de piso é calculada pela faixa de piso, nunca pela área da parede."),
    ("faixa_protecao", "Largura da faixa de proteção de piso (opcional)", "numero", "", "m", False, "Hipótese a registrar."),
    ("ocupado", "Ambiente ocupado ou com mobiliário/equipamentos a proteger?", "sim_nao", "", "", True, ""),
]

REGRAS = [
    # chave, etapa, condicao, classificacao, status, tipo_ref, codigo, formula, inclui, depende, observacao
    ("vistoria", "Vistoria e medição", "", "operacional", "confirmado", "nenhuma", "", "", "", "",
     "Tarefa operacional: confirma dimensões e áreas com problema. Normalmente não é item medido."),
    ("protecao_mobiliario", "Retirada/proteção de mobiliário e equipamentos", "ocupado", "operacional", "condicional", "nenhuma", "", "", "", "",
     "Conferir se é coberto pela administração/BDI ou se há composição própria; não duplicar."),
    ("protecao_piso", "Proteção de piso (faixa junto às paredes)", "comprimento_parede > 0 and faixa_protecao > 0", "item", "condicional",
     "nenhuma", "", "comprimento_parede * faixa_protecao", "", "",
     "Sem composição SINAPI específica identificada para pintura: selecionar referência ou composição própria. Quantidade = comprimento × faixa (hipótese)."),
    ("raspagem", "Raspagem de pintura solta", "area_raspagem > 0", "item", "condicional", "nenhuma", "", "area_raspagem", "", "",
     "Referência a selecionar. Quantidade pela área medida em vistoria, não pela área total."),
    ("lavagem", "Limpeza da superfície com jato de alta pressão", "estado == 'ruim'", "item", "condicional", "composicao", "99814", "area_parede", "", "",
     "Só se houver sujidade/mofo constatados. Conferir adequação ao ambiente interno."),
    ("diagnostico_umidade", "Diagnóstico e correção da causa de umidade/infiltração", "estado == 'ruim'", "pendente", "condicional", "nenhuma", "", "", "", "",
     "Pintar por cima não resolve umidade. Serviço próprio (impermeabilização/hidráulica) após diagnóstico."),
    ("massa_1", "Emassamento — uma demão (com lixamento manual)", "area_massa > 0 and demaos_massa == '1'", "item", "condicional",
     "composicao", "88495", "area_massa", "lixamento", "",
     "A descrição oficial inclui 'LIXAMENTO MANUAL'. Quantidade = área medida de massa."),
    ("massa_2", "Emassamento — duas demãos (com lixamento manual)", "area_massa > 0 and demaos_massa == '2'", "item", "condicional",
     "composicao", "88497", "area_massa", "lixamento", "",
     "A descrição oficial inclui 'LIXAMENTO MANUAL'. Quantidade = área medida de massa."),
    ("lixamento", "Lixamento da massa", "area_massa > 0", "incluida", "confirmado", "nenhuma", "", "", "", "",
     "Já incluído na composição de emassamento (descrição oficial: 'LIXAMENTO MANUAL'). Não cobrar separadamente."),
    ("fundo_selador", "Fundo selador acrílico — uma demão", "fundo", "item", "confirmado", "composicao", "88485", "area_parede", "", "",
     "Aplicar conforme especificação/fabricante."),
    ("pintura_economica", "Pintura látex acrílica econômica — duas demãos", "linha_tinta == 'economica'", "item", "confirmado",
     "composicao", "104641", "area_parede", "", "",
     "A descrição oficial já indica DUAS DEMÃOS: não multiplicar a área pelo número de demãos."),
    ("pintura_standard", "Pintura látex acrílica standard — duas demãos", "linha_tinta == 'standard'", "item", "confirmado",
     "composicao", "104642", "area_parede", "", "",
     "A descrição oficial já indica DUAS DEMÃOS: não multiplicar a área pelo número de demãos."),
    ("pintura_premium", "Pintura látex acrílica premium — duas demãos", "linha_tinta == 'premium'", "item", "confirmado",
     "composicao", "88489", "area_parede", "", "",
     "A descrição oficial já indica DUAS DEMÃOS: não multiplicar a área pelo número de demãos."),
    ("andaime", "Andaime/plataforma de trabalho", "altura > 3", "pendente", "condicional", "nenhuma", "", "", "", "",
     "Altura acima de 3 m: definir solução de acesso (andaime, PTA) e verificar se a composição já prevê. Atender NR-35."),
    ("limpeza_final", "Limpeza de respingos e final", "", "operacional", "confirmado", "nenhuma", "", "", "", "",
     "Limpeza de respingos costuma ser tarefa operacional; conferir no caderno técnico antes de cobrar à parte."),
]


class Command(BaseCommand):
    help = "Cria perfis de acesso e modelos de serviço iniciais (idempotente)."

    @transaction.atomic
    def handle(self, *args, **opts):
        for nome in PERFIS:
            Group.objects.get_or_create(name=nome)
        m, criado = ModeloServico.objects.get_or_create(
            nome="Pintura de parede (interna)",
            defaults={"descricao": "Repintura ou pintura nova de paredes internas com látex acrílica. Regras conferidas "
                                   "com descrições do SINAPI 10/2026. Inclusões detalhadas devem ser conferidas no caderno "
                                   "técnico de cada composição."})
        if criado:
            for n, (chave, texto, tipo, opcoes, un, obrig, ajuda) in enumerate(PERGUNTAS, start=1):
                Pergunta.objects.create(modelo=m, chave=chave, texto=texto, tipo=tipo, opcoes=opcoes, unidade=un,
                                        obrigatoria=obrig, ajuda=ajuda, ordem=n * 10)
            for n, (chave, etapa, cond, cls, st, tref, cod, form, inc, dep, obs) in enumerate(REGRAS, start=1):
                RegraEtapa.objects.create(modelo=m, chave=chave, etapa=etapa, condicao=cond, classificacao=cls,
                                          status_sugerido=st, tipo_ref=tref, codigo_ref=cod, formula_quantidade=form,
                                          inclui=inc, depende_de=dep, observacao=obs, ordem=n * 10)
        self.stdout.write(self.style.SUCCESS(f"Perfis: {', '.join(PERFIS)}. Modelo '{m.nome}' {'criado' if criado else 'já existia'}."))
