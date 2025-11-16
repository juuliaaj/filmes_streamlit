import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Dashboard Netflix 🎬",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar dados
@st.cache_data
def load_data():
    df = pd.read_csv('data/movies.csv')
    
    # Processamento das datas - CORREÇÃO APLICADA
    # Primeiro remove espaços extras, depois converte
    df['date_added'] = df['date_added'].str.strip()  # Remove espaços no início e fim
    df['date_added'] = pd.to_datetime(df['date_added'], format='%B %d, %Y', errors='coerce')
    
    # Criar colunas derivadas
    df['year_added'] = df['date_added'].dt.year
    df['month_added'] = df['date_added'].dt.month_name()
    df['month_year_added'] = df['date_added'].dt.to_period('M')
    
    # Extrair primeiro país e primeiro gênero
    df['primary_country'] = df['country'].str.split(',').str[0].str.strip()
    df['primary_genre'] = df['listed_in'].str.split(',').str[0].str.strip()
    
    # Processar duração
    df['duration_num'] = df['duration'].str.extract('(\d+)').astype(float)
    df['duration_type'] = df['duration'].str.extract('(min|Season|Seasons)')
    
    return df

df = load_data()

# Sidebar com filtros
st.sidebar.title("Filtros")

# Filtro por tipo
type_filter = st.sidebar.multiselect(
    "Tipo de Conteúdo:",
    options=df['type'].unique(),
)

# Filtro por ano de lançamento
release_years = sorted(df['release_year'].dropna().unique())
year_range = st.sidebar.slider(
    "Ano de Lançamento:",
    min_value=int(min(release_years)),
    max_value=int(max(release_years)),
    value=(int(min(release_years)), int(max(release_years)))
)

# Filtro por classificação
available_ratings = sorted(df['rating'].dropna().unique())
ratings = st.sidebar.multiselect(
    "Classificação Indicativa:",
    options=available_ratings,
)

# Filtro por país
available_countries = sorted(df['primary_country'].dropna().unique())
countries = st.sidebar.multiselect(
    "País:",
    options=available_countries[:50],  # Limita para performance
)

# Filtro por gênero
available_genres = sorted(df['primary_genre'].dropna().unique())
genres = st.sidebar.multiselect(
    "Gênero:",
    options=available_genres,
)

# Aplicar filtros
filtered_df = df.copy()

if type_filter:
    filtered_df = filtered_df[filtered_df['type'].isin(type_filter)]

filtered_df = filtered_df[
    (filtered_df['release_year'] >= year_range[0]) & 
    (filtered_df['release_year'] <= year_range[1])
]

if ratings:
    filtered_df = filtered_df[filtered_df['rating'].isin(ratings)]

if countries:
    filtered_df = filtered_df[filtered_df['primary_country'].isin(countries)]

if genres:
    filtered_df = filtered_df[filtered_df['primary_genre'].isin(genres)]

# Layout principal com abas
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral", 
    "🎭 Análise de Conteúdo", 
    "🌍 Distribuição Global", 
    "🔍 Explorar Catálogo"
])

with tab1:
    st.header("📊 Visão Geral do Catálogo Netflix")
    
    # Métricas iniciais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_content = len(filtered_df)
        st.metric("Total de Conteúdos", f"{total_content:,}")
    with col2:
        movies_count = len(filtered_df[filtered_df['type'] == 'Movie'])
        st.metric("Filmes", f"{movies_count:,}")
    with col3:
        tv_count = len(filtered_df[filtered_df['type'] == 'TV Show'])
        st.metric("Séries", f"{tv_count:,}")
    with col4:
        latest_year = filtered_df['release_year'].max()
        st.metric("Ano Mais Recente", int(latest_year) if not pd.isna(latest_year) else "N/A")
    
    # Gráfico 1: Distribuição por Tipo
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição por Tipo")
        type_counts = filtered_df['type'].value_counts()
        fig1 = px.pie(values=type_counts.values, names=type_counts.index,
                     title="Proporção de Filmes vs Séries")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Conteúdo Adicionado por Ano")
        # Filtrar apenas anos com dados válidos
        yearly_data = filtered_df[filtered_df['year_added'].notna()]
        yearly_additions = yearly_data['year_added'].value_counts().sort_index()
        
        fig2 = px.line(x=yearly_additions.index, y=yearly_additions.values,
                      title='Evolução de Conteúdos Adicionados',
                      labels={'x': 'Ano', 'y': 'Número de Conteúdos'})
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.header("🎭 Análise de Conteúdo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Gêneros")
        genre_counts = filtered_df['primary_genre'].value_counts().head(10)
        fig3 = px.bar(x=genre_counts.values, y=genre_counts.index, orientation='h',
                     title="Top 10 Gêneros no Catálogo",
                     labels={'x': 'Número de Conteúdos', 'y': 'Gênero'})
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        st.subheader("Classificação Indicativa")
        rating_counts = filtered_df['rating'].value_counts().head(8)
        fig4 = px.pie(values=rating_counts.values, names=rating_counts.index,
                     title="Distribuição por Classificação")
        st.plotly_chart(fig4, use_container_width=True)
    
    # Gráfico interativo 1: Duração de Filmes
    st.subheader("Análise de Duração")
    
    content_type = st.radio(
        "Selecione o tipo:",
        ['Movie', 'TV Show'],
        horizontal=True
    )
    
    if content_type == 'Movie':
        movies_df = filtered_df[filtered_df['type'] == 'Movie'].dropna(subset=['duration_num'])
        if not movies_df.empty:
            fig5 = px.histogram(movies_df, x='duration_num', 
                               title='Distribuição de Duração de Filmes (minutos)',
                               labels={'duration_num': 'Duração (minutos)'},
                               nbins=20)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Nenhum filme encontrado com os filtros atuais.")
    else:
        tv_df = filtered_df[filtered_df['type'] == 'TV Show']
        if not tv_df.empty:
            season_counts = tv_df['duration'].value_counts().head(10)
            fig5 = px.bar(x=season_counts.index, y=season_counts.values,
                         title='Séries por Número de Temporadas',
                         labels={'x': 'Temporadas', 'y': 'Número de Séries'})
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Nenhuma série encontrada com os filtros atuais.")

