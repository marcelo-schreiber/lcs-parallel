import pandas as pd
import numpy as np

# Carregar os dados
mpi_data = pd.read_csv('csvs/mpi.csv')

# Threads e tamanhos desejados
threads_list = [1, 2, 4, 6, 8, 10, 12, 14, 16]
lengths_list = [10000, 20000, 40000, 60000, 80000, 100000]

# Filtrar dados válidos
mpi_data = mpi_data[mpi_data['np'].isin(threads_list) & mpi_data['length'].isin(lengths_list)]

# Dados sequenciais
sequential_data = mpi_data[mpi_data['np'] == 1].copy()
sequential_times = dict(zip(sequential_data['length'], sequential_data['user_avg']))
mpi_data['sequential_time'] = mpi_data['length'].map(sequential_times)

# Calcular métricas
mpi_data['speedup'] = mpi_data['sequential_time'] / mpi_data['user_avg']
mpi_data['efficiency'] = mpi_data['speedup'] / mpi_data['np']

speedup_table = mpi_data.pivot(index='length', columns='np', values='speedup')
efficiency_table = mpi_data.pivot(index='length', columns='np', values='efficiency')

def generate_tikz_tempos():
    latex = """\\begin{figure}[htpb]
\\centering
\\setlength\\figureheight{3cm}
\\setlength\\figurewidth{9.0cm}
\\begin{tikzpicture}
\\begin{axis}[
    width=.95\\figurewidth,
    height=1.8\\figureheight,
    xlabel={Tamanho},
    ylabel={Tempo médio (s)},
    legend pos=north west,
    error bars/y dir=both,
    error bars/y explicit,
    error bars/error bar style={line width=1.5pt},
    error bars/error mark options={line width=1.5pt},
    y label style={at={(axis description cs:-0.1,.5)},anchor=south},
    log ticks with fixed point,
    xtick={10000,20000,40000,60000,80000,100000},
    xticklabels={10K,20K,40K,60K,80K,100K},
    grid=both,
]
% Sequencial
\\addplot+[color=black,mark=star,mark options={fill=black}] plot coordinates {
"""
    for _, row in sequential_data.iterrows():
        length = int(row['length'])
        avg = row['user_avg']
        dev = row['user_dev']
        latex += f"    ({length},{avg:.6f}) +- (0,{dev:.6f})\n"
    latex += """};
\\addlegendentry{Sequencial}
"""

    threads_to_plot = [2, 4, 6, 8, 10, 12, 14, 16]
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'cyan', 'magenta', 'brown']
    marks = ['*', 'diamond*', 'triangle*', 'pentagon*', 'square*', 'o', 'x', '+']

    for i, threads in enumerate(threads_to_plot):
        thread_data = mpi_data[mpi_data['np'] == threads].sort_values('length')
        if not thread_data.empty:
            latex += f"% {threads} Threads\n\\addplot+[color={colors[i]},mark={marks[i]}] plot coordinates {{\n"
            for _, row in thread_data.iterrows():
                length = int(row['length'])
                avg = row['user_avg']
                dev = row['user_dev']
                latex += f"    ({length},{avg:.6f}) +- (0,{dev:.6f})\n"
            latex += "};\n"
            latex += f"\\addlegendentry{{{threads} Threads}}\n"

    latex += """\\end{axis}
\\end{tikzpicture}
\\caption{Tempo médio de execução com desvio padrão para diferentes tamanhos e número de threads}
\\label{fig:exec-tempos-final}
\\end{figure}"""
    return latex

