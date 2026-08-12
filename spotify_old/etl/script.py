import requests
import pandas as pd
from sqlalchemy import create_engine



# SQL

# get_data()

data_csv = pd.read_csv("teste.csv")

engine = create_engine(
    "mssql+pyodbc://DESKTOP-AKTMQH7\\SQLEXPRESS/Spotify?"
    "driver=ODBC+Driver+17+for+SQL+Server&"
    "trusted_connection=yes"
)

conn = engine.connect()

print(conn)

data_csv.to_sql(
    "listening_history",
    engine,
    if_exists="replace",
    index=False
)



# df = pd.DataFrame(data)

# # salva csv
# df.to_csv("usuarios.csv", index=False)

# print("CSV salvo!")