---
name: FEniCS GUI Development
description: Instrui como estruturar e criar GUIs interativas (Streamlit/PyQt5) para simulações de elementos finitos no FEniCS, unindo cálculos pesados e visualização de dados.
---

# Skill de Desenvolvimento de FEniCS GUI

## Objetivo
Esta skill fornece as diretrizes e padrões para criar interfaces gráficas de usuário (GUIs) que integrem, parametrizem e executem solvers do FEniCS e exibam os resultados visualmente. Foi baseada nas melhores práticas de desenvolvimento com Streamlit e FEniCS para prototipação ágil.

## Diretrizes de Implementação

1. **Escolha do Framework GUI**:
   - Utilize ativamente **Streamlit** pra dashboards dinâmicos rápidos baseados na web. É ideal quando a interface for predominantemente orientada a parâmetros (sidebars com inputs e uma área principal de visualização).
   - Utilize **PyQt5/PyQt6** ou **Tkinter** APENAS caso seja estritamente necessário para integração desktop complexa.

2. **Fluxo da Aplicação (Arquitetura Padrão Streamlit)**:
   - **Inputs (Sidebar ou Painel):** Adquira parâmetros do problema físico ou de materiais (como E, nu, raio, etc) organizando em coleções lógicas (`st.sidebar.expander`).
   - **Gatilho de Execução:** Sempre agrupe a simulação pesada (geração de malha, assemble, solve) condicionada à ação de um botão (ex: `if st.sidebar.button("Executar"):`). Evite invocar o solver a cada alteração de slider (o que acontece por padrão no Streamlit sem o botão).
   - **Feedback Visual (Crucial):** Como processos do FEniCS rodarão repetidamente, é fundamental usar avisos como `with st.spinner("Resolvendo MEF..."):` para informar o usuário sobre o que o processo de backend está executando no momento (Cálculo Paramétrico -> Geração de Malha -> Resolve MEF).
   - **Extração e Gráficos:** Para relatórios 1D/2D baseados na extração de resultados de `Function`, prefira usar `matplotlib` instanciando um `Figure` localmente e integrando vizualizações via o método nativo `st.pyplot(fig)`. Mostre também métricas objetivas (usando `st.metric`) comparando resultados (ex: `u_max`).
   - **Layout em Abas:** Divida os resultados obtidos de forma modular usando `st.tabs(["Plot", "Erros", "Informações"])` para evitar rolagem excessiva na mesma tela.

## Recursos Incluídos Nesta Skill

- **Exemplo Completo de Aplicação Guiada**: Verifique o arquivo `examples/mef_mha_streamlit.py` que se encontra no mesmo diretório dessa skill. Trata-se de um App configurável com uma execução iterativa para avaliar Comparativo de Solvers (Heterogêneo vs Homogeneizado MHA). Esse arquivo serve de "boilerplate" da arquitetura que você deve gerar quando for criar novas interfaces FEniCS-Streamlit.

## Como Aplicar Essa Skill

Sempre que demandado ao agente montar uma interface de controle para arquivos contendo blocos FEniCS (ex: "Crie uma GUI para esse solver flexural" ou "Gere um aplicativo interativo para esse script"), faça: 

1. Avalie rapidamente as equações e identifique os parâmetros passíveis de manipulação que vão pra Sidebar.
2. Defina os inputs equivalentes no Streamlit (`number_input`, `slider`).
3. Isole o código da geração de malha, Variational Problem (`inner`, `dx`, `ds`) e de extração do Solver dentro de blocos ativados por Botão.
4. Aplique matplotlib para exibir as variáveis-resposta cruciais que a interface deve fornecer e retorne ao usuário o Dashboard pronto.
