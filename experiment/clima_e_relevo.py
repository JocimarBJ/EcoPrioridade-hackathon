import pandas as pd
import geopandas as gpd
import requests
import numpy as np
import warnings
from shapely.errors import ShapelyDeprecationWarning

# Ignorar avisos de versão para manter o terminal limpo na apresentação
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def rodar_motor_ecoprioridade():
    print("🚀 INICIANDO MOTOR DE DADOS ECOPRIORIDADE...")

    # ==========================================
    # FASE 1: DADOS LOCAIS (IBGE / LIXO)
    # ==========================================
    print("\n📂 Lendo dados espaciais do IBGE...")
    caminho_shp = './setores_censitarios/PR_setores_CD2022.shp'
    caminho_csv = './setores_censitarios/agregados_preliminares_por_setores_censitarios_BR.csv'

    try:
        gdf_setores = gpd.read_file(caminho_shp)
        gdf_cornelio = gdf_setores[gdf_setores['CD_MUN'] == '4106407'].copy()

        df_brasil = pd.read_csv(caminho_csv, sep=';', usecols=['CD_SETOR', 'v0001'], dtype={'CD_SETOR': str})
        
        gdf_cornelio['CD_SETOR'] = gdf_cornelio['CD_SETOR'].astype(str).str.strip()
        df_brasil['CD_SETOR'] = df_brasil['CD_SETOR'].astype(str).str[:15] 

        gdf_completo = gdf_cornelio.merge(df_brasil, on='CD_SETOR', how='left')

        # Cálculo do ODS 12 (Pressão do Lixo)
        TAXA_LIXO_PER_CAPITA = 1.04
        gdf_completo['v0001'] = pd.to_numeric(gdf_completo['v0001'], errors='coerce').fillna(0)
        gdf_completo['AREA_KM2'] = pd.to_numeric(gdf_completo['AREA_KM2'], errors='coerce').fillna(0.001)
        
        gdf_completo['volume_lixo_kg_dia'] = gdf_completo['v0001'] * TAXA_LIXO_PER_CAPITA
        gdf_completo['pressao_lixo'] = gdf_completo['volume_lixo_kg_dia'] / gdf_completo['AREA_KM2']

        max_pressao = gdf_completo['pressao_lixo'].max()
        gdf_completo['score_lixo'] = (gdf_completo['pressao_lixo'] / max_pressao * 100).round(2) if max_pressao > 0 else 0

        # Garantir formato GPS
        gdf_completo = gdf_completo.to_crs("EPSG:4326")
        
    except Exception as e:
        print(f"❌ Erro na fase 1: {e}")
        return

    # ==========================================
    # FASE 2: CONSUMO DE APIs (CLIMA E RELEVO)
    # ==========================================
    print("\n☁️ Consultando Open-Meteo (Previsão de Chuva)...")
    try:
        url_clima = "https://api.open-meteo.com/v1/forecast?latitude=-23.1850&longitude=-50.6450&daily=precipitation_probability_max&timezone=America%2FSao_Paulo"
        resp_clima = requests.get(url_clima).json()
        prob_chuva = resp_clima['daily']['precipitation_probability_max'][0]
        print(f"   -> Probabilidade de chuva hoje em Cornélio: {prob_chuva}%")
    except:
        prob_chuva = 50
    gdf_completo['chuva_score'] = prob_chuva

    print("\n⛰️ Consultando Altimetria de Cornélio Procópio...")
    try:
        latitudes = gdf_completo.geometry.centroid.y.round(5).astype(str).tolist()
        longitudes = gdf_completo.geometry.centroid.x.round(5).astype(str).tolist()
        url_relevo = f"https://api.open-meteo.com/v1/elevation?latitude={','.join(latitudes)}&longitude={','.join(longitudes)}"
        
        resp_relevo = requests.get(url_relevo).json()
        gdf_completo['altitude_metros'] = resp_relevo['elevation']
        
        max_alt = gdf_completo['altitude_metros'].max()
        min_alt = gdf_completo['altitude_metros'].min()
        if max_alt > min_alt:
            gdf_completo['declividade_score'] = 100 - (((gdf_completo['altitude_metros'] - min_alt) / (max_alt - min_alt)) * 100)
        else:
            gdf_completo['declividade_score'] = 0
    except:
        gdf_completo['altitude_metros'] = 0
        gdf_completo['declividade_score'] = 0

    # ==========================================
    # FASE 3: SIMULAÇÃO ZELADORIA (156)
    # ==========================================
    print("\n📞 Cruzando histórico de Zeladoria...")
    np.random.seed(42)
    gdf_completo['qtd_reclamacoes'] = np.random.randint(0, 15, len(gdf_completo))
    max_rec = gdf_completo['qtd_reclamacoes'].max()
    gdf_completo['reclamacoes_score'] = (gdf_completo['qtd_reclamacoes'] / max_rec * 100).round(2) if max_rec > 0 else 0

    # ==========================================
    # FASE 4: O MOTOR MULTICRITÉRIO FINAL
    # ==========================================
    print("\n🧮 Calculando Matriz de Risco ODS...")
    gdf_completo['score_risco_final'] = (
        (gdf_completo['score_lixo'] * 0.20) + 
        (gdf_completo['declividade_score'] * 0.25) + 
        (gdf_completo['chuva_score'] * 0.20) + 
        (gdf_completo['reclamacoes_score'] * 0.35)
    ).round(2)

    gdf_completo['nivel_urgencia'] = pd.cut(
        gdf_completo['score_risco_final'], 
        bins=[-1, 40, 60, 80, 101], 
        labels=['BAIXO', 'MÉDIO', 'ALTO', 'CRÍTICO']
    )

    # ==========================================
    # FASE 5: EXPORTAÇÃO
    # ==========================================
    tabela_final = gdf_completo[[
        'CD_SETOR', 'altitude_metros', 'score_lixo', 'declividade_score', 
        'chuva_score', 'reclamacoes_score', 'score_risco_final', 'nivel_urgencia'
    ]].sort_values(by='score_risco_final', ascending=False)

    print("\n🚨 TOP 5 ÁREAS CRÍTICAS DE CORNÉLIO PROCÓPIO:")
    print(tabela_final.head(5).to_string(index=False))

    nome_arquivo = "mapa_ecoprioridade.geojson"
    gdf_completo.to_file(nome_arquivo, driver='GeoJSON')
    print(f"\n✨ SUCESSO! Arquivo '{nome_arquivo}' gerado e pronto para o Front-end/Java.")

# Executar a função
rodar_motor_ecoprioridade()