from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import math
import motor_preditivo
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory=".", html=True), name="static")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ARQUIVO = "./mapa_preventivo.geojson"

def calcular_distancia(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

def gerar_rota_dijkstra(features):
    bairros = {}
    for f in features:
        p = f['properties']
        nome = p.get('nome_zona', 'Desconhecido') # Corrigido para nome_zona
        peso = p.get('volume_lixo', 0) + p.get('score_risco_final', 0)
        
        if nome not in bairros:
            bairros[nome] = {'lat': p['lat_alerta'], 'lng': p['lng_alerta'], 'peso': peso}
        else:
            bairros[nome]['peso'] += peso
            
    nos_criticos = sorted(bairros.items(), key=lambda x: x[1]['peso'], reverse=True)[:4]
    
    caminhos = []
    atual_nome = "Garagem Municipal"
    atual_lat, atual_lng = -23.18, -50.64
    dist_total = 0
    nao_visitados = nos_criticos.copy()

    while nao_visitados:
        mais_proximo, menor_dist = None, float('inf')
        for nome, dados in nao_visitados:
            dist = calcular_distancia(atual_lat, atual_lng, dados['lat'], dados['lng'])
            if dist < menor_dist:
                menor_dist = dist
                mais_proximo = (nome, dados)
        
        caminhos.append({"de": atual_nome, "para": mais_proximo[0], "km": round(menor_dist * 1.45, 2)})
        dist_total += menor_dist * 1.45
        atual_nome = mais_proximo[0]
        atual_lat, atual_lng = mais_proximo[1]['lat'], mais_proximo[1]['lng']
        nao_visitados.remove(mais_proximo)

    km_volta = calcular_distancia(atual_lat, atual_lng, -23.18, -50.64) * 1.45
    caminhos.append({"de": atual_nome, "para": "Garagem Municipal", "km": round(km_volta, 2)})
    dist_total += km_volta

    dist_nao_otimizada = dist_total * 2.5
    economia_co2 = (dist_nao_otimizada - dist_total) * 1.2

    return {"caminhos": caminhos, "km_total": round(dist_total, 2), "co2_poupado": round(economia_co2, 2)}

class AcaoGestor(BaseModel):
    bairro: str
    acao: str

@app.get("/api/mapa")
async def obter_mapa():
    with open(ARQUIVO, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    dados["inteligencia_logistica"] = gerar_rota_dijkstra(dados["features"])
    return dados

@app.post("/api/acao")
async def registrar_acao(payload: AcaoGestor):
    pesos = {"desentupimento": -30, "coleta_extra": -45, "fiscalizacao": -15}
    with open(ARQUIVO, 'r', encoding='utf-8') as f: dados = json.load(f)
    
    for feature in dados['features']:
        props = feature['properties']
        if props.get('nome_zona') == payload.bairro:
            props['score_risco_final'] = max(0, props['score_risco_final'] + pesos[payload.acao])
            if payload.acao == "coleta_extra": 
                props['volume_lixo'] = max(0, props.get('volume_lixo',0) - 50)
            
    with open(ARQUIVO, 'w', encoding='utf-8') as f: json.dump(dados, f)
    
    motor_preditivo.motor_final_ecoprioridade() # Atualiza e roda o Voronoi novamente
    return {"status": "ok"}