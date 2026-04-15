import streamlit as st
from dolfin import *
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="MEF vs MHA - Análise Comparativa", layout="wide")

st.title("🔬 Comparação: MEF Heterogêneo vs MHA Homogeneizado")

# ===== SIDEBAR: PARÂMETROS =====
st.sidebar.header("⚙️ Parâmetros do Problema")

with st.sidebar.expander("🔧 Geometria", expanded=True):
    R_int = st.number_input("Raio Interno (m)", value=9.0, min_value=1.0)
    R_ext = st.number_input("Raio Externo (m)", value=11.0, min_value=R_int+0.1)
    H = st.number_input("Espessura (m)", value=2.0, min_value=0.1)
    P_int = st.number_input("Pressão Interna (Pa)", value=10e6, format="%.2e")

with st.sidebar.expander("🧱 Material 1 (Aço)", expanded=True):
    E1 = st.number_input("Módulo Young E₁ (Pa)", value=200e9, format="%.2e")
    nu1 = st.slider("Coef. Poisson ν₁", 0.0, 0.5, 0.3)

with st.sidebar.expander("🔩 Material 2 (Alumínio)", expanded=True):
    E2 = st.number_input("Módulo Young E₂ (Pa)", value=70e9, format="%.2e")
    nu2 = st.slider("Coef. Poisson ν₂", 0.0, 0.5, 0.33)

with st.sidebar.expander("📊 Discretização", expanded=True):
    N_camadas = st.slider("Número de Camadas", 10, 500, 200, step=10)
    n_elem_r = st.slider("Elementos Radiais", 100, 2000, 800, step=100)
    n_elem_z = st.slider("Elementos Axiais", 5, 50, 10)

V1 = st.sidebar.slider("Fração Volumétrica Mat. 1", 0.0, 1.0, 0.5, step=0.05)
V2 = 1.0 - V1