def generate_tikz_escalabilidade_forte():
    fixed_length = 100000
    data = mpi_data[mpi_data['length'] == fixed_length].sort_values('np')
    if data.empty:
        return "% Nenhum dado para escalabilidade forte"
    latex = """\\begin{figure}[htbp]
\\centering
\\setlength{\\figurewidth}{8cm}
\\setlength{\\figureheight}{3.5cm}
\\begin{tikzpicture}
\\begin{axis}[
    width=.95\\figurewidth,
    height=\\figureheight,
    xlabel={Threads (com entrada $N = 100.000$)},
    ylabel={Tempo real (s)},
    xtick={""" + ",".join(str(int(n)) for n in data['np']) + """},
    grid=both,
    error bars/y dir=both,
    error bars/y explicit,
    error bars/error bar,
    error bars/error mark,
    ymin=0,
    legend pos=north east,
    y label style={at={(axis description cs:-0.1,.5)},anchor=south},
]
\\addplot+[color=blue,mark=*] coordinates {
"""
    for _, row in data.iterrows():
        np_val = int(row['np'])
        avg = row['user_avg']
        std = row['user_dev']
        latex += f"    ({np_val},{avg:.3f}) +- (0,{std:.3f})\n"
    latex += """};
\\end{axis}
\\end{tikzpicture}
\\caption{Escalabilidade forte: tempo real com entrada fixa ($N=100.000$)}
\\label{fig:esc_forte}
\\end{figure}"""
    return latex

def generate_tikz_escalabilidade_fraca():
    data = mpi_data[mpi_data.apply(lambda row: row['length'] == row['np'] * 10000, axis=1)].sort_values('np')
    if data.empty:
        return "% Nenhum dado para escalabilidade fraca"
    latex = """\\begin{figure}[htbp]
\\centering
\\setlength{\\figurewidth}{8cm}
\\setlength{\\figureheight}{3.5cm}
\\begin{tikzpicture}
\\begin{axis}[
    width=.95\\figurewidth,
    height=\\figureheight,
    xlabel={Threads (com entrada $N = 10.000 \\times \\text{threads}$)},
    ylabel={Tempo real (s)},
    xtick={""" + ",".join(str(int(n)) for n in data['np']) + """},
    grid=both,
    error bars/y dir=both,
    error bars/y explicit,
    error bars/error bar,
    error bars/error mark,
    ymin=0,
    legend pos=north west,
    y label style={at={(axis description cs:-0.1,.5)},anchor=south},
]
\\addplot+[color=red,mark=*] coordinates {
"""
    for _, row in data.iterrows():
        np_val = int(row['np'])
        avg = row['user_avg']
        std = row['user_dev']
        latex += f"    ({np_val},{avg:.3f}) +- (0,{std:.3f})\n"
    latex += """};
\\end{axis}
\\end{tikzpicture}
\\caption{Escalabilidade fraca: tempo real com carga proporcional ($N = 10.000 \\times$ threads)}
\\label{fig:esc_fraca}
\\end{figure}"""
    return latex

def generate_latex_table(df, caption):
    latex = "\\begin{tabular}{|" + "c|" * (len(df.columns) + 1) + "}\n\\hline\n"
    latex += "N / Threads" + ''.join(f" & {col}" for col in sorted(df.columns)) + " \\\\ \n\\hline\n"
    for idx in df.index:
        latex += f"{idx:,}"
        max_val = df.loc[idx].max()
        for col in sorted(df.columns):
            val = df.loc[idx, col]
            if pd.notna(val):
                bold = "\\textbf{" if abs(val - max_val) < 0.01 else ""
                endbold = "}" if abs(val - max_val) < 0.01 else ""
                latex += f" & {bold}{val:.2f}{endbold}"
            else:
                latex += " & -"
        latex += " \\\\ \n"
    latex += "\\hline\n\\end{tabular}"
    return latex

# SAÍDAS
print("=== GRÁFICO TEMPO EXECUÇÃO ===")
print(generate_tikz_tempos())

print("\n=== ESCALABILIDADE FORTE ===")
print(generate_tikz_escalabilidade_forte())

print("\n=== ESCALABILIDADE FRACA ===")
print(generate_tikz_escalabilidade_fraca())

print("\n=== TABELA DE SPEEDUP ===")
print(generate_latex_table(speedup_table, "Speedup"))

print("\n=== TABELA DE EFICIÊNCIA ===")
print(generate_latex_table(efficiency_table, "Eficiência"))
