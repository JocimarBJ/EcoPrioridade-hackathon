import requests
import geopandas as gpd
from shapely.geometry import Point, MultiPoint
from shapely.ops import voronoi_diagram
import random
import warnings

warnings.filterwarnings('ignore')

def gerar_malha_urbana(nome_cidade):
    print(f"\n🌍 1. A extrair infraestruturas de {nome_cidade} via Overpass API...")
    headers = {'User-Agent': 'EcoPrioridade-Hackathon-Bot/1.0'}
    
    url_overpass = "https://overpass-api.de/api/interpreter"
    
    query = f"""
    [out:json][timeout:50];
    area[name="{nome_cidade}"]->.searchArea;
    (
      nwr["amenity"](area.searchArea);
      nwr["leisure"](area.searchArea);
      nwr["highway"="bus_stop"](area.searchArea);
      nwr["amenity"="waste_basket"](area.searchArea);
    );
    out center;
    """
    
    resposta_over = requests.post(url_overpass, data={'data': query}, headers=headers)
    
    if resposta_over.status_code != 200:
        print(f"❌ Erro Overpass: {resposta_over.text}")
        return

    dados_json = resposta_over.json()
    
    pontos_extraidos = []
    for elemento in dados_json.get('elements', []):
        if 'lat' in elemento and 'lon' in elemento:
            pontos_extraidos.append(Point(elemento['lon'], elemento['lat']))
        elif 'center' in elemento:
            pontos_extraidos.append(Point(elemento['center']['lon'], elemento['center']['lat']))

    if not pontos_extraidos:
         print(f"❌ Nenhuma infraestrutura encontrada.")
         return

    print(f"✅ Encontradas {len(pontos_extraidos)} infraestruturas.")
    
    # 2. A MÁGICA DO PERÍMETRO URBANO
    lista_pontos = MultiPoint(pontos_extraidos)
    
    # Cria uma "capa" orgânica ao redor de todos os pontos (que estão na área urbana)
    # buffer(0.015) dá uma margem de "respiro" para não cortar as bordas dos bairros periféricos
    limite_urbano = lista_pontos.convex_hull.buffer(0.015)
    gdf_limite_urbano = gpd.GeoDataFrame(geometry=[limite_urbano], crs="EPSG:4326")
    
    # 3. Gerar a Malha de Voronoi Gigante
    caixa_gigante = lista_pontos.envelope.buffer(0.1) 
    regioes_voronoi = voronoi_diagram(lista_pontos, envelope=caixa_gigante)
    gdf_voronoi_gigante = gpd.GeoDataFrame(geometry=[poly for poly in regioes_voronoi.geoms], crs="EPSG:4326")
    
    print(f"✂️ 3. A recortar a malha apenas para a Área Urbana...")
    # 4. Cortar o quadradão usando a nossa "bolha" urbana!
    gdf_voronoi_final = gpd.clip(gdf_voronoi_gigante, gdf_limite_urbano)
    
    # 5. Aplicar Scores de Risco
    scores = []
    niveis = []
    for _ in range(len(gdf_voronoi_final)):
        score = random.randint(10, 100)
        scores.append(score)
        if score >= 80: niveis.append('CRÍTICO')
        elif score >= 60: niveis.append('ALTO')
        elif score >= 40: niveis.append('MÉDIO')
        else: niveis.append('BAIXO')

    gdf_voronoi_final['score_risco'] = scores
    gdf_voronoi_final['nivel_risco'] = niveis
    
    # 6. Salvar o arquivo
    nome_ficheiro = "malha_voronoi_nivel3.geojson"
    gdf_voronoi_final.to_file(nome_ficheiro, driver='GeoJSON')
    print(f"🚀 Sucesso! O mapa urbano foi guardado como: {nome_ficheiro}\n")

# Rodar para Cornélio Procópio
gerar_malha_urbana("Cornélio Procópio")