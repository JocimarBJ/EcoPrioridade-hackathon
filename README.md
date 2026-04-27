Projeto desenvolvido por 3 dias durante a Competição de Programação:
## 🐝 Hackabee 6.0 - 2026- UTFPR 🐝
### Tema do Hackathon:
Dados e Tecnologias como Ferramentas para Impulsionar a Inovação na Gestão Pública  

### Tema do Projeto:
Plataforma Preditiva de Zeladoria Urbana


**Arquivos Principais**:
- `index.html`
- `motor_preditivo.py`
- `api_server.py`
<br>

## Modelo de Negócio:
A solução além de evitar desastres, a solução melhora a saúde pública, garante a mobilidade urbana e aumenta a percepção de segurança e zeladoria pela população, refletindo em aprovação política. 

**Product Discovery**:
- Mapa de Empatia
- Canvas da Proposta de Valor
- Business Canvas Model

**Cliente Principal**: Prefeituras de pequeno e medio porte (cidades com relevo desafiador e recursos limitados)  

**Usuário Final**: Gestores Municipais (Secretários de Obras, Procuradoria, Planejamento, Meio Ambiente, Serviços Urbanos)

**Beneficiário Indireto**: A população local, que sofre com enchentes e ruas esburacadas, com doenças espalhadas pelo lixo e água acumulada propícia para desenvolvimento de outras doenças.

**Que Problema Ajudamos a Resolver e quais ganhos entregamos?**: 
- De Reativo para Proativo: Antecipação de desastres urbanos (enchentes) através do cruzamento de alertas de chuvas intensas com heatmaps de risco e volume de lixo, prevendo antes que ocorra com utilizando IA para previsão (ou forecasting).
- Redução de Custos com Otimização de rotas de caminhões, economizando combustível e reduzindo a necessidade de horas extras para equipes de manutenção emergencial.
- Empoderamento Político e Orçamentário: Fornecimento de argumentos visuais em dados estatísticos para que o Secretário justifique pedidos de orçamento ao Prefeito.
- Alinhamento ODS: entrega de métricas claras para adequação às metas da Agenda 2030 (ODS 11 e 12), gerando reconhecimento por uma gestão inovadora e tecnológica.

**Como alcançamos nssos segmentos de Clientes?**:
- Vendas B2G: participação em processos licitatórios (ou enquadramento no Marco Legal das Startups para contratação de testes de Inovação pelo poder público)
- Eventos e Feiras: apresentações em congresoss de municípios (ex: Eventos da CNM) e feiras de Smart Cities.
- Demonstrações Diretas: Reuniões presenciais ou virtuais diretamente com as secretarias alvo, usando o município deles como exemplo no dashboard (prova de conceito rápida)

**Por quais valores nososs clientes estão dispostos a pagar?**  
- Assinatura SaaS: cobrança mensal ou anual pelo uso da plataforma (licenciamento de software)
- Taxa de setup/implantação: cobrança unica para configuração inicial, integração das APIs específicas da região e treinamento da equipe operacional reduzida da prefeitura.

## Desenvolvimento:

**Ingestão de Dados**:  
- Periodicidade da coleta de lixo pelos bairros (seletiva e normal)
- Densidade populacional do município
- Volume de resíduos do município
- Relatos da Ouvidoria do município
- Dados topográficos do município

**Parâmetros dos Cálculos**:  
*Cada bairro é formado pela junção de vários setores*
- Malha do município através de técnicas usando Modelos Matemáticos de Geometria Computacional e Geoprocessamento. 
    - Diagrama de Voronoi e Envoltória Convexa [Convex Hull]
- Periodicidade da coleta de lixo pelos bairros (seletiva e normal)
- Cálculo da Densidade populacional por setor
- Cálculo do Volume de resíduos por setor
- Reclamações da Ouvidoria filtradas por NLP
- Cálculo da Declinidade de cada bairro

**APIs Públicas Utilizadas:**  
*tais quais utilizadas para maior precisão dos cálculos e os fatores variáveis*
- Open-meteo, INMET, SIMEPAR (metereologia)
- IBGE e SIDRA IBGE
- Ouvidoria da Plataforma de Transparência de Cornélio Procópio (classificação ML)
- Elevation-API (Declinidade de cada bairro)
- OpenStreetMap (reconhecimento das localizações centrais)
- Overpass API (OSM) (buscar infraestrutura)
- Nominatim API (geocodificação, endereços -> coordenadas)

**Bibliotecas**:
- geopandas
- pandas
- fastAPI
- folium
- sklearn
- shapely
- numpy
- requests

## Execução:

Com o Docker instalado e aberto digite nesta sequencia:
- `docker compose build`
- `docker compose up -d`

SWAGGER: `http://localhost:8000/docs`  

API: `http://localhost:8000/api/mapa`  

HTML: `http://localhost:8000/static/index.html`  

## Licença
Confira a Licença do Projeto em [LICENSE](./LICENSE) e os [AUTORES](./AUTHORS.md).