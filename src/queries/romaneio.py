from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
import re
import pandas as pd
from datetime import datetime

from google.cloud import bigquery


@dataclass
class RomaneioData:
    data: Optional[str] = None
    total_notas: Optional[int] = None
    realizadas: Optional[int] = None
    notas_leves: Optional[int] = None
    notas_pesadas: Optional[int] = None
    fat_notas_leves: Optional[float] = None
    fat_notas_pesadas: Optional[float] = None
    valor_total: Optional[float] = None
    ceps: Optional[str] = None
    despesas: dict[str, float] = field(default_factory=dict)


class ProcessRomaneio:
    def __init__(self, input_text: str, year: int | None = None):
        self.input_text = input_text
        self.year = year
        self.result = RomaneioData()

    def _notas_regex(self):
        notas = re.findall(
            r"(\d+)\s+notas\s+a\s+\$(\d+,\d+).*?\$(\d+,\d+)",
            self.input_text,
        )
        return notas

    def set_data(self) -> str:
        date_match = re.search(r"Romaneio\s+(\d{2})/(\d{2})", self.input_text)
        day, month = map(int, date_match.groups())

        data = datetime(self.year, month, day).strftime("%Y-%m-%d")

        self.result.data = data

    def set_notas_geral(self):
        total_notas = int(re.search(r"Total de notas\s+(\d+)", self.input_text).group(1))
        realizadas = int(re.search(r"Realizadas\s+(\d+)", self.input_text).group(1))

        self.result.total_notas = total_notas
        self.result.realizadas = realizadas

    def set_notas_por_peso(self) -> None:
        notas = self._notas_regex()

        for qtd, valor, _ in notas:
            valor_unit = float(valor.replace(",", "."))
            if valor_unit < 30:
                self.result.notas_leves = int(qtd)
            else:
                self.result.notas_pesadas = int(qtd)

    def set_faturamento_por_peso(self) -> None:
        notas = self._notas_regex()

        fat_nota_leve = float(notas[0][2].replace(",", "."))
        fat_nota_pesada = float(notas[1][2].replace(",", "."))

        self.result.fat_notas_leves = fat_nota_leve
        self.result.fat_notas_pesadas = fat_nota_pesada

    def set_valor_total(self) -> None:
        valor_total = self.result.fat_notas_leves + self.result.fat_notas_pesadas
        self.result.valor_total = valor_total

 
    def set_despesas(self) -> None:
        despesas = re.findall(
            r"(Pedágio|Café|Almoço|Abastecimento)\s+\$(\d+,\d+)",
            self.input_text,
        )

        for categoria, valor in despesas:
            valor_float = float(valor.replace(",", "."))
            self.result.despesas[categoria] = valor_float

    def set_ceps(self) -> None:
        match = re.search(
            r"Ceps\s+(?:do\s+)?(\d{3})\s+ao\s+(\d{3})",
            self.input_text,
            re.IGNORECASE,
        )

        if not match:
            self.result.ceps = ""
            return

        cep_start, cep_end = map(int, match.groups())

        self.result.ceps = ", ".join(str(c) for c in range(cep_start, cep_end + 1))

    def process(self) -> RomaneioData:
        self.set_data()
        self.set_ceps()
        self.set_notas_geral()
        self.set_notas_por_peso()
        self.set_faturamento_por_peso()
        self.set_valor_total()
        self.set_despesas()
        return self.result



class BuildDataFrames:
    def __init__(self, romaneio_data: RomaneioData):
        self.romaneio_data = romaneio_data

    def build_df_receitas(self) -> pd.DataFrame:
        data = {
            "DATA": [self.romaneio_data.data],
            "TOTAL_NOTAS": [self.romaneio_data.total_notas],
            "NOTAS_REALIZADAS": [self.romaneio_data.realizadas],
            "VALOR_TOTAL": [self.romaneio_data.valor_total],
            "CEPS": [self.romaneio_data.ceps],
            "CREATED_AT": [datetime.now().strftime("%Y-%m-%d")]
        }
        df_receitas = pd.DataFrame(data)
        return df_receitas
    
    def build_df_despesas(self) -> pd.DataFrame:
        despesas = self.romaneio_data.despesas
        data = {
            "DATA": [self.romaneio_data.data] * len(despesas),
            "CATEGORIA": list(despesas.keys()),
            "VALOR": list(despesas.values()),
            "CREATED_AT": [datetime.now().strftime("%Y-%m-%d")] * len(despesas)
        }
        df_despesas = pd.DataFrame(data)
        return df_despesas
    
    def build_df_peso_notas(self) -> pd.DataFrame:
        data = {
            "DATA": [self.romaneio_data.data],
            "NOTAS_LEVES": [self.romaneio_data.notas_leves],
            "NOTAS_PESADAS": [self.romaneio_data.notas_pesadas],
            "FAT_NOTA_LEVE": [self.romaneio_data.fat_notas_leves],
            "FAT_NOTA_PESADA": [self.romaneio_data.fat_notas_pesadas],
            "CREATED_AT": [datetime.now().strftime("%Y-%m-%d")]
        }
        df_peso_notas = pd.DataFrame(data)
        return df_peso_notas
    

def convert_types(df:pd.DataFrame, lista_datas: list) -> pd.DataFrame:
    for coluna in df.columns:
        if coluna in lista_datas:
            df[coluna] = pd.to_datetime(df[coluna], format="%Y-%m-%d")
        elif coluna == "VALOR" or coluna == "VALOR_TOTAL" or coluna.startswith("FAT_"):
            df[coluna] = df[coluna].astype(float)
        elif coluna.startswith("NOTAS") or coluna == "TOTAL_NOTAS" or coluna == "NOTAS_REALIZADAS":
            df[coluna] = df[coluna].astype(int)
    return df


def append_df_to_bq(
    client: bigquery.Client,
    df,
    table_id: str,
):
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )

    job = client.load_table_from_dataframe(
        df,
        table_id,
        job_config=job_config,
    )

    job.result()  # aguarda finalizar