const ApiSimulador = (() => {
  const logs = [];
  let prioridadeAtual = null;

  function agoraISO() {
    return new Date().toISOString();
  }

  function registrar(tipo, payload) {
    logs.unshift({
      id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      data: agoraISO(),
      tipo,
      payload
    });
    if (logs.length > 200) logs.pop();
  }

  function podeExecutar(comando) {
    if (prioridadeAtual === "emergencia" && comando !== "emergencia" && comando !== "silenciar") {
      return {
        ok: false,
        motivo: "Emergência ativa. Outros comandos estão bloqueados."
      };
    }
    return { ok: true };
  }

  async function enviarComando(comando, payload = {}) {
    const cheque = podeExecutar(comando);
    if (!cheque.ok) {
      registrar("bloqueio", { comando, motivo: cheque.motivo, payload });
      return {
        success: false,
        message: cheque.motivo
      };
    }

    if (comando === "emergencia") prioridadeAtual = "emergencia";
    if (comando === "silenciar") prioridadeAtual = null;

    registrar("comando", { comando, payload });

    await new Promise(resolve => setTimeout(resolve, 180));

    return {
      success: true,
      message: `Comando "${comando}" executado`,
      payload
    };
  }

  async function carregarConfig() {
    const response = await fetch("./config.json");
    if (!response.ok) {
      throw new Error("Não foi possível carregar o config.json");
    }
    return response.json();
  }

  function listarLogs() {
    return [...logs];
  }

  function limparLogs() {
    logs.length = 0;
  }

  function getPrioridadeAtual() {
    return prioridadeAtual;
  }

  return {
    enviarComando,
    carregarConfig,
    listarLogs,
    limparLogs,
    getPrioridadeAtual
  };
})();
