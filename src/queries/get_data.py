
import sys
import os
# Caminho para o root do projeto
root_path = os.path.abspath("..")   # sobe 1 nível — ajuste se precisar

sys.path.append(root_path)

from database.db_connection import get_bigquery_client


class BusinessData:
    def __init__(self):
        self.client = get_bigquery_client()

    def get_receitas(self):

        query = "SELECT * FROM SBOX_ISRAEL.RECEITAS"

        df = self.client.query(query).to_dataframe()

        return df

    def get_despesas(self):

        query = "SELECT * FROM SBOX_ISRAEL.DESPESAS"

        df = self.client.query(query).to_dataframe()

        return df
    
    def get_peso_notas(self):

        query = "SELECT * FROM SBOX_ISRAEL.PESO_NOTAS"

        df = self.client.query(query).to_dataframe()

        return df




