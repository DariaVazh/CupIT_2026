import numpy as np

def priority_formula(mentions, weights=[1]):
    criteries = np.array([mentions])
    w = np.array(weights)
    return np.sum(criteries * w)


def do_priority_list(df):
    df['Домен'] = df['Домен'].apply(lambda x: x.lower())
    df['Вес'] = df['Упоминаний'].apply(lambda x: priority_formula(x))
    df['Доля упоминаний от общего числа'] = df['Упоминаний'] / len(df)
    return df.sort_values('Вес', ascending=False)

def merge(df_usual,df_gen):
    df_gen = df_gen.rename(columns={
        'Доля упоминаний от общего числа': 'упоминаний_ген'
    })
    df_usual = df_usual.rename(columns={
        'Доля упоминаний от общего числа': 'упоминаний_поиск'
    })
    merged_df = df_gen.merge(df_usual[['Домен','упоминаний_поиск']], on='Домен', how='left')
    merged_df['упоминаний_поиск'] = merged_df['упоминаний_поиск'].fillna(0)
    return merged_df

def calculate_mismatch_coefficient(df):
    result = df.copy()
    result['ранг_обычн'] = result['упоминаний_поиск'].rank(ascending=False, method='min').astype(int)
    result['ранг_генер'] = result['упоминаний_ген'].rank(ascending=False, method='min').astype(int)
    result['коэф_несоотв'] = result['ранг_обычн'] - result['ранг_генер']
    result['лог_частоты'] = np.log1p(result['упоминаний_поиск'] + result['упоминаний_ген'])
    result['коэф_взвеш'] = result['коэф_несоотв'] * result['лог_частоты']
    result['abs_разница'] = abs(result['упоминаний_поиск'] - result['упоминаний_ген'])
    max_possible_diff = len(df) - 1
    result['расхождение_%'] = (result['abs_разница'] / max_possible_diff * 100).round(10)


    def categorize(x):
        if x > 1:
            return 'ПЕРЕОЦЕНЕН (приоритет)'
        elif x < -1:
            return 'НЕДООЦЕНЕН (осторожно)'
        else:
            return 'СБАЛАНСИРОВАН'


    result['статус'] = result['коэф_несоотв'].apply(categorize)
    result = result.sort_values('коэф_взвеш', ascending=False)

    median_mismatch = result['расхождение_%'].mean().round(10)
    print(median_mismatch)

    return result, median_mismatch





