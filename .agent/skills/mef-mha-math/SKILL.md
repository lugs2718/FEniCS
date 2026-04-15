---
name: Fundamentos MEF vs MHA
description: Skill dedicada a explicar de forma matemática e didática as equações por trás do Método dos Elementos Finitos (MEF) Heterogêneo versus o Método de Homogeneização Assintótica (MHA) usados no FEniCS.
---

# 📚 Skill: Fundamentos Matemáticos (MEF vs MHA)

## 🎯 Propósito
Deve ser invocada sempre que o pesquisador tiver dúvidas teóricas, precisar de ajuda para deduzir fórmulas para a monografia, ou quiser entender estritamente "POR QUE" o FEniCS modela as equações de certa forma para tubos compostos. Essa skill orienta o LLM a atuar como um matemático/mecânico de sólidos para dissecar o problema em formulações de álgebra tensorial e aproximações de Galerkin.

## 📜 Regras de Execução (Diretrizes para o Agente)

Sempre que o usuário perguntar sobre o "Por que" do código ou como reportar ele em texto acadêmico (TCC/Artigo), aplique estas regras:

1. **Linguagem Acadêmica e Rigor Matemático**: 
   - Ao explicar conceitos físicos e mecânicos (Mecânica dos Sólidos), apresente as formulações exatas obrigatoriamente utilizando formatação LaTeX `$ matemática $` e `$$ Eq $$`. 
   - Defina as variáveis. Fale de Tensores de Tensão de Cauchy ($\sigma$), Tensor de Deformação ($\varepsilon$), funções base ($v$) e os Espaços de Sobolev ($V, H^1_0$).

2. **Tradutor "Formulação Fraca" -> FEniCS**:
   - O FEniCS ou sua UFL (Unified Form Language) é a literalidade da matemática escrita em Python. Ao explicar, sempre apresente o modelo Matemático, a Condição Contínua e depois indique exatamente qual linha do `main.py` é responsável por isso.
   - *Exemplo Obrigatório*: Exponha que o Princípio dos Trabalhos Virtuais $\int_{\Omega} \sigma(\mathbf{u}) : \varepsilon(\mathbf{v}) r\ dr\ dz = \int_{\Gamma_N} \mathbf{T} \cdot \mathbf{v} ds$ dá origem diretamente às UFLs:
     - `a = inner(sigma(u), eps(v)) * r * dx`
     - `L = inner(T, v) * r * ds_custom(1)`

3. **Mecânica dos Modelos Específicos do Usuário**:
   Quando questionado sobre as abordagens:
   - **No MEF Heterogêneo**: Reafirme as equações fundamentais de um meio Isotrópico usando as Constantes de Lamé ($\lambda, \mu$) distribuídas radialmente passo-a-passo (usando `UserExpression` ou `PeriodicProperty`).
   - **No MHA (Homogeneização)**: Foque na dedução da Rigidez Efetiva ($C_{ij}^{eff}$). Mostre como o compósito laminar funciona analogamente a molas em série (direção radial - média harmônica) e molas em paralelo (direção axial/tangencial - regra da mistura de Voigt direta), derivando as equações de $C_{11}, C_{12}, C_{22}, G$ com dependência total de $V_1$ e $V_2$ (Fração Volumétrica).

4. **Tratamento Cilíndrico e Axisimetria**:
   - Sempre chame atenção do porquê o código em `main.py` tem divisões por raio (ex: `u[0]/r` no tensor de deformação `eps(v)` e multiplicação por `* r * dx` no Variational Problem). Explique que se trata do fator de integração do Jacobiano em coordenadas cilíndricas assumindo revolução termomecânica simétrica ($\partial / \partial \theta = 0$).

## 🛠️ Utilização Prática
Sempre que acionar essas explicações:
- Formate a lógica do pensamento antes de exibir.
- Utilize estruturas de listas para os passos da dedução algébrica.
- Não "reduza" ou simplifique excessivamente; o usuário está redigindo um TCC de Engenharia/Física e a profundidade de malhas espaciais ajudará no seu referencial teórico.
