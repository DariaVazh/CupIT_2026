import streamlit as st
import pandas as pd
import numpy as np

from CupIT_2026.for_files import LoadFiles
from CupIT_2026.prioritization import do_priority_list

st.set_page_config(
    page_title="Модель",
    layout="wide"
)

# Заголовок
st.title("Анализ площадок")
st.markdown("---")

col1, col2 = st.columns(2)
loader = LoadFiles()
df = loader.load_excel('data/domains_analysis.xlsx')
df = do_priority_list(df)
with col1:
    st.subheader("📋 Данные")
    st.dataframe(df.head(10), use_container_width=True)

    # Статистика
    st.subheader("📈 Основная статистика")
    st.dataframe(df.describe(), use_container_width=True)