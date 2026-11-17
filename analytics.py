"""Estimativas pontuais ponderadas; cada visão principal usa um trimestre."""
import pandas as pd

RACES = {1: 'Branca', 2: 'Preta', 3: 'Amarela', 4: 'Parda', 5: 'Indígena', 9: 'Ignorado'}
EDUCATION = {1: 'Sem instrução / < 1 ano', 2: 'Fundamental incompleto',
             3: 'Fundamental completo', 4: 'Médio incompleto', 5: 'Médio completo',
             6: 'Superior incompleto', 7: 'Superior completo'}
SECTORS = {1: 'Agropecuária e pesca', 2: 'Indústria', 3: 'Construção',
           4: 'Comércio e reparação', 5: 'Transporte e correio', 6: 'Alojamento e alimentação',
           7: 'Informação, finanças e serviços profissionais', 8: 'Administração pública',
           9: 'Educação, saúde e serviços sociais', 10: 'Outros serviços',
           11: 'Serviços domésticos', 12: 'Atividades mal definidas'}


def filtered(frame, geography='bahia', races=None, education=None, ages=None, sector=None):
    result = frame.copy()
    if geography == 'salvador':
        result = result.loc[result.capital.eq(29)]
    elif geography == 'interior':
        result = result.loc[~result.capital.eq(29)]
    for column, values in [('v2010', races), ('vd3004', education), ('vd4010', sector)]:
        if values:
            result = result.loc[result[column].isin(values)]
    if ages:
        result = result.loc[result.v2009.between(*ages)]
    return result


def weight(frame):
    return float(frame.v1028.sum())


def ratio(numerator, denominator):
    return 100 * numerator / denominator if denominator > 0 else None


def income(frame):
    valid = frame.loc[frame.vd4016.notna()]
    return float((valid.vd4016 * valid.v1028).sum() / weight(valid)) if weight(valid) else None


def metrics(frame):
    entrepreneurs = frame.loc[frame.vd4009.isin([8, 9])]
    women = entrepreneurs.loc[entrepreneurs.v2007.eq(2)]
    men = entrepreneurs.loc[entrepreneurs.v2007.eq(1)]
    black_women = women.loc[women.v2010.isin([2, 4])]
    known = women.loc[women.v4019.isin([1, 2])]
    wi, mi = income(women), income(men)
    return {
        'women_total': weight(women) if not frame.empty else None,
        'women_share': ratio(weight(women), weight(entrepreneurs)),
        'black_share': ratio(weight(black_women), weight(women)),
        'formal_rate': ratio(weight(known.loc[known.v4019.eq(1)]), weight(known)),
        'women_income': wi,
        'income_gap': (100 * (1 - wi / mi)) if wi is not None and mi is not None and mi > 0 else None,
        'n': len(women), 'income_n': int(women.vd4016.notna().sum()),
        'formal_n': len(known),
    }


def intersection(frame):
    rows = []
    ent = frame.loc[frame.vd4009.isin([8, 9])]
    for (sex, race), group in ent.groupby(['v2007', 'v2010']):
        known = group.loc[group.v4019.isin([1, 2])]
        rows.append({'Sexo': {1: 'Homens', 2: 'Mulheres'}.get(sex, 'Ignorado'),
                     'Raça/cor': RACES.get(race, 'Ignorado'), 'Amostra': len(group),
                     'População estimada': weight(group), 'Renda média (R$)': income(group),
                     'Com CNPJ (%)': ratio(weight(known.loc[known.v4019.eq(1)]), weight(known))})
    return pd.DataFrame(rows, columns=['Sexo', 'Raça/cor', 'Amostra', 'População estimada',
                                     'Renda média (R$)', 'Com CNPJ (%)'])
