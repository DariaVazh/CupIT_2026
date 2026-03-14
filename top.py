import streamlit as st


# Теперь можно импортировать нормально
from for_files import LoadFiles
from prioritization import do_priority_list, merge, calculate_mismatch_coefficient

st.set_page_config(
    page_title="Обычный vs Генеративный",
    page_icon="📈"
)

col1, col2 = st.columns(2)
loader = LoadFiles()
df = loader.load_excel('data/domains_analysis.xlsx')
df = do_priority_list(df)

df_usual_search = loader.load_excel('data/domains_analysis_yandex.xlsx')
df_usual_search = do_priority_list(df_usual_search)

df_common = merge(df, df_usual_search)
df_diff, med_missmatch =  calculate_mismatch_coefficient(df_common)
print(df_diff.head())

with col1:
    st.subheader("Топ 5 обычного поиска")
    st.dataframe(df_usual_search['Домен'].head(5), use_container_width=True)

    st.subheader('10 доменов, которые гораздо важнее для нейросети')
    df_display = df_diff['Домен'].head(10).reset_index(drop=True)
    df_display.index = range(1, len(df_display) + 1)  # Индексы с 1 до 10
    st.dataframe(df_display, use_container_width=True)

with col2:
    # Статистика
    st.subheader("Топ 5 генеративного поиска")
    st.dataframe(df['Домен'].head(5), use_container_width=True)

    st.metric(label="Усредненный процент расхождений", value=str(med_missmatch))




if st.button("На главную"):
    st.switch_page("app.py")