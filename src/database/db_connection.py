import os
import json
import tempfile
from google.cloud import bigquery
from dotenv import load_dotenv
import streamlit as st

def get_bigquery_client():
    # Tenta carregar do Streamlit Secrets primeiro (produção)
    if hasattr(st, 'secrets') and 'PROJECT_ID' in st.secrets:
        project_id = st.secrets["PROJECT_ID"]
        
        # Cria arquivo temporário com as credenciais JSON
        credentials_json = json.loads(st.secrets["SECRET_JSON"])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(credentials_json, temp_file)
            temp_path = temp_file.name
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
        client = bigquery.Client(project=project_id)
        
        return client
    
    # Fallback para .env local (desenvolvimento)
    else:
        load_dotenv()
        
        project_id = os.getenv("PROJECT_ID")
        secret_path = os.getenv("SECRET_PATH")
        
        if not project_id:
            raise ValueError("PROJECT_ID não encontrado")
        
        if not secret_path or not os.path.exists(secret_path):
            raise ValueError("SECRET_PATH inválido ou arquivo não encontrado")
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = secret_path
        client = bigquery.Client(project=project_id)
        
        return client