# ===== BOTÃO RESOLVER =====
if st.sidebar.button("🚀 Executar Simulação", type="primary"):
    
    with st.spinner("⚙️ Calculando coeficientes homogeneizados..."):
        # Função auxiliar
        def get_C_matrix(E, nu):
            C11 = E * (1 - nu) / ((1 + nu) * (1 - 2 * nu))
            C12 = E * nu / ((1 + nu) * (1 - 2 * nu))
            G = E / (2 * (1 + nu))
            return C11, C12, G

        C11_1, C12_1, G_1 = get_C_matrix(E1, nu1)
        C11_2, C12_2, G_2 = get_C_matrix(E2, nu2)

        # Coeficientes efetivos
        C11_eff = 1.0 / (V1/C11_1 + V2/C11_2)
        C12_eff = C11_eff * (V1 * C12_1/C11_1 + V2 * C12_2/C11_2)
        C22_eff = (V1*C11_1 + V2*C11_2) - (V1*(C12_1**2)/C11_1 + V2*(C12_2**2)/C11_2) + (C12_eff**2)/C11_eff
        G_eff = 1.0 / (V1/G_1 + V2/G_2)
    
    # Mostrar coeficientes
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("C₁₁ Efetivo", f"{C11_eff/1e9:.2f} GPa")
    col2.metric("C₁₂ Efetivo", f"{C12_eff/1e9:.2f} GPa")
    col3.metric("C₂₂ Efetivo", f"{C22_eff/1e9:.2f} GPa")
    col4.metric("G Efetivo", f"{G_eff/1e9:.2f} GPa")
    
    with st.spinner("🔨 Gerando malha..."):
        interfaces = np.linspace(R_int, R_ext, N_camadas + 1)[1:-1]
        mesh = RectangleMesh(Point(R_int, 0.0), Point(R_ext, H), n_elem_r, n_elem_z)
        
        # Configuração comum
        boundaries = MeshFunction("size_t", mesh, mesh.topology().dim() - 1)
        boundaries.set_all(0)
        CompiledSubDomain("near(x[0], R_int)", R_int=R_int).mark(boundaries, 1)
        CompiledSubDomain("near(x[1], 0.0)").mark(boundaries, 2)
        CompiledSubDomain("near(x[1], H)", H=H).mark(boundaries, 3)
        ds_custom = Measure("ds", domain=mesh, subdomain_data=boundaries)
        
        V = VectorFunctionSpace(mesh, "CG", 1)
        u = TrialFunction(V)
        v = TestFunction(V)
        x = SpatialCoordinate(mesh)
        r = x[0]
        
        bcs = [
            DirichletBC(V.sub(1), Constant(0.0), boundaries, 2),
            DirichletBC(V.sub(1), Constant(0.0), boundaries, 3)
        ]
        
        T = -Constant(P_int) * FacetNormal(mesh)
        L = inner(T, v) * r * ds_custom(1)
    
    # Resolver MEF
    with st.spinner("🧮 Resolvendo MEF Heterogêneo..."):
        class PeriodicProperty(UserExpression):
            def __init__(self, val1, val2, interfaces, **kwargs):
                super().__init__(**kwargs)
                self.val1, self.val2 = val1, val2
                self.interfaces = interfaces
            def eval(self, values, x):
                idx = 0
                for r_int in self.interfaces:
                    if x[0] <= r_int: break
                    idx += 1
                values[0] = self.val1 if idx % 2 == 0 else self.val2
            def value_shape(self): return ()

        E_func = PeriodicProperty(E1, E2, interfaces, degree=0)
        nu_func = PeriodicProperty(nu1, nu2, interfaces, degree=0)
        
        lmbda_func = (E_func * nu_func) / ((1.0 + nu_func) * (1.0 - 2.0 * nu_func))
        mu_func = E_func / (2.0 * (1.0 + nu_func))
        
        def eps(u):
            return sym(as_tensor([[u[0].dx(0), 0, u[0].dx(1)], 
                                  [0, u[0]/r, 0], 
                                  [u[1].dx(0), 0, u[1].dx(1)]]))
        
        def sigma_mef(u):
            return lmbda_func * tr(eps(u)) * Identity(3) + 2.0 * mu_func * eps(u)
        
        a_mef = inner(sigma_mef(u), eps(v)) * r * dx
        u_mef = Function(V)
        solve(a_mef == L, u_mef, bcs)
    
    # Resolver MHA
    with st.spinner("🧮 Resolvendo MHA Homogeneizado..."):
        def sigma_mha(u):
            err = u[0].dx(0)
            ett = u[0]/r
            ezz = u[1].dx(1)
            erz = 0.5 * (u[0].dx(1) + u[1].dx(0))
            
            srr = C11_eff*err + C12_eff*ett + C12_eff*ezz
            stt = C12_eff*err + C22_eff*ett + C12_eff*ezz
            szz = C12_eff*err + C12_eff*ett + C22_eff*ezz
            srz = 2.0 * G_eff * erz
            
            return as_tensor([[srr, 0, srz], [0, stt, 0], [srz, 0, szz]])
        
        a_mha = inner(sigma_mha(u), eps(v)) * r * dx
        u_mha = Function(V)
        solve(a_mha == L, u_mha, bcs)
    
    # Extração de resultados
    R_vals = np.linspace(R_int, R_ext, 1000)
    Z_val = H / 2.0
    
    u_r_mef = [u_mef(r, Z_val)[0] for r in R_vals]
    u_r_mha = [u_mha(r, Z_val)[0] for r in R_vals]
    
    # Cálculo de erro
    erro_abs = np.abs(np.array(u_r_mef) - np.array(u_r_mha))
    erro_rel = 100 * erro_abs / (np.abs(u_r_mef) + 1e-15)
    
    # ===== VISUALIZAÇÃO =====
    st.success("✅ Simulação concluída!")
    
    tab1, tab2, tab3 = st.tabs(["📈 Deslocamentos", "📊 Erro", "ℹ️ Informações"])
    
    with tab1:
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(R_vals, u_r_mef, 'b-', label='MEF (Heterogêneo)', linewidth=2)
        ax1.plot(R_vals, u_r_mha, 'r--', label='MHA (Homogeneizado)', linewidth=2.5)
        
        for r_int in interfaces[::10]:  # Mostrar 1 a cada 10
            ax1.axvline(r_int, color='k', linestyle=':', alpha=0.1)
        
        ax1.set_xlabel('Raio (m)', fontsize=12)
        ax1.set_ylabel('Deslocamento Radial (m)', fontsize=12)
        ax1.set_title('Comparação: MEF vs MHA', fontsize=14)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        st.pyplot(fig1)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("u_max (MEF)", f"{max(u_r_mef):.3e} m")
        col2.metric("u_max (MHA)", f"{max(u_r_mha):.3e} m")
        col3.metric("Diferença", f"{abs(max(u_r_mef)-max(u_r_mha)):.3e} m")
    
    with tab2:
        fig2, (ax2a, ax2b) = plt.subplots(2, 1, figsize=(12, 8))
        
        ax2a.plot(R_vals, erro_abs, 'g-', linewidth=2)
        ax2a.set_xlabel('Raio (m)')
        ax2a.set_ylabel('Erro Absoluto (m)')
        ax2a.set_title('Erro Absoluto: |MEF - MHA|')
        ax2a.grid(True, alpha=0.3)
        
        ax2b.plot(R_vals, erro_rel, 'orange', linewidth=2)
        ax2b.set_xlabel('Raio (m)')
        ax2b.set_ylabel('Erro Relativo (%)')
        ax2b.set_title('Erro Relativo')
        ax2b.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig2)
        
        st.metric("Erro Médio", f"{np.mean(erro_rel):.4f} %")
        st.metric("Erro Máximo", f"{np.max(erro_rel):.4f} %")
    
    with tab3:
        st.markdown(f"""
        ### Configuração da Simulação
        
        **Geometria:**
        - Raio interno: {R_int} m
        - Raio externo: {R_ext} m
        - Espessura: {H} m
        
        **Carregamento:**
        - Pressão interna: {P_int:.2e} Pa
        
        **Materiais:**
        - Material 1: E = {E1:.2e} Pa, ν = {nu1}
        - Material 2: E = {E2:.2e} Pa, ν = {nu2}
        
        **Discretização:**
        - Camadas: {N_camadas}
        - Elementos radiais: {n_elem_r}
        - Elementos axiais: {n_elem_z}
        - Total de elementos: {n_elem_r * n_elem_z}
        
        **Frações Volumétricas:**
        - Material 1: {V1*100:.1f}%
        - Material 2: {V2*100:.1f}%
        """)

# ===== INFORMAÇÕES INICIAIS =====
else:
    st.info("👈 Configure os parâmetros na barra lateral e clique em 'Executar Simulação'")
    
    st.markdown("""
    ## Sobre este Simulador
    
    Esta aplicação compara duas abordagens para análise de estruturas compostas laminadas:
    
    1. **MEF Heterogêneo**: Modelo detalhado com múltiplas camadas
    2. **MHA (Método de Homogeneização Assintótica)**: Modelo homogeneizado equivalente
    
    ### Funcionalidades
    - ⚙️ Configuração interativa de geometria e materiais
    - 📊 Visualização comparativa de resultados
    - 📈 Análise de erro entre modelos
    - 🔧 Controle fino de discretização
    
    ### Como Usar
    1. Ajuste os parâmetros geométricos
    2. Configure as propriedades dos materiais
    3. Defina a discretização (camadas e elementos)
    4. Clique em "Executar Simulação"
    5. Analise os resultados nas diferentes abas
    """)
