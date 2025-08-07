# Simulação de Captura de Estado Global com Clocks de Lamport

Este projeto é uma implementação em Python de uma simulação de sistema distribuído, desenvolvida para a disciplina de **Sistemas Distribuídos** do Instituto Federal da Bahia (IFBA) - Campus Santo Antônio de Jesus.

O objetivo principal é aplicar e visualizar o funcionamento de algoritmos fundamentais para a computação distribuída, especificamente os **Relógios Lógicos de Lamport** e o algoritmo de **Captura de Estado Global de Chandy-Lamport**.

## 1. Visão Geral do Projeto

A simulação consiste em três processos que se comunicam concorrentemente através de sockets. Cada processo mantém um estado local simples (um contador) e um relógio lógico de Lamport para ordenar os eventos de forma causal.

O sistema demonstra como é possível capturar um *snapshot* global consistente (o estado de todos os processos e as mensagens em trânsito nos canais de comunicação) sem interromper a execução normal do sistema, conforme o algoritmo de Chandy-Lamport.

## 2. Conceitos Implementados

### 2.1. Relógios Lógicos de Lamport

Para garantir uma ordenação causal dos eventos, cada processo implementa um relógio lógico que segue duas regras fundamentais:

1.  **Incremento Local:** Antes de qualquer evento (geração interna ou envio de mensagem), o relógio do processo é incrementado.
2.  **Atualização no Recebimento:** Ao receber uma mensagem, o processo ajusta seu relógio para `max(relógio_local, timestamp_recebido) + 1`.

### 2.2. Algoritmo de Captura de Estado de Chandy-Lamport

O núcleo da simulação é a implementação do algoritmo de snapshot, que opera da seguinte forma:

1.  **Iniciação:** Um processo (o coordenador) inicia o snapshot, gravando seu próprio estado e enviando uma mensagem especial de **marcador** (*marker*) para todos os outros processos.
2.  **Gravação de Estado:** Ao receber um marcador pela primeira vez, um processo imediatamente grava seu estado local e retransmite o marcador para seus pares.
3.  **Captura de Mensagens em Trânsito:** Após gravar seu estado, um processo começa a registrar todas as mensagens que chegam de canais dos quais ainda não recebeu um marcador. Essas mensagens representam o estado do canal (mensagens "em voo").
4.  **Finalização:** Quando um processo recebe marcadores de todos os canais, sua parte do snapshot está completa. Ele envia seu estado local e os estados dos canais capturados para o coordenador, que consolida e exibe o estado global consistente.

## 3. Estrutura do Código

O projeto está organizado de forma modular para separar as responsabilidades, utilizando threads para simular o paralelismo conforme sugerido na atividade:

-   `main.py`: Arquivo principal que inicializa os três processos, define as portas e inicia a simulação, incluindo o gatilho para o snapshot.
-   `process.py`: Contém a classe `Process`, que encapsula toda a lógica de um processo distribuído, incluindo o servidor de sockets, a geração de eventos, o relógio de Lamport e a implementação completa do algoritmo de Chandy-Lamport.
-   `utils.py`: Módulo utilitário que contém a implementação da classe `LamportClock` e a função de log.

## 4. Como Executar

Para executar a simulação, basta rodar o arquivo `main.py` em um ambiente com Python 3.

```bash
python main.py
