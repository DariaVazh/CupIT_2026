from CupIT_2026.for_files import LoadFiles
from CupIT_2026.prioritization import do_priority_list, merge, calculate_mismatch_coefficient


loader = LoadFiles()
df = loader.load_excel('data/domains_analysis.xlsx')
df_usual_search = loader.load_excel('data/domains_analysis_yandex.xlsx')

df_gen = do_priority_list(df)
df_usual = do_priority_list(df_usual_search)

new_df = merge(df_gen, df_usual)
print(calculate_mismatch_coefficient(new_df).head())

