import streamlit as st


st.set_page_config(
    page_title="Главная",
    layout="wide"
)


st.title("Главная страница")


st.write("В данном приложении вы можете ознакомиться с данными о площадках для P&G")
st.page_link("top.py", label="Перейти к топам", icon="📈")


# # Заголовок
# st.title("Анализ площадок")
# st.markdown("---")

# col1, col2 = st.columns(2)
# loader = LoadFiles()
# df = loader.load_excel('data/domains_analysis.xlsx')
# df = do_priority_list(df)
#
# df_usual_search = loader.load_excel('data/domains_analysis_yandex.xlsx')
# df_usual_search = do_priority_list(df_usual_search)
#
# with col1:
#     st.subheader("Топ 5 обычного поиска")
#     st.dataframe(df_usual_search['Домен'].head(5), use_container_width=True)
#
#     # Статистика
#     st.subheader("Топ 5 генеративного поиска")
#     st.dataframe(df['Домен'].head(5), use_container_width=True)