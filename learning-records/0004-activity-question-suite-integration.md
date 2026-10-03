# Integração da Bateria de Perguntas de Negócio do CineData

O notebook `main.ipynb` foi estruturado com as 14 perguntas analíticas oficiais da atividade Visagio RocketLab, distribuídas pelas 5 dimensões de negócio (Finanças, Popularidade, Elenco, Gêneros/Produtoras e Avaliações de Usuários). Cada pergunta foi configurada com o padrão executivo e chamada ao agente seguro `run_cinedata_agente`.

## Evidence
- O agente respondeu com sucesso à pergunta piloto (contagem total de 95.645 filmes e top 3 de lucro bruto em reais com junção entre fato e dimensão).
- Todas as 5 seções e 14 subperguntas foram inseridas no `main.ipynb` respeitando a formatação estipulada pelo estudante.

## Implications
- O estudante agora pode executar as perguntas de negócio uma a uma no Jupyter, observando as chamadas de tools intermediárias e a síntese analítica final do modelo `openai/gpt-oss-120b`.
