# Separação da GUI (Streamlit) da Lógica de Simulação (FEniCS)

## Contexto

Atualmente o arquivo [MHA vs FEM - GUI.py](file:///c:/Users/gusta/Google%20drive/UFF/TCC%20-%20Wesley/Codigos%20produzidos%20para%20TCC/Numerical%20Solution%20via%20FEM/MHA%20vs%20FEM%20-%20GUI.py) contém **tanto** a interface Streamlit **quanto** toda a lógica do solver FEniCS embarcada diretamente no corpo do `if st.sidebar.button(...)`.

O objetivo é desacoplar:
- **GUI** (`MHA vs FEM - GUI.py`) → apenas Streamlit: inputs, botão, visualização
- **Lógica** (`MHA vs FEM - main - EDITAR APENAS ESSE.py`) → todo o solver, reutilizável

---

## Proposta de Mudanças

### Componente 1 — Lógica do Solver

#### [MODIFY] [MHA vs FEM - main - EDITAR APENAS ESSE.py](file:///c:/Users/gusta/Google%20drive/UFF/TCC%20-%20Wesley/Codigos%20produzidos%20para%20TCC/Numerical%20Solution%20via%20FEM/MHA%20vs%20FEM%20-%20main%20-%20EDITAR%20APENAS%20ESSE.py)

A função `comparar_mha_mef()` **já existe** e contém toda a lógica. Vamos apenas adaptá-la:

| Mudança | Detalhe |
|---------|---------|
| Aceitar parâmetros opcionais | `def comparar_mha_mef(R_int=9.0, R_ext=11.0, H=2.0, P_int=10e6, E1=200e9, nu1=0.3, E2=70e9, nu2=0.33, V1=0.5, N_camadas=200, n_elem_r=800, n_elem_z=10)` — todos com **defaults idênticos** aos valores hardcoded atuais |
| Retornar resultados | No final, em vez de plotar, retorna um `dict` com `R_vals`, `u_r_mef`, `u_r_mha`, `erro_abs`, `interfaces` e metadados da malha |
| Mover plotagem para `__main__` | O bloco `if __name__ == "__main__"` chama `comparar_mha_mef()`, recebe o dict, e plota com matplotlib como antes |

**Assinatura resultante:**

```python
def comparar_mha_mef(
    R_int=9.0, R_ext=11.0, H=2.0, P_int=10e6,
    E1=200e9, nu1=0.3, E2=70e9, nu2=0.33,
    V1=0.5,
    N_camadas=200, n_elem_r=800, n_elem_z=10,
    callback=None
):
    """
    Executa a simulação MEF vs MHA.
    
    callback (opcional): função callback(etapa: str), chamada entre
    cada fase para feedback visual (spinners do Streamlit, por exemplo).
    Quando None, usa print().
    
    Retorna dict com:
        R_vals, u_r_mef, u_r_mha, erro_abs, interfaces,
        N_camadas, n_elem_r, n_elem_z, total_elementos
    """
```

> [!NOTE]
> Os valores default são **exatamente** os valores hardcoded atuais. Executar `comparar_mha_mef()` sem argumentos produz o mesmo resultado de antes — nenhuma quebra de comportamento.

---

### Componente 2 — Interface Gráfica

#### [MODIFY] [MHA vs FEM - GUI.py](file:///c:/Users/gusta/Google%20drive/UFF/TCC%20-%20Wesley/Codigos%20produzidos%20para%20TCC/Numerical%20Solution%20via%20FEM/MHA%20vs%20FEM%20-%20GUI.py)

Será reescrito para conter **somente** interface Streamlit:

1. **Imports** — `streamlit`, `matplotlib`, `numpy` + importação via `importlib` da função `comparar_mha_mef` do main
2. **Sidebar com inputs** — Idêntica ao que já existe (geometria, materiais, discretização)
3. **Botão "Executar"** — Monta os parâmetros e chama `comparar_mha_mef(...)`, recebendo o dict de resultados
4. **Visualização** — Plota as 3 tabs (deslocamento, erro, log da malha) usando o dict retornado

**Nenhum código FEniCS/dolfin permanecerá neste arquivo.** O import `from dolfin import *` será removido.

```python
# Import via importlib (nome do arquivo tem espaços/hífens)
import importlib
main_module = importlib.import_module("MHA vs FEM - main - EDITAR APENAS ESSE")
comparar_mha_mef = main_module.comparar_mha_mef
```

> [!IMPORTANT]
> O nome do arquivo `main` contém espaços e hífens, impossibilitando `import` convencional. O `importlib` resolve isso sem renomear arquivos. Caso prefira renomear para algo como `mha_vs_fem_main.py`, me avise.

---

## Verificação

- `streamlit run "MHA vs FEM - GUI.py"` — funciona como antes, com parâmetros da sidebar
- `python "MHA vs FEM - main - EDITAR APENAS ESSE.py"` — funciona como antes, standalone com plotagem matplotlib
- `MHA vs FEM - GUI.py` **não** importa `dolfin`
- `MHA vs FEM - main - EDITAR APENAS ESSE.py` **não** importa `streamlit`
