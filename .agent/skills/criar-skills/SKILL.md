---
name: Skiller (Skill Creation)
description: Diretrizes e gabarito para a criação de novas Skills para o Agente. Use esta skill ao ser incumbido de documentar, arquitetar ou criar novas skills no diretório .agent.
---

# 🧠 Skill de Criação de Skills (Skiller)

Esta skill orienta o agente em como criar e estruturar **Novas Skills** para expandir as suas próprias capacidades futuras.

## 📁 Estrutura de uma Skill

Todas as skills devem viver no diretório base do projeto (ou diretório local do agente) sob o caminho:
`.agent/skills/<nome-da-skill>/`

Toda skill é essencialmente um miniprojeto que **deve conter** obrigatoriamente um arquivo chamado `SKILL.md` na raiz de sua pasta, e pode opcionalmente conter subpastas como `examples/`, `scripts/` e `resources/`.

### O arquivo `SKILL.md`

O arquivo `SKILL.md` é a "alma" da skill e deve ser estruturado em Markdown, contendo regras que o próprio LLM (Agente) irá ler e seguir estritamente.

**Gabarito Obrigatório do `SKILL.md`:**

```yaml
---
name: [Nome Humanamente Legível da Skill]
description: [Uma descrição de 1 a 2 frases explicando exatemente quando o agente deve aplicar esta skill]
---

# [Título da Skill]

## 🎯 Propósito
Breve descrição explicando à inteligência artificial qual problema esta skill resolve e em quais contextos ela deve acionada.

## 📜 Regras de Execução (Diretrizes para o Agente)
Liste os passos ou regras arquiteturais que o LLM deve seguir à risca. Seja impositivo:
1. **Regra 1**: Use X no lugar de Y.
2. **Regra 2**: Ao criar o arquivo X, sempre importe as bibliotecas A, B e C.
3. **Regra 3**: Formate a saída de tal jeito.

## 🛠️ Subdiretórios (Opcional, porém recomendado)
- Avise o LLM da existência e da utilidade dos arquivos na pasta `examples/` para servirem de boilerplate/template na geração de código.
- Se necessário, informe sobre scripts em `scripts/` que podem ser invocados com `run_command` durante a execução da skill.

```

## 📝 Passo a Passo para o Agente (Você) Criar uma Nova Skill

Quando o usuário pedir: *"Crie uma skill para X"*:

1. **Analise o Pedido**: Entenda perfeitamente o escopo técnico. Solicite referências ou tutoriais se for algo muito nichado. Se o usuário fornecer um arquivo pré-existente como base (ex. um `task.md`), aplique a ferramenta `view_file` para lê-lo.
2. **Crie o Diretório e Estrutura**: Exemplo: `.agent/skills/nova-tecnologia`. Use `write_to_file` para salvar novos arquivos e o comando nativo que criará os subdiretórios automaticamente.
3. **Escreva o `SKILL.md`**: Imprima o arquivo utilizando o *YAML frontmatter* e os tópicos obrigatórios expostos acima. As "Regras de Execução" devem ser escritas *de agente para agente*.
4. **Extraia Códigos Preciosos**: Se houverem exemplos práticos que a skill ensina, guarde-os dentro do subdiretório `examples/meu_exemplo.py`. Isso enriquece drasticamente o poder e velocidade da skill no futuro.
5. **Reporte ao Usuário**: Uma vez finalizado, explique ao usuário o que a nova skill engloba e encerre o turno.
