import sys
import os
root_path = os.path.abspath("..")
sys.path.append(root_path)

from queries.get_data import BusinessData
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


class VizReceitas:
    def __init__(self):
        self.reload_data()


    def reload_data(self):
        business_data = BusinessData()
        self.dados_receitas = business_data.get_receitas()
        self.dados_despesas = business_data.get_despesas()
        self.dados_peso = business_data.get_peso_notas()
        # garantir tipos
        self.dados_receitas['DATA'] = pd.to_datetime(self.dados_receitas['DATA'])
        if 'DATA' in self.dados_despesas.columns:
            self.dados_despesas['DATA'] = pd.to_datetime(self.dados_despesas['DATA'])
        self.dados_peso['DATA'] = pd.to_datetime(self.dados_peso['DATA'])

        self.last_update = datetime.now() - timedelta(hours=3)
        
    def set_title(self):
        st.set_page_config(page_title="Dashboard Financeiro", layout="wide", initial_sidebar_state="expanded")
        
        # Header com estilo
        st.markdown("""
            <style>
            .main-header {
                font-size: 3rem;
                font-weight: 700;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 10px;
                color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-header">📊 Dashboard Financeiro</h1>', unsafe_allow_html=True)
        st.markdown("---")

    def show_kpis(self):
        """Exibe KPIs principais"""
        # Preparar dados
        df_rec = self.dados_receitas.copy()
        df_desp = self.dados_despesas.copy()
        
        # Filtro de período
        col1, col2, col3 = st.columns([2, 2, 6])
        with col1:
            periodo = st.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todo período"])
        
        # Aplicar filtro
        hoje = pd.Timestamp.now()
        if periodo == "Últimos 7 dias":
            data_inicio = hoje - timedelta(days=7)
        elif periodo == "Últimos 30 dias":
            data_inicio = hoje - timedelta(days=30)
        elif periodo == "Últimos 90 dias":
            data_inicio = hoje - timedelta(days=90)
        else:
            data_inicio = df_rec['DATA'].min()
        
        df_rec_filtrado = df_rec[df_rec['DATA'] >= data_inicio]
        df_desp_filtrado = df_desp[df_desp['DATA'] >= data_inicio] if 'DATA' in df_desp.columns else df_desp
        
        # Calcular métricas
        total_receitas = df_rec_filtrado['VALOR_TOTAL'].sum()
        total_despesas = df_desp_filtrado['VALOR'].sum() if 'VALOR' in df_desp_filtrado.columns else 0
        lucro = total_receitas - total_despesas
        total_notas = df_rec_filtrado['NOTAS_REALIZADAS'].sum()
        ticket_medio = total_receitas / total_notas if total_notas > 0 else 0
        
        # Exibir KPIs
        st.markdown("### 📈 Indicadores Principais")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Receita Total",
                value=f"R$ {total_receitas:,.2f}",
                delta=f"{(total_receitas/1000000):.1f}M" if total_receitas > 1000000 else None
            )
        
        with col2:
            st.metric(
                label="💸 Despesas",
                value=f"R$ {total_despesas:,.2f}",
                delta=f"-{(total_despesas/total_receitas*100):.1f}%" if total_receitas > 0 else None,
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                label="📊 Lucro Líquido",
                value=f"R$ {lucro:,.2f}",
                delta=f"{(lucro/total_receitas*100):.1f}% margem" if total_receitas > 0 else None
            )
        
        with col4:
            st.metric(
                label="🎯 Ticket Médio",
                value=f"R$ {ticket_medio:,.2f}",
                delta=f"{total_notas:.0f} notas"
            )
        
        st.markdown("---")

    def show_receitas_evolution(self):
        """Gráfico de evolução de receitas"""
        df = self.dados_receitas.copy()
        df = df.sort_values('DATA')
        
        col1, col2 = st.columns([7, 3])
        
        with col1:
            st.markdown("### 📈 Evolução das Receitas")
            
            # Gráfico de linha com área
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['DATA'],
                y=df['VALOR_TOTAL'],
                mode='lines+markers+text',
                name='Receita',
                fill='tozeroy',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#764ba2'),
                text=[f'R$ {val:,.2f}' for val in df['VALOR_TOTAL']],
                textposition='top center',
                textfont=dict(size=10, color="#F2ECEC")
            ))
            
            fig.update_layout(
                height=400,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', title='Valor (R$)'),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Estatísticas")
            
            receita_media = df['VALOR_TOTAL'].mean()
            receita_max = df['VALOR_TOTAL'].max()
            receita_min = df['VALOR_TOTAL'].min()
            
            st.metric("Média Diária", f"R$ {receita_media:,.2f}")
            st.metric("Maior Receita", f"R$ {receita_max:,.2f}")
            st.metric("Menor Receita", f"R$ {receita_min:,.2f}")
            
            # Taxa de crescimento
            if len(df) > 1:
                crescimento = ((df['VALOR_TOTAL'].iloc[-1] / df['VALOR_TOTAL'].iloc[0]) - 1) * 100
                st.metric("Crescimento", f"{crescimento:+.1f}%")

    def show_notas_analysis(self):
        """Análise de notas leves vs pesadas"""
        df = self.dados_peso.copy()
        
        st.markdown("### ⚖️ Análise de Peso das Notas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza
            total_leves = df['NOTAS_LEVES'].sum()
            total_pesadas = df['NOTAS_PESADAS'].sum()
            
            fig = go.Figure(data=[go.Pie(
                labels=['Notas Leves', 'Notas Pesadas'],
                values=[total_leves, total_pesadas],
                hole=0.4,
                marker=dict(colors=['#667eea', '#764ba2']),
                textinfo='label+percent+value',
                textfont=dict(size=14)
            )])
            
            fig.update_layout(
                height=350,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Evolução temporal
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df['DATA'],
                y=df['NOTAS_LEVES'],
                name='Leves',
                marker_color='#667eea'
            ))
            
            fig.add_trace(go.Bar(
                x=df['DATA'],
                y=df['NOTAS_PESADAS'],
                name='Pesadas',
                marker_color='#764ba2'
            ))
            
            fig.update_layout(
                height=350,
                barmode='stack',
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', title='Quantidade'),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    def show_faturamento_analysis(self):
        """Análise de faturamento por tipo de nota"""
        df = self.dados_peso.copy()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💵 Faturamento por Tipo")
            
            # Calcular totais
            fat_leve_total = df['FAT_NOTA_LEVE'].sum()
            fat_pesada_total = df['FAT_NOTA_PESADA'].sum()
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Notas Leves', 'Notas Pesadas'],
                y=[fat_leve_total, fat_pesada_total],
                marker=dict(
                    color=['#667eea', '#764ba2'],
                    line=dict(color='white', width=2)
                ),
                text=[f'R$ {fat_leve_total:,.0f}', f'R$ {fat_pesada_total:,.0f}'],
                textposition='outside',
                textfont=dict(size=12)
            ))
            
            # Ajustar range do eixo Y para dar espaço aos rótulos
            y_max = max(fat_leve_total, fat_pesada_total) * 1.25
            
            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(128,128,128,0.2)', 
                    title='Faturamento (R$)',
                    range=[0, y_max]
                ),
                margin=dict(t=50, b=40, l=60, r=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Ticket Médio por Tipo")
            
            # Calcular tickets médios
            ticket_leve = fat_leve_total / df['NOTAS_LEVES'].sum() if df['NOTAS_LEVES'].sum() > 0 else 0
            ticket_pesada = fat_pesada_total / df['NOTAS_PESADAS'].sum() if df['NOTAS_PESADAS'].sum() > 0 else 0
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Ticket Médio Leve', 'Ticket Médio Pesada'],
                y=[ticket_leve, ticket_pesada],
                marker=dict(
                    color=['#667eea', '#764ba2'],
                    line=dict(color='white', width=2)
                ),
                text=[f'R$ {ticket_leve:,.2f}', f'R$ {ticket_pesada:,.2f}'],
                textposition='outside',
                textfont=dict(size=12)
            ))
            
            # Ajustar range do eixo Y para dar espaço aos rótulos
            y_max = max(ticket_leve, ticket_pesada) * 1.25
            
            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(128,128,128,0.2)', 
                    title='Valor (R$)',
                    range=[0, y_max]
                ),
                margin=dict(t=50, b=40, l=60, r=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)

    def show_despesas_breakdown(self):
        """Análise de despesas"""
        df = self.dados_despesas.copy()
        
        if 'CATEGORIA' in df.columns or 'TIPO' in df.columns:
            st.markdown("### 💸 Breakdown de Despesas")
            
            col1, col2 = st.columns(2)
            
            categoria_col = 'CATEGORIA' if 'CATEGORIA' in df.columns else 'TIPO'
            
            with col1:
                # Despesas por categoria
                despesas_cat = df.groupby(categoria_col)['VALOR'].sum().reset_index()
                despesas_cat = despesas_cat.sort_values('VALOR', ascending=False)
                
                fig = px.bar(
                    despesas_cat,
                    x=categoria_col,
                    y='VALOR',
                    color='VALOR',
                    color_continuous_scale=['#667eea', '#764ba2'],
                    title='Despesas por Categoria',
                    text='VALOR'
                )
                
                fig.update_traces(
                    texttemplate='R$ %{text:,.0f}',
                    textposition='outside',
                    textfont=dict(size=12)
                )
                
                # Ajustar range do eixo Y para dar espaço aos rótulos
                y_max = despesas_cat['VALOR'].max() * 1.25
                
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False),
                    yaxis=dict(
                        showgrid=True, 
                        gridcolor='rgba(128,128,128,0.2)', 
                        title='Valor (R$)',
                        range=[0, y_max]
                    ),
                    margin=dict(t=60, b=40, l=60, r=40)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Top 5 maiores despesas
                st.markdown("#### 🔝 Top 5 Maiores Despesas")
                top_despesas = df.nlargest(5, 'VALOR')[[categoria_col, 'VALOR', 'DATA']]
                top_despesas['DATA'] = top_despesas['DATA'].dt.strftime('%Y-%m-%d')
                
                for idx, row in top_despesas.iterrows():
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%); 
                                padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;'>
                        <b>{row[categoria_col]}</b><br>
                        💰 R$ {row['VALOR']:,.2f} • 📅 {row['DATA']}
                    </div>
                    """, unsafe_allow_html=True)

    def show_data_table(self):
        """Exibe tabelas de dados"""
        st.markdown("### 📋 Dados Detalhados")
        
        tab1, tab2, tab3 = st.tabs(["💰 Receitas", "💸 Despesas", "⚖️ Peso das Notas"])
        
        with tab1:
            df_to_show_receitas = self.dados_receitas.copy()
            df_to_show_receitas['DATA'] = df_to_show_receitas['DATA'].dt.strftime('%Y-%m-%d')
            st.dataframe(
                df_to_show_receitas.sort_values('DATA', ascending=False),
                use_container_width=True,
                height=400
            )
            
        with tab2:
            df_to_show_despesas = self.dados_despesas.copy()
            df_to_show_despesas['DATA'] = df_to_show_despesas['DATA'].dt.strftime('%Y-%m-%d')
            st.dataframe(
                df_to_show_despesas.sort_values('DATA', ascending=False) if 'DATA' in df_to_show_despesas.columns else df_to_show_despesas,
                use_container_width=True,
                height=400
            )
            
        with tab3:
            df_to_show_peso_notas = self.dados_peso.copy()
            df_to_show_peso_notas['DATA'] = df_to_show_peso_notas['DATA'].dt.strftime('%Y-%m-%d')
            st.dataframe(
                df_to_show_peso_notas.sort_values('DATA', ascending=False),
                use_container_width=True,
                height=400
            )

    def render(self):
        """Renderiza todo o dashboard"""
        self.set_title()
        if st.button("🔄 Atualizar dados"):
            st.cache_data.clear()
            st.cache_resource.clear()
            with st.spinner("Carregando dados do banco..."):
                self.reload_data()
            st.success("Dados atualizados com sucesso!")
            st.rerun()

        self.show_kpis()
        self.show_receitas_evolution()
        self.show_notas_analysis()
        self.show_faturamento_analysis()
        self.show_despesas_breakdown()
        st.markdown("---")
        self.show_data_table()
        st.markdown(
    f"🕒 **Última atualização:** {self.last_update.strftime('%d/%m/%Y %H:%M:%S')}")
