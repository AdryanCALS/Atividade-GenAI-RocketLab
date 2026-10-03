# Text-to-SQL com LangChain e Guardrails Resources

## Knowledge

- [Paper: _CHESS — Contextual Harnessing for Efficient SQL Synthesis_ (Talaei et al., 2024)](https://arxiv.org/abs/2405.16755)
  O framework moderno mais influente em Text-to-SQL. Use para: compreender a separação entre Schema Linking (seleção de tabelas/colunas), recuperação de valores e validação unitária.

- [Paper: _CHASE-SQL — Multi-Path Reasoning and Candidate Selection_ (Pourreza et al., 2024)](https://arxiv.org/abs/2410.01943)
  Paper que analisa auto-correção e geração multi-caminho. Use para: entender estratégias de auto-correção e como o modelo aprende com erros de execução.

- [Paper: _BIRD — Can LLM Already Serve as a Database Interface?_ (Li et al., 2023)](https://arxiv.org/abs/2305.03111)
  O benchmark de referência para Text-to-SQL em bases reais complexas. Use para: entender as principais falhas de LLMs (valores sujos, ambiguidade de termos de negócio, joins implícitos).

- [Documentação Oficial do LangChain: Tool Calling](https://python.langchain.com/docs/concepts/tool_calling/)
  Guia oficial de como vincular funções e ferramentas a modelos com suporte nativo a chamadas de função. Use para: entender `bind_tools`, formatação de mensagens `ToolMessage` e ciclo do agente.

- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
  Padrão de segurança para aplicações de IA generativa. Use para: embasar guardrails contra injeção indireta de prompt e execução insegura de código/queries (LLM07).

- [Documentação do SQLite: PRAGMA query_only & Read-Only Connections](https://www.sqlite.org/pragma.html#pragma_query_only)
  Mecanismo nativo do SQLite para impedir qualquer escrita em disco no nível do driver. Use para: criar o guardrail de infraestrutura intransponível.

## Wisdom (Communities)

- Comunidade Visagio RocketLab 2026 (Slack/Discord de Turma)
  Canal oficial de dúvidas e mentorias da turma. Use para: alinhar regras de negócio dos dados do CineData e feedbacks de monitores.

- [LangChain Community Forum / Discord](https://discord.com/invite/langchain)
  Comunidade global de desenvolvedores de agentes com LangChain. Use para: acompanhar discussões sobre padrões de agentes e tool calling.
