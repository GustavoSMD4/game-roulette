const CHAVE_USUARIO = "gameRouletteUsuario";

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
