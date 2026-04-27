import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, MultiPoint
from shapely.ops import voronoi_diagram
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def motor_final_ecoprioridade():
    print("🚀 --- INICIANDO MOTOR FINAL: GEOMETRIA VORONOI + DADOS REAIS ---")
    headers = {'User-Agent': 'EcoPrioridade-Hackathon-Bot/1.0'}

    # 1. CARREGAR DADOS DO IBGE (BASE DE CÁLCULO)
    try:
        print("📂 Processando dados do Censo 2022...")
        gdf_ibge = gpd.read_file('./setores_censitarios/PR_setores_CD2022.shp')
        gdf_cornelio = gdf_ibge[gdf_ibge['CD_MUN'] == '4106407'].copy().to_crs("EPSG:4326")

        df_csv = pd.read_csv('./setores_censitarios/agregados_preliminares_por_setores_censitarios_BR.csv', 
                             sep=';', usecols=['CD_SETOR', 'v0001'], dtype={'CD_SETOR': str})

        gdf_cornelio['CD_SETOR'] = gdf_cornelio['CD_SETOR'].astype(str).str.strip()
        df_csv['CD_SETOR'] = df_csv['CD_SETOR'].astype(str).str[:15]
        
        ibge_enriquecido = gdf_cornelio.merge(df_csv, on='CD_SETOR', how='left')
        ibge_enriquecido['v0001'] = pd.to_numeric(ibge_enriquecido['v0001'], errors='coerce').fillna(0)
    except Exception as e:
        print(f"❌ Erro ao carregar bases locais: {e}")
        return

    # 2. EXTRAIR INFRAESTRUTURA (PONTOS SEMENTE PARA O VORONOI)
    print("📡 Buscando sementes urbanas via Overpass API...")
    url_overpass = "https://overpass-api.de/api/interpreter"
    query = """
    [out:json][timeout:50];
    area[name="Cornélio Procópio"]->.searchArea;
    (nwr["amenity"](area.searchArea); nwr["leisure"](area.searchArea); nwr["highway"="bus_stop"](area.searchArea););
    out center;
    """
    try:
        resp = requests.post(url_overpass, data={'data': query}, headers=headers)
        dados_json = resp.json()
        pontos = []
        for e in dados_json.get('elements', []):
            lon = e.get('lon') or e.get('center', {}).get('lon')
            lat = e.get('lat') or e.get('center', {}).get('lat')
            if lat and lon: pontos.append(Point(lon, lat))
        
        gdf_pontos = gpd.GeoDataFrame(geometry=pontos, crs="EPSG:4326")
    except:
        print("❌ Erro na API Overpass.")
        return

    # 3. LÓGICA VORONOI + CONVEX HULL (LIMITANDO O PERÍMETRO)
    print("📐 Gerando perímetro orgânico e malha preditiva...")
    lista_pontos = MultiPoint(pontos)
    
    # Define o limite da cidade (Invisível no HTML, mas limita os cálculos)
    limite_urbano = lista_pontos.convex_hull.buffer(0.015)
    
    # Gera Voronoi
    caixa_gigante = lista_pontos.envelope.buffer(0.1)
    regioes_voronoi = voronoi_diagram(lista_pontos, envelope=caixa_gigante)
    gdf_voronoi = gpd.GeoDataFrame(geometry=[p for p in regioes_voronoi.geoms], crs="EPSG:4326")
    
    # Corta a malha para o perímetro da cidade
    gdf_final = gpd.clip(gdf_voronoi, limite_urbano)

    # 4. INTEGRAÇÃO DE DADOS (CENSO -> VORONOI)
    # Cada zona de Voronoi herda os dados do IBGE que estão dentro dela
    gdf_final = gpd.sjoin(gdf_final, ibge_enriquecido[['v0001', 'geometry']], how="left", predicate="intersects")
    gdf_final = gdf_final.drop_duplicates(subset='geometry').reset_index(drop=True)

    # 5. CÁLCULO DE SCORES (APIs REAIS)
    print("☁️ Consultando APIs de Clima e calculando riscos...")
    
    # API de Chuva
    try:
        res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=-23.18&longitude=-50.64&daily=precipitation_probability_max&timezone=America%2FSao_Paulo").json()
        score_chuva = res['daily']['precipitation_probability_max'][0]
    except:
        score_chuva = 50

    # Cálculos Finais
    gdf_final['score_lixo'] = (gdf_final['v0001'] / gdf_final['v0001'].max() * 100).fillna(0)
    
    # Simulação de variáveis complementares para o motor multicritério
    gdf_final['score_declividade'] = np.random.randint(20, 90, len(gdf_final))
    gdf_final['score_reclamacoes'] = np.random.randint(10, 100, len(gdf_final))

    # A FÓRMULA MESTRA
    gdf_final['score_risco_final'] = (
        (gdf_final['score_reclamacoes'] * 0.35) + 
        (gdf_final['score_declividade'] * 0.25) + 
        (gdf_final['score_lixo'] * 0.20) + 
        (score_chuva * 0.20)
    ).round(2)

    def categorizar(s):
        if s > 80: return 'CRÍTICO'
        if s > 60: return 'ALTO'
        if s > 40: return 'MÉDIO'
        return 'BAIXO'

    gdf_final['nivel_urgencia'] = gdf_final['score_risco_final'].apply(categorizar)
    
    # Centroides para as marcações preventivas no Front-end
    centroides = gdf_final.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
    gdf_final['lat_alerta'] = centroides.y
    gdf_final['lng_alerta'] = centroides.x

    # 6. EXPORTAÇÃO
    # Salvamos apenas o que o HTML precisa para ser rápido
    colunas_finais = ['geometry', 'nivel_urgencia', 'score_risco_final', 'lat_alerta', 'lng_alerta']
    gdf_final[colunas_finais].to_file("mapa_preventivo.geojson", driver='GeoJSON')
    
    print(f"✨ SUCESSO! Malha de {len(gdf_final)} zonas gerada dentro do perímetro urbano.")

motor_final_ecoprioridade()