import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modeling import load_data, simulate_linear_investment, simulate_with_coef

#upd
#upd
print('yes')

st.set_page_config(
    page_title="P&G Экономическая модель",
    page_icon="📊",
    layout="wide"
)

# Заголовок
st.title("📊 Экономическая модель продвижения в генеративном поиске")
st.markdown("### Моделирование эффекта инвестиций по категориям площадок")

df = load_data()
st.sidebar.header("⚙️ Параметры модели")

budget = st.sidebar.slider(
    "Бюджет на продвижение (руб.):",
    min_value=100000,
    max_value=5000000,
    value=1000000,
    step=100000,
    format="%d"
)

# Выбор коэффициента эффективности
efficiency_coef = st.sidebar.slider(
    "Коэффициент эффективности:",
    min_value=0.1,
    max_value=1.0,
    value=0.3,
    step=0.05,
    help="Чем выше коэффициент, тем больше прирост от каждой единицы продвижения"
)

# Режим распределения
distribution_mode = st.sidebar.radio(
    "Режим распределения бюджета:",
    ["Пропорционально потенциалу", "Равномерно", "Фокус на топ-3"]
)

result = simulate_with_coef(df, budget, efficiency_coef, distribution_mode)

# Основной контент
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Эффект инвестиций по категориям")

    # График 1: Столбчатая диаграмма (текущая + прирост)
    fig1 = go.Figure()

    # Текущая видимость
    fig1.add_trace(go.Bar(
        name='Текущая видимость',
        x=result['Категория'],
        y=result['Суммарная доля, %'],
        marker_color='lightblue',
        text=result['Суммарная доля, %'].round(1),
        textposition='inside',
    ))

    # Прирост
    fig1.add_trace(go.Bar(
        name='Прирост от инвестиций',
        x=result['Категория'],
        y=result['прирост_пп'],
        marker_color='coral',
        text=result['прирост_пп'].round(1),
        textposition='outside',
        base=result['Суммарная доля, %']
    ))

    # Инвестиции на второй оси
    fig1.add_trace(go.Scatter(
        name='Инвестиции (тыс. руб.)',
        x=result['Категория'],
        y=result['инвестиции'] / 1000,
        yaxis='y2',
        mode='markers+text',
        marker=dict(size=12, color='darkgreen', symbol='diamond'),
        text=(result['инвестиции'] / 1000).round(0),
        textposition='top center',
    ))

    fig1.update_layout(
        title=f'При бюджете {budget / 1000:.0f}K руб. (коэф. {efficiency_coef})',
        xaxis_title='Категория',
        yaxis_title='Видимость в генеративном поиске (%)',
        yaxis2=dict(
            title='Инвестиции (тыс. руб.)',
            overlaying='y',
            side='right',
        ),
        barmode='group',
        bargap=0.3,
        height=500,
        hovermode='x unified'
    )

    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("📊 Ключевые метрики")

    total_current = result['Суммарная доля, %'].sum()
    total_new = result['новая_видимость'].sum()

    # Метрики в карточках
    st.metric(
        label="💰 Общий бюджет",
        value=f"{budget / 1000000:.2f} млн руб."
    )

    st.metric(
        label="📈 Текущая суммарная видимость",
        value=f"{total_current:.1f}%"
    )

    st.metric(
        label="🎯 Новая суммарная видимость",
        value=f"{total_new:.1f}%",
        delta=f"{total_new - total_current:.1f} п.п."
    )

    st.metric(
        label="⚡ Эффективность (п.п./млн руб.)",
        value=f"{result['эффективность'].mean():.2f}"
    )

    # Лучшая категория
    best_cat = result.iloc[0]
    st.info(f"🏆 **Лучшая категория**: {best_cat['Категория']}\n\n"
            f"Эффективность: {best_cat['эффективность']:.2f} п.п./млн руб.\n"
            f"Прирост: +{best_cat['прирост_пп']:.1f} п.п.")

# Второй ряд графиков
st.subheader("📉 Детальный анализ эффективности")

col3, col4 = st.columns(2)

with col3:
    # График 2: Эффективность инвестиций
    fig2 = px.bar(
        result,
        x='Категория',
        y='эффективность',
        color='эффективность',
        color_continuous_scale='RdYlGn',
        text=result['эффективность'].round(2),
        title="Эффективность инвестиций (п.п. прироста на 1 млн руб.)"
    )
    fig2.update_traces(textposition='outside')
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

with col4:
    # График 3: Круговая диаграмма распределения бюджета
    fig3 = px.pie(
        result,
        values='инвестиции',
        names='Категория',
        title="Распределение бюджета по категориям",
        hole=0.4
    )
    fig3.update_traces(textposition='inside', textinfo='percent+label')
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

# Таблица с результатами
st.subheader("📋 Детальные результаты по категориям")

# Форматируем таблицу
display_df = result[['Категория', 'Суммарная доля, %', 'Условные затраты на продвижение',
                     'инвестиции', 'единиц_продвижения', 'прирост_пп',
                     'новая_видимость', 'эффективность']].copy()

display_df['инвестиции'] = display_df['инвестиции'].apply(lambda x: f"{x:,.0f} ₽")
display_df['Условные затраты на продвижение'] = display_df['Условные затраты на продвижение'].apply(
    lambda x: f"{x:,.0f} ₽")
display_df['единиц_продвижения'] = display_df['единиц_продвижения'].round(2)
display_df['прирост_пп'] = display_df['прирост_пп'].round(1)
display_df['новая_видимость'] = display_df['новая_видимость'].round(1)
display_df['эффективность'] = display_df['эффективность'].round(2)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'Категория': 'Категория',
        'Суммарная доля, %': 'Текущая доля (%)',
        'Условные затраты на продвижение': 'Стоимость',
        'инвестиции': 'Инвестиции',
        'единиц_продвижения': 'Единиц',
        'прирост_пп': 'Прирост (п.п.)',
        'новая_видимость': 'Новая доля (%)',
        'эффективность': 'Эффект/млн'
    }
)

# Сводные метрики
st.subheader("🎯 Итоговый эффект стратегии")

col5, col6, col7, col8 = st.columns(4)

with col5:
    roi = (total_new - total_current) / (budget / 1000000)
    st.metric("ROI стратегии", f"{roi:.2f} п.п./млн руб.")

with col6:
    st.metric("Категорий с приростом >5 п.п.",
              len(result[result['прирост_пп'] > 5]))

with col7:
    st.metric("Средний прирост на категорию",
              f"{result['прирост_пп'].mean():.1f} п.п.")

with col8:
    st.metric("Макс. эффективность",
              f"{result['эффективность'].max():.2f}")

# Экспорт данных
st.download_button(
    label="📥 Скачать результаты (CSV)",
    data=result.to_csv(index=False).encode('utf-8'),
    file_name=f"economic_model_results_{budget}.csv",
    mime="text/csv"
)