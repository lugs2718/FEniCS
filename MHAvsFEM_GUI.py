import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import importlib

# Importa a função do main (nome do arquivo contém espaços/hífens)
main_module = importlib.import_module("MHA vs FEM - main - EDITAR APENAS ESSE")
comparar_mha_mef = main_module.comparar_mha_mef

st.set_page_config(page_title="Análise MEF vs MHA", layout="wide")

st.title("🔬 Interface Interativa: Influência de Camadas e Elementos (MEF vs MHA)")

# ===== SIDEBAR: PARÂMETROS =====
st.sidebar.header("⚙️ Parâmetros do Problema")

with st.sidebar.expander("🔧 Geometria e Carga", expanded=False):
    R_int = st.number_input("Raio Interno (mm)", value=9.0, min_value=1.0)
    R_ext = st.number_input("Raio Externo (mm)", value=11.0, min_value=R_int+0.1)
    H = st.number_input("Espessura (mm)", value=2.0, min_value=0.1)
    P_int = st.number_input("Pressão Interna (MPa)", value=10.0, format="%.2f")

with st.sidebar.expander("🧱 Materiais", expanded=False):
    st.markdown("**Material 1 (ex: Aço)**")
    E1 = st.number_input("Módulo Young E₁ (MPa)", value=200e3, format="%.2e")
    nu1 = st.slider("Coef. Poisson ν₁", 0.0, 0.49, 0.3)
    
    st.markdown("**Material 2 (ex: Alumínio)**")
    E2 = st.number_input("Módulo Young E₂ (MPa)", value=70e3, format="%.2e")
    nu2 = st.slider("Coef. Poisson ν₂", 0.0, 0.49, 0.33)
    
    V1 = st.slider("Fração Volumétrica Mat. 1", 0.0, 1.0, 0.5, step=0.05)

with st.sidebar.expander("📊 Discretização (Foco de Análise)", expanded=True):
    N_camadas = st.number_input("Número de Camadas", min_value=1,  max_value=1000, value=200, step=10)
    st.markdown("---")
    st.markdown("### Tamanho dos Elementos")
    n_elem_r = st.number_input("Elementos na direção Radial (r)", min_value=10, max_value=5000, value=800, step=100)
    n_elem_z = st.number_input("Elementos na direção Axial (z)", min_value=1, max_value=200, value=10, step=5)

# ===== BOTÃO RESOLVER =====
if st.sidebar.button("🚀 Executar Simulação", type="primary"):
    
    # Container para feedback visual das etapas
    status_placeholder = st.empty()
    
    def atualizar_status(etapa):
        status_placeholder.info(f"⚙️ {etapa}")
    
    with st.spinner("Executando simulação..."):
        resultados = comparar_mha_mef(
            R_int=R_int, R_ext=R_ext, H=H, P_int=P_int,
            E1=E1, nu1=nu1, E2=E2, nu2=nu2,
            V1=V1,
            N_camadas=int(N_camadas), n_elem_r=int(n_elem_r), n_elem_z=int(n_elem_z),
            callback=atualizar_status
        )
    
    status_placeholder.empty()
    
    # ===== VISUALIZAÇÃO =====
    st.success("✅ Simulação concluída!")
    
    R_vals = resultados["R_vals"]
    u_r_mef = resultados["u_r_mef"]
    u_r_mha = resultados["u_r_mha"]
    erro_abs = resultados["erro_abs"]
    
    tab1, tab2, tab3 = st.tabs(["📉 Análise de Deslocamento", "📊 Erro MHA vs MEF", "📋 Log das Camadas e Malha"])
    
    with tab1:
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(R_vals, u_r_mef, 'b-', label=f'MEF Heterogêneo ({N_camadas} Camadas)', linewidth=2)
        ax1.plot(R_vals, u_r_mha, 'r--', label='MHA Homogeneizado', linewidth=2)
        
        ax1.set_xlabel('Raio (mm)')
        ax1.set_ylabel('Deslocamento Radial (mm)')
        ax1.set_title('Comparação dos Deslocamentos Rádais na Metade da Espessura')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        st.pyplot(fig1)

    with tab2:
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(R_vals, erro_abs, 'g-', linewidth=2)
        ax2.set_xlabel('Raio (mm)')
        ax2.set_ylabel('Erro Absoluto (mm)')
        ax2.set_title('Diferença Absoluta entre MEF e MHA ao Longo do Raio')
        ax2.grid(True, alpha=0.3)
        st.pyplot(fig2)

    with tab3:
        st.markdown(f"**Detalhes da Discretização:**")
        st.write(f"- Camadas Modeladas: **{resultados['N_camadas']}**")
        st.write(f"- Elementos Radiais (n_elem_r): **{resultados['n_elem_r']}**")
        st.write(f"- Elementos Axiais (n_elem_z): **{resultados['n_elem_z']}**")
        st.write(f"- Total de Elementos: **{resultados['total_elementos']}**")
        
        elementos_por_camada = resultados['n_elem_r'] / resultados['N_camadas']
        if elementos_por_camada < 1:
            st.error(f"Aviso: Você tem {elementos_por_camada:.2f} elementos por camada. A malha está muito grossa para as {resultados['N_camadas']} camadas, os resultados focarão em ruído.")
        else:
            st.success(f"Status da Discretização Radiial: ~{elementos_por_camada:.1f} elementos por camada.")

else:
    st.info("👈 Utilize o painel da esquerda para interagir com o Solver MEF do FEniCS!")
    st.markdown("""
    ### Bem-vindo ao Ambiente de Testes do `main.py`
    Esta interface facilita o estudo de como a discretização afeta uma simulação baseada em métodos de elementos finitos para laminados compósitos.
    
    1. Abra o painel **Discretização** ao lado.
    2. Altere o *número de camadas* e/ou ajuste a quantidade de *elementos radiais e axiais*.
    3. Clique em **Executar Simulação** para atualizar os gráficos!
    """)
