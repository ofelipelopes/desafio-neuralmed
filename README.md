# Desafio Neuralmed

Este projeto possui dois endpoints:
		
- [POST] /patients: Que recebe os dados de um paciente, os processa usando [clinicalnerpt-disorder](https://huggingface.co/pucpr/clinicalnerpt-disorder/tree/main) e os envia para uma fila no RabbitMQ. Caso um paciente seja diagnosticado com câncer (ou na abreviação CA), coloca-se uma tag "cancer_detected" e salva a data junto com o diagnostico. 
		
- [GET] /patients/{patient_id}: Que recebe um ID de um paciente e retorna uma lista com os resultados de seus atendimentos.

## Instalação & Execução

Entre na pasta /app, dentro do projeto, e execute o comando:

```bash
docker-compose up
```
Acesse pelo navegador:
```bash
http://localhost:8000/
```

## Bibliotecas utilizadas:
fastapi, uvicorn
pydantic,
pika,
torch,
transformers.

## Sobre a arquitetura:
Foi mantida uma arquitetura mais simples, devido a baixa complexidade do projeto. Com um maior numero de features, rotas ou até adição de um DB, é interessante separar as rotas em um diretório próprio e usar o ApiRouter do fastapi.

## Resposta da pergunta extra:
Uma opção seria mudar o delivery_mode do RabbitMQ no código, desativando as mensagens persistentes, que são salvas no HD, permitindo elas serem armazenadas em memoria, possuindo processos de leitura/escrita mais rápidos.

Existe a opção de usar o [Celery](https://docs.celeryq.dev/en/stable/), permitindo escalar de forma horizontal usando queues assíncronas, além de funcionar muito bem em conjunto com o RabbitMQ.
