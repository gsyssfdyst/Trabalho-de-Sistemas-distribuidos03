# Prompt para o Copilot: Refatoração para Simulação de Algoritmos de Eleição (Bully e Anel)

## 1. Avaliação do Código Existente

O código atual implementa o algoritmo de Chandy-Lamport para captura de estado global e utiliza relógios lógicos de Lamport para ordenação de eventos. O objetivo agora é transformar o projeto para simular e analisar os algoritmos de eleição distribuída Bully e Anel.

## 2. Remoção de Código Irrelevante

- Remova toda a lógica relacionada ao algoritmo de Chandy-Lamport, incluindo variáveis e métodos como `snapshot_active`, `local_snapshot`, `channel_states`, `marker_received`, `snapshots_collected`, `is_coordinator`, `_handle_marker`, `_send_marker`, `_handle_snapshot_result`, `initiate_snapshot`, etc.
- Remova a classe `LamportClock` e toda a lógica associada a relógios lógicos, pois não são necessários para os algoritmos de eleição.

## 3. Manutenção e Adaptação da Base do Projeto

- Mantenha a estrutura de processos (`Process`), a comunicação via sockets e threads.
- Mantenha o conceito de ID do processo e porta.
- Mantenha a noção de um coordenador e a capacidade de enviar mensagens entre processos.
- Adapte a lógica de geração de eventos para incluir a verificação periódica de falha do coordenador (por exemplo, usando heartbeat ou timeout).

## 4. Implementação dos Novos Algoritmos

- Implemente o algoritmo de Bully, onde processos com IDs maiores têm prioridade na eleição.
- Implemente o algoritmo de Anel, onde a eleição é feita por passagem de um token em um anel virtual de processos.

## 5. Correção do Arquivo main.py

- Altere o `main.py` para simular os cenários de falha e eleição:
    - Cenário A: O coordenador falha, ocorre uma eleição, e o coordenador original retorna.
    - Cenário B: Vários processos falham simultaneamente, e uma nova eleição precisa ser concluída.
- O `main.py` deve iniciar o algoritmo de eleição apropriado após a detecção de falha.

## 6. Atualização do Sistema de Logs

- Modifique a função de log (`log_event`) ou a lógica do `Process` para registrar eventos importantes dos algoritmos de eleição, incluindo:
    - Qual processo detectou a falha do coordenador.
    - Mensagens de eleição enviadas e recebidas.
    - Qual processo foi eleito como novo coordenador.

## 7. Atualização do README.md

- Reescreva o `README.md` para descrever a nova simulação, explicando os algoritmos de eleição Bully e Anel, como a simulação funciona, exemplos de execução e instruções de uso.

---
**Siga estas instruções para refatorar o projeto e garantir que ele atenda aos novos requisitos de simulação e análise dos algoritmos de eleição distribuída.**
