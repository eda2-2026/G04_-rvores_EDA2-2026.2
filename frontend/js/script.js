
"use strict";

const ABERTURA = 7 * 60;
const FECHAMENTO = 22 * 60;
const TOTAL = FECHAMENTO - ABERTURA;

const $ = (id) => document.getElementById(id);

const estado = {
  dia: hojeISO(),
  dados: null,
};

function pad(n) { return String(n).padStart(2, "0"); }

function paraISO(data) {
  return `${data.getFullYear()}-${pad(data.getMonth() + 1)}-${pad(data.getDate())}`;
}

function hojeISO() { return paraISO(new Date()); }

function dataDeISO(iso) {
  const [a, m, d] = iso.split("-").map(Number);
  return new Date(a, m - 1, d);
}

function somarDias(iso, dias) {
  const data = dataDeISO(iso);
  data.setDate(data.getDate() + dias);
  return paraISO(data);
}

function paraMinutos(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
}

function deMinutos(min) { return `${pad(Math.floor(min / 60))}:${pad(min % 60)}`; }

function horaDe(isoDataHora) { return isoDataHora.slice(11, 16); }

function dataLonga(iso) {
  return dataDeISO(iso).toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
}

function plural(n, singular, pluralTexto) { return `${n} ${n === 1 ? singular : pluralTexto}`; }

async function api(url, opcoes) {
  try {
    const resposta = await fetch(url, opcoes);
    const dados = await resposta.json().catch(() => ({}));
    return { ok: resposta.ok, status: resposta.status, dados };
  } catch (erro) {
    return { ok: false, status: 0, dados: { erro: "Não foi possível falar com o servidor." } };
  }
}

function enviarJSON(metodo, corpo) {
  return {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  };
}

function mensagem(elemento, texto, tipo) {
  elemento.textContent = texto || "";
  elemento.classList.toggle("mensagem--ok", tipo === "ok");
  elemento.classList.toggle("mensagem--erro", tipo === "erro");
}

function criar(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) elemento.className = classe;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

async function carregarAgenda() {
  const resposta = await api(`/api/agenda?dia=${estado.dia}`);
  if (!resposta.ok) {
    mensagem($("msg-mapa"), resposta.dados.erro || "Erro ao carregar a agenda.", "erro");
    return;
  }
  mensagem($("msg-mapa"), "");
  estado.dados = resposta.dados;
  preencherSelectsDeSala();
  desenharMapa();
}

function desenharMapa() {
  const { salas } = estado.dados;
  const mapa = $("mapa");
  mapa.replaceChildren();

  $("titulo-mapa").textContent = dataLonga(estado.dia);
  $("form-dia").textContent = `Para ${dataLonga(estado.dia)}.`;

  const linhaEixo = criar("div", "linha linha--eixo");
  linhaEixo.append(criar("div", "sala-nome"));
  const eixo = criar("div", "eixo");
  for (let hora = ABERTURA / 60; hora < FECHAMENTO / 60; hora++) {
    eixo.append(criar("span", "", `${hora}h`));
  }
  linhaEixo.append(eixo);
  mapa.append(linhaEixo);

  const minutosAgora = estado.dia === hojeISO()
    ? new Date().getHours() * 60 + new Date().getMinutes()
    : null;

  for (const sala of salas) {
    const linha = criar("div", "linha");

    const nome = criar("div", "sala-nome");
    nome.append(criar("strong", "", sala.nome));
    nome.append(criar("span", "", `${sala.capacidade} lugares`));
    linha.append(nome);

    const trilha = criar("div", "trilha");
    trilha.dataset.salaId = sala.id;
    trilha.title = "Clique para reservar neste horário";
    trilha.addEventListener("click", aoClicarNaTrilha);

    for (const reserva of sala.reservas) {
      trilha.append(criarBloco(sala, reserva));
    }

    if (minutosAgora !== null && minutosAgora >= ABERTURA && minutosAgora <= FECHAMENTO) {
      const marca = criar("div", "agora");
      marca.style.left = `${((minutosAgora - ABERTURA) / TOTAL) * 100}%`;
      marca.title = "Agora";
      trilha.append(marca);
    }

    linha.append(trilha);
    mapa.append(linha);
  }
}

function criarBloco(sala, reserva) {
  const inicio = paraMinutos(horaDe(reserva.inicio));
  const fim = paraMinutos(horaDe(reserva.fim));

  const bloco = criar("button", "bloco");
  bloco.type = "button";
  bloco.dataset.reservaId = reserva.id;
  bloco.style.left = `${((inicio - ABERTURA) / TOTAL) * 100}%`;
  bloco.style.width = `${((fim - inicio) / TOTAL) * 100}%`;
  bloco.title = `${reserva.titulo} — ${reserva.responsavel}\n${horaDe(reserva.inicio)}–${horaDe(reserva.fim)}`;

  bloco.append(criar("span", "bloco__titulo", reserva.titulo));
  if (fim - inicio >= 60) {
    bloco.append(criar("span", "bloco__hora", `${horaDe(reserva.inicio)}–${horaDe(reserva.fim)}`));
  }

  bloco.addEventListener("click", (evento) => {
    evento.stopPropagation();
    abrirDetalhe(sala, reserva);
  });
  return bloco;
}

