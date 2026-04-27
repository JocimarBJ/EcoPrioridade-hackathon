import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, MultiPoint
from shapely.ops import voronoi_diagram
import numpy as np
import warnings
import folium
from folium.plugins import HeatMap
from sklearn.ensemble import RandomForestRegressor

warnings.filterwarnings('ignore')

def gerar_mapas_folium(gdf_final):
    print("🗺️ A gerar os 4 mapas de visualização (Folium)...")
    centro_mapa = [-23.18, -50.64]
    
    # 1. Mapa de Risco (Score Preditivo)
    m_risco = folium.Map(location=centro_mapa, zoom_start=14, tiles='cartodbpositron')
    HeatMap([[r['lat_alerta'], r['lng_alerta'], r['score_risco_final']] for i, r in gdf_final.iterrows()], radius=25, blur=15).add_to(m_risco)
    m_risco.save("mapa_risco.html")

    # 2. Mapa de Risco por Região
    m_regiao = folium.Map(location=centro_mapa, zoom_start=14, tiles='cartodbpositron')
    zonas_agg = gdf_final.groupby('zona')['score_risco_final'].mean().to_dict()
    HeatMap([[r['lat_alerta'], r['lng_alerta'], zonas_agg[r.get('zona', 'Centro')]] for i, r in gdf_final.iterrows()], radius=45, blur=25).add_to(m_regiao)
    m_regiao.save("mapa_regiao.html")

    # 3. Mapa de Volume de Resíduos (ODS 12)
    m_lixo = folium.Map(location=centro_mapa, zoom_start=14, tiles='cartodbpositron')
    HeatMap([[r['lat_alerta'], r['lng_alerta'], r['v0001']] for i, r in gdf_final.iterrows()], radius=20, blur=15, gradient={0.4: 'cyan', 0.8: 'blue', 1.0: 'purple'}).add_to(m_lixo)
    m_lixo.save("mapa_residuos.html")

    # 4. Mapa de Densidade Populacional
    m_pop = folium.Map(location=centro_mapa, zoom_start=14, tiles='cartodbpositron')
    HeatMap([[r['lat_alerta'], r['lng_alerta'], r['v0001']] for i, r in gdf_final.iterrows()], radius=20, blur=15, gradient={0.4: 'yellow', 1.0: 'orange'}).add_to(m_pop)
    m_pop.save("mapa_densidade.html")

