import streamlit as st
from dolfin import *
import numpy as np
import matplotlib.pyplot as plt

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
    V2 = 1.0 - V1

with st.sidebar.expander("📊 Discretização (Foco de Análise)", expanded=True):
    N_camadas = st.number_input("Número de Camadas", min_value=1,  max_value=1000, value=200, step=10)
    st.markdown("---")
    st.markdown("### Tamanho dos Elementos")
    n_elem_r = st.number_input("Elementos na direção Radial (r)", min_value=10, max_value=5000, value=800, step=100)
    n_elem_z = st.number_input("Elementos na direção Axial (z)", min_value=1, max_value=200, value=10, step=5)

# ===== BOTÃO RESOLVER =====
if st.sidebar.button("🚀 Executar Simulação", type="primary"):
    
    with st.spinner("⚙️ Calculando coeficientes homogeneizados..."):
        def get_C_matrix(E, nu):
            C11 = E * (1 - nu) / ((1 + nu) * (1 - 2 * nu))
            C12 = E * nu / ((1 + nu) * (1 - 2 * nu))
            G = E / (2 * (1 + nu))
            return C11, C12, G

        C11_1, C12_1, G_1 = get_C_matrix(E1, nu1)
        C11_2, C12_2, G_2 = get_C_matrix(E2, nu2)

        C11_eff = 1.0 / (V1/C11_1 + V2/C11_2)
        C12_eff = C11_eff * (V1 * C12_1/C11_1 + V2 * C12_2/C11_2)
        C22_eff = (V1*C11_1 + V2*C11_2) - (V1*(C12_1**2)/C11_1 + V2*(C12_2**2)/C11_2) + (C12_eff**2)/C11_eff
        G_eff = 1.0 / (V1/G_1 + V2/G_2)
    
    with st.spinner("🔨 Gerando malha e definindo subdomínios..."):
        interfaces = np.linspace(R_int, R_ext, int(N_camadas) + 1)[1:-1]
        mesh = RectangleMesh(Point(R_int, 0.0), Point(R_ext, H), int(n_elem_r), int(n_elem_z))
        
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
    R_vals = np.linspace(R_int, R_ext, 1000) # Passando para mm
    Z_val = H / 2.0
    
    u_r_mef = [u_mef(r, Z_val)[0] for r in R_vals]
    u_r_mha = [u_mha(r, Z_val)[0] for r in R_vals]
    
    erro_abs = np.abs(np.array(u_r_mef) - np.array(u_r_mha))
    
    # ===== VISUALIZAÇÃO =====
    st.success("✅ Simulação concluída!")
    
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
        st.write(f"- Camadas Modeladas: **{N_camadas}**")
        st.write(f"- Elementos Radiais (n_elem_r): **{n_elem_r}**")
        st.write(f"- Elementos Axiais (n_elem_z): **{n_elem_z}**")
        st.write(f"- Total de Elementos: **{n_elem_r * n_elem_z}**")
        
        elementos_por_camada = n_elem_r / N_camadas
        if elementos_por_camada < 1:
            st.error(f"Aviso: Você tem {elementos_por_camada:.2f} elementos por camada. A malha está muito grossa para as {N_camadas} camadas, os resultados focarão em ruído.")
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
