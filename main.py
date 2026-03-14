import streamlit as st

main_page = st.Page("app.py", title="Главная")
an_page = st.Page("top.py", title="Обычный vs Генеративный")

pg = st.navigation([main_page, an_page])
pg.run()