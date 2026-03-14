import pandas as pd


class LoadFiles:
    def load_excel(self, filename):
        return pd.read_excel(filename)