with tab3:
    st.header("🌍 Distribuição Global")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Países Produtores")
        country_counts = filtered_df['primary_country'].value_counts().head(15)
        fig6 = px.bar(x=country_counts.values, y=country_counts.index, orientation='h',
                     title="Top 15 Países com Mais Conteúdos",
                     labels={'x': 'Número de Conteúdos', 'y': 'País'})
        st.plotly_chart(fig6, use_container_width=True)
    
    with col2:
        st.subheader("Distribuição por País e Tipo")
        country_type = filtered_df.groupby(['primary_country', 'type']).size().reset_index(name='count')
        top_countries = filtered_df['primary_country'].value_counts().head(10).index
        country_type_top = country_type[country_type['primary_country'].isin(top_countries)]
        
        if not country_type_top.empty:
            fig7 = px.bar(country_type_top, x='primary_country', y='count', color='type',
                         title='Conteúdos por País e Tipo (Top 10)',
                         labels={'primary_country': 'País', 'count': 'Número de Conteúdos'})
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("Nenhum dado disponível para os filtros atuais.")
    
    # Gráfico interativo 2: Timeline de lançamentos
    st.subheader("Timeline de Lançamentos")
    
    group_types = {
        'release_year': 'Ano de Lançamento',
        'year_added': 'Ano de Adição'
    }

    timeline_type = st.selectbox(
        "Agrupar por:",
        group_types.keys(),
        format_func=lambda x: group_types[x]
    )
    
    timeline_data = filtered_df.groupby([timeline_type, 'type']).size().reset_index(name='count')
    
    if not timeline_data.empty:
        fig8 = px.line(timeline_data, x=timeline_type, y='count', color='type',
                      title=f'Evolução de Conteúdos por {("Ano de Lançamento" if timeline_type == "release_year" else "Ano de Adição")}',
                      labels={timeline_type: 'Ano', 'count': 'Número de Conteúdos'})
        st.plotly_chart(fig8, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para a timeline com os filtros atuais.")

with tab4:
    st.header("🔍 Explorar Catálogo")
    
    # Busca e filtros avançados
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Filtros Avançados")
        
        search_title = st.text_input("Buscar por título:")
        search_director = st.text_input("Buscar por diretor:")
        search_cast = st.text_input("Buscar por ator:")
        
        sort_types = {
            'title': 'Título',
            'release_year': 'Ano de Lançamento',
            'date_added': 'Data de Adição',
            'rating': 'Classificação'
        }

        sort_by = st.selectbox(
            "Ordenar por:",
            list(sort_types.keys()),
            format_func=lambda x: sort_types[x]
        )
        
        sort_order = st.radio(
            "Ordem:",
            ['Crescente', 'Decrescente'],
            horizontal=True
        )
    
    with col2:
        st.subheader("Resultados da Busca")
        
        # Aplicar filtros de busca
        result_df = filtered_df.copy()
        
        if search_title:
            result_df = result_df[result_df['title'].str.contains(search_title, na=False, case=False)]
        
        if search_director:
            result_df = result_df[result_df['director'].str.contains(search_director, na=False, case=False)]
        
        if search_cast:
            result_df = result_df[result_df['cast'].str.contains(search_cast, na=False, case=False)]
        
        # Ordenar resultados
        ascending = True if sort_order == 'Crescente' else False
        result_df = result_df.sort_values(sort_by, ascending=ascending)
        
        # Mostrar resultados
        st.write(f"**{len(result_df)} resultados encontrados**")
        
        for idx, row in result_df.head(30).iterrows():
            with st.expander(f"🎬 {row['title']} ({row['release_year']}) - {row['type']}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Tipo:** {row['type']}")
                    st.write(f"**Ano de Lançamento:** {row['release_year']}")
                    st.write(f"**Classificação:** {row['rating']}")
                    if pd.notna(row['date_added']):
                        st.write(f"**Adicionado em:** {row['date_added'].strftime('%B %d, %Y')}")
                with col_b:
                    st.write(f"**Duração:** {row['duration']}")
                    st.write(f"**Gênero:** {row['primary_genre']}")
                    st.write(f"**País:** {row['primary_country']}")
                st.write(f"**Descrição:** {row['description']}")
                
                if pd.notna(row['director']):
                    st.write(f"**Diretor:** {row['director']}")
                if pd.notna(row['cast']):
                    st.write(f"**Elenco:** {row['cast']}")

# Documentação no sidebar
st.sidebar.markdown("---")
st.sidebar.header("📖 Como Usar Este Dashboard")

st.sidebar.markdown("""
**🎯 Objetivo:**
Explorar e analisar o catálogo completo da Netflix, identificando padrões e tendências.

**🧭 Navegação:**
- **Visão Geral**: Métricas principais e distribuição básica
- **Análise de Conteúdo**: Gêneros, classificações e durações
- **Distribuição Global**: Análise geográfica e temporal
- **Explorar Catálogo**: Busca detalhada e filtros avançados

**🎛️ Filtros:**
Todos os filtros na sidebar afetam simultaneamente todos os gráficos e visualizações.
""")

# Informações adicionais
st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Dica:** Use a aba 'Explorar Catálogo' para buscar "
    "conteúdos específicos por diretor, ator ou outros critérios."
)