function aoClicarNaTrilha(evento) {
  if (evento.target !== evento.currentTarget) return;

  const trilha = evento.currentTarget;
  const retangulo = trilha.getBoundingClientRect();
  const fracao = (evento.clientX - retangulo.left) / retangulo.width;

  let inicio = ABERTURA + Math.floor((fracao * TOTAL) / 30) * 30;
  inicio = Math.min(inicio, FECHAMENTO - 30);
  let fim = Math.min(inicio + 60, FECHAMENTO);

  const sala = estado.dados.salas.find((s) => s.id === Number(trilha.dataset.salaId));
  for (const reserva of sala.reservas) {
    const comecoDela = paraMinutos(horaDe(reserva.inicio));
    if (comecoDela > inicio && comecoDela < fim) fim = comecoDela;
  }

  preencherFormulario(sala.id, deMinutos(inicio), deMinutos(fim));
}

function preencherFormulario(salaId, inicio, fim) {
  $("f-sala").value = String(salaId);
  $("f-inicio").value = inicio;
  $("f-fim").value = fim;
  mensagem($("msg-reserva"), "");
  $("f-titulo").focus();
  if (window.innerWidth < 1000) {
    $("form-reserva").scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function destacarBloco(reservaId) {
  const bloco = document.querySelector(`.bloco[data-reserva-id="${reservaId}"]`);
  if (!bloco) return;
  bloco.classList.add("bloco--conflito");
  bloco.scrollIntoView({ block: "nearest", inline: "center" });
  setTimeout(() => bloco.classList.remove("bloco--conflito"), 3500);
}

function preencherSelectsDeSala() {
  for (const id of ["f-sala", "a-sala"]) {
    const select = $(id);
    const anterior = select.value;
    select.replaceChildren();
    for (const sala of estado.dados.salas) {
      const opcao = criar("option", "", `${sala.nome} (${sala.capacidade})`);
      opcao.value = String(sala.id);
      select.append(opcao);
    }
    if (anterior && [...select.options].some((o) => o.value === anterior)) {
      select.value = anterior;
    }
  }
}

async function enviarReserva(evento) {
  evento.preventDefault();
  const aviso = $("msg-reserva");

  if (!$("f-inicio").value || !$("f-fim").value) {
    mensagem(aviso, "Informe o horário de início e de fim.", "erro");
    return;
  }

  const corpo = {
    sala_id: Number($("f-sala").value),
    titulo: $("f-titulo").value,
    responsavel: $("f-responsavel").value,
    inicio: `${estado.dia}T${$("f-inicio").value}`,
    fim: `${estado.dia}T${$("f-fim").value}`,
  };

  const resposta = await api("/api/reservas", enviarJSON("POST", corpo));

  if (resposta.ok) {
    const { custo } = resposta.dados;
    mensagem(
      aviso,
      `Reserva confirmada. O horário foi verificado em ${plural(custo.comparacoes, "comparação", "comparações")}, ` +
      `numa sala com ${plural(custo.reservas_na_sala, "reserva", "reservas")}.`,
      "ok"
    );
    $("f-titulo").value = "";
    guardarResponsavel(corpo.responsavel);
    await recarregarTudo();
    return;
  }

  if (resposta.status === 409) {
    const { custo, conflito } = resposta.dados;
    mensagem(
      aviso,
      `${resposta.dados.erro} (verificado em ${plural(custo.comparacoes, "comparação", "comparações")}.)`,
      "erro"
    );
    destacarBloco(conflito.id);
    return;
  }

  mensagem(aviso, resposta.dados.erro || "Não foi possível reservar.", "erro");
}

function guardarResponsavel(nome) {
  try { localStorage.setItem("responsavel", nome.trim()); } catch (e) { }
}

function lerResponsavel() {
  try { return localStorage.getItem("responsavel") || ""; } catch (e) { return ""; }
}

async function procurarSalaLivre(evento) {
  evento.preventDefault();
  const aviso = $("msg-livre");
  const lista = $("resultado-livre");
  lista.replaceChildren();

  const inicio = $("l-inicio").value;
  const fim = $("l-fim").value;
  if (!inicio || !fim) {
    mensagem(aviso, "Informe o horário de início e de fim.", "erro");
    return;
  }

  const parametros = new URLSearchParams({
    inicio: `${estado.dia}T${inicio}`,
    fim: `${estado.dia}T${fim}`,
    capacidade: $("l-capacidade").value || "0",
  });
  if ($("l-tipo").value) parametros.set("tipo", $("l-tipo").value);

  const resposta = await api(`/api/salas-livres?${parametros}`);
  if (!resposta.ok) {
    mensagem(aviso, resposta.dados.erro || "Erro na busca.", "erro");
    return;
  }

  const { salas, custo } = resposta.dados;
  if (salas.length === 0) {
    mensagem(aviso, "Nenhuma sala livre nesse horário com esses filtros.", "erro");
    return;
  }

  mensagem(
    aviso,
    `${plural(salas.length, "sala livre", "salas livres")}, da menor para a maior. ` +
    `Foram verificadas ${plural(custo.salas_verificadas, "sala", "salas")} em ` +
    `${plural(custo.comparacoes, "comparação", "comparações")}.`,
    "ok"
  );

  for (const sala of salas) {
    const item = criar("li");
    const texto = criar("div");
    texto.append(criar("strong", "", sala.nome));
    texto.append(criar("small", "", `${sala.capacidade} lugares`));
    const botao = criar("button", "", "Reservar aqui");
    botao.type = "button";
    botao.addEventListener("click", () => preencherFormulario(sala.id, inicio, fim));
    item.append(texto, botao);
    lista.append(item);
  }
}

function abrirDetalhe(sala, reserva) {
  $("d-titulo").textContent = reserva.titulo;
  $("d-info").textContent =
    `${sala.nome} · ${horaDe(reserva.inicio)}–${horaDe(reserva.fim)} · ${reserva.responsavel}`;
  $("d-cancelar").dataset.reservaId = reserva.id;
  $("detalhe").showModal();
}

async function cancelarReserva() {
  const id = $("d-cancelar").dataset.reservaId;
  const resposta = await api(`/api/reservas/${id}`, { method: "DELETE" });
  $("detalhe").close();

  if (resposta.ok) {
    await recarregarTudo();
    mensagem($("msg-mapa"), `Reserva "${resposta.dados.reserva.titulo}" cancelada.`, "ok");
  } else {
    mensagem($("msg-mapa"), resposta.dados.erro || "Não foi possível cancelar.", "erro");
  }
}

async function carregarArvore() {
  const salaId = $("a-sala").value;
  if (!salaId) return;

  const [desenho, estatisticas] = await Promise.all([
    fetch(`/api/arvore/${salaId}`).then((r) => (r.ok ? r.text() : "")).catch(() => ""),
    api("/api/estatisticas"),
  ]);

  $("arvore-desenho").innerHTML = desenho || "<p>Não foi possível carregar o desenho.</p>";

  const dados = estatisticas.ok
    ? estatisticas.dados.salas.find((s) => String(s.sala_id) === salaId)
    : null;
  if (!dados) { $("arvore-numeros").textContent = ""; return; }

  const visitaNoMaximo = 2 * dados.altura;
  $("arvore-numeros").textContent =
    `${plural(dados.reservas, "reserva", "reservas")} · altura ${dados.altura} · ` +
    `altura negra ${dados.altura_negra} · ${plural(dados.rotacoes, "rotação", "rotações")} até agora · ` +
    `propriedades rubro-negras: ${dados.valida ? "todas satisfeitas" : "VIOLADAS"}. ` +
    (visitaNoMaximo < dados.reservas
      ? `Verificar um horário aqui visita no máximo ${visitaNoMaximo} nós, em vez de percorrer as ${dados.reservas} reservas.`
      : "");
}

async function recarregarTudo() {
  await carregarAgenda();
  if ($("arvore-detalhes").open) await carregarArvore();
}

function irParaDia(iso) {
  estado.dia = iso || hojeISO();
  $("dia").value = estado.dia;
  recarregarTudo();
}

$("dia").addEventListener("change", () => irParaDia($("dia").value));
$("dia-anterior").addEventListener("click", () => irParaDia(somarDias(estado.dia, -1)));
$("dia-seguinte").addEventListener("click", () => irParaDia(somarDias(estado.dia, 1)));
$("dia-hoje").addEventListener("click", () => irParaDia(hojeISO()));

$("form-reserva").addEventListener("submit", enviarReserva);
$("form-livre").addEventListener("submit", procurarSalaLivre);

$("d-fechar").addEventListener("click", () => $("detalhe").close());
$("d-cancelar").addEventListener("click", cancelarReserva);

$("arvore-detalhes").addEventListener("toggle", () => {
  if ($("arvore-detalhes").open) carregarArvore();
});
$("a-sala").addEventListener("change", carregarArvore);

$("f-responsavel").value = lerResponsavel();
irParaDia(hojeISO());
