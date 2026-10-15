const CHAVE_USUARIO = "gameRouletteUsuario";
const CHAVE_MENU = "gameRouletteMenuRecolhido";

function salvarUsuario(usuario) {
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(usuario));
}

function obterUsuario() {
    try {
        return JSON.parse(localStorage.getItem(CHAVE_USUARIO));
    } catch (error) {
        return null;
    }
}

function limparUsuario() {
    localStorage.removeItem(CHAVE_USUARIO);
}

function sair() {
    limparUsuario();
    window.location.href = "/front/login";
}

function exigirUsuario() {
    const usuario = obterUsuario();

    if (!usuario || usuario.id === undefined) {
        window.location.href = "/front/login";
        return null;
    }

    return usuario;
}

async function api(url, metodo, corpo) {
    const resposta = await fetch(url, {
        method: metodo || "GET",
        headers: { "Content-Type": "application/json" },
        body: corpo ? JSON.stringify(corpo) : undefined
    });

    const dados = await resposta.json().catch(() => ({}));

    if (!resposta.ok) {
        if (resposta.status === 429) {
            throw new Error(dados.error || "Muitas requisições em pouco tempo. Aguarde um instante e tente novamente.");
        }

        throw new Error(dados.error || "Não foi possível concluir a operação");
    }

    return dados;
}

function formatarReal(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function escapar(texto) {
    return String(texto === null || texto === undefined ? "" : texto)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function exibirMensagem(elemento, texto, tipo) {
    elemento.textContent = texto;
    elemento.className = "mensagem " + (tipo || "");
}

function tratarSessaoInvalida(error) {
    if (error && error.message === "Usuário não encontrado") {
        limparUsuario();
        window.location.href = "/front/login";
        return true;
    }

    return false;
}

function iniciarMenu() {
    const botao = document.getElementById("btnMenu");
    const recolher = document.getElementById("btnRecolher");
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("backdrop");

    if (!sidebar) {
        return;
    }

    if (localStorage.getItem(CHAVE_MENU) === "1") {
        document.body.classList.add("menu-recolhido");
    }

    if (recolher) {
        recolher.addEventListener("click", () => {
            document.body.classList.toggle("menu-recolhido");
            localStorage.setItem(CHAVE_MENU, document.body.classList.contains("menu-recolhido") ? "1" : "0");
        });
    }

    const fechar = () => {
        sidebar.classList.remove("aberta");
        backdrop.classList.remove("aberta");
    };

    if (botao) {
        botao.addEventListener("click", () => {
            sidebar.classList.toggle("aberta");
            backdrop.classList.toggle("aberta");
        });
    }

    if (backdrop) {
        backdrop.addEventListener("click", fechar);
    }

    document.querySelectorAll(".item-nav").forEach(item => {
        const caminho = window.location.pathname;

        item.classList.toggle("ativo", item.getAttribute("href") === caminho);
        item.addEventListener("click", fechar);
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarMenu);
} else {
    iniciarMenu();
}
