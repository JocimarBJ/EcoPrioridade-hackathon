import osmnx as ox
import geopandas as gpd
import pandas as pd
from geopy.geocoders import Nominatim
import time

# ==================================================
# 1. BAIRROS DE CORNÉLIO PROCÓPIO
# ==================================================
place = "Cornélio Procópio, Paraná, Brazil"

tags = {
    "place": [
        "suburb",
        "neighbourhood"
    ]
}


print("Buscando bairros no OpenStreetMap...")

gdf = ox.features_from_place(place,tags)

gdf = gdf[gdf["admin_level"].isin(["9", "10"])]
# ==================================================
# 2. RESET INDEX
# ==================================================
gdf = gdf.reset_index()

# ==================================================
# 3. COLUNAS IMPORTANTESA
# ==================================================
cols = [
    "name",
    "geometry"
]

gdf = gdf[cols]

# ==================================================
# 4. LIMPEZA
# ==================================================
gdf = gdf.dropna(subset=["name"])

gdf["name"] = (
    gdf["name"]
    .astype(str)
    .str.strip()
)

gdf = gdf.drop_duplicates(subset=["name"])

# ==================================================
# 5. GEOCODER
# ==================================================
geolocator = Nominatim(
    user_agent="ecoprioridade"
)

# ==================================================
# 6. BUSCAR CEP/LAT/LON
# ==================================================
ceps = []
lats = []
lons = []
enderecos = []

print("\nBuscando coordenadas e CEPs...\n")

for bairro in gdf["name"]:

    query = f"{bairro}, Cornélio Procópio, Paraná, Brasil"

    try:

        location = geolocator.geocode(query)

        if location:

            endereco = location.address

            # tenta extrair CEP do texto
            cep = None

            partes = endereco.split(",")

            for p in partes:

                p = p.strip()

                if "-" in p and any(c.isdigit() for c in p):
                    cep = p

            ceps.append(cep)

            lats.append(location.latitude)
            lons.append(location.longitude)

            enderecos.append(endereco)

            print(f"✓ {bairro}")

        else:

            ceps.append(None)
            lats.append(None)
            lons.append(None)
            enderecos.append(None)

            print(f"✗ {bairro}")

    except Exception as e:

        ceps.append(None)
        lats.append(None)
        lons.append(None)
        enderecos.append(None)

        print(f"Erro em {bairro}: {e}")

    time.sleep(1)

# ==================================================
# 7. NOVAS COLUNAS
# ==================================================
gdf["cep"] = ceps
gdf["latitude"] = lats
gdf["longitude"] = lons
gdf["endereco"] = enderecos

# ==================================================
# 8. RESULTADO
# ==================================================
print("\n=== BAIRROS ===\n")

for _, r in gdf.iterrows():

    print(f"Bairro: {r['name']}")
    print(f"CEP: {r['cep']}")
    print(f"Latitude: {r['latitude']}")
    print(f"Longitude: {r['longitude']}")
    print("-" * 40)

# ==================================================
# 9. SALVAR GEOJSON
# ==================================================
gdf.to_file(
    "bairros_cornelio3.geojson",
    driver="GeoJSON"
)

print("\nGeoJSON salvo!")