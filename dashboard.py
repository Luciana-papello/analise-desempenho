import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard RH - Análise de Desempenho",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');
    
    /* Aplicar Montserrat globalmente */
    html, body, [class*="css"], h1, h2, h3, h4, h5, h6, p, div, span {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Personalizar sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #96CA00 0%, #C5DF56 50%, #84A802 100%) !important;
        padding: 1rem !important;
    }
    
    .css-1d391kg .stSelectbox label,
    .css-1d391kg .stDateInput label,
    .css-1d391kg h2,
    .css-1d391kg h3 {
        color: white !important;
        font-weight: 600 !important;
        font-family: 'Montserrat', sans-serif !important;
    }
    
    .css-1d391kg .stButton button {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 2px solid white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Montserrat', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .css-1d391kg .stButton button:hover {
        background: white !important;
        color: #96CA00 !important;
    }
    
    .css-1d391kg .stMetric {
        background: rgba(255, 255, 255, 0.15) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin: 0.5rem 0 !important;
    }
    
    .css-1d391kg .stMetric label,
    .css-1d391kg .stMetric [data-testid="metric-container"] {
        color: white !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Logo na sidebar */
    .sidebar-logo {
        text-align: center;
        margin: 1rem 0 2rem 0;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    .main-header {
        background: linear-gradient(90deg, #96CA00 0%, #C5DF56 50%, #84A802 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        font-family: 'Montserrat', sans-serif;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-weight: 700;
        font-family: 'Montserrat', sans-serif;
    }
    
    .section-header-producao {
        background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.8rem;
        font-family: 'Montserrat', sans-serif;
    }
    
    .section-header-administrativo {
        background: linear-gradient(90deg, #2196F3 0%, #64B5F6 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.8rem;
        font-family: 'Montserrat', sans-serif;
    }
    
    .section-header-comercial {
        background: linear-gradient(90deg, #FF9800 0%, #FFB74D 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.8rem;
        font-family: 'Montserrat', sans-serif;
    }
    
    .section-header-clima {
        background: linear-gradient(90deg, #E91E63 0%, #F8BBD9 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.8rem;
        font-family: 'Montserrat', sans-serif;
    }
    
    .category-header {
        background: linear-gradient(90deg, #96CA00 0%, #C5DF56 100%);
        color: white;
        padding: 0.6rem;
        border-radius: 6px;
        margin: 0.8rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.4rem;
        font-family: 'Montserrat', sans-serif;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        text-align: center;
        margin-left: auto;
        margin-right: auto;
        font-family: 'Montserrat', sans-serif;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #96CA00;
        margin: 0;
        font-family: 'Montserrat', sans-serif;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 0.2rem;
        font-family: 'Montserrat', sans-serif;
        font-weight: 500;
    }
    
    .logo-container {
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Função para carregar dados do Google Sheets
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data():
    try:
        # Configurar credenciais do Google Sheets usando o arquivo JSON das secrets
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        
        # Carregando credenciais do secrets.toml
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        
        client = gspread.authorize(credentials)
        
        # ID da sua planilha
        sheet_id = "1rwo4nu_DJNgUdb65UQ9e3AbiQacEHiRXA0hBbpvuULU"
        spreadsheet = client.open_by_key(sheet_id)
        
        # Carregar cada aba
        sheets_data = {}
        sheet_names = ["PRODUÇÃO", "ADMINISTRATIVO", "COMERCIAL", "CLIMA"]
        
        for sheet_name in sheet_names:
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                data = worksheet.get_all_records()
                if data:
                    df = pd.DataFrame(data)
                    sheets_data[sheet_name] = df
                    
                else:
                    sheets_data[sheet_name] = pd.DataFrame()
                    st.warning(f"⚠️ Aba {sheet_name} está vazia")
            except Exception as e:
                st.error(f"❌ Erro ao carregar aba {sheet_name}: {str(e)}")
                sheets_data[sheet_name] = pd.DataFrame()
        
        return sheets_data
    
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Google Sheets: {str(e)}")
        st.info("🔧 Verifique se:")
        st.write("- As credenciais estão corretas no arquivo secrets.toml")
        st.write("- A planilha foi compartilhada com o email da Service Account")
        st.write("- As APIs do Google Sheets e Drive estão ativadas")
        return {}

# Mapeamento das colunas por categoria
ASPECTOS_PESSOAIS = [
    "Aparência (Uniforme limpo, asseado, faz uso de touca etc.)?",
    "Assiduidade (Comparece ao trabalho sem faltas)?", 
    "Pontualidade (Comparece no trabalho no horário estipulado e cumpre carga pré-definida)?",
    "Faz uso correto dos EPI’s disponibilizados?"
]

DESENVOLVIMENTO = [
    "Relacionamento com Colegas (habilidade no trato com os colegas, influenciando positivamente e obtendo aceitação pessoal) ",
    "Relacionamento com a Liderança (habilidade para se comunicar com a chefia de maneira adequada) ",
    "Comunicação (capacidade para receber e emitir informações corretamente com os colegas e público em geral) ",
    "Demonstra interesse em aprender novas habilidades e conhecimentos? ",
    "Demonstra adequação à cultura organizacional da Papello? "
]

DESEMPENHO_PROFISSIONAL = [
    "Produtividade (ritmo de trabalho, aliado ao rendimento e qualidade com que o colaborador desenvolve as tarefas)",
    "\nQualidade do Trabalho (grau de perfeição, correção do trabalho e eficiência do trabalho executado) ",
    "Conhecimento do Trabalho (habilidade para reter /assimilar informações recebidas, usá-las e ensiná-las corretamente)",
    "Iniciativa (habilidade em agir/executar as tarefas e solucionar problemas sem necessidade de supervisão constante)",
    "Solução de Problemas (capacidade para buscar e dar soluções aos problemas rotineiros das atividades de trabalho)",
    "Atende às competências técnicas para o cargo (habilidade do colaborador na execução das atividades inerentes ao cargo)",
    "Tem domínio das ferramentas necessárias para a realização do trabalho?",
    "Garante que os procedimentos do processo estejam sendo cumpridos? ",
    "Busca exercer as diretrizes organizacionais da empresa (missão, visão, valores, política) "
]

CLIMA_ORGANIZACIONAL = [
    "Treinamento para desempenhar as suas atividades (em sala ou no local de trabalho)",
    "Conhecimento e habilidade para execução das tarefas",
    "Possibilidade de crescimento dentro da empresa",
    "Satisfação pelas atividades realizadas",
    "Reconhecimento pelo seu trabalho realizado",
    "Máquinas, ferramentas e instalações para desempenhar suas funções",
    "Organização e limpeza do seu local de trabalho",
    "Refeitório (qualidade da refeição, instalações, organização e limpeza)",
    "Banheiros (instalações, organização e limpeza)",
    "Vestiários (instalações, organização, limpeza)",
    "Segurança do seu local de trabalho",
    "Relacionamento entre os colegas de trabalho",
    "Relacionamento com as lideranças",
    "Comunicação entre as áreas",
    "Comunicação da empresa para os colaboradores",
    "Comunicação dos colaboradores para a empresa",
    "Liberdade para manifestar opiniões e propor sugestões",
    "O quanto você se sente realizado(a) profissionalmente?  "
]

def process_dataframe(df):
    """Processa o DataFrame para converter datas e valores numéricos"""
    if df.empty:
        return df
    
    # Fazer uma cópia para não modificar o original
    df = df.copy()
    
    # Converter coluna de data
    if 'Carimbo de data/hora' in df.columns:
        try:
            df['Carimbo de data/hora'] = pd.to_datetime(df['Carimbo de data/hora'], errors='coerce')
            df['Data'] = df['Carimbo de data/hora'].dt.date
        except Exception as e:
            st.warning(f"Erro ao processar datas: {str(e)}")
            df['Data'] = None
    
    # Converter colunas numéricas (escala 1-10)
    numeric_columns = []
    for col in df.columns:
        # Pular colunas não numéricas
        if col in ['Carimbo de data/hora', 'AVALIADOR', 'CARGO', 'COLABORADOR', 'CARGO DO COLABORADOR', 'SETOR', 'Data']:
            continue
        if col.startswith('OBSERVAÇÕES'):
            continue
        
        try:
            # Converter para numérico
            original_values = df[col].copy()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Filtrar apenas valores entre 1 e 10
            df[col] = df[col].where((df[col] >= 1) & (df[col] <= 10))
            
            # Verificar se a conversão funcionou
            if df[col].notna().any():
                numeric_columns.append(col)
                
        except Exception as e:
            # Se não conseguir converter, manter valores originais
            df[col] = original_values
    
    return df

def create_pie_chart(values, title, full_title, colors=None):
    """Cria gráfico de pizza"""
    # Corrigir verificação para Series do pandas
    if values is None or len(values) == 0 or values.empty:
        return go.Figure()
    
    # Remover valores nulos
    clean_values = values.dropna()
    
    if len(clean_values) == 0:
        return go.Figure()
    
    # Contar distribuição de notas
    counts = clean_values.value_counts().sort_index()
    
    if len(counts) == 0:
        return go.Figure()
    
    if colors is None:
        colors = px.colors.qualitative.Set3
    
    fig = go.Figure(data=[go.Pie(
        labels=[f'Nota {int(k)}' for k in counts.index],
        values=counts.values,
        hole=0.4,
        marker_colors=colors[:len(counts)],
        hovertemplate='<b>%{label}</b><br>Quantidade: %{value}<br>Porcentagem: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}  # Fonte maior como solicitado
        },
        font=dict(size=12),
        height=350,
        margin=dict(t=60, b=30, l=10, r=10)
    )
    
    return fig
    

def display_category_analysis(df, category_columns, category_name, colors=None):
    """Exibe análise de uma categoria"""
    st.markdown(f'<div class="category-header">ANÁLISE - {category_name.upper()}</div>', unsafe_allow_html=True)
    
    # Verificar se as colunas existem no DataFrame
    existing_columns = [col for col in category_columns if col in df.columns]
    
    if not existing_columns:
        st.warning(f"Nenhuma coluna encontrada para a categoria {category_name}")
        st.info("Colunas esperadas:")
        for col in category_columns[:3]:  # Mostrar apenas as primeiras 3
            st.write(f"- {col}")
        if len(category_columns) > 3:
            st.write(f"... e mais {len(category_columns) - 3} colunas")
        return
    
    # Criar colunas para os gráficos
    n_cols = min(4, len(existing_columns))
    cols = st.columns(n_cols)
    
    category_means = []
    
    for i, col in enumerate(existing_columns):
        col_idx = i % n_cols
        
        with cols[col_idx]:
            try:
                values = df[col].dropna()
                
                if len(values) > 0:
                    # Verificar se são valores numéricos válidos
                    numeric_values = pd.to_numeric(values, errors='coerce').dropna()
                    
                    if len(numeric_values) > 0:
                        mean_val = numeric_values.mean()
                        category_means.append(mean_val)
                        
                        # Nome curto para o gráfico
                        short_name = col.split('(')[0].strip()

                       # Renomear "Faz uso correto dos EPI's" para "Segurança"  
                        if "EPI" in col:
                            short_name = "Segurança"
                        
                        # Limitar nome para exibição
                        display_name = short_name if len(short_name) <= 20 else short_name[:17] + "..."
                        
                        # Criar container com tooltip para o título
                        st.markdown(f'''
                        <div title="{col}" style="text-align: center; margin-bottom: 10px; 
                             font-weight: bold; font-size: 18px; color: #333; cursor: help;
                             padding: 5px; border-radius: 5px; background: rgba(150, 202, 0, 0.1);">
                            {display_name}
                        </div>
                        ''', unsafe_allow_html=True)
                        
                        fig = create_pie_chart(numeric_values, "", col, colors)  # Título vazio para evitar duplicação
                        chart_key = f"chart_{category_name}_{i}_{hash(col) % 10000}"

                        if fig:  # Verificar se o gráfico foi criado com sucesso
                            st.plotly_chart(fig, use_container_width=True, key=chart_key)
                        else:
                            st.warning("Erro ao criar gráfico")
                        
                        # Métrica abaixo do gráfico - centralizada
                
                        st.markdown(f"""
                        <div class="metric-card" style="text-align: center; margin-bottom: 2rem;">
                            <div class="metric-value" style="margin: 0 auto;">{mean_val:.2f}</div>
                            <div class="metric-label" style="margin: 0.2rem auto 0;">Média</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning(f"Sem dados numéricos válidos para: {col[:30]}...")
                else:
                    st.warning(f"Sem dados para: {col[:30]}...")
                    
            except Exception as e:
                st.error(f"Erro ao processar coluna {col[:30]}...: {str(e)}")
    
    # Média da categoria - em maiúsculas
    if category_means:
        overall_mean = np.mean(category_means)
        st.markdown(f"""
        <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px; margin: 1rem 0; text-align: center;">
            <h3 style="color: #2e7d32; margin: 0;">MÉDIA {category_name.upper()}</h3>
            <h2 style="color: #2e7d32; margin: 0.5rem 0;">{overall_mean:.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"Não foi possível calcular a média para {category_name}")

def filter_dataframe(df, start_date, end_date, selected_colaborador):
    """Aplica filtros ao DataFrame"""
    filtered_df = df.copy()
    
    # Filtro por data
    if 'Data' in filtered_df.columns and start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df['Data'] >= start_date) & 
            (filtered_df['Data'] <= end_date)
        ]
    
    # Filtro por colaborador
    if selected_colaborador and selected_colaborador != "Todos" and 'COLABORADOR' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['COLABORADOR'] == selected_colaborador]
    
    return filtered_df

# Interface principal
def main():
    # Verificação de senha
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("""
        <div class="main-header">
            <h1>🔐 Acesso Restrito - Dashboard RH</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="max-width: 450px; margin: 2rem auto; padding: 1rem; 
                    background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <img src="https://acdn-us.mitiendanube.com/stores/002/907/105/themes/common/logo-1336738559-1706047471-a90c2b04f7208c4f190adf866d8df0b51706047472-320-0.webp" 
                     style="max-width: 280px; height: auto; border-radius: 8px;">
            </div>
        """, unsafe_allow_html=True)
        
        password = st.text_input("Digite a senha:", type="password", key="password_input")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Entrar", use_container_width=True):
                try:
                    correct_password = st.secrets["senha_acesso"]
                    if password == correct_password:
                        st.session_state.authenticated = True
                        st.success("✅ Acesso autorizado!")
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta!")
                except Exception:
                    st.error("❌ Erro ao verificar senha. Verifique o arquivo secrets.toml")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Sidebar com logo e logout
    with st.sidebar:
        # Logo na sidebar
        st.markdown("""
        <div class="sidebar-logo">
            <img src="https://acdn-us.mitiendanube.com/stores/002/907/105/themes/common/ogimage-1149314976-1685710658-ab8c89cb60705e9411f6e0d3a4338ae61685710659.png?0" 
                 style="max-height: 60px; margin-bottom: 0.5rem;">
            <div style="color: BLACK; font-weight: 600; font-size: 0.9rem; margin-top: 0.5rem;">
               ANÁLISE DE DESEMPENHO
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
    
    # Logo e cabeçalho
    st.markdown("""
    <div class="logo-container">
        <img src="https://acdn-us.mitiendanube.com/stores/002/907/105/themes/common/ogimage-1149314976-1685710658-ab8c89cb60705e9411f6e0d3a4338ae61685710659.png?0" 
             style="max-height: 80px; margin-bottom: 1rem;">
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard RH - Análise de Desempenho</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = load_data()
    
    if not data:
        st.error("Não foi possível carregar os dados. Verifique as credenciais e a conexão.")
        return
    
    # Sidebar para filtros
    st.sidebar.header("🔍 Filtros")
    
    # Seleção de aba
    selected_tab = st.sidebar.selectbox(
        "Selecione o Setor:",
        ["PRODUÇÃO", "ADMINISTRATIVO", "COMERCIAL", "CLIMA"]
    )
    
    # Processar dados da aba selecionada
    if selected_tab in data and not data[selected_tab].empty:
        df = process_dataframe(data[selected_tab])
        
        # Filtros adicionais
        if 'Data' in df.columns and df['Data'].notna().any():
            # Filtrar apenas valores de data válidos (não NaN e não None)
            valid_dates = df['Data'].dropna()
            if len(valid_dates) > 0:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
            else:
                min_date = None
                max_date = None
        else:
            min_date = None
            max_date = None
        
        # Só mostrar filtros de data se houver datas válidas
        if min_date and max_date:
            
            start_date = st.sidebar.date_input(
                "Data inicial:",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY"
            )
            
            end_date = st.sidebar.date_input(
                "Data final:",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY"
            )
        else:
            start_date = None
            end_date = None
        
        # Filtro por colaborador
        if 'COLABORADOR' in df.columns:
            colaboradores = ["Todos"] + sorted(df['COLABORADOR'].dropna().unique().tolist())
            selected_colaborador = st.sidebar.selectbox(
                "Colaborador:",
                colaboradores
            )
        else:
            selected_colaborador = None
        
        # Aplicar filtros
        filtered_df = filter_dataframe(df, start_date, end_date, selected_colaborador)
        
        # Exibir informações da seleção
        st.sidebar.markdown("---")
        st.sidebar.metric("Total de Avaliações", len(filtered_df))
        
        if not filtered_df.empty:
            # Cabeçalho da seção
            if selected_tab == "PRODUÇÃO":
                st.markdown('<div class="section-header-producao">ANÁLISE DE DESEMPENHO - PRODUÇÃO</div>', unsafe_allow_html=True)
                colors = px.colors.qualitative.Set2
            elif selected_tab == "ADMINISTRATIVO":
                st.markdown('<div class="section-header-administrativo">ANÁLISE DE DESEMPENHO - ADMINISTRATIVO</div>', unsafe_allow_html=True)
                colors = px.colors.qualitative.Set1
            elif selected_tab == "COMERCIAL":
                st.markdown('<div class="section-header-comercial">ANÁLISE DE DESEMPENHO - COMERCIAL</div>', unsafe_allow_html=True)
                colors = px.colors.qualitative.Pastel1
            else:  # CLIMA
                st.markdown('<div class="section-header-clima">PESQUISA DE CLIMA ORGANIZACIONAL</div>', unsafe_allow_html=True)
                colors = px.colors.qualitative.Pastel2
            
            if selected_tab == "CLIMA":
                # Análise do Clima Organizacional
                display_category_analysis(filtered_df, CLIMA_ORGANIZACIONAL, "CLIMA ORGANIZACIONAL", colors)
                
                # Média geral do clima
                all_means = []
                for col in CLIMA_ORGANIZACIONAL:
                    if col in filtered_df.columns:
                        values = filtered_df[col].dropna()
                        if len(values) > 0:
                            all_means.append(values.mean())
                
                if all_means:
                    overall_mean = np.mean(all_means)
                    st.markdown(f"""
                    <div style="background: linear-gradient(90deg, #E91E63 0%, #F8BBD9 100%); 
                                color: white; padding: 1.5rem; border-radius: 10px; 
                                margin: 2rem 0; text-align: center;">
                        <h2 style="margin: 0;">MÉDIA GERAL DO CLIMA</h2>
                        <h1 style="margin: 0.5rem 0; font-size: 3rem;">{overall_mean:.2f}</h1>
                    </div>
                    """, unsafe_allow_html=True)
            
            else:
                # Análise das três categorias para setores produtivos
                display_category_analysis(filtered_df, ASPECTOS_PESSOAIS, "ASPECTOS PESSOAIS", colors)
                display_category_analysis(filtered_df, DESENVOLVIMENTO, "DESENVOLVIMENTO", colors)
                display_category_analysis(filtered_df, DESEMPENHO_PROFISSIONAL, "DESEMPENHO PROFISSIONAL", colors)
                
                # Média geral
                all_categories = ASPECTOS_PESSOAIS + DESENVOLVIMENTO + DESEMPENHO_PROFISSIONAL
                all_means = []
                
                for col in all_categories:
                    if col in filtered_df.columns:
                        values = filtered_df[col].dropna()
                        if len(values) > 0:
                            all_means.append(values.mean())
                
                if all_means:
                    overall_mean = np.mean(all_means)
                    
                    # Cor do header baseada no setor
                    if selected_tab == "PRODUÇÃO":
                        bg_color = "linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%)"
                    elif selected_tab == "ADMINISTRATIVO":
                        bg_color = "linear-gradient(90deg, #2196F3 0%, #64B5F6 100%)"
                    else:  # COMERCIAL
                        bg_color = "linear-gradient(90deg, #FF9800 0%, #FFB74D 100%)"
                    
                    st.markdown(f"""
                    <div style="background: {bg_color}; 
                                color: white; padding: 1.5rem; border-radius: 10px; 
                                margin: 2rem 0; text-align: center;">
                        <h2 style="margin: 0;">MÉDIA GERAL</h2>
                        <h1 style="margin: 0.5rem 0; font-size: 3rem;">{overall_mean:.2f}</h1>
                    </div>
                    """, unsafe_allow_html=True)
        
        else:
            st.warning("Nenhum dado encontrado com os filtros aplicados.")
    
    else:
        st.warning(f"Nenhum dado encontrado para a aba {selected_tab}")

if __name__ == "__main__":
    main()