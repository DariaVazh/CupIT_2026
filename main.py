import streamlit as st
from streamlit import title

main_page = st.Page("app.py", title="Главная")
an_page = st.Page("top.py", title="Обычный vs Генеративный")
t_page = st.Page('model.py', title='Экономическая модель')


pg = st.navigation([main_page, an_page, t_page])
pg.run()