# Qualificador de Leads com IA

API que analisa a mensagem de um lead, extrai as informações importantes e classifica o potencial de compra (quente, morno ou frio), de acordo com o segmento do negócio.

Projeto de estudo criado a partir da minha experiência com vendas consultivas.

## Como funciona

1. O lead envia uma mensagem (ex.: pelo WhatsApp ou formulário)
2. A API identifica o segmento e aplica os critérios de qualificação dele
3. A IA devolve um JSON padronizado com: classificação, pontuação, dados extraídos, informações que faltam, resumo e próxima ação sugerida para o vendedor

## Decisões do projeto

- **Segmentos configuráveis:** os critérios de cada nicho ficam em `segmentos.py`, separados da lógica. Adicionar um novo segmento não exige mudar o código da API.
- **Saída estruturada:** a resposta da IA segue um schema fixo, pronta para ser integrada a um CRM.
- **Redução de alucinação:** a IA usa apenas o que está escrito na mensagem e lista o que o lead não informou.

## Segmentos disponíveis

- Academia
- Mercado imobiliário

## Tecnologias

Python · FastAPI · Pydantic · Google Gemini API

## Como rodar localmente

1. Clone o repositório
2. Crie um ambiente virtual e instale as dependências: `pip install -r requirements.txt`
3. Crie um arquivo `.env` com `GEMINI_API_KEY=sua_chave`
4. Rode: `uvicorn main:app --reload`
5. Acesse `http://127.0.0.1:8000/docs`