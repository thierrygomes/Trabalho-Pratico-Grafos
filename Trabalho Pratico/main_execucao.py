import os    # Importa o módulo 'os' para interagir com o sistema operacional (ex: criar diretórios, listar arquivos)
import re    # Importa o módulo 're' para usar expressões regulares (útil para ordenar nomes de arquivos)
import time  # Importa o módulo 'time' para medir o tempo de execução
import sys   # Importa o módulo 'sys' para interagir com o sistema (ex: sair do script em caso de erro)

# Importa a função principal do otimizador da Etapa 2
# Esta função é responsável por carregar os dados, construir o grafo,
# calcular o APSP e gerar a solução inicial.
from otimizador import gerar_solucao_inicial_aprimorada 

def processar_arquivos(input_directory, output_directory):
    """
    Processa todos os arquivos .dat de um diretório de entrada, gera as soluções
    da Etapa 2 para cada um e salva os resultados em um diretório de saída.
    
    Args:
        input_directory (str): O caminho para o diretório contendo os arquivos .dat de instância.
        output_directory (str): O caminho para o diretório onde as soluções serão salvas.
    """
    # Tenta criar o diretório de saída. Se já existir, a função não faz nada (exist_ok=True).
    try:
        os.makedirs(output_directory, exist_ok=True)
    except OSError as e:
        # Em caso de erro na criação do diretório (ex: permissões), imprime uma mensagem e sai do script.
        print(f"ERRO: Não foi possível criar o diretório de saída '{output_directory}': {e}")
        print("Verifique as permissões de escrita ou se o caminho é válido.")
        sys.exit(1)

    # Tenta listar os arquivos .dat no diretório de entrada
    dat_files = []
    try:
        # Filtra apenas os arquivos que terminam com '.dat'
        raw_dat_files = [f for f in os.listdir(input_directory) if f.endswith('.dat')]
        
        # Define uma função para ordenar os arquivos numericamente.
        # Isso é útil para instâncias como 'bhw1.dat', 'bhw2.dat', 'bhw10.dat' serem ordenadas corretamente.
        def sort_key(filename):
            match = re.search(r'(\d+)', filename) # Procura por um ou mais dígitos no nome do arquivo
            if match:
                return int(match.group(1)) # Converte o número encontrado para inteiro para ordenação
            return float('inf') # Coloca arquivos sem números no final (maior valor possível)

        dat_files = sorted(raw_dat_files, key=sort_key) # Aplica a ordenação personalizada

    except FileNotFoundError:
        # Se o diretório de entrada não for encontrado, imprime um erro crítico e sai.
        print(f"ERRO CRÍTICO: O diretório de entrada '{input_directory}' NÃO FOI ENCONTRADO.")
        print("Certifique-se de que o caminho 'input_directory' no código esteja correto e que a pasta exista.")
        sys.exit(1) 

    # Se nenhum arquivo .dat for encontrado, imprime um aviso e sai (sem erro, pois não há nada para processar).
    if not dat_files:
        print(f"AVISO: Nenhum arquivo .dat encontrado no diretório: '{input_directory}'.")
        print("Verifique se os arquivos estão lá e se a extensão é '.dat'.")
        sys.exit(0) 

    print(f"Iniciando processamento de {len(dat_files)} arquivos .dat...")
    print(f"Arquivos de entrada em: '{input_directory}'")
    print(f"Arquivos de saída serão salvos em: '{output_directory}'\n")

    processed_count = 0 # Contador de arquivos processados
    start_time_batch = time.perf_counter() # Marca o tempo de início do processamento em lote

    # Itera sobre cada arquivo .dat encontrado
    for dat_file in dat_files:
        processed_count += 1
        current_file_start_time = time.perf_counter() # Marca o tempo de início para o arquivo atual

        # Constrói os caminhos completos para o arquivo de entrada e para o arquivo de saída
        full_instance_filepath = os.path.join(input_directory, dat_file) # Caminho completo do arquivo de instância
        
        # Formata o nome do arquivo de saída (ex: "instancia.dat" -> "sol-instancia.dat")
        output_filename_base = "sol-" + dat_file
        full_output_filepath = os.path.join(output_directory, output_filename_base) # Caminho completo do arquivo de saída

        print(f"[{processed_count}/{len(dat_files)}] Processando: '{dat_file}'...")

        try:
            # Chama a função principal da Etapa 2 para gerar a solução inicial
            # Retorna custo total, número de rotas, tempo de execução total, tempo de APSP e os dados das rotas.
            total_cost, num_routes, clocks_ref_exec, clocks_ref_find, routes_data = \
                gerar_solucao_inicial_aprimorada(full_instance_filepath)
            
            # Abre o arquivo de saída no modo de escrita ('w')
            with open(full_output_filepath, 'w') as f:
                # Escreve o custo total (inteiro) da solução
                f.write(f"{int(total_cost)}\n")
                # Escreve o número total de rotas
                f.write(f"{num_routes}\n")
                # Escreve o tempo total de execução da Etapa 2 (em milissegundos)
                f.write(f"{int(clocks_ref_exec)}\n")
                # Escreve o tempo de cálculo da matriz APSP (em milissegundos)
                f.write(f"{int(clocks_ref_find)}\n")

                # Itera sobre cada rota gerada para formatar e escrever no arquivo
                for route in routes_data:
                    total_visits_in_route = len(route['visits']) # Conta o número de visitas na rota
                    # Formata a linha da rota conforme o padrão exigido
                    route_line = f"0 1 {route['route_id']} {int(route['demand'])} {int(route['cost'])} {total_visits_in_route}" 

                    # Adiciona os detalhes de cada visita (Depósito ou Serviço)
                    for visit_type, service_id, from_node, to_node in route['visits']:
                        if visit_type == 'D':
                            route_line += f" (D {service_id},{from_node},{to_node})" # Formato para visita ao Depósito
                        elif visit_type == 'S':
                            route_line += f" (S {service_id},{from_node},{to_node})" # Formato para visita a Serviço
                    f.write(route_line + "\n") # Escreve a linha da rota no arquivo, seguida de uma quebra de linha
            
            # Calcula e imprime o tempo que levou para processar o arquivo atual
            elapsed_time_file = (time.perf_counter() - current_file_start_time) * 1000 # em milissegundos
            print(f"  Concluído: '{os.path.basename(full_output_filepath)}' em {elapsed_time_file:.2f} ms")

        except Exception as e:
            # Em caso de qualquer erro durante o processamento de um arquivo, imprime a mensagem de erro.
            print(f"  ERRO ao processar '{dat_file}': {type(e).__name__}: {e}")
            print(f"  Saída para '{os.path.basename(full_output_filepath)}' pode estar incompleta ou ausente.")
        print("-" * 50) # Imprime um separador visual entre os arquivos processados

    end_time_batch = time.perf_counter() # Marca o tempo final do processamento em lote
    total_elapsed_batch_time = (end_time_batch - start_time_batch) # Calcula o tempo total em segundos

    print(f"\n--- Processamento de todos os arquivos concluído ---")
    print(f"Total de arquivos processados: {processed_count}")
    print(f"Tempo total de execução: {total_elapsed_batch_time:.2f} segundos")
    print(f"Todos os arquivos de saída foram gerados em: '{output_directory}'")

# Este bloco garante que o código abaixo só será executado quando o script for chamado diretamente
if __name__ == "__main__":
    # 1. ***CONFIGURAÇÃO DO DIRETÓRIO DE ENTRADA***
    # Define a pasta onde os arquivos de instância (.dat) estão localizados.
    input_directory = "instancias" 

    # 2. ***CONFIGURAÇÃO DO DIRETÓRIO DE SAÍDA***
    # Define a pasta onde os arquivos de solução da Etapa 2 serão salvos.
    output_directory = "saidas" 
    
    # Chama a função principal para iniciar o processamento dos arquivos
    processar_arquivos(input_directory, output_directory)