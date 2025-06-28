# GCC218/GCC262 - Trabalho Prático em Grafos

Este repositório contém a implementação do trabalho prático das disciplinas **GCC218 - Algoritmos em Grafos** e **GCC262 - Grafos e Suas Aplicações**, ministradas na Universidade Federal de Lavras (UFLA), sob orientação do professor **Mayron César O. Moreira**.

---

## 🎯 Objetivo

Realizar o pré-processamento de instâncias do problema logístico com grafos direcionados e não-direcionados, implementando a leitura dos dados e cálculo de estatísticas estruturais do grafo. O trabalho também visa desenvolver algoritmos para encontrar soluções iniciais e aprimoradas para o problema de roteamento de veículos com serviços em nós, arestas e arcos.

---

## 📂 Estrutura do Projeto

A organização do projeto foi aprimorada e agora segue uma estrutura modularizada para melhor organização, manutenibilidade e reusabilidade do código.

TrabalhoPratico/

├── instancias/                 # Contém os arquivos de instâncias de entrada (.dat)

├── saidas/                     # Armazena os arquivos de saída gerados pela Etapa 2 (solução inicial)

├── saidas_Melhoradas/          # Armazena os arquivos de saída gerados pela Etapa 3 (solução aprimorada)

├── analise_grafo_visualizacao.ipynb  # Notebook Jupyter para análise e visualização de grafos

├── grafo_estatisticas.py       # Módulo com funções para construção do grafo e cálculo de estatísticas

├── leitor_dados.py             # Módulo responsável pela leitura e parsing dos dados dos arquivos .dat

├── main_execucao.py            # Script principal para a execução da Etapa 2 (solução inicial) em lote

├── main_execucao_etapa3.py     # Script principal para a execução da Etapa 3 (solução aprimorada) em lote

├── otimizador.py               # Módulo contendo a lógica da solução inicial (Etapa 2)

├── otimizador_melhorado.py     # Módulo contendo a lógica de aprimoramento da solução (Etapa 3), incluindo operadores de busca local

└── README.md                   # Explicação do projeto e suas etapas

---

## 🚀 Etapas do Desenvolvimento

### Etapa 1: Pré-processamento e Estatísticas

Esta etapa focou na implementação da leitura de dados e no cálculo de estatísticas estruturais de grafos direcionados e não-direcionados. As funções de leitura (em `leitor_dados.py`) e as estatísticas do grafo (em `grafo_estatisticas.py`) foram modularizadas para uma arquitetura de código mais limpa e reutilizável.

### Etapa 2: Solução Inicial

Nesta etapa, foi desenvolvido um algoritmo construtivo para o problema. O módulo `otimizador.py` contém a implementação da solução inicial, que respeita a capacidade dos veículos e garante que cada serviço seja executado por exatamente uma rota. O script `main_execucao.py` orquestra a execução da Etapa 2 para múltiplas instâncias.

### Etapa 3: Métodos de Melhoria

A Etapa 3 aprimora a solução construtiva da Etapa 2 através da aplicação de heurísticas de busca local. O módulo `otimizador_melhorado.py` é o responsável por esta fase, incorporando:
* Um algoritmo construtivo interno para gerar a solução inicial (evitando dependências externas e duplicidade de cálculo de APSP).
* Cálculo otimizado do All-Pairs Shortest Path (APSP), paralelizado para melhor desempenho em instâncias grandes.
* Operadores de busca local, como 2-opt, Relocate Intra-rota e Relocate Inter-rota, que tentam reduzir o custo total das rotas através de rearranjos dos serviços.
* Estratégias de Variable Neighborhood Descent (VND) para iterar sobre os operadores e buscar melhorias contínuas.

O script `main_execucao_etapa3.py` é utilizado para executar esta fase de otimização em lote, salvando as soluções aprimoradas na pasta `saidas_Melhoradas/`.

---

## 📊 Estatísticas Calculadas

Os módulos `leitor_dados.py` e `grafo_estatisticas.py` em conjunto são responsáveis por processar as instâncias e calcular as seguintes informações estruturais do grafo, que são essenciais para o entendimento da instância e para as etapas de otimização:

1.  Quantidade de vértices
2.  Quantidade de arestas
3.  Quantidade de arcos
4.  Quantidade de vértices requeridos
5.  Quantidade de arestas requeridas
6.  Quantidade de arcos requeridos
7.  Densidade do grafo (incluindo a métrica "Order Strength" para grafos direcionados)
8.  Componentes conectados
9.  Grau mínimo e máximo dos vértices
10. Intermediação dos nós (Betweenness Centrality), que mede a frequência com que um nó aparece nos caminhos mais curtos entre outros nós
11. Caminho médio (Average Shortest Path Length)
12. Diâmetro do grafo

Importante: A matriz de caminhos mais curtos de múltiplas fontes (APSP) é um produto fundamental da Etapa 1 e é utilizada por diversas métricas e pelos algoritmos construtivos e de busca local.

---
## 👥 Dupla

* **Thierry Jacinto Gomes**
* **Glaucia Flavia de Lima**

---
