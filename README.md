# 🪙 AlertaCripto

Um sistema full-stack completo para monitoramento de preço de Bitcoin, com um backend em Python (FastAPI) e um aplicativo cliente para Android (Java). O sistema envia notificações push em tempo real quando um alvo de preço de compra ou venda é atingido.

*(Sugestão: Grave um GIF do seu app funcionando e substitua o link desta imagem\!)*

## 📋 Sobre o Projeto

Este projeto foi desenvolvido como um sistema completo de ponta a ponta, abrangendo desde a criação de uma API RESTful até o desenvolvimento de um aplicativo mobile nativo. A aplicação permite que o usuário defina alertas de preço para o Bitcoin e seja notificado em tempo real via push notification quando o mercado atinge os valores definidos.

Toda a lógica de monitoramento, consulta a APIs externas e envio de notificações é centralizada no backend, garantindo eficiência e desacoplamento do cliente mobile.

## ✨ Funcionalidades

  * **Monitoramento em Tempo Real:** O backend verifica o preço do Bitcoin (BRL) a cada 3 minutos usando a API do Mercado Bitcoin.
  * **Alertas Personalizados:** O usuário pode definir alvos de preço para compra (quando o preço cair) e venda (quando o preço subir) através do aplicativo Android.
  * **Notificações Push:** Utiliza o Firebase Cloud Messaging (FCM) para enviar alertas instantâneos para o dispositivo do usuário assim que um preço-alvo é alcançado.
  * **Persistência de Dados:** Alertas e tokens de dispositivos são armazenados de forma segura em um banco de dados NoSQL na nuvem (MongoDB Atlas).
  * **Arquitetura Profissional:** Clara separação entre o backend (lógica de negócio) e o frontend (interface do usuário), comunicando-se através de uma API RESTful.

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído com um ecossistema de tecnologias modernas:

#### **Backend**

  * **Linguagem:** [Python 3](https://www.python.org/)
  * **Framework API:** [FastAPI](https://fastapi.tiangolo.com/)
  * **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
  * **Banco de Dados:** [MongoDB](https://www.mongodb.com/pt-br) com [PyMongo](https://pymongo.readthedocs.io/en/stable/)
  * **Notificações:** [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
  * **Configuração:** [python-dotenv](https://pypi.org/project/python-dotenv/)

#### **Frontend (Mobile)**

  * **Linguagem:** [Java](https://www.java.com/pt-BR/)
  * **Plataforma:** Android Nativo
  * **Comunicação com API:** [Retrofit 2](https://square.github.io/retrofit/)
  * **Parsing de JSON:** [Gson](https://github.com/google/gson)
  * **UI:** Layouts XML com View Binding

#### **Infraestrutura e Deploy**

  * **Banco de Dados na Nuvem:** [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
  * **Serviço de Notificação:** [Firebase Cloud Messaging (FCM)](https://firebase.google.com/docs/cloud-messaging)
  * **Plataforma de Deploy:** [Render.com](https://render.com/)
  * **Controle de Versão:** [Git](https://git-scm.com/) & [GitHub](https://github.com/)

## 🏗️ Arquitetura do Sistema

O sistema opera com uma arquitetura cliente-servidor desacoplada:

```
[App Android (Java)] <--> [API RESTful (Python/Render)] <--> [MongoDB Atlas]
        ^                                |                             |
        | (Notificação)                  | (Busca Preço)               |
        |                                V                             V
        +------------ [Firebase] <-------+-------------> [API do Mercado Bitcoin]
```

## 🚀 Como Executar o Projeto Localmente

Para executar este projeto no seu ambiente de desenvolvimento, siga os passos abaixo.

### Pré-requisitos

  * [Python 3.10+](https://www.python.org/downloads/)
  * [Git](https://git-scm.com/)
  * [Android Studio](https://developer.android.com/studio) (para o app mobile)
  * Contas nos serviços: [MongoDB Atlas](https://www.mongodb.com/cloud/atlas), [Firebase](https://firebase.google.com/) e [Render](https://render.com/).

### Configuração do Backend

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/lucassanttana25/alerta-cripto-backend.git
    cd alerta-cripto-backend
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**

    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências Python:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**

      * Crie um arquivo chamado `.env` na raiz do projeto.
      * Adicione as seguintes chaves, substituindo pelos seus valores:
        ```env
        MONGO_URI="sua_string_de_conexao_do_mongodb"
        FIREBASE_CREDENTIALS_PATH="seu_arquivo_de_credenciais.json"
        ```

5.  **Adicione o arquivo de credenciais do Firebase:**

      * Coloque o seu arquivo de credenciais do Firebase (com o nome que você especificou na variável acima) na raiz do projeto.

6.  **Execute o servidor localmente:**

    ```bash
    uvicorn main:app --reload
    ```

    A API estará disponível em `http://127.0.0.1:8000`.

### Configuração do Frontend (Android)

1.  **Abra o projeto no Android Studio:**

      * Abra o Android Studio e selecione "Open".
      * Navegue até a pasta do projeto que você clonou e selecione-a.
      * Aguarde o Gradle sincronizar o projeto.

2.  **Aponte para a API correta:**

      * No arquivo `MainActivity.java`, no método `setupRetrofit`, certifique-se de que a `baseUrl` está apontando para o endereço correto (para o servidor local `http://10.0.2.2:8000/` se estiver usando um emulador, ou para a sua URL do Render se o backend estiver na nuvem).

3.  **Execute o aplicativo:**

      * Conecte um celular com Depuração USB ou inicie um emulador.
      * Clique no botão "Play" (▶️) no Android Studio.

## Futuras Melhorias

  * [ ] Implementar um sistema de autenticação de usuários para alertas privados.
  * [ ] Adicionar suporte a outras criptomoedas.
  * [ ] Criar uma tela de histórico de alertas atingidos.
  * [ ] Desenvolver um gráfico de preços no aplicativo.
  * [ ] Melhorar a interface do usuário com animações e um design mais refinado.

-----

Feito por **Lucas Santana**.