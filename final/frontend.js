// --- 1. GERENCIAMENTO DE ESTADO ---
let mapaGlobal; 
let heatLayerAtual;
let dadosGeoJSON; // Cache do último estado recebido do Backend

// Inicialização (Executada ao abrir a página)
document.addEventListener("DOMContentLoaded", () => {
    inicializarMapaBase();
    carregarDadosDoServidor();
});

function inicializarMapaBase() {
    mapaGlobal = L.map('map', {
        center: [-23.18, -50.64], zoom: 14, minZoom: 13, maxZoom: 17
    });
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(mapaGlobal);
}

// --- 2. COMUNICAÇÃO COM A API ---
async function carregarDadosDoServidor() {
    try {
        const response = await fetch('http://localhost:8000/api/mapa');
        dadosGeoJSON = await response.json();
        
        atualizarInterfaceCompleta('risco'); // 'risco' é o filtro padrão
    } catch (error) {
        console.error("Erro de API. O Backend está rodando?", error);
    }
}

// --- 3. FILTROS E RENDERIZAÇÃO DO MAPA ---
function atualizarInterfaceCompleta(tipoFiltro) {
    renderizarHeatmap(tipoFiltro);
    renderizarPaineisDashboards();
    verificarAlertasCriticos();
}

function renderizarHeatmap(tipoFiltro) {
    if (heatLayerAtual) mapaGlobal.removeLayer(heatLayerAtual);

    const pontosCalor = dadosGeoJSON.features.map(f => {
        const props = f.properties;
        let intensidade = 0;

        // LÓGICA DE FILTROS APLICADA AO LEAFLET
        switch(tipoFiltro) {
            case 'risco': // Visão Padrão: Formula Mestra
                intensidade = props.score_risco_final / 100; 
                break;
            case 'volume': // Visão de Resíduos (ODS 12)
                const maxPop = 1000; // Valor arbitrário de normalização
                intensidade = (props.v0001 / maxPop); 
                break;
            case 'densidade': // Visão Estrutural (IBGE puro)
                intensidade = props.score_estimado_ouvidoria / 100;
                break;
        }
        return [props.lat_alerta, props.lng_alerta, Math.min(intensidade, 1.0)];
    });

    // Paletas de cores diferentes baseadas no filtro
    const gradientes = {
        'risco': {0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'},
        'volume': {0.4: 'cyan', 0.6: 'blue', 1.0: 'purple'},
        'densidade': {0.4: 'white', 0.8: 'yellow', 1.0: 'orange'}
    };

    heatLayerAtual = L.heatLayer(pontosCalor, {
        radius: 18, blur: 15, max: 0.8, 
        gradient: gradientes[tipoFiltro]
    }).addTo(mapaGlobal);
}

// --- 4. RENDERIZAÇÃO DA UI (BARRA HORIZONTAL E LISTA) ---
function renderizarPaineisDashboards() {
    const container = document.getElementById('lista-bairros-container');
    if(!container) return; // Segurança caso o HTML não tenha a div

    // Ordena do pior score para o melhor
    const zonasOrdenadas = [...dadosGeoJSON.features].sort((a,b) => 
        b.properties.score_risco_final - a.properties.score_risco_final
    );

    let htmlBuilder = '';
    
    zonasOrdenadas.forEach(f => {
        const p = f.properties;
        const id_unico = p.CD_SETOR || `${p.lat_alerta}_${p.lng_alerta}`;
        const cor = p.score_risco_final > 75 ? '#ef4444' : p.score_risco_final > 50 ? '#f59e0b' : '#22c55e';
        
        // Estrutura de Barra de Nível exigida
        htmlBuilder += `
        <div class="zona-card" style="margin-bottom:15px; background: #1e293b; padding:10px; border-radius:5px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span>Setor / Zona ${id_unico.substring(0,6)}...</span>
                <span style="font-weight:bold; color:${cor}">${p.nivel_urgencia} (${p.score_risco_final})</span>
            </div>
            
            <div style="width:100%; background:#334155; height:10px; border-radius:5px; overflow:hidden;">
                <div style="width:${p.score_risco_final}%; background:${cor}; height:100%; transition: width 0.5s;"></div>
            </div>
            
            ${p.ultima_intervencao ? `<div style="font-size:10px; color:#94a3b8; margin-top:5px;">✅ Última Ação: ${p.ultima_intervencao}</div>` : ''}

            <button onclick="abrirModalAcao('${id_unico}')" style="margin-top:10px; background:#2563eb; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">
                Executar Ação Preventiva
            </button>
        </div>`;
    });

    container.innerHTML = htmlBuilder;
}

// --- 5. MOTOR DE NOTIFICAÇÕES E IA ---
function verificarAlertasCriticos() {
    const central = document.getElementById('alertas-ia-container');
    if(!central) return;

    let alertasHtml = '';

    dadosGeoJSON.features.forEach(f => {
        const p = f.properties;
        const id_unico = p.CD_SETOR || `${p.lat_alerta}_${p.lng_alerta}`;

        // Regra de Negócio: Notificação Automática Nível Crítico
        if (p.score_risco_final > 75 && p.status_notificacao !== "RESOLVIDO") {
            alertasHtml += `
            <div class="alerta critico" style="border-left: 4px solid red; padding: 10px; background: rgba(255,0,0,0.1); margin-bottom: 10px;">
                <strong>🚨 ALERTA IMEDIATO:</strong> A zona ${id_unico.substring(0,6)} atingiu score crítico (${p.score_risco_final}). 
                <br><span style="font-size:11px;"><em>IA sugere: Desentupimento de bueiro preventivo devido à alta densidade e declividade.</em></span>
            </div>`;
        }

        // Regra de Negócio: Volume de Lixo
        if (p.v0001 > 800) { // Limiar técnico populacional
             alertasHtml += `
            <div class="alerta volume" style="border-left: 4px solid blue; padding: 10px; background: rgba(0,0,255,0.1); margin-bottom: 10px;">
                <strong>🚛 COLETA EXTRAORDINÁRIA:</strong> Volume de resíduos projetado excede capacidade normal.
            </div>`;
        }
    });

    central.innerHTML = alertasHtml || "<p>Nenhum alerta crítico ativo. Cidade operando dentro da normalidade.</p>";
}

// --- 6. COMANDO DO GESTOR (O RECÁLCULO) ---
async function enviarAcaoParaBackend(setor_id, tipoAcaoSelecionada) {
    try {
        // Envia o comando POST para a API Python mutar o GeoJSON
        const response = await fetch('http://localhost:8000/api/acao', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                setor_id: setor_id,
                tipo_acao: tipoAcaoSelecionada
            })
        });

        if (response.ok) {
            alert("✅ Ação registrada! Recalculando Inteligência Espacial...");
            // O Segredo: Recarrega os dados do servidor. Como o GeoJSON foi alterado, 
            // a barra de progresso vai diminuir, o mapa vai mudar de cor e o alerta some.
            await carregarDadosDoServidor(); 
            fecharModalAcao();
        } else {
            alert("Erro ao processar ação no servidor.");
        }
    } catch(err) {
        console.error(err);
        alert("Erro de conexão com o Motor Preditivo.");
    }
}