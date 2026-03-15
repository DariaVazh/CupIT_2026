from for_files import LoadFiles

#upd
print('yes')

def load_data():
    l = LoadFiles()
    df = l.load_excel('data/domains_categories_all.xlsx')
    #Определим условную стоимость размещения на категории в зависимости от ее важности
    max_cost = 100000
    fraction = max_cost / len(df)
    df['Условные затраты на продвижение'] = (len(df) - df['№']) * fraction
    df['Потенциал'] = 100 / df['Суммарная доля, %'] # чем меньше доля, тем больше потенциал
    return df


def simulate_linear_investment(df, budget_total, investments=None):
    """
    Линейная модель: эффект = (инвестиции / стоимость) * потенциал
    """
    if investments is None:
        # По умолчанию распределяем пропорционально потенциалу
        total_potential = df['Потенциал'].sum()
        investments = (df['Потенциал'] / total_potential * budget_total).round(0)
        df['инвестиции'] = investments
    else:
        df['инвестиции'] = df['Категория'].map(investments).fillna(0)

    # Сколько "единиц продвижения" мы можем купить
    df['единиц_продвижения'] = df['инвестиции'] / df['Условные затраты на продвижение']
    df['единиц_продвижения'] = df['единиц_продвижения'].clip(0, 10)  # ограничиваем

    # Эффект: каждая единица дает +X% к видимости
    df['прирост_пп'] = df['единиц_продвижения'] * df['Потенциал'] * 0.3  # 0.3 - коэф. эффективности

    # Новая видимость
    df['новая_видимость'] = df['Суммарная доля, %'] + df['прирост_пп']

    # Эффективность (прирост на 1 млн инвестиций)
    df['эффективность'] = (df['прирост_пп'] / (df['инвестиции'] / 1000)).round(2)

    return df


# Модифицируем функцию с учетом коэффициента
def simulate_with_coef(df, budget, coef, mode):
    if mode == "Равномерно":
        inv = {cat: budget / len(df) for cat in df['Категория']}
    elif mode == "Фокус на топ-3":
        # 70% бюджета в топ-3 категории по потенциалу
        top_cats = df.nlargest(3, 'Потенциал')['Категория'].tolist()
        inv = {}
        for cat in df['Категория']:
            if cat in top_cats:
                inv[cat] = budget * 0.7 / 3
            else:
                inv[cat] = budget * 0.3 / (len(df) - 3)
    else:
        inv = None

    df_result = simulate_linear_investment(df, budget, inv)

    # Обновляем коэффициент
    df_result['прирост_пп'] = df_result['единиц_продвижения'] * df_result['Потенциал'] * coef
    df_result['новая_видимость'] = df_result['Суммарная доля, %'] + df_result['прирост_пп']
    df_result['эффективность'] = (df_result['прирост_пп'] / (df_result['инвестиции'] / 1000)).round(2)

    return df_result



df = load_data()
# Пробуем с бюджетом 1 млн рублей
budget = 1000000  # 1 млн руб.
result_df = simulate_linear_investment(df.copy(), budget)

print(result_df[['Категория', 'Условные затраты на продвижение',
                 'инвестиции', 'единиц_продвижения', 'прирост_пп', 'эффективность']])







