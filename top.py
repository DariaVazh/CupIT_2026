import streamlit as st


# Теперь можно импортировать нормально
from for_files import LoadFiles
from prioritization import do_priority_list

st.set_page_config(
    page_title="Топ доменов",
    page_icon="📈"
)

col1, col2 = st.columns(2)
loader = LoadFiles()
df = loader.load_excel('data/domains_analysis.xlsx')
df = do_priority_list(df)

df_usual_search = loader.load_excel('data/domains_analysis_yandex.xlsx')
df_usual_search = do_priority_list(df_usual_search)

with col1:
    st.subheader("Топ 5 обычного поиска")
    st.dataframe(df_usual_search['Домен'].head(5), use_container_width=True)

    # Статистика
    st.subheader("Топ 5 генеративного поиска")
    st.dataframe(df['Домен'].head(5), use_container_width=True)


if st.button("На главную"):
    st.switch_page("app.py")