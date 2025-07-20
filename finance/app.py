import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from PIL import Image
import base64

# Configuração da página
st.set_page_config(layout="wide", page_title="Análise Fundamentalista", page_icon="📊")

# CSS customizado
st.markdown("""
<style>
    .stApp {
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .metric-box {
        background-color: rgba(240, 242, 246, 0.9);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .positive {
        color: green;
        font-weight: bold;
    }
    .negative {
        color: red;
        font-weight: bold;
    }
    .header {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 5px;
        color: #1f77b4;
    }
    .dataframe {
        width: 100%;
    }
    .comparison-table {
        font-size: 0.9em;
    }
    .comparison-table th {
        background-color: #1f77b4;
        color: white;
        text-align: center;
    }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        return stock, info, hist
    except Exception as e:
        st.error(f"Erro ao buscar dados para {ticker}: {str(e)}")
        return None, None, None

def format_number(num):
    try:
        if pd.isna(num):
            return "-"
        if abs(num) >= 1e12:
            return f"{num/1e12:.2f}T"
        elif abs(num) >= 1e9:
            return f"{num/1e9:.2f}B"
        elif abs(num) >= 1e6:
            return f"{num/1e6:.2f}M"
        elif abs(num) >= 1e3:
            return f"{num/1e3:.2f}K"
        return f"{num:.2f}"
    except Exception as e:
        return "-"

def compare_stocks(tickers):
    comparison_data = []
    
    for ticker in tickers:
        try:
            stock, info, _ = get_stock_data(ticker)
            
            if not info or 'currentPrice' not in info:
                continue
                
            data = {
                "Ticker": ticker,
                "Nome": info.get('longName', ticker),
                "Preço Atual": info.get('currentPrice', info.get('regularMarketPrice', 0)),
                "Preço-Alvo": info.get('targetMeanPrice', None),
                "Potencial": ((info.get('targetMeanPrice', 0) - info.get('currentPrice', 1)) / info.get('currentPrice', 1)) * 100 if info.get('targetMeanPrice') else None,
                "P/L": info.get('trailingPE'),
                "P/VP": info.get('priceToBook'),
                "Dividend Yield": info.get('dividendYield', 0)*100 if info.get('dividendYield') else None,
                "ROE": info.get('returnOnEquity', 0)*100 if info.get('returnOnEquity') else None,
                "Margem Líq.": info.get('profitMargins', 0)*100 if info.get('profitMargins') else None,
                "Valor Mercado": info.get('marketCap')
            }
            comparison_data.append(data)
        except Exception as e:
            st.error(f"Erro ao processar {ticker}: {str(e)}")
            continue
    
    return pd.DataFrame(comparison_data)

# Interface principal
st.title("📊 Análise Fundamentalista")

# Abas para análise única ou comparação
tab_single, tab_compare = st.tabs(["Análise Individual", "Comparar Ações"])

with tab_single:
    ticker = st.text_input("Digite o ticker da ação (ex: AAPL, PETR4.SA):", "AAPL", key="single_ticker").upper()
    


    if ticker:
        try:
            stock, info, hist = get_stock_data(ticker)
            
            if not info or 'currentPrice' not in info:
                st.error("Ticker não encontrado ou dados indisponíveis")
                st.stop()
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                st.markdown(f"### {info.get('longName', ticker)}")
                st.markdown(f"**Setor:** {info.get('sector', '-')}")
                st.markdown(f"**Indústria:** {info.get('industry', '-')}")
                
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                previous_close = info.get('previousClose', current_price)
                change_percent = ((current_price - previous_close) / previous_close) * 100
                
                st.markdown("### Preço Atual")
                st.markdown(f"<h2 style='color: {'green' if change_percent >= 0 else 'red'}'>{current_price:.2f}</h2>", 
                           unsafe_allow_html=True)
                st.markdown(f"<span class={'positive' if change_percent >= 0 else 'negative'}>"
                           f"{change_percent:.2f}% ({current_price - previous_close:.2f})</span> vs fechamento anterior",
                           unsafe_allow_html=True)
                
                target_price = info.get('targetMeanPrice', None)
                if target_price:
                    potential = ((target_price - current_price) / current_price) * 100
                    st.markdown("### Preço-Alvo")
                    st.markdown(f"**Média dos Analistas:** {target_price:.2f}")
                    st.markdown(f"**Potencial:** <span class={'positive' if potential >= 0 else 'negative'}>"
                               f"{potential:.2f}%</span>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("### Valuation")
                
                valuation_data = {
                    "P/L": info.get('trailingPE'),
                    "P/VP": info.get('priceToBook'),
                    "EV/EBITDA": info.get('enterpriseToEbitda'),
                    "Dividend Yield": f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-",
                    "VP/ação": info.get('bookValue'),
                    "Lucro/ação": info.get('trailingEps')
                }
                
                for metric, value in valuation_data.items():
                    st.markdown(f"**{metric}:** {value if value else '-'}")
                
                market_cap = info.get('marketCap')
                st.markdown(f"**Valor de Mercado:** {format_number(market_cap) if market_cap else '-'}")
            
            with col3:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name='Preço'
                ))
                
                if target_price:
                    fig.add_hline(y=target_price, line_dash="dot", 
                                 annotation_text=f"Preço-Alvo: {target_price:.2f}", 
                                 line_color="green")
                
                fig.update_layout(
                    title=f"Histórico de Preços - {ticker}",
                    xaxis_rangeslider_visible=False,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("## Indicadores Financeiros")
            
            col4, col5, col6 = st.columns(3)
            
            with col4:
                st.markdown("### Endividamento")
                debt_data = {
                    "Div. Liq. / VP": info.get('debtToEquity'),
                    "Div. Liq. /EBITDA": info.get('debtToEbitda'),
                    "Liq. Corrente": info.get('currentRatio')
                }
                for metric, value in debt_data.items():
                    st.markdown(f"**{metric}:** {value if value else '-'}")
            
            with col5:
                st.markdown("### Eficiência")
                efficiency_data = {
                    "Margem Bruta": f"{info.get('grossMargins', 0)*100:.2f}%" if info.get('grossMargins') else "-",
                    "Margem EBITDA": f"{info.get('ebitdaMargins', 0)*100:.2f}%" if info.get('ebitdaMargins') else "-",
                    "Margem Líquida": f"{info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "-"
                }
                for metric, value in efficiency_data.items():
                    st.markdown(f"**{metric}:** {value}")
            
            with col6:
                st.markdown("### Rentabilidade")
                profitability_data = {
                    "ROE": f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "-",
                    "ROA": f"{info.get('returnOnAssets', 0)*100:.2f}%" if info.get('returnOnAssets') else "-",
                    "ROIC": f"{info.get('returnOnInvestedCapital', 0)*100:.2f}%" if info.get('returnOnInvestedCapital') else "-",
                    "Giro Ativos": info.get('assetTurnover')
                }
                for metric, value in profitability_data.items():
                    st.markdown(f"**{metric}:** {value}")
            
            st.markdown("---")
            st.markdown("## Dados Fundamentais Completos")
            
            try:
                tab1, tab2, tab3 = st.tabs(["DRE", "Balanço", "Fluxo de Caixa"])
                
                with tab1:
                    income_stmt = stock.financials
                    if not income_stmt.empty:
                        st.dataframe(income_stmt.style.format("${:,.0f}"))
                    else:
                        st.warning("Dados não disponíveis")
                
                with tab2:
                    balance_sheet = stock.balance_sheet
                    if not balance_sheet.empty:
                        st.dataframe(balance_sheet.style.format("${:,.0f}"))
                    else:
                        st.warning("Dados não disponíveis")
                
                with tab3:
                    cashflow = stock.cashflow
                    if not cashflow.empty:
                        st.dataframe(cashflow.style.format("${:,.0f}"))
                    else:
                        st.warning("Dados não disponíveis")
                        
            
            except Exception as e:
                st.error(f"Erro ao carregar dados fundamentais: {str(e)}")
        
        except Exception as e:
            st.error(f"Erro ao buscar dados para o ticker {ticker}: {str(e)}")

            

with tab_compare:
    st.markdown("### 🔍 Comparação entre Ações")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker1 = st.text_input("Ticker 1:", "AAPL").upper()
    with col2:
        ticker2 = st.text_input("Ticker 2:", "MSFT").upper()
    with col3:
        ticker3 = st.text_input("Ticker 3:", "GOOGL").upper()
    
    if st.button("Comparar"):
        tickers = [t for t in [ticker1, ticker2, ticker3] if t]
        
        if len(tickers) < 2:
            st.warning("Digite pelo menos 2 tickers para comparar")
        else:
            with st.spinner("Coletando dados..."):
                comparison_df = compare_stocks(tickers)
                
                if not comparison_df.empty:
                    formatted_df = comparison_df.copy()
                    formatted_df['Valor Mercado'] = formatted_df['Valor Mercado'].apply(format_number)
                    formatted_df['Potencial'] = formatted_df['Potencial'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "-")
                    
                    for col in ['Preço Atual', 'Preço-Alvo', 'P/L', 'P/VP', 'Dividend Yield', 'ROE', 'Margem Líq.']:
                        formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                    
                    st.markdown("#### Comparativo entre Ações")
                    st.dataframe(
                        formatted_df.set_index('Ticker').style.applymap(
                            lambda x: 'color: green' if '%' in str(x) and '-' not in str(x) and float(x.replace('%','')) > 0 
                            else ('color: red' if '%' in str(x) and '-' in str(x) else ''),
                            subset=['Potencial']
                        ),
                        use_container_width=True
                    )
                    
                    # Botão para baixar os dados
                    csv = formatted_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Baixar Dados da Comparação",
                        csv,
                        "comparacao_acoes.csv",
                        "text/csv",
                        key='download-comparison'
                    )
                    
                    fig_compare = go.Figure()
                    
                    for ticker in tickers:
                        try:
                            _, _, hist = get_stock_data(ticker)
                            fig_compare.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist['Close'],
                                name=ticker,
                                mode='lines'
                            ))
                        except:
                            continue
                    
                    fig_compare.update_layout(
                        title="Comparação de Preços (12 meses)",
                        xaxis_title="Data",
                        yaxis_title="Preço (USD)",
                        height=400
                    )
                    st.plotly_chart(fig_compare, use_container_width=True)
                else:
                    st.error("Não foi possível obter dados para comparação")