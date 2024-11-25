import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout = 'wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['','mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhoes'

url = 'https://labdados.com/produtos'
st.title('DASHBOARD DE VENDAS :shopping_trolley:')

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao =st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''
    
todos_anos = st.sidebar.checkbox('Dados de todo o periodo', value = True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(), 'ano': ano}
response = requests.get(url, params= query_string ,verify=False)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas

receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

## Tabelas de quantidade de vendas

quantidade_vendas_estado = dados.groupby('Local da compra')[['Local da compra']].count()
quantidade_vendas_estado = quantidade_vendas_estado.rename(columns={'Local da compra': 'Quantidade'})
quantidade_vendas_estado = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    quantidade_vendas_estado,
    left_on='Local da compra',
    right_index=True
).sort_values('Quantidade', ascending=False)

quantidade_vendas_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].count().reset_index()
quantidade_vendas_mensal = quantidade_vendas_mensal.rename(columns={'Preço': 'Quantidade'})
quantidade_vendas_mensal['Ano'] = quantidade_vendas_mensal['Data da Compra'].dt.year
quantidade_vendas_mensal['Mês'] = quantidade_vendas_mensal['Data da Compra'].dt.month_name(locale='pt_BR')

top_5_estados_vendas = quantidade_vendas_estado.head(5)

quantidade_vendas_categoria = dados.groupby('Categoria do Produto').size().reset_index(name='Quantidade')

## Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

# Gráfico de barras quantidades de vendas por categoria

fig_quantidade_categoria = px.bar(
    quantidade_vendas_categoria,
    x='Categoria do Produto',
    y='Quantidade',
    text_auto=True,
    title='Quantidade de Vendas por Categoria',
    labels={'Categoria do Produto': 'Categoria', 'Quantidade': 'Número de Vendas'},
    template='seaborn'
)

# Gráfico de barras Top 5 estado com maiores quantidades de vendas

fig_top_5_estados = px.bar(
    top_5_estados_vendas,
    x='Local da compra',  
    y='Quantidade',  
    title='Top 5 Estados com Maior Quantidade de Vendas',
    labels={'Local da compra': 'Estado', 'Quantidade de Vendas': 'Número de Vendas'},
    text_auto=True,
    template='seaborn'
)

# Gráfico no mapa para quantidade de vendas
fig_mapa_quantidade = px.scatter_geo(
    quantidade_vendas_estado,
    lat='lat',
    lon='lon',
    scope='south america',
    size='Quantidade',
    template='seaborn',
    hover_name='Local da compra',
    hover_data={'lat': False, 'lon': False, 'Quantidade': True},
    title="Quantidade de Vendas por Estado"
)

# Gráfico de linhas para quantidade de vendas

fig_quantidade_mensal = px.line(
    quantidade_vendas_mensal,
    x='Mês',
    y='Quantidade',
    color='Ano',
    markers=True,
    title='Quantidade de Vendas por Mês',
    labels={'Mês': 'Mês', 'Quantidade': 'Quantidade de Vendas'}
)

fig_quantidade_mensal.update_layout(
    xaxis_title='Mês',
    yaxis_title='Quantidade de Vendas',
    xaxis=dict(tickmode='linear')  # Garante a ordem correta dos meses
)


## Gráficos

fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = 'lat',
                                  lon = 'lon',
                                  scope = 'south america',
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data= {'lat': False, 'lon': False},
                                  title="Receita por estado")

fig_receita_mensal = px.line(receita_mensal,
                                x = 'Mês',
                                y = 'Preço',
                                markers = True,
                                range_y = (0, receita_mensal.max()),
                                color='Ano',
                                line_dash = 'Ano',
                                title = 'Receita mensal')

fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto=True,
                             title='Top estados (receita)')

fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por categoria')

fig_receita_categorias.update_layout(yaxis_title = 'Receita')
## Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)     

with aba2: 
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Total de Vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_mapa_quantidade, use_container_width=True)
        st.plotly_chart(fig_quantidade_categoria, use_container_width=True)

    with coluna2:
        st.metric('Quantidade de Estados', quantidade_vendas_estado.shape[0])
        st.plotly_chart(fig_quantidade_mensal, use_container_width=True)
        st.plotly_chart(fig_top_5_estados, use_container_width=True) 
        
with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(
            vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
            x='sum',
            y=vendedores[['sum']].sort_values(['sum'], ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (receita)'
            )
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(
            vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
            x='count',
            y=vendedores[['count']].sort_values(['count'], ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
        )

        st.plotly_chart(fig_vendas_vendedores)

