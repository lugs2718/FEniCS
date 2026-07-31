from dolfin import *
import numpy as np
import matplotlib.pyplot as plt

def comparar_mha_mef(
    R_int=9.0, R_ext=11.0, H=2.0, P_int=10e6,
    E1=200e9, nu1=0.3, E2=70e9, nu2=0.33,
    V1=0.5,
    N_camadas=200, n_elem_r=800, n_elem_z=10,
    callback=None
):
    """
    Executa a simulação comparativa MEF Heterogêneo vs MHA Homogeneizado.

    Parâmetros (todos opcionais, com defaults dos valores originais):
        R_int, R_ext : Raio interno e externo (mm)
        H            : Espessura (mm)
        P_int        : Pressão interna (Pa)
        E1, nu1      : Módulo de Young e Poisson do Material 1 (Aço)
        E2, nu2      : Módulo de Young e Poisson do Material 2 (Alumínio)
        V1           : Fração volumétrica do Material 1
        N_camadas    : Número de camadas
        n_elem_r     : Elementos na direção radial
        n_elem_z     : Elementos na direção axial
        callback     : Função callback(etapa: str) para feedback visual (ex: spinners do Streamlit).
                       Quando None, usa print().

    Retorna:
        dict com: R_vals, u_r_mef, u_r_mha, erro_abs, interfaces,
                  N_camadas, n_elem_r, n_elem_z, total_elementos
    """
    def notificar(etapa):
        if callback:
            callback(etapa)
        else:
            print(etapa)

    V2 = 1.0 - V1

    # =======================================================
    # 1. PARÂMETROS DERIVADOS
    # =======================================================
    interfaces = np.linspace(R_int, R_ext, N_camadas + 1)[1:-1] # Exclui as extremidades

    # =======================================================
    # 2. CÁLCULO DOS COEFICIENTES HOMOGENEIZADOS (MHA)
    # Baseado na Teoria de Laminação (Homogeneização Assintótica 1D)
    # =======================================================
    notificar("Calculando coeficientes homogeneizados...")

    def get_C_matrix(E, nu):
        # Retorna C11 e C12 para material isotrópico
        C11 = E * (1 - nu) / ((1 + nu) * (1 - 2 * nu))
        C12 = E * nu / ((1 + nu) * (1 - 2 * nu))
        G = E / (2 * (1 + nu))
        return C11, C12, G

    C11_1, C12_1, G_1 = get_C_matrix(E1, nu1)
    C11_2, C12_2, G_2 = get_C_matrix(E2, nu2)

    # Coeficientes Efetivos (Média Harmônica na direção radial, Aritmética nas outras)
    C11_eff = 1.0 / (V1/C11_1 + V2/C11_2)
    C12_eff = C11_eff * (V1 * C12_1/C11_1 + V2 * C12_2/C11_2)
    C22_eff = (V1*C11_1 + V2*C11_2) - (V1*(C12_1**2)/C11_1 + V2*(C12_2**2)/C11_2) + (C12_eff**2)/C11_eff
    G_eff = 1.0 / (V1/G_1 + V2/G_2)

    # =======================================================
    # 3. MALHA E FRONTEIRAS (Comum para ambos os modelos)
    # =======================================================
    notificar("Gerando malha e definindo subdomínios...")

    mesh = RectangleMesh(Point(R_int, 0.0), Point(R_ext, H), int(n_elem_r), int(n_elem_z))

    boundaries = MeshFunction("size_t", mesh, mesh.topology().dim() - 1)
    boundaries.set_all(0)
    CompiledSubDomain("near(x[0], R_int)", R_int=R_int).mark(boundaries, 1) # Parede Interna
    CompiledSubDomain("near(x[1], 0.0)").mark(boundaries, 2)                # Base
    CompiledSubDomain("near(x[1], H)", H=H).mark(boundaries, 3)             # Topo
    ds_custom = Measure("ds", domain=mesh, subdomain_data=boundaries)

    V_space = VectorFunctionSpace(mesh, "CG", 1)
    u = TrialFunction(V_space)
    v = TestFunction(V_space)
    x = SpatialCoordinate(mesh)
    r = x[0]

    # Condições de Contorno (Travando Z para simular Estado Plano 1D do seu Notebook)
    bcs = [
        DirichletBC(V_space.sub(1), Constant(0.0), boundaries, 2), # Trava base
        DirichletBC(V_space.sub(1), Constant(0.0), boundaries, 3)  # Trava topo
    ]

    T = -Constant(P_int) * FacetNormal(mesh)
    L = inner(T, v) * r * ds_custom(1)

    # =======================================================
    # 4. MODELO 1: MEF HETEROGÊNEO (Múltiplas Camadas)
    # =======================================================
    notificar("Resolvendo modelo MEF Heterogêneo...")

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
        return sym(as_tensor([[u[0].dx(0), 0, u[0].dx(1)], [0, u[0]/r, 0], [u[1].dx(0), 0, u[1].dx(1)]]))

    def sigma_mef(u):
        return lmbda_func * tr(eps(u)) * Identity(3) + 2.0 * mu_func * eps(u)

    a_mef = inner(sigma_mef(u), eps(v)) * r * dx
    u_mef = Function(V_space)
    solve(a_mef == L, u_mef, bcs)

    # =======================================================
    # 5. MODELO 2: MHA HOMOGENEIZADO (Material Equivalente)
    # =======================================================
    notificar("Resolvendo modelo MHA Homogeneizado...")

    def sigma_mha(u):
        # Tensor de tensão para o material homogeneizado transversalmente isotrópico
        err = u[0].dx(0)
        ett = u[0]/r
        ezz = u[1].dx(1)
        erz = 0.5 * (u[0].dx(1) + u[1].dx(0))

        # Leis constitutivas homogeneizadas
        srr = C11_eff*err + C12_eff*ett + C12_eff*ezz
        stt = C12_eff*err + C22_eff*ett + C12_eff*ezz
        szz = C12_eff*err + C12_eff*ett + C22_eff*ezz
        srz = 2.0 * G_eff * erz

        return as_tensor([[srr, 0, srz], [0, stt, 0], [srz, 0, szz]])

    a_mha = inner(sigma_mha(u), eps(v)) * r * dx
    u_mha = Function(V_space)
    solve(a_mha == L, u_mha, bcs)

    # =======================================================
    # 6. EXTRAÇÃO DE RESULTADOS
    # =======================================================
    notificar("Extraindo resultados...")

    R_vals = np.linspace(R_int, R_ext, 1000)
    Z_val = H / 2.0 # Extrai na metade da altura

    u_r_mef = [u_mef(r, Z_val)[0] for r in R_vals]
    u_r_mha = [u_mha(r, Z_val)[0] for r in R_vals]

    erro_abs = np.abs(np.array(u_r_mef) - np.array(u_r_mha))

    return {
        "R_vals": R_vals,
        "u_r_mef": u_r_mef,
        "u_r_mha": u_r_mha,
        "erro_abs": erro_abs,
        "interfaces": interfaces,
        "N_camadas": N_camadas,
        "n_elem_r": n_elem_r,
        "n_elem_z": n_elem_z,
        "total_elementos": n_elem_r * n_elem_z,
    }


if __name__ == "__main__":
    resultados = comparar_mha_mef()

    R_vals = resultados["R_vals"]
    u_r_mef = resultados["u_r_mef"]
    u_r_mha = resultados["u_r_mha"]
    interfaces = resultados["interfaces"]

    plt.figure(figsize=(10, 6))
    plt.plot(R_vals, u_r_mef, 'b-', label='MEF (Heterogêneo - 40 Camadas)', linewidth=1.5)
    plt.plot(R_vals, u_r_mha, 'r--', label='MHA (Homogeneizado)', linewidth=2.5)

    # Adicionando linhas de grade sutis para visualizar as interfaces
    for r_int in interfaces:
        plt.axvline(r_int, color='k', linestyle=':', alpha=0.1)

    plt.xlabel('Raio (m)', fontsize=12)
    plt.ylabel('Deslocamento Radial (m)', fontsize=12)
    plt.title('Comparação: MEF vs Homogeneização Assintótica (MHA)', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('/plots/comparacao_mha_mef.png')
    plt.show()