import pandas as pd
import geopandas as gpd

print("🚀 Iniciando Motor de Densidade por Setor...")

caminho_shp = './setores_censitarios/PR_setores_CD2022.shp'
caminho_csv = './setores_censitarios/agregados_preliminares_por_setores_censitarios_BR.csv'

# 1. Carregar Dados
gdf_setores = gpd.read_file(caminho_shp)
gdf_cornelio = gdf_setores[gdf_setores['CD_MUN'] == '4106407'].copy()

df_brasil = pd.read_csv(caminho_csv, 
                        sep=';', 
                        usecols=['CD_SETOR', 'v0001'],
                        dtype={'CD_SETOR': str})

# 2. Limpeza (O truque de tirar o 'P' e os espaços)
gdf_cornelio['CD_SETOR'] = gdf_cornelio['CD_SETOR'].astype(str).str.strip()
df_brasil['CD_SETOR'] = df_brasil['CD_SETOR'].astype(str).str[:15] 

# 3. União
gdf_completo = gdf_cornelio.merge(df_brasil, on='CD_SETOR', how='left')

# Garantir que são números
gdf_completo['v0001'] = pd.to_numeric(gdf_completo['v0001'], errors='coerce').fillna(0)
gdf_completo['AREA_KM2'] = pd.to_numeric(gdf_completo['AREA_KM2'], errors='coerce').fillna(0.001)

# 4. CÁLCULO DIRETO POR SETOR (Sem agrupar por bairro)
gdf_completo['densidade'] = gdf_completo['v0001'] / gdf_completo['AREA_KM2']

# 4. CÁLCULO DE VOLUME DE LIXO (Alinhado com o ODS 12 da sua proposta)
TAXA_LIXO_PER_CAPITA = 1.04 # Média nacional em KG/dia

# Calcula o volume total gerado no setor
gdf_completo['volume_lixo_kg_dia'] = gdf_completo['v0001'] * TAXA_LIXO_PER_CAPITA

# Calcula a "Pressão" (KG de lixo por Km2)
gdf_completo['pressao_lixo'] = gdf_completo['volume_lixo_kg_dia'] / gdf_completo['AREA_KM2']

# 5. Gerar o Score Lixo (Normalizado de 0 a 100)
max_pressao = gdf_completo['pressao_lixo'].max()
if max_pressao > 0:
    gdf_completo['score_lixo'] = (gdf_completo['pressao_lixo'] / max_pressao) * 100
    gdf_completo['score_lixo'] = gdf_completo['score_lixo'].round(2)
else:
    gdf_completo['score_lixo'] = 0

# Vamos mostrar o ID do setor e o Score gerado
resultado_final = gdf_completo[['CD_SETOR', 'v0001', 'AREA_KM2', 'densidade', 'score_lixo']]
resultado_final = resultado_final.sort_values(by='score_lixo', ascending=False)

print("\n🏆 RESULTADO FINAL (TOP 10 SETORES MAIS DENSOS):")
print(resultado_final.head(10).to_string(index=False))