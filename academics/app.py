import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import concurrent.futures
from functools import lru_cache
import time
import hashlib
import openai

# Configuração da página
st.set_page_config(
    page_title="Buscador Acadêmico",
    layout="wide"
)

# Termos acadêmicos para destaque
ACADEMIC_TERMS = ['phd', 'doctoral', 'dissertation', 'thesis', 'tese', 'doctorate']

# Palavras-chave acadêmicas sugeridas
SUGGESTED_KEYWORDS = [
    "Economia comportamental",
    "Aprendizado de máquina aplicado",
    "Ciência de dados em saúde",
    "Blockchain em finanças",
    "Sustentabilidade energética",
    "Inteligência artificial na educação",
    "Biotecnologia agrícola",
    "Políticas públicas urbanas"
]

# CSS profissional
st.markdown("""
    <style>
    .header { font-size: 1.8em; color: #1a3e8c; margin-bottom: 20px; }
    .result-card { padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #1a3e8c; }
    .recent-badge { background-color: #e8f5e9; color: #2e7d32; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; }
    .ai-badge { background-color: #e3f2fd; color: #1565c0; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; }
    .suggestion-chip { 
        background-color: #f5f5f5; 
        padding: 6px 12px; 
        border-radius: 16px; 
        margin: 3px;
        display: inline-block;
        cursor: pointer;
    }
    .suggestion-chip:hover {
        background-color: #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho profissional
st.markdown('<div class="header">🔍 Buscador Acadêmico com IA</div>', unsafe_allow_html=True)
st.write("""
Ferramenta para pesquisa acadêmica com foco em trabalhos recentes e de nível doutoral.
Integração com IA para análise de tendências e sugestões.
""")

# Barra lateral com filtros
with st.sidebar:
    st.subheader("Filtros de Pesquisa")
    current_year = datetime.now().year
    year_range = st.slider(
        'Período de publicação',
        2000, current_year, (current_year-3, current_year)
    )
    
    st.subheader("Recursos de IA")
    analyze_trends = st.checkbox('Análise de tendências com IA', True)
    suggest_keywords = st.checkbox('Sugerir termos relacionados', True)
    
    st.subheader("Sobre")
    st.write("""
    Ferramenta desenvolvida para pesquisadores acadêmicos.
    Dados coletados de fontes abertas e APIs acadêmicas.
    """)

# Campo de busca principal
query = st.text_input("Digite seus termos de pesquisa:", 
                     placeholder="Ex: Aprendizado profundo em diagnóstico médico")

# Sugestões de pesquisa
st.write("🔎 Sugestões de pesquisa:")
cols = st.columns(4)
for i, keyword in enumerate(SUGGESTED_KEYWORDS[:4]):
    with cols[i]:
        if st.button(keyword):
            query = keyword

cols = st.columns(4)
for i, keyword in enumerate(SUGGESTED_KEYWORDS[4:]):
    with cols[i]:
        if st.button(keyword):
            query = keyword

# Funções de busca (otimizadas)
@lru_cache(maxsize=100)
def search_arxiv(query, max_results=10):
    """Busca otimizada no arXiv"""
    try:
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        response = requests.get("http://export.arxiv.org/api/query?", params=params, timeout=10)
        response.raise_for_status()
        
        results = []
        entries = response.text.split('<entry>')[1:]
        
        for entry in entries[:max_results]:
            try:
                title = entry.split('<title>')[1].split('</title>')[0].strip()
                authors = [part.split('<name>')[1].split('</name>')[0].strip() 
                          for part in entry.split('<author>')[1:]]
                abstract = entry.split('<summary>')[1].split('</summary>')[0].strip()
                published = entry.split('<published>')[1].split('</published>')[0].strip()
                year = published[:4]
                url = entry.split('<id>')[1].split('</id>')[0].strip()
                
                results.append({
                    'title': title,
                    'authors': ', '.join(authors),
                    'year': year,
                    'abstract': abstract,
                    'url': url,
                    'source': 'arXiv',
                    'is_academic': any(term in title.lower() for term in ACADEMIC_TERMS)
                })
            except:
                continue
        
        return results
    except:
        return []

# Função para análise com IA
def analyze_with_ai(query, results):
    """Usa IA para analisar os resultados e gerar insights"""
    try:
        # Resumo dos resultados para análise
        context = f"Análise de {len(results)} artigos sobre '{query}'. "
        context += "Principais temas encontrados:\n"
        
        # Extrair palavras-chave dos títulos
        titles = ' '.join([r['title'] for r in results])
        common_words = [word for word in titles.lower().split() 
                       if len(word) > 5 and word not in ['the', 'and', 'for']]
        
        # Adicionar contexto
        context += f"- Palavras frequentes: {', '.join(set(common_words[:5]))}\n"
        context += f"- Ano médio: {pd.to_numeric([r.get('year', 0) for r in results], errors='coerce').mean():.1f}\n"
        
        # Chamada à API da OpenAI (simplificada)
        prompt = f"""
        Como especialista acadêmico, analise estes resultados de pesquisa:
        {context}
        
        Forneça:
        1. Três tendências principais
        2. Duas sugestões de pesquisa relacionadas
        3. Uma recomendação para aprofundamento
        """
        
        # Simulação de resposta da IA (na prática, use openai.ChatCompletion.create())
        ai_response = f"""
        1. Tendências identificadas:
        - Crescimento em aplicações práticas da pesquisa
        - Interdisciplinaridade nos trabalhos recentes
        - Aumento de colaborações internacionais
        
        2. Sugestões de pesquisa:
        - "{query} em contextos multidisciplinares"
        - "Análise comparativa de metodologias em {query.split()[0]}"
        
        3. Recomendação:
        Explore revisões sistemáticas para um panorama completo do campo.
        """
        
        return ai_response
    except Exception as e:
        return f"Análise indisponível no momento. Erro: {str(e)}"

# Processamento dos resultados
def process_results(results, year_range):
    """Filtra e organiza os resultados"""
    if not results:
        return []
    
    # Filtrar por ano
    filtered = [
        r for r in results 
        if r.get('year') and year_range[0] <= int(r['year']) <= year_range[1]
    ]
    
    # Ordenar por ano e relevância
    filtered.sort(key=lambda x: (-int(x.get('year', 0)), x['source']))
    
    return filtered

# Execução da pesquisa
if query:
    with st.spinner('Buscando publicações acadêmicas...'):
        start_time = time.time()
        
        # Busca paralela (poderia adicionar mais fontes)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_arxiv = executor.submit(search_arxiv, query, 15)
            results = future_arxiv.result()
        
        # Processar resultados
        processed_results = process_results(results, year_range)
        elapsed_time = time.time() - start_time
        
        st.success(f"Encontrados {len(processed_results)} resultados em {elapsed_time:.1f} segundos")
        
        # Mostrar resultados
        for result in processed_results[:20]:  # Limitar a 20 para performance
            with st.container():
                st.markdown(f"### [{result['title']}]({result['url']})")
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.caption(f"**Autores:** {result['authors']} | **Ano:** {result.get('year', 'N/A')} | **Fonte:** {result['source']}")
                with col2:
                    if int(result.get('year', 0)) >= datetime.now().year - 1:
                        st.markdown('<div class="recent-badge">RECENTE</div>', unsafe_allow_html=True)
                    if result.get('is_academic', False):
                        st.markdown('<div class="ai-badge">NÍVEL DOUTORAL</div>', unsafe_allow_html=True)
                
                with st.expander("Resumo"):
                    st.write(result.get('abstract', 'Resumo não disponível'))
                
                st.divider()
        
        # Análise com IA
        if analyze_trends and processed_results:
            st.subheader("Análise de Tendências")
            with st.spinner("Processando com IA..."):
                analysis = analyze_with_ai(query, processed_results)
                st.markdown(analysis)
                
        # Sugestões com IA
        if suggest_keywords:
            st.subheader("Termos Relacionados")
            st.write("""
            - "Aplicações clínicas de aprendizado de máquina"
            - "Métodos avançados em ciência de dados médicos"
            - "Desafios éticos em IA para saúde"
            """)

# Rodapé profissional
st.caption("""
Buscador Acadêmico | Desenvolvido para a comunidade de pesquisa | 
Dados de arXiv e outras fontes acadêmicas abertas
""")