import pandas as pd
import numpy as np

# Carregar os dados
mpi_data = pd.read_csv('mpi.csv')
sequential_data = pd.read_csv('sequential.csv')

# Criar um dicionário com os tempos sequenciais para cada tamanho
sequential_times = dict(zip(sequential_data['length'], sequential_data['user_avg']))

# Adicionar coluna de tempo sequencial aos dados MPI
mpi_data['sequential_time'] = mpi_data['length'].map(sequential_times)

# Calcular speedup
mpi_data['speedup'] = mpi_data['sequential_time'] / mpi_data['user_avg']

# Calcular eficiência
mpi_data['efficiency'] = mpi_data['speedup'] / mpi_data['np']

# Criar tabela pivot para speedup
speedup_table = mpi_data.pivot(index='length', columns='np', values='speedup')

# Criar tabela pivot para eficiência
efficiency_table = mpi_data.pivot(index='length', columns='np', values='efficiency')

# Função para gerar gráfico TikZ de tempos de execução
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
    
    # Dados sequenciais
    for _, row in sequential_data.iterrows():
        length = int(row['length'])
        avg = row['user_avg']
        dev = row['user_dev']
        latex += f"        ({length},{avg:.6f}) +- (0,{dev:.6f})\n"
    
    latex += """    };
    \\addlegendentry{Sequencial}
"""
    
    # Dados MPI para threads específicas
    threads_to_plot = [4, 8, 10, 14, 16]
    colors = ['red', 'green', 'orange', 'cyan', 'purple']
    marks = ['diamond*', 'triangle*', 'pentagon*', 'otimes*', 'square*']
    
    for i, threads in enumerate(threads_to_plot):
        thread_data = mpi_data[mpi_data['np'] == threads].sort_values('length')
        latex += f"    % {threads} Threads\n"
        latex += f"    \\addplot+[color={colors[i]},mark={marks[i]}] plot coordinates {{\n"
        
        for _, row in thread_data.iterrows():
            length = int(row['length'])
            avg = row['user_avg']
            dev = row['user_dev']
            latex += f"        ({length},{avg:.6f}) +- (0,{dev:.6f})\n"
        
        latex += "    };\n"
        latex += f"    \\addlegendentry{{{threads} Threads}}\n"
    
    latex += """    \\end{axis}
    \\end{tikzpicture}
    \\caption{Tempo médio de execução com desvio padrão para diferentes tamanhos e número de threads}
    \\label{fig:exec-tempos-final}
\\end{figure}"""
    
    return latex

# Função para gerar LaTeX da tabela de speedup
def generate_latex_speedup_table(speedup_df):
    latex = "\\begin{tabular}{|c|c|c|c|c|c|c|c|c|}\n"
    latex += "\\hline\n"
    latex += "N / Threads"
    
    for col in speedup_df.columns:
        latex += f" & {col}"
    latex += " \\\\ \n\\hline\n"
    
    for idx in speedup_df.index:
        latex += f"{idx:,}"
        max_val = speedup_df.loc[idx].max()
        
        for col in speedup_df.columns:
            val = speedup_df.loc[idx, col]
            if pd.notna(val):
                if abs(val - max_val) < 0.01:
                    latex += f" & \\textbf{{{val:.2f}}}"
                else:
                    latex += f" & {val:.2f}"
            else:
                latex += " & -"
        latex += " \\\\ \n"
    
    latex += "\\hline\n"
    latex += "\\end{tabular}"
    return latex

# Função para gerar LaTeX da tabela de eficiência
def generate_latex_efficiency_table(efficiency_df):
    latex = "\\begin{tabular}{|c|c|c|c|c|c|c|c|c|}\n"
    latex += "\\hline\n"
    latex += "N / Threads"
    
    for col in efficiency_df.columns:
        latex += f" & {col}"
    latex += " \\\\ \n\\hline\n"
    
    for idx in efficiency_df.index:
        latex += f"{idx:,}"
        max_val = efficiency_df.loc[idx].max()
        
        for col in efficiency_df.columns:
            val = efficiency_df.loc[idx, col]
            if pd.notna(val):
                if abs(val - max_val) < 0.01:
                    latex += f" & \\textbf{{{val:.2f}}}"
                else:
                    latex += f" & {val:.2f}"
            else:
                latex += " & -"
        latex += " \\\\ \n"
    
    latex += "\\hline\n"
    latex += "\\end{tabular}"
    return latex

# SAÍDAS
print("=== GRÁFICO TEMPO EXECUÇÃO ===")
print(generate_tikz_tempos())

print("\n=== SPEEDUP TABLE ===")
print(generate_latex_speedup_table(speedup_table))

print("\n=== EFFICIENCY TABLE ===")
print(generate_latex_efficiency_table(efficiency_table))
