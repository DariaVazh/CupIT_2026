import numpy as np

def priority_formula(mentions, weights=[1]):
    criteries = np.array([mentions])
    w = np.array(weights)
    return np.sum(criteries * w)


def do_priority_list(df):
    df['Вес'] = df['Упоминаний'].apply(lambda x: priority_formula(x))
    return df