def motor_final_ecoprioridade():
    print("🚀 --- A INICIAR MOTOR ML: VORONOI + MACHINE LEARNING ---")
    headers = {'User-Agent': 'EcoPrioridade-Hackathon-Bot/1.0'}

    # 1. CARREGAR DADOS DO IBGE
    print("📂 A processar dados do Censo 2022...")
    try:
        gdf_ibge = gpd.read_file('./setores_censitarios/PR_setores_CD2022.shp')
        gdf_cornelio = gdf_ibge[gdf_ibge['CD_MUN'] == '4106407'].copy().to_crs("EPSG:4326")
        df_csv = pd.read_csv('./setores_censitarios/agregados_preliminares_por_setores_censitarios_BR.csv', sep=';', usecols=['CD_SETOR', 'v0001'], dtype={'CD_SETOR': str})
        gdf_cornelio['CD_SETOR'] = gdf_cornelio['CD_SETOR'].astype(str).str.strip()
        df_csv['CD_SETOR'] = df_csv['CD_SETOR'].astype(str).str[:15]
        ibge_enriquecido = gdf_cornelio.merge(df_csv, on='CD_SETOR', how='left')
        ibge_enriquecido['v0001'] = pd.to_numeric(ibge_enriquecido['v0001'], errors='coerce').fillna(0)
    except Exception as e:
        print(f"❌ Erro ao carregar bases locais: {e}")
        return

    # 2. EXTRAIR INFRAESTRUTURA (OVERPASS)
    print("📡 A procurar sementes urbanas via Overpass API...")
    url_overpass = "https://overpass-api.de/api/interpreter"
    query = '[out:json][timeout:50];area[name="Cornélio Procópio"]->.a;(nwr["amenity"](area.a);nwr["leisure"](area.a);nwr["highway"="bus_stop"](area.a););out center;'
    pontos = []
    try:
        resp = requests.post(url_overpass, data={'data': query}, headers=headers, timeout=30)
        if resp.status_code == 200:
            for e in resp.json().get('elements', []):
                lon = e.get('lon') or e.get('center', {}).get('lon')
                lat = e.get('lat') or e.get('center', {}).get('lat')
                if lat and lon: pontos.append(Point(lon, lat))
    except: pass
    
    if len(pontos) < 10: # Fallback de segurança
        lats, lngs = np.linspace(-23.21, -23.15, 10), np.linspace(-50.68, -50.60, 10)
        pontos = [Point(lng, lat) for lat in lats for lng in lngs]

    # 3. LÓGICA VORONOI + CONVEX HULL
    print("📐 A gerar perímetro orgânico e malha preditiva...")
    lista_pontos = MultiPoint(pontos)
    limite_urbano = lista_pontos.convex_hull.buffer(0.015)
    caixa_gigante = lista_pontos.envelope.buffer(0.1)
    regioes_voronoi = voronoi_diagram(lista_pontos, envelope=caixa_gigante)
    gdf_voronoi = gpd.GeoDataFrame(geometry=[p for p in regioes_voronoi.geoms], crs="EPSG:4326")
    gdf_final = gpd.clip(gdf_voronoi, limite_urbano)

    # 4. INTEGRAÇÃO DE DADOS
    gdf_final = gpd.sjoin(gdf_final, ibge_enriquecido[['CD_SETOR', 'v0001', 'geometry']], how="left", predicate="intersects")
    gdf_final = gdf_final.drop_duplicates(subset='geometry').reset_index(drop=True)
    gdf_final['v0001'] = gdf_final['v0001'].fillna(0)

    # Atribuição de Bairros (Mock para o Dashboard)
    bairros_reais = ['Jd. Panorama', 'Centro', 'Boa Vista', 'Cohab', 'São Domingos', 'Jd. Primavera', 'São Paulo']
    zonas = ['Norte', 'Sul', 'Leste', 'Oeste', 'Centro']
    np.random.seed(42)
    gdf_final['nome_bairro'] = np.random.choice(bairros_reais, size=len(gdf_final))
    gdf_final['zona'] = np.random.choice(zonas, size=len(gdf_final))

    # 5. MACHINE LEARNING (A PREVISÃO)
    print("🧠 A treinar o modelo de Machine Learning...")
    try:
        res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=-23.18&longitude=-50.64&daily=precipitation_probability_max&timezone=America%2FSao_Paulo").json()
        score_chuva = res['daily']['precipitation_probability_max'][0]
    except: score_chuva = 50

    gdf_final['declividade'] = np.random.randint(5, 40, len(gdf_final))
    
    # Dados históricos fictícios para treinar a IA
    X_train = pd.DataFrame({'pop': np.random.randint(50, 1000, 500), 'declividade': np.random.randint(5, 40, 500)})
    y_train = np.clip((X_train['pop'] * 0.05) + (X_train['declividade'] * 1.5) + (score_chuva * 0.2), 0, 100)
    
    modelo = RandomForestRegressor(n_estimators=50, random_state=42)
    modelo.fit(X_train, y_train)

    # Previsão sobre os dados atuais da cidade
    X_real = gdf_final[['v0001', 'declividade']].rename(columns={'v0001': 'pop'})
    gdf_final['score_risco_final'] = np.clip(modelo.predict(X_real), 0, 100).round(2)

    def categorizar(s):
        if s > 75: return 'CRÍTICO'
        if s > 50: return 'ALTO'
        if s > 25: return 'MÉDIO'
        return 'BAIXO'
    gdf_final['nivel_urgencia'] = gdf_final['score_risco_final'].apply(categorizar)
    
    centroides = gdf_final.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
    gdf_final['lat_alerta'], gdf_final['lng_alerta'] = centroides.y, centroides.x

    # 6. EXPORTAÇÃO
    colunas_finais = ['geometry', 'CD_SETOR', 'nome_bairro', 'zona', 'nivel_urgencia', 'score_risco_final', 'lat_alerta', 'lng_alerta', 'v0001']
    gdf_final[colunas_finais].to_file("mapa_preventivo.geojson", driver='GeoJSON')
    
    gerar_mapas_folium(gdf_final)
    print(f"✨ SUCESSO! Malha inteligente de {len(gdf_final)} zonas gerada.")

if __name__ == "__main__":
    motor_final_ecoprioridade()