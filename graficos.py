import streamlit as st
import pandas as pd
import plotly_express as px

import teste

dados = teste.teste()

df = pd.DataFrame(dados)

df = df.groupby("won", as_index=False).sum().reset_index(drop=True)

st.write(df)