# Dockerfile

# Passo 1: Usar uma imagem base oficial e leve do Python.
FROM python:3.11-slim

# Passo 2: Definir o diretório de trabalho dentro do container.
WORKDIR /app

# Passo 3: Copiar o arquivo de dependências para o container.
COPY requirements.txt .

# Passo 4: Instalar as dependências.
RUN pip install --no-cache-dir -r requirements.txt

# Passo 5: Copiar todos os outros arquivos do projeto para o container.
COPY . .

# Passo 6: Expor a porta 80, que será usada pelo Uvicorn.
EXPOSE 80

# Passo 7: Definir o comando que será executado quando o container iniciar.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]