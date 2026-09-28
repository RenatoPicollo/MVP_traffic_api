# MVP - Minimum Viable Product

Este projeto faz parte do MVP desenvolvido para a disciplina **Desenvolvimento Full Stack Básico**

## Descrição do Projeto

Esta API foi desenvolvida com objetivo de alimentar um banco de dados através de imagens geradas por câmeras espalhadas por ruas da cidade, que identificam veículos em movimento, e capturam uma foto de sua placa. Essa imagem da placa é processada através de um algoritmo de reconhecimento e leitura de imagens utilizando a biblioteca "easyocr" para Python. Esse algoritmo lê a placa do carro, realiza um pós processamento visando eliminar ambiguidades de interpretação do modelo e chama uma algoritmo de criptografia SHA-256, cujo objetivo é proteger a informação da placa do carro, baseado na LGPD. Esses dados são armazenados numa tabela de um banco de dados SQL chamada "registro", que contém os seguintes dados: "id" (primary key gerada através da placa do carro criptografada, juntamente com a data e hora da imagem obtida), "placa_criptografada", "data", "hora" e "local_id". Essa última coluna, possui uma referência FK com a coluna "id" da tabela chamada "local". Essa tabela possui também as colunas "nome" e "descrição". O objetivo desse sistema é coletar uma quantidade massiva de dados dos veículos que transitam pela cidade, de forma a treinar um modelo de machine learning, que tente prever o comportamento do trânsito e ajude na tomada de decisões que impactem no fluxo de veículos como temporização de semáforos, aplicação de faixas reversíveis, etc. Para testar o sistema, foi desenvolvido uma página web, que simula o envio de imagens para o servidor.

Link para vídeo no YouTube: https://youtu.be/qNiny70rtZA

---
### Como Executar

Será necessário ter todas as libs python listadas no `requirements.txt` instaladas.

1 - Crie uma pasta chamada "MVP", que será a pasta raiz do projeto.

2 - Clone dentro da pasta "MVP" o repositório contido no endereço "https://github.com/RenatoPicollo/MVP_traffic_api". Este repositório contém a pasta "traffic_api" e o arquivo "requeriments.txt".

3 - Clone dentro da pasta "MVP" o repositório contido no endereço "https://github.com/RenatoPicollo/MVP_traffic_front". Este repositório contém a pasta "traffic_front" e o arquivo "exemplos_placas.zip", contendo dois arquivos de imagens, que deverá ser descompactado para alguma pasta de escolha do usuário.

4 - Execute os seguintes comandos na sequência apresentada (execute na pasta raiz do projeto):


C:\Users\user\AppData\Local\Programs\Python\Python39\python.exe -m venv env

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

.\env\Scripts\Activate.ps1

python -m pip install --upgrade pip

python -m pip install -r .\requirements.txt

python -c "from traffic_api.services.criptografia import gerar_nova_chave; print(gerar_nova_chave())"


5 - Crie um arquivo na pasta raiz do projeto chamado ".env". Copie do terminal a chave de criptografia gerada e cole dentro do arquivo ".env" da seguinte forma:

CHAVE_CRIPTOGRAFIA="DIGITE_AQUI_SUA_CHAVE"

6 - Execute a API através do comando abaixo:
flask --app traffic_api/app run --host 0.0.0.0 --port 5000 --reload


Abra o [http://localhost:5000/#/](http://localhost:5000/#/) no navegador para verificar o status da API em execução.

Para execução da página HTML, siga as instruções no arquivo README.md, contido na pasta "traffic_front".