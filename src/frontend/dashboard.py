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
        # default period
        self.periodo = "Todo período"
        # filtered frames will be criados quando apply_period_filter for chamado

    def set_title(self):
        st.set_page_config(page_title="Dashboard Financeiro", layout="wide", initial_sidebar_state="expanded")
        
        st.markdown("""
            <style>
            .main-header {
                font-size: 3rem;
                font-weight: 700;
                background: linear-gradient(90deg, #4caf50 0%, #2e7d32 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }
            .metric-card {
                background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%);
                padding: 1.5rem;
                border-radius: 10px;
                color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<h1 class="main-header">📊 Dashboard Financeiro</h1>', unsafe_allow_html=True)
        st.markdown("---")


    def apply_period_filter(self):
        """Aplica o filtro de período e popula atributos filtrados:
        self.df_rec_filtrado, self.df_desp_filtrado, self.df_peso_filtrado
        """
        hoje = pd.Timestamp.now()
        if self.periodo == "Últimos 7 dias":
            data_inicio = hoje - timedelta(days=7)
        elif self.periodo == 'Últimos 3 dias':
            data_inicio = hoje - timedelta(days=3)
        elif self.periodo == 'Últimos 14 dias':
            data_inicio = hoje - timedelta(days=14)
        elif self.periodo == "Últimos 30 dias":
            data_inicio = hoje - timedelta(days=30)
        elif self.periodo == "Últimos 90 dias":
            data_inicio = hoje - timedelta(days=90)
        else:
            data_inicio = self.dados_receitas['DATA'].min()

        # Receitas
        df_rec = self.dados_receitas.copy()
        self.df_rec_filtrado = df_rec[df_rec['DATA'] >= data_inicio].copy() if not df_rec.empty else df_rec

        # Despesas
        if hasattr(self, 'dados_despesas') and 'DATA' in self.dados_despesas.columns:
            df_desp = self.dados_despesas.copy()
            self.df_desp_filtrado = df_desp[df_desp['DATA'] >= data_inicio].copy()
        else:
            # fallback: keep original
            self.df_desp_filtrado = self.dados_despesas.copy()

        # Peso das notas
        df_peso = self.dados_peso.copy()
        self.df_peso_filtrado = df_peso[df_peso['DATA'] >= data_inicio].copy() if not df_peso.empty else df_peso

    def show_kpis(self):
        """Exibe KPIs principais"""
        # Usar frames filtrados (se existirem)
        df_rec = getattr(self, 'df_rec_filtrado', self.dados_receitas).copy()
        df_desp = getattr(self, 'df_desp_filtrado', self.dados_despesas).copy()
        
        # Calcular métricas
        total_receitas = df_rec['VALOR_TOTAL'].sum()
        total_despesas = df_desp['VALOR'].sum() if 'VALOR' in df_desp.columns else 0
        lucro = total_receitas - total_despesas
        total_notas = df_rec['NOTAS_REALIZADAS'].sum() if 'NOTAS_REALIZADAS' in df_rec.columns else 0
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
        """Gráfico de evolução das receitas"""
        df = getattr(self, 'df_rec_filtrado', self.dados_receitas).copy()

        # garantir DATA como datetime (importante para range/padding)
        df['DATA'] = pd.to_datetime(df['DATA'])
        df = df.sort_values('DATA')

        # cálculo de padding no eixo X para evitar corte do último ponto
        min_dt = df['DATA'].min()
        max_dt = df['DATA'].max()
        pad = pd.Timedelta(days=1)  # ajuste se precisar de mais/menos espaço
        x_range = [min_dt - pad, max_dt + pad]

        col1, col2 = st.columns([8, 2])

        with col1:
            st.markdown("### 📈 Evolução das Receitas")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df['DATA'],
                y=df['VALOR_TOTAL'],
                mode='lines+markers+text',
                name='Receita',
                fill='tozeroy',
                line=dict(color="#66ea73", width=3),
                marker=dict(size=8, color="#14c72f"),
                text=[f'R$ {val:,.2f}' for val in df['VALOR_TOTAL']],
                textposition='top center',
                textfont=dict(size=10, color="#F2ECEC"),
                hovertemplate='Data: %{x|%d/%m/%Y}<br>Receita: R$ %{y:,.2f}<extra></extra>',
                cliponaxis=False  # importante para não cortar os textos fora do plot
            ))

            # forçar range com padding, formato de tick e margens maiores
            fig.update_xaxes(
                tickformat='%d/%m/%Y',
                range=x_range,
                tickangle=0,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            )

            fig.update_layout(
                height=400,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', title='Valor (R$)'),
                showlegend=False,
                autosize=True,
                margin=dict(l=60, r=80, t=40, b=60)  # r aumentado para evitar corte pelo painel de estatísticas
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 📊 Estatísticas")

            receita_media = df['VALOR_TOTAL'].mean() if not df.empty else 0
            receita_max = df['VALOR_TOTAL'].max() if not df.empty else 0
            receita_min = df['VALOR_TOTAL'].min() if not df.empty else 0

            st.metric("Média Diária", f"R$ {receita_media:,.2f}")
            st.metric("Maior Receita", f"R$ {receita_max:,.2f}")
            st.metric("Menor Receita", f"R$ {receita_min:,.2f}")

            if len(df) > 1 and df['VALOR_TOTAL'].iloc[0] != 0:
                crescimento = ((df['VALOR_TOTAL'].iloc[-1] / df['VALOR_TOTAL'].iloc[0]) - 1) * 100
                st.metric("Crescimento", f"{crescimento:+.1f}%")


    def show_despesas_evolution(self):
        """Gráfico de evolução das receitas"""
        df = getattr(self, 'df_desp_filtrado', self.dados_despesas).copy()

        df = df.groupby("DATA")["VALOR"].sum().reset_index()

        # garantir DATA como datetime (importante para range/padding)
        df['DATA'] = pd.to_datetime(df['DATA'])
        df = df.sort_values('DATA')

        # cálculo de padding no eixo X para evitar corte do último ponto
        min_dt = df['DATA'].min()
        max_dt = df['DATA'].max()
        pad = pd.Timedelta(days=1)  # ajuste se precisar de mais/menos espaço
        x_range = [min_dt - pad, max_dt + pad]

        col1, col2 = st.columns([8, 2])

        with col1:
            st.markdown("### 📉 Evolução das Despesas")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df['DATA'],
                y=df['VALOR'],
                mode='lines+markers+text',
                name='Despesa',
                fill='tozeroy',
                line=dict(color="#ea6a66", width=3),
                marker=dict(size=8, color="#c72914"),
                text=[f'R$ {val:,.2f}' for val in df['VALOR']],
                textposition='top center',
                textfont=dict(size=10, color="#F2ECEC"),
                hovertemplate='Data: %{x|%d/%m/%Y}<br>Despesa: R$ %{y:,.2f}<extra></extra>',
                cliponaxis=False  # importante para não cortar os textos fora do plot
            ))

            # forçar range com padding, formato de tick e margens maiores
            fig.update_xaxes(
                tickformat='%d/%m/%Y',
                range=x_range,
                tickangle=0,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            )

            fig.update_layout(
                height=400,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', title='Valor (R$)'),
                showlegend=False,
                autosize=True,
                margin=dict(l=60, r=80, t=40, b=60)  # r aumentado para evitar corte pelo painel de estatísticas
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 📊 Estatísticas")

            despesa_media = df['VALOR'].mean() if not df.empty else 0
            despesa_max = df['VALOR'].max() if not df.empty else 0
            despesa_min = df['VALOR'].min() if not df.empty else 0

            st.metric("Média Diária", f"R$ {despesa_media:,.2f}")
            st.metric("Maior Despesa", f"R$ {despesa_max:,.2f}")
            st.metric("Menor Despesa", f"R$ {despesa_min:,.2f}")

            if len(df) > 1 and df['VALOR'].iloc[0] != 0:
                crescimento = ((df['VALOR'].iloc[-1] / df['VALOR'].iloc[0]) - 1) * 100
                st.metric("Crescimento", f"{crescimento:+.1f}%")


    def show_notas_analysis(self):
        """Análise de notas leves vs pesadas"""
        df = getattr(self, 'df_peso_filtrado', self.dados_peso).copy()
        
        st.markdown("### ⚖️ Análise de Peso das Notas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza
            total_leves = df['NOTAS_LEVES'].sum() if 'NOTAS_LEVES' in df.columns else 0
            total_pesadas = df['NOTAS_PESADAS'].sum() if 'NOTAS_PESADAS' in df.columns else 0
            
            fig = go.Figure(data=[go.Pie(
                labels=['Notas Leves', 'Notas Pesadas'],
                values=[total_leves, total_pesadas],
                hole=0.4,
                marker=dict(colors=['#FFFFFF', '#413F3F']),
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
                marker_color="#FFFFFF",
                text=df['NOTAS_LEVES'],        # Rótulos
                textposition='inside'          # Pode ser 'outside', 'auto', 'inside'
            ))
            
            fig.add_trace(go.Bar(
                x=df['DATA'],
                y=df['NOTAS_PESADAS'],
                name='Pesadas',
                marker_color="#413F3F",
                text=df['NOTAS_PESADAS'],      # Rótulos
                textposition='inside'
            ))
            
            fig.update_layout(
                height=350,
                barmode='stack',
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, tickangle=-45, tickmode='auto'),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', title='Quantidade'),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.28,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(t=20, b=90, l=40, r=20)  # espaço extra embaixo pro legend
            )
            
            st.plotly_chart(fig, use_container_width=True)

    def show_faturamento_analysis(self):
        """Análise de faturamento por tipo de nota"""
        df = getattr(self, 'df_peso_filtrado', self.dados_peso).copy()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💵 Faturamento por Tipo")
            
            # Calcular totais
            fat_leve_total = df['FAT_NOTA_LEVE'].sum() if 'FAT_NOTA_LEVE' in df.columns else 0
            fat_pesada_total = df['FAT_NOTA_PESADA'].sum() if 'FAT_NOTA_PESADA' in df.columns else 0
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Notas Leves', 'Notas Pesadas'],
                y=[fat_leve_total, fat_pesada_total],
                marker=dict(
                    color=["#d4d6de", "#363537"],
                    line=dict(color='white', width=2)
                ),
                text=[f'R$ {fat_leve_total:,.0f}', f'R$ {fat_pesada_total:,.0f}'],
                textposition='outside',
                textfont=dict(size=12)
            ))
            
            # Ajustar range do eixo Y para dar espaço aos rótulos
            y_max = max(fat_leve_total, fat_pesada_total) * 1.25 if max(fat_leve_total, fat_pesada_total) > 0 else 1
            
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
            ticket_leve = fat_leve_total / df['NOTAS_LEVES'].sum() if 'NOTAS_LEVES' in df.columns and df['NOTAS_LEVES'].sum() > 0 else 0
            ticket_pesada = fat_pesada_total / df['NOTAS_PESADAS'].sum() if 'NOTAS_PESADAS' in df.columns and df['NOTAS_PESADAS'].sum() > 0 else 0
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Ticket Médio Leve', 'Ticket Médio Pesada'],
                y=[ticket_leve, ticket_pesada],
                marker=dict(
                    color=['#d4d6de', '#363537'],
                    line=dict(color='white', width=2)
                ),
                text=[f'R$ {ticket_leve:,.2f}', f'R$ {ticket_pesada:,.2f}'],
                textposition='outside',
                textfont=dict(size=12)
            ))
            
            # Ajustar range do eixo Y para dar espaço aos rótulos
            y_max = max(ticket_leve, ticket_pesada) * 1.25 if max(ticket_leve, ticket_pesada) > 0 else 1
            
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
        df = getattr(self, 'df_desp_filtrado', self.dados_despesas).copy()
        
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
                    color_continuous_scale=["#df9898", "#a24b4b"],
                    title='Despesas por Categoria',
                    text='VALOR'
                )
                
                fig.update_traces(
                    texttemplate='R$ %{text:,.0f}',
                    textposition='outside',
                    textfont=dict(size=12)
                )
                
                # Ajustar range do eixo Y para dar espaço aos rótulos
                y_max = despesas_cat['VALOR'].max() * 1.25 if despesas_cat['VALOR'].max() > 0 else 1
                
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
                top_despesas['DATA'] = pd.to_datetime(top_despesas['DATA']).dt.strftime('%Y-%m-%d')
                
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
            df_to_show_receitas = getattr(self, 'df_rec_filtrado', self.dados_receitas).copy()
            df_to_show_receitas['DATA'] = pd.to_datetime(df_to_show_receitas['DATA']).dt.strftime('%Y-%m-%d')
            st.dataframe(
                df_to_show_receitas.sort_values('DATA', ascending=False),
                use_container_width=True,
                height=400
            )
            
        with tab2:
            df_to_show_despesas = getattr(self, 'df_desp_filtrado', self.dados_despesas).copy()
            if 'DATA' in df_to_show_despesas.columns:
                df_to_show_despesas['DATA'] = pd.to_datetime(df_to_show_despesas['DATA']).dt.strftime('%Y-%m-%d')
            st.dataframe(
                df_to_show_despesas.sort_values('DATA', ascending=False) if 'DATA' in df_to_show_despesas.columns else df_to_show_despesas,
                use_container_width=True,
                height=400
            )
            
        with tab3:
            df_to_show_peso_notas = getattr(self, 'df_peso_filtrado', self.dados_peso).copy()
            df_to_show_peso_notas['DATA'] = pd.to_datetime(df_to_show_peso_notas['DATA']).dt.strftime('%Y-%m-%d')
            st.dataframe(
                df_to_show_peso_notas.sort_values('DATA', ascending=False),
                use_container_width=True,
                height=400
            )

    def render(self):
        """Renderiza todo o dashboard"""
        self.set_title()

        # Período global agora no topo — afeta todas as visões
        col1, col2, col3 = st.columns([2, 2, 6])
        with col1:
            self.periodo = st.selectbox("Período", ["Últimos 3 dias","Últimos 7 dias", "Últimos 14 dias","Últimos 30 dias", "Últimos 90 dias", "Todo período"], key="global_periodo")

        # aplicar filtro global
        self.apply_period_filter()

        if st.button("🔄 Atualizar dados"):
            st.cache_data.clear()
            st.cache_resource.clear()
            with st.spinner("Carregando dados do banco..."):
                self.reload_data()
                # reaplicar filtro após recarregar dados
                self.apply_period_filter()
            st.success("Dados atualizados com sucesso!")
            st.rerun()

        self.show_kpis()
        
        self.show_receitas_evolution()
        self.show_despesas_evolution()
        self.show_despesas_breakdown()
    
        self.show_faturamento_analysis()
        self.show_notas_analysis()
     
        st.markdown("---")
        self.show_data_table()
        st.markdown(
    f"🕒 **Última atualização:** {self.last_update.strftime('%d/%m/%Y %H:%M:%S')}")


