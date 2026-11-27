// Teste final de aceite pelas telas (navegador real, sem IA).
// Uso: BASE_URL=http://127.0.0.1:8000 ADMIN_SENHA=... SINAPI_ARQUIVO=/caminho/SINAPI-AAAA-MM-formato-xlsx.zip \
//      CAPTURAS=/pasta node e2e/aceite.js
// Os dados digitados são de TESTE (escola e empresa fictícias).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const URL = process.env.BASE_URL || 'http://127.0.0.1:8000';
const CAP = process.env.CAPTURAS || '/tmp/capturas';
const SINAPI = process.env.SINAPI_ARQUIVO;
const ADMIN_SENHA = process.env.ADMIN_SENHA;
fs.mkdirSync(CAP, { recursive: true });

let passo = 0;
function ok(msg) { console.log(`✔ ${msg}`); }
async function foto(page, nome) {
  passo += 1;
  await page.screenshot({ path: path.join(CAP, `${String(passo).padStart(2, '0')}-${nome}.png`), fullPage: true });
}
async function semErro(page) {
  const msgErro = await page.locator('.msg.error').allTextContents();
  if (msgErro.length) throw new Error('Mensagem de erro na tela: ' + msgErro.join(' | '));
  const listaErro = await page.locator('.errorlist').allTextContents();
  if (listaErro.length) throw new Error('Erro de formulário: ' + listaErro.join(' | '));
}
async function entrar(page, usuario, senha) {
  await page.goto(`${URL}/entrar/`);
  await page.fill('#id_username', usuario);
  await page.fill('#id_password', senha);
  await page.click('button:has-text("Entrar")');
  await page.waitForURL(`${URL}/`);
}
async function salvar(page) { await page.click('button:has-text("Salvar")'); await page.waitForLoadState('networkidle'); await semErro(page); }

