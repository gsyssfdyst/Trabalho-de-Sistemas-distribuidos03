Simulação e Análise de Algoritmos de Eleição em Sistemas Distribuídos: Bully e Anel

Este projeto é uma implementação em Python de uma simulação de sistema distribuído, desenvolvida para a disciplina de Sistemas Distribuídos do Instituto Federal da Bahia (IFBA) - Campus Santo Antônio de Jesus.

O objetivo principal é aplicar e visualizar o funcionamento de dois algoritmos fundamentais para a computação distribuída: o Algoritmo de Eleição Bully e o Algoritmo de Eleição em Anel. A simulação permite observar como cada algoritmo se comporta frente à ausência de um coordenador e garante a eleição de um novo líder em diferentes cenários de falha.

1. Visão Geral do Projeto

A simulação consiste em um conjunto de processos que se comunicam concorrentemente através de sockets. Cada processo possui um identificador único (ID), um estado local simples (um contador) e um mecanismo para detectar a falha do coordenador. Quando a falha é detectada, um dos dois algoritmos de eleição é acionado para escolher um novo líder.

2. Conceitos Implementados

2.1. Algoritmo de Eleição Bully

Este algoritmo se baseia nos IDs dos processos. Quando um processo detecta a falha do coordenador, ele inicia a eleição:

    Envia uma mensagem de ELEIÇÃO para todos os processos com IDs maiores que o seu.

    Se nenhum processo de ID maior responder, ele se declara o novo coordenador e envia uma mensagem de COORDENADOR para todos os processos.

    Se um processo de ID maior responder com uma mensagem de OK, o processo que iniciou a eleição desiste e aguarda a proclamação de um novo líder.

2.2. Algoritmo de Eleição em Anel

Este algoritmo utiliza a passagem de um token em um anel virtual de processos, ordenados por seus IDs.

    Um processo que detecta a falha do coordenador cria um token de ELEIÇÃO contendo seu próprio ID e o passa para o próximo processo no anel.

    Cada processo que recebe o token adiciona seu ID à lista e o repassa.

    Quando o token retorna ao iniciador, ele contém a lista de todos os processos ativos. O iniciador escolhe o maior ID da lista como novo coordenador e envia uma mensagem de COORDENADOR pelo anel para anunciá-lo.

3. Estrutura do Código

O projeto está organizado de forma modular, utilizando threads para simular o paralelismo:

    main.py: Arquivo principal que inicializa os processos, define a topologia e executa os cenários de simulação.

    process.py: Contém a classe Process, que encapsula toda a lógica de um processo distribuído, incluindo o servidor de sockets, a detecção de falhas e as implementações completas dos algoritmos Bully e Anel.

    utils.py: Módulo utilitário com funções auxiliares como o registro de eventos (log_event).

4. Como Executar

Para executar a simulação, basta rodar o arquivo main.py em um ambiente com Python 3. O programa solicitará a escolha entre dois cenários:
Bash

python main.py

    Opção 1 (Bully): Simula a falha e o retorno do coordenador. O algoritmo Bully é ativado para eleger um novo líder.

    Opção 2 (Anel): Simula a falha de múltiplos processos de maior ID, e o algoritmo de Anel é ativado para eleger um novo coordenador entre os processos restantes.
