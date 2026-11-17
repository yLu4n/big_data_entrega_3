"""Dashboard PNAD Contínua: execute python app.py."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, dash_table, no_update

from analytics import EDUCATION, RACES, SECTORS, filtered, income, intersection, metrics, weight
from data_source import load_data

app = Dash(__name__, title='Entre Elas • Bahia', update_title='Atualizando…')
server = app.server
COLORS = ['#6238a5', '#dc7749', '#247e86', '#bc587d', '#9c8450', '#607d9f']
REFRESH = max(15, int(os.getenv('REFRESH_SECONDS', '60')))


def dropdown(label, ident, options, value=None, multi=False):
    return html.Div([html.Label(label, htmlFor=ident), dcc.Dropdown(
        id=ident, options=options, value=value, multi=multi,
        clearable=multi, placeholder='Todas as categorias' if multi else 'Selecione',
    )], className='filter')


def options(mapping):
    return [{'label': name, 'value': code} for code, name in mapping.items()]


def number(value, kind='number'):
    if value is None or pd.isna(value):
        return 'Sem base'
    text = (f'{value:,.0f}' if kind == 'number' else f'{value:,.1f}')
    text = text.replace(',', '_').replace('.', ',').replace('_', '.')
    return ('R$ ' if kind == 'money' else '') + text + ('%' if kind == 'percent' else '')


def card(label, value, note, kind='number'):
    return html.Article([html.P(label, className='metric-label'),
                         html.Strong(number(value, kind)), html.P(note, className='metric-note')], className='metric')


def figure_style(fig, title, y=None):
    fig.update_layout(title=dict(text=title, font=dict(size=17)), template='plotly_white',
                      colorway=COLORS, font=dict(family='Segoe UI, Arial', color='#293343'),
                      margin=dict(l=35, r=20, t=65, b=65), height=355,
                      paper_bgcolor='white', plot_bgcolor='white',
                      legend=dict(title='', orientation='h', y=-0.25),
                      separators=',.')
    fig.update_xaxes(title=None, showgrid=False)
    fig.update_yaxes(title=y, gridcolor='#edf0f4')
    return fig


def empty(title, message='Sem observações para este recorte.'):
    fig = figure_style(go.Figure(), title)
    fig.add_annotation(text=message, x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


app.layout = html.Div([
    html.A('Ir para os indicadores', href='#indicadores', className='skip-link'),
    html.Header([html.Div([html.Span('E', className='brand-icon'), html.Strong('Entre Elas'),
                           html.Span('OBSERVATÓRIO BAHIA', className='brand-sub')], className='brand'),
                 html.Div('PNAD Contínua / IBGE', className='header-source')], className='topbar'),
    html.Main([
        html.Div([html.Div([html.P('TRABALHO, RENDA E DIREITOS', className='eyebrow'),
                           html.H1(['Empreender na Bahia.', html.Br(), html.Span('Enxergar as desigualdades.')]),
                           html.P('Explore como sexo, raça/cor e território atravessam as oportunidades de quem empreende.', className='intro')]),
                  html.Div([html.Div([html.Strong('05'), html.Span('Igualdade de gênero')], className='ods ods5'),
                            html.Div([html.Strong('18'), html.Span('Igualdade étnico-racial')], className='ods ods18')], className='ods-group')], className='hero'),
        html.Div([html.Div(id='connection', role='status'), html.Button('Atualizar dados ↻', id='refresh', n_clicks=0)], className='source-bar'),
        html.Section([
            dropdown('Trimestre', 'period', [], None),
            dropdown('Território', 'geography', options({'bahia': 'Bahia (inclui Salvador)', 'salvador': 'Salvador', 'interior': 'Bahia fora de Salvador'}), 'bahia'),
            dropdown('Raça/cor', 'races', options(RACES), [], True),
            dropdown('Escolaridade', 'education', options(EDUCATION), [], True),
            dropdown('Atividade econômica', 'sector', options(SECTORS), [], True),
            html.Div([html.Label('Faixa etária', htmlFor='ages'), dcc.RangeSlider(
                id='ages', min=14, max=130, step=1, value=[14, 130],
                marks={14: '14', 35: '35', 60: '60', 100: '100', 130: '130'}, tooltip={'placement': 'bottom', 'always_visible': False})], className='filter age-filter'),
        ], className='filters', **{'aria-label': 'Filtros do dashboard'}),
        html.Div(id='sample-note', className='sample-note', role='status'),
        dcc.Loading(html.Section(id='indicadores', className='metrics'), type='circle'),
        html.Div([dcc.Graph(id='income-chart', config={'displaylogo': False}),
                  dcc.Graph(id='formal-chart', config={'displaylogo': False}),
                  dcc.Graph(id='sector-chart', config={'displaylogo': False}),
                  dcc.Graph(id='trend-chart', config={'displaylogo': False})], className='charts'),
        html.Section([html.Div([html.Div([html.P('SEXO × RAÇA/COR', className='eyebrow'), html.H2('Os recortes por trás dos números')]),
                               html.Button('Baixar tabela CSV ↓', id='export', n_clicks=0)], className='table-heading'),
                      html.P('Empregadores e trabalhadores por conta própria. A exportação contém somente os resultados agregados.', className='muted'),
                      dash_table.DataTable(id='intersection-table', columns=[{'name': c, 'id': c} for c in intersection(pd.DataFrame(columns=['vd4009', 'v2007', 'v2010'])).columns],
                          data=[], sort_action='native', page_size=12,
                          style_table={'overflowX': 'auto'},
                          style_cell={'fontFamily': 'Segoe UI, Arial', 'fontSize': 13, 'padding': '13px', 'textAlign': 'left', 'border': 'none', 'borderBottom': '1px solid #edf0f4'},
                          style_header={'fontWeight': '600', 'backgroundColor': '#f6f4fa'},
                          style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#fcfbfe'}]),
                      dcc.Download(id='download'), html.Div(id='export-message', role='status')], className='table-panel'),
        html.Section([html.Article([html.Span('ODS 5', className='tag'), html.H2('Autonomia econômica das mulheres'),
                       html.P('A participação no empreendedorismo, a renda e o acesso ao CNPJ ajudam a examinar desigualdades de oportunidades e recursos econômicos. Os cruzamentos consideram raça/cor, idade, escolaridade e território.'),
                       html.A('Conheça as metas brasileiras ↗', href='https://www.ipea.gov.br/ods/ods5.html', target='_blank', rel='noopener noreferrer')]),
                      html.Article([html.Span('ODS 18 · BRASIL', className='tag'), html.H2('Igualdade étnico-racial'),
                       html.P('Objetivo voluntariamente adotado pelo Brasil, complementar aos 17 ODS globais. O painel evidencia a situação de mulheres negras (pretas e pardas) e preserva as demais categorias, inclusive indígenas, nos filtros e cruzamentos.'),
                       html.A('Conheça o ODS 18 ↗', href='https://ods.igualdaderacial.gov.br/ods18', target='_blank', rel='noopener noreferrer')])], className='context-grid'),
        html.Details([html.Summary('Como ler os indicadores e quais são os limites'),
            html.Ul([
                html.Li('Universo: pessoas ocupadas da Bahia. Empreendedores: VD4009 = 8 ou 9 (empregador ou conta própria). Sexo corresponde à variável V2007 do IBGE; não mede identidade de gênero.'),
                html.Li('População estimada: soma dos pesos V1028. Participação feminina: peso das empreendedoras / peso de todos os empreendedores. Mulheres negras: peso das empreendedoras pretas e pardas / peso das empreendedoras.'),
                html.Li('Formalização: peso das empreendedoras com CNPJ / peso das empreendedoras com resposta válida em V4019. Ausentes são excluídos do denominador.'),
                html.Li('Renda média: soma(renda VD4016 × peso) / soma(peso), apenas entre rendas informadas. Renda habitual nominal do trabalho principal; não há deflacionamento.'),
                html.Li('Diferença de renda: 100 × (1 − renda média feminina / masculina), entre empreendedores sob os mesmos filtros. Valor negativo indica renda feminina maior. Sem comparador válido, aparece Sem base.'),
                html.Li('Um trimestre por vez evita somar pessoas que podem reaparecer em períodos diferentes. A evolução mostra cada trimestre separadamente, mantendo os outros filtros. Salvador já integra Bahia.'),
                html.Li('São estimativas pontuais exploratórias, sem erros padrão ou intervalos de confiança do desenho amostral. Grupos pequenos exigem cautela; n < 30 é um alerta operacional, não um critério oficial do IBGE.'),
                html.Li('A base não permite medir desemprego, violência de gênero, trabalho de cuidado ou todos os direitos abrangidos pelos ODS. Estes são indicadores analíticos do projeto, não os indicadores oficiais dos ODS.'),
            ]), html.A('Fonte: PNAD Contínua / IBGE ↗', href='https://www.ibge.gov.br/estatisticas/sociais/trabalho/9173-pnadcontinua.html', target='_blank', rel='noopener noreferrer')], className='methodology'),
        html.Footer('Entre Elas • Bahia | Dados para tornar as desigualdades visíveis.'),
    ]),
    dcc.Interval(id='clock', interval=REFRESH * 1000, n_intervals=0),
])


def prepare(period, geography, races, education, ages, sector):
    frame, source = load_data()
    all_periods = sorted(frame.periodo.unique())
    selected = period if period in all_periods else (all_periods[-1] if all_periods else None)
    history = filtered(frame, geography, races, education, ages, sector)
    return history.loc[history.periodo.eq(selected)], history, source, all_periods, selected


@app.callback(
    Output('indicadores', 'children'), Output('income-chart', 'figure'),
    Output('formal-chart', 'figure'), Output('sector-chart', 'figure'),
    Output('trend-chart', 'figure'), Output('intersection-table', 'data'),
    Output('connection', 'children'), Output('sample-note', 'children'),
    Output('period', 'options'), Output('period', 'value'),
    Input('clock', 'n_intervals'), Input('refresh', 'n_clicks'), Input('period', 'value'),
    Input('geography', 'value'), Input('races', 'value'), Input('education', 'value'),
    Input('ages', 'value'), Input('sector', 'value'),
)
def render_dashboard(_tick, _click, period, geography, races, education, ages, sector):
    try:
        current, history, source, periods, selected = prepare(period, geography, races, education, ages, sector)
    except Exception:
        # Não enviar detalhes internos da fonte ou da rede ao navegador.
        message = 'Falha ao consultar a API. Inicie a API e verifique API_BASE_URL no .env. Os indicadores ficam indisponíveis até a conexão ser restabelecida.'
        return [], *[empty('Fonte indisponível', 'Não foi possível consultar os dados.') for _ in range(4)], [], message, 'Indicadores indisponíveis.', no_update, no_update
    m = metrics(current)
    cards = [card('Empreendedoras estimadas', m['women_total'], 'Soma dos pesos · empregadoras e conta própria'),
             card('Participação feminina', m['women_share'], 'Entre todos os empreendedores do recorte', 'percent'),
             card('Mulheres negras', m['black_share'], 'Pretas e pardas entre as empreendedoras', 'percent'),
             card('Formalização feminina', m['formal_rate'], f"CNPJ · {m['formal_n']} respostas válidas na amostra", 'percent'),
             card('Renda média feminina', m['women_income'], f"Trabalho principal · {m['income_n']} rendas informadas", 'money'),
             card('Diferença de renda por sexo', m['income_gap'], 'Quanto a média feminina fica abaixo da masculina', 'percent')]
    table = intersection(current)
    if table.empty:
        income_fig, formal_fig = empty('Renda de empreendedores<br><sup>Por sexo e raça/cor</sup>'), empty('Acesso ao CNPJ por sexo e raça/cor')
    else:
        income_fig = figure_style(px.bar(table, x='Raça/cor', y='Renda média (R$)', color='Sexo', barmode='group', color_discrete_map={'Mulheres': COLORS[0], 'Homens': COLORS[1]}, hover_data=['Amostra']), 'Renda de empreendedores<br><sup>Por sexo e raça/cor</sup>', 'R$ / mês')
        formal_fig = figure_style(px.bar(table, x='Raça/cor', y='Com CNPJ (%)', color='Sexo', barmode='group', color_discrete_map={'Mulheres': COLORS[0], 'Homens': COLORS[1]}, hover_data=['Amostra']), 'Acesso ao CNPJ por sexo e raça/cor', '% das respostas válidas')
    women = current.loc[current.v2007.eq(2) & current.vd4009.isin([8, 9])]
    groups = [{'Atividade': SECTORS.get(code, str(code)), 'Estimativa': weight(group), 'Amostra': len(group)} for code, group in women.groupby('vd4010')]
    if groups:
        sector_frame = pd.DataFrame(groups).sort_values('Estimativa').tail(7)
        sector_fig = figure_style(px.bar(sector_frame, x='Estimativa', y='Atividade', orientation='h', hover_data=['Amostra'], color_discrete_sequence=[COLORS[0]]), 'Onde as mulheres empreendem · top 7')
        sector_fig.update_yaxes(automargin=True)
    else:
        sector_fig = empty('Onde as mulheres empreendem')
    trend = [{'Trimestre': p, 'Participação feminina (%)': metrics(g)['women_share']} for p, g in history.groupby('periodo')]
    trend_fig = figure_style(px.line(pd.DataFrame(trend), x='Trimestre', y='Participação feminina (%)', markers=True, color_discrete_sequence=[COLORS[0]]), 'Participação feminina por trimestre', '% dos empreendedores') if trend else empty('Participação feminina por trimestre')
    display_table = table.copy()
    for column in ['População estimada', 'Renda média (R$)', 'Com CNPJ (%)']:
        if not display_table.empty:
            display_table[column] = display_table[column].map(lambda value: number(value, 'number' if column == 'População estimada' else 'decimal'))
    now = datetime.now(ZoneInfo('America/Bahia')).strftime('%d/%m/%Y às %H:%M:%S')
    note = f"{selected or 'Sem período'} · {len(current):,} observações de ocupados · {m['n']:,} empreendedoras na amostra.".replace(',', '.')
    if m['n'] < 30:
        note += ' Atenção: recorte com menos de 30 empreendedoras; interprete com cautela.'
    return cards, income_fig, formal_fig, sector_fig, trend_fig, display_table.to_dict('records'), f'{source} | Consulta: {now} | Atualização: {REFRESH}s', note, options({p: p for p in periods}), selected


@app.callback(Output('download', 'data'), Output('export-message', 'children'),
              Input('export', 'n_clicks'), State('period', 'value'), State('geography', 'value'),
              State('races', 'value'), State('education', 'value'), State('ages', 'value'), State('sector', 'value'), prevent_initial_call=True)
def export_table(clicks, period, geography, races, education, ages, sector):
    try:
        current, _, _, _, selected = prepare(period, geography, races, education, ages, sector)
        table = intersection(current)
        table.insert(0, 'Trimestre', selected)
        table.insert(1, 'Território', geography)
        return dcc.send_data_frame(table.to_csv, 'indicadores_interseccionais.csv', index=False, sep=';', decimal=',', encoding='utf-8-sig'), 'Tabela exportada com os filtros atuais.'
    except Exception:
        return no_update, 'Exportação indisponível: verifique a conexão com a fonte.'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '8050')), debug=False)