(async () => {
  if (!SINAPI || !ADMIN_SENHA) throw new Error('Defina SINAPI_ARQUIVO e ADMIN_SENHA');
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ acceptDownloads: true, viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();

  // Preparação (administrador): empresa e usuário orçamentista
  await entrar(page, 'admin', ADMIN_SENHA);
  await page.goto(`${URL}/empresa/editar/`);
  await page.fill('#id_razao_social', 'EMPRESA DE TESTE LTDA');
  await page.fill('#id_cnpj', 'CNPJ-DE-TESTE');
  await page.fill('#id_regime_tributario', 'a definir (teste)');
  await salvar(page);
  await page.goto(`${URL}/usuarios/novo/`);
  await page.fill('#id_username', 'orcamentista');
  await page.fill('#id_first_name', 'Usuário de teste');
  await page.selectOption('#id_perfil', 'Orçamentista');
  await page.fill('#id_senha', 'Orcamentista-Teste-2026');
  await salvar(page);
  ok('Administrador cadastrou empresa e usuário orçamentista');
  await page.click('button:has-text("Sair")');

  await entrar(page, 'orcamentista', 'Orcamentista-Teste-2026');
  // Orçamentista não acessa gestão de usuários (permissão no servidor)
  const r403 = await page.goto(`${URL}/usuarios/`);
  if (r403.status() !== 403) throw new Error('Perfil orçamentista deveria receber 403 em /usuarios/');
  ok('Permissão verificada no servidor (403 para gestão de usuários)');

  // 1. Cadastrar obra (cliente, obra, ambiente)
  await page.goto(`${URL}/clientes/novo/`);
  await page.fill('#id_nome', 'Escola Estadual de Teste (fictícia)');
  await page.selectOption('#id_tipo', 'escola');
  await page.fill('#id_municipio', 'Vila Velha');
  await salvar(page);
  await page.goto(`${URL}/obras/nova/`);
  await page.selectOption('#id_cliente', { label: 'Escola Estadual de Teste (fictícia)' });
  await page.fill('#id_nome', 'Manutenção — pintura da sala 1');
  await page.fill('#id_municipio', 'Vila Velha');
  await salvar(page);
  await page.click('a:has-text("Novo ambiente")');
  await page.fill('#id_nome', 'Sala 1');
  await page.fill('#id_comprimento', '8,00');
  await page.fill('#id_largura', '6,00');
  await page.fill('#id_pe_direito', '3,00');
  await salvar(page);
  await foto(page, 'obra-cadastrada');
  ok('1. Obra cadastrada com ambiente');
  const obraUrl = page.url();

  // 2. Importar base oficial (arquivo real), conferir prévia e confirmar
  await page.goto(`${URL}/bases/importar/`);
  await page.setInputFiles('#id_arquivo', SINAPI);
  await page.fill('#id_uf', 'ES');
  await page.selectOption('#id_regime', 'SD');
  await page.click('button:has-text("Salvar")');
  await page.waitForURL(/\/bases\/\d+\/$/, { timeout: 300000 });
  await semErro(page);
  await foto(page, 'base-previa');
  const conferencia = await page.locator('tr:has(th:has-text("Conferência analítica")) td').textContent();
  ok('2a. Prévia: ' + conferencia.trim().slice(0, 120));
  await page.click('button:has-text("Confirmar importação")');
  await page.waitForLoadState('networkidle');
  await semErro(page);
  ok('2b. Base confirmada');
  // Consulta por descrição
  await page.goto(`${URL}/bases/consulta/?tipo=composicao&q=pintura+latex+standard+paredes&unidade=M2`);
  const achou = await page.locator('td:has-text("104642")').count();
  if (!achou) throw new Error('Consulta não encontrou 104642');
  await foto(page, 'consulta');
  ok('Consulta por descrição/unidade encontra a composição 104642');

  // Orçamento + parâmetros (BDI)
  await page.goto(obraUrl);
  await page.click('a:has-text("Novo orçamento")');
  await page.fill('#id_titulo', 'Pintura da sala 1 — teste de aceite');
  await page.selectOption('#id_finalidade', 'proposta');
  await page.selectOption('#id_base', { index: 1 });
  await salvar(page);
  const orcUrl = page.url();

  // 3. Informar o serviço e responder ao modelo
  await page.click('a:has-text("Detalhar serviço por modelo")');
  await page.click('button:has-text("Continuar")');
  await page.selectOption('select[name=ambiente]', { label: 'Sala 1' });
  const resp = { area_parede: '30', area_massa: '4,5', altura: '3', area_raspagem: '0', comprimento_parede: '10', faixa_protecao: '1' };
  for (const [k, v] of Object.entries(resp)) await page.fill(`input[name=p_${k}]`, v);
  await page.selectOption('select[name=p_tipo_servico]', 'repintura');
  await page.selectOption('select[name=p_estado]', 'regular');
  await page.selectOption('select[name=p_demaos_massa]', '1');
  await page.selectOption('select[name=p_fundo]', 'nao');
  await page.selectOption('select[name=p_linha_tinta]', 'standard');
  await page.selectOption('select[name=p_ocupado]', 'sim');
  await page.click('button:has-text("Ver etapas sugeridas")');
  await page.waitForLoadState('networkidle');
  await semErro(page);
  await foto(page, 'modelo-etapas-sugeridas');
  ok('3. Perguntas respondidas e etapas sugeridas exibidas');

  // 4. Conferir etapas, composições e quantitativos
  const txt = await page.locator('table').last().textContent();
  for (const esperado of ['104642', '88495', 'Lixamento da massa', 'Já incluída em outra composição', 'referência a definir']) {
    if (!txt.includes(esperado)) throw new Error('Etapa esperada não apareceu: ' + esperado);
  }
  await page.click('button:has-text("Incluir etapas marcadas")');
  await page.waitForURL(orcUrl);
  await semErro(page);
  ok('4. Etapas conferidas e incluídas (lixamento não duplicado; proteção de piso sem referência)');

  // 5. Composição própria para a proteção de piso
  await page.goto(`${URL}/composicoes-proprias/nova/`);
  await page.fill('#id_descricao', 'Proteção de piso com lona plástica (teste)');
  await page.fill('#id_unidade', 'M2');
  await page.fill('#id_justificativa', 'Não identificada composição SINAPI específica para proteção de piso em pintura.');
  await salvar(page);
  const cpUrl = page.url();
  const cpCodigo = (await page.locator('h1').textContent()).split(' ')[0];
  await page.click('a:has-text("Adicionar insumo/serviço")');
  await page.selectOption('#id_tipo', 'mo_propria');
  await page.fill('#id_descricao', 'Servente (equipe própria)');
  await page.fill('#id_unidade', 'H');
  await page.fill('#id_coeficiente', '0,05');
  await page.fill('#id_preco_informado', '12,00');
  await page.fill('#id_encargos_pct', '80');
  await page.fill('#id_fonte', 'Custo horário de teste');
  await salvar(page);
  await page.goto(cpUrl);
  await foto(page, 'composicao-propria');
  await page.goto(orcUrl);
  await page.locator('tr:has-text("Proteção de piso") a:has-text("editar")').click();
  await page.selectOption('#id_tipo_ref', 'cp');
  await page.fill('#id_codigo', cpCodigo);
  await page.selectOption('#id_status', 'confirmado');
  await salvar(page);
  ok(`5. Composição própria ${cpCodigo} criada e aplicada ao item de proteção de piso`);

  // 6. Encargos e BDI
  await page.click('a:has-text("Parâmetros")');
  const bdi = { bdi_ac: '3', bdi_s: '0,8', bdi_r: '1,27', bdi_g: '0', bdi_df: '1,23', bdi_l: '6,16', bdi_i: '8,65' };
  for (const [k, v] of Object.entries(bdi)) await page.fill(`#id_${k}`, v);
  await page.fill('#id_justificativa_bdi', 'Valores de TESTE para o aceite; substituir pelos dados reais da empresa.');
  await salvar(page);
  await foto(page, 'orcamento-rascunho');
  const bdiTexto = await page.locator('p.suave').first().textContent();
  ok('6. BDI aplicado — ' + bdiTexto.match(/BDI serviços: [^·]+/)[0].trim());

  // 7. Revisar e salvar versão
  await page.click('a:has-text("Revisar e salvar versão")');
  await page.fill('#id_descricao', 'Emissão inicial (teste de aceite)');
  await page.fill('#id_revisado_por', 'Revisor de teste');
  await salvar(page);
  if (!(await page.locator('h1 .tag:has-text("R00")').count())) throw new Error('Versão R00 não exibida');
  await foto(page, 'versao-R00');
  ok('7. Versão R00 salva e congelada');

  // 8. Exportar XLSX e PDF
  for (const fmt of ['XLSX', 'PDF']) {
    const [dl] = await Promise.all([page.waitForEvent('download'), page.click(`a:has-text("Exportar ${fmt}")`)]);
    const destino = path.join(CAP, dl.suggestedFilename());
    await dl.saveAs(destino);
    const tam = fs.statSync(destino).size;
    if (tam < 2000) throw new Error(`${fmt} pequeno demais`);
    ok(`8. ${fmt} exportado: ${destino} (${tam} bytes)`);
  }
  await browser.close();
  console.log('ACEITE CONCLUÍDO');
})().catch((e) => { console.error('FALHOU:', e.message); process.exit(1); });
