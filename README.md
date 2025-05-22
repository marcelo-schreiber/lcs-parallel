# Paralelização de LCS com OpenMP

Este repositório contém a implementação paralela do algoritmo de **Longest Common Subsequence (LCS)** utilizando a biblioteca **OpenMP**.

## 🧠 Objetivo

Acelerar a execução do algoritmo LCS usando múltiplas threads, mantendo os resultados corretos e analisando o ganho de desempenho com diferentes tamanhos de entrada.

## ⚙️ Como funciona

- O algoritmo LCS compara duas sequências de caracteres e encontra a maior subsequência comum entre elas.
- A versão sequencial usa uma matriz de pontuação preenchida com programação dinâmica.
- A versão paralela divide essa matriz em blocos (tiling) e usa paralelismo em diagonais para melhorar a performance.

## 🏁 Estratégias testadas

- **Wavefront puro**: respeita dependências, mas piora o desempenho por conta de muitos cache misses e trocas de contexto.
- ✅ **Tiling + Wavefront** (final): melhora o uso de cache e reduz context switches, resultando em melhor performance geral.

## 🧪 Testes e Resultados

- As entradas variaram de 10.000 a 80.000 caracteres.
- A versão com tiling reduziu drasticamente os context switches em comparação à versão alternativa.
- Apesar de mais cache misses, a redução nos context switches trouxe melhor desempenho final.

## 🖥️ Ambiente de Execução

- **SO**: Linux Mint 22.1
- **Compilador**: GCC 13.3.0
- **Processador**: Intel i5-13450HX
- **Flags de compilação**: `-O3 -march=native -mavx`

## 📄 Relatório

Para mais detalhes sobre a paralelização, estratégias testadas e tabelas com dados de performance, veja o PDF do relatório disponível neste repositório.

---
