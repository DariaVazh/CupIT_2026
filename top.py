
import streamlit as st
import pandas as pd
from for_files import LoadFiles
from prioritization import do_priority_list, merge, calculate_mismatch_coefficient

# Настройка страницы
st.set_page_config(
    page_title="Сравнение поисковых систем",
    page_icon="📊",
    layout="wide"
)

st.title("🔍 Сравнение обычного и генеративного поиска")
st.markdown("---")


@st.cache_data
def load_data():
    loader = LoadFiles()
    try:
        df_gen = loader.load_excel('data/domains_analysis.xlsx')
        df_gen = do_priority_list(df_gen)

        df_usual = loader.load_excel('data/domains_analysis_yandex.xlsx')
        df_usual = do_priority_list(df_usual)

        df_common = merge(df_gen, df_usual)
        df_diff, med_missmatch = calculate_mismatch_coefficient(df_common)

        return df_gen, df_usual, df_diff, med_missmatch
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None, None, None, None


# Загружаем данные
df_gen, df_usual, df_diff, med_missmatch = load_data()

if df_gen is not None:
    # Создаем вкладки для лучшей организации
    tab1, tab2 = st.tabs(["📊 Сравнение топов", " ... "])

    with tab1:
        # Две основные колонки
        col1, col2 = st.columns(2)

        with col1:
            # Карточка обычного поиска
            with st.container(border=True):
                st.markdown("### 🔎 Обычный поиск (Яндекс)")
                st.caption("Топ-5 доменов в традиционной выдаче")

                # Красивое отображение списка
                for i, domain in enumerate(df_usual['Домен'].head(5).values, 1):
                    st.markdown(f"{i}. **{domain}**")

                st.markdown("---")

                st.markdown(f"**Всего доменов:** {len(df_usual)}")

        with col2:
            # Карточка генеративного поиска
            with st.container(border=True):
                st.markdown("### 🤖 Генеративный поиск (Нейросети)")
                st.caption("Топ-5 доменов в выдаче нейросетей")

                # Красивое отображение списка
                for i, domain in enumerate(df_gen['Домен'].head(5).values, 1):
                    st.markdown(f"{i}. **{domain}**")

                st.markdown("---")

                st.markdown(f"**Всего доменов:** {len(df_gen)}")

        # Метрика расхождений
        st.markdown("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m2:
            st.metric(
                label="📊 СРЕДНЕЕ РАСХОЖДЕНИЕ",
                value=str(med_missmatch),
                delta="между обычным и генеративным поиском",
                delta_color="off"
            )
        st.markdown("---")

        # Блок с доменами для нейросети
        with st.container(border=True):
            st.markdown("### 🌟 Топ-10 доменов, важных для нейросетей")
            st.caption("Домены, которые получают более высокий приоритет в генеративном поиске")

            # Создаем колонки для красивого отображения
            cols = st.columns(2)

            # Разбиваем на две колонки по 5 доменов
            domains_list = df_diff['Домен'].head(10).values
            for i, domain in enumerate(domains_list[:5]):
                with cols[0]:
                    st.markdown(f"{i + 1}. {domain}")
            for i, domain in enumerate(domains_list[5:], 5):
                with cols[1]:
                    st.markdown(f"{i + 1}. {domain}")

    with tab2:
        st.markdown(" ... ")



    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b2:
        if st.button("🏠 На главную", use_container_width=True, type="primary"):
            st.switch_page("app.py")

else:
    st.error("Не удалось загрузить данные. Проверьте наличие файлов в папке data/")
#
# import streamlit as st
#
#
# # Теперь можно импортировать нормально
# from for_files import LoadFiles
# from prioritization import do_priority_list, merge, calculate_mismatch_coefficient
#
# st.set_page_config(
#     page_title="Обычный vs Генеративный",
#     page_icon="📈"
# )
#
# col1, col2 = st.columns(2)
# loader = LoadFiles()
# df = loader.load_excel('data/domains_analysis.xlsx')
# df = do_priority_list(df)
#
# df_usual_search = loader.load_excel('data/domains_analysis_yandex.xlsx')
# df_usual_search = do_priority_list(df_usual_search)
#
# df_common = merge(df, df_usual_search)
# df_diff, med_missmatch =  calculate_mismatch_coefficient(df_common)
# print(df_diff.head())
#
# with col1:
#     st.subheader("Топ 5 обычного поиска")
#     st.dataframe(df_usual_search['Домен'].head(5), use_container_width=True)
#
#     st.subheader('10 доменов, которые гораздо важнее для нейросети')
#     df_display = df_diff['Домен'].head(10).reset_index(drop=True)
#     df_display.index = range(1, len(df_display) + 1)  # Индексы с 1 до 10
#     st.dataframe(df_display, use_container_width=True)
#
# with col2:
#     # Статистика
#     st.subheader("Топ 5 генеративного поиска")
#     st.dataframe(df['Домен'].head(5), use_container_width=True)
#
#     st.metric(label="Усредненный процент расхождений", value=str(med_missmatch))
#
#
# if st.button("На главную"):
#     st.switch_page("app.py")
