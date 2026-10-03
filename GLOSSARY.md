# Text-to-SQL & Agentes com LangChain Glossary

Vocabulário canônico para o projeto de agente Text-to-SQL seguro no CineData Analytics com LangChain e Groq.

## Segurança e Guardrails

**Guardrail Determinístico**:
Mecanismo de controle implementado puramente em código (Python, regex, AST ou flags de driver) que valida, sanitiza ou bloqueia ações de forma binária e previsível, sem depender da probabilidade de um modelo de linguagem.
_Avoid_: Prompt de segurança, filtro comportamental

**Stacked Queries (Consultas Encadeadas)**:
Técnica de injeção SQL onde o invasor finaliza uma consulta legítima com ponto e vírgula e anexa um segundo comando arbitrário (como `DROP` ou `DELETE`) na mesma transação.
_Avoid_: Injeção dupla, query combinada

**PRAGMA query_only**:
Diretiva nativa do motor em C do SQLite que bloqueia fisicamente qualquer tentativa de escrita ou alteração no arquivo de banco de dados, retornando erro imediato se uma instrução de escrita for tentada.
_Avoid_: Trava de software, modo seguro

## Orquestração e LangChain

**Tool Calling**:
Mecanismo pelo qual um modelo de linguagem detecta a necessidade de dados externos e retorna uma estrutura padronizada (JSON) contendo o nome da ferramenta e seus argumentos, delegando a execução física ao ambiente hospedeiro.
_Avoid_: Execução de função pelo modelo, automação de IA

**Schema Linking**:
Fase inicial do pipeline de Text-to-SQL que mapeia os termos em linguagem natural da pergunta do usuário às tabelas e colunas candidatas no banco de dados, evitando carregar o esquema inteiro no contexto do modelo.
_Avoid_: Dump de esquema, injeção de DDL

**ToolMessage**:
Tipo de mensagem no protocolo do LangChain que encapsula o resultado produzido pela execução local de uma ferramenta, associado ao identificador único da requisição (`tool_call_id`).
_Avoid_: Resposta da função, retorno do sistema

## Conversa

**Turno**:
Par formado por uma pergunta do usuário em linguagem natural e a resposta final do agente a ela, sem contar as chamadas de ferramenta intermediárias.
_Avoid_: Interação, mensagem

**Janela de Memória**:
Conjunto dos últimos turnos (pergunta + resposta final, sem ToolMessages) reenviados ao modelo para permitir perguntas de continuação sem estourar o orçamento de tokens.
_Avoid_: Histórico completo, contexto

**Rastro de Execução**:
Sequência ordenada de Passos que o agente executou para responder a um Turno, encerrada pela resposta final ou por uma falha. Mostra as ações do agente, não o pensamento interno do modelo.
_Avoid_: Raciocínio, trace, log do agente

**Passo**:
Uma única chamada de ferramenta dentro de um Rastro de Execução: o nome da ferramenta, os argumentos enviados pelo modelo e o resultado devolvido (incluindo, quando houver, o SQL efetivamente executado e as linhas retornadas).
_Avoid_: Etapa, iteração
