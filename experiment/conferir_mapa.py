import geopandas as gpd
import pandas as pd

def conferir_dados_do_mapa():
    print("🕵️ Analisando o Raio-X do GeoJSON final...")
    arquivo_geojson = "mapa_preventivo.geojson"
    
    try:
        # 1. Carregar o arquivo
        gdf = gpd.read_file(arquivo_geojson)
        
        # 2. Calcular coordenadas reais dos alertas (sem erro de CRS)
        centroides = gdf.to_crs(epsg=3857).geometry.centroid.to_crs(epsg=4326)
        gdf['lat'] = centroides.y.round(6)
        gdf['lng'] = centroides.x.round(6)
        
        # 3. Verificar quais colunas realmente existem para não dar erro de Index
        colunas_no_arquivo = gdf.columns.tolist()
        colunas_desejadas = ['score_risco_final', 'nivel_urgencia', 'score_reclamacoes', 'bairro_voronoi', 'lat', 'lng']
        
        # Filtra apenas as que existem
        colunas_exibir = [c for c in colunas_desejadas if c in colunas_no_arquivo]
        
        # 4. Ordenar pelos mais críticos
        ranking = gdf[colunas_exibir].sort_values(by='score_risco_final', ascending=False)
        
        print(f"\n📊 TOP 15 ZONAS CRÍTICAS NO MAPA:")
        print("=" * 90)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(ranking.head(15))
        print("=" * 90)
        
        # 5. Resumo para você comparar com o CSV
        if 'score_risco_final' in gdf.columns:
            print("\n📈 RESUMO ESTATÍSTICO (Check de Variedade):")
            print(f"- Score Máximo: {gdf['score_risco_final'].max()}")
            print(f"- Score Médio:  {gdf['score_risco_final'].mean():.2f}")
            print(f"- Score Mínimo: {gdf['score_risco_final'].min()}")
            
        if 'score_reclamacoes' not in colunas_no_arquivo:
            print("\n⚠️ ALERTA: A coluna 'score_reclamacoes' não foi exportada pelo motor_final.py!")
            print(f"Colunas encontradas no arquivo: {colunas_no_arquivo}")

    except Exception as e:
        print(f"🚨 Erro ao ler dados: {e}")

if __name__ == "__main__":
    conferir_dados_do_mapa()