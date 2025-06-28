# main_execucao_etapa3.py
import os    # Importa o módulo 'os' para interagir com o sistema operacional (ex: criar diretórios, listar arquivos)
import re    # Importa o módulo 're' para usar expressões regulares (útil para ordenar nomes de arquivos)
import time  # Importa o módulo 'time' para medir o tempo de execução
import sys   # Importa o módulo 'sys' para interagir com o sistema (ex: sair do script em caso de erro)

# Importa a função principal de otimização da Etapa 3.
# Esta função é agora autocontida, ou seja, ela gerará a solução inicial e fará a busca local internamente.
from otimizador_melhorado import otimizar_solucao 

def processar_arquivos_etapa3(input_directory, output_directory_improved):
    """
    Processa todos os arquivos .dat de um diretório de entrada, gera soluções
    aprimoradas (Etapa 3) para cada um e salva os resultados em um diretório de saída dedicado.
    
    Args:
        input_directory (str): O caminho para o diretório contendo os arquivos .dat de instância.
        output_directory_improved (str): O caminho para o diretório onde as soluções melhoradas serão salvas.
    """
    # Tenta criar o diretório de saída para as soluções melhoradas.
    # Se já existir, a função não faz nada (exist_ok=True).
    try:
        os.makedirs(output_directory_improved, exist_ok=True)
    except OSError as e:
        # Em caso de erro na criação do diretório (ex: permissões insuficientes),
        # imprime uma mensagem de erro e encerra o script.
        print(f"ERRO: Não foi possível criar o diretório de saída '{output_directory_improved}': {e}")
        print("Verifique as permissões de escrita ou se o caminho é válido.")
        sys.exit(1)

    dat_files = [] # Lista para armazenar os nomes dos arquivos .dat encontrados

    # Tenta listar os arquivos no diretório de entrada
    try:
        # Lista todos os arquivos no diretório de entrada e filtra os que terminam com '.dat'
        raw_dat_files = [f for f in os.listdir(input_directory) if f.endswith('.dat')]
        
        # Define uma função para ordenar os arquivos numericamente.
        # Isso é importante para que instâncias como 'bhw1.dat', 'bhw2.dat', 'bhw10.dat' sejam processadas na ordem correta.
        def sort_key(filename):
            match = re.search(r'(\d+)', filename) # Procura por um ou mais dígitos no nome do arquivo
            if match:
                return int(match.group(1)) # Se encontrar, converte para inteiro para usar na ordenação
            return float('inf') # Se não encontrar números, coloca o arquivo no final da lista

        dat_files = sorted(raw_dat_files, key=sort_key) # Aplica a ordenação personalizada à lista de arquivos

    except FileNotFoundError:
        # Se o diretório de entrada especificado não for encontrado,
        # imprime uma mensagem de erro crítico e encerra o script.
        print(f"ERRO CRÍTICO: O diretório de entrada '{input_directory}' NÃO FOI ENCONTRADO.")
        print("Certifique-se de que o caminho 'input_directory' no código esteja correto e que a pasta exista.")
        sys.exit(1)

    # Verifica se foram encontrados arquivos .dat para processar
    if not dat_files:
        print(f"AVISO: Nenhum arquivo .dat encontrado no diretório: '{input_directory}'.")
        print("Verifique se os arquivos estão lá e se a extensão é '.dat'.")
        sys.exit(0) # Encerra o script sem erro, pois não há trabalho a ser feito

    # Mensagens iniciais de status do processamento
    print(f"Iniciando processamento da ETAPA 3 de {len(dat_files)} arquivos .dat...")
    print(f"Arquivos de instância em: '{input_directory}'")
    print(f"Arquivos de saída melhorados (Etapa 3) serão salvos em: '{output_directory_improved}'\n")

    processed_count = 0 # Contador para o número de arquivos processados
    start_time_batch = time.perf_counter() # Marca o tempo de início do processamento em lote

    # Loop principal para processar cada arquivo .dat
    for dat_file in dat_files:
        processed_count += 1 # Incrementa o contador de arquivos processados
        current_file_start_time = time.perf_counter() # Marca o tempo de início para o processamento do arquivo atual

        # Constrói o caminho completo para o arquivo de instância atual
        full_instance_filepath = os.path.join(input_directory, dat_file)
        
        # Define o nome do arquivo de saída para a solução melhorada (ex: "sol-melhorada-BHW1.dat")
        output_filename_base = "sol-" + dat_file 
        # Constrói o caminho completo para o arquivo de saída
        full_output_filepath = os.path.join(output_directory_improved, output_filename_base)

        print(f"[{processed_count}/{len(dat_files)}] Processando (Etapa 3): '{dat_file}'...")

        try:
            # Chama a função principal de otimização da Etapa 3.
            # Esta função retorna o custo total da solução melhorada, o número de rotas,
            # o tempo total de execução da Etapa 3, o tempo gasto no cálculo do APSP,
            # e os dados detalhados das rotas otimizadas.
            total_cost, num_routes, clocks_ref_exec, clocks_ref_find, routes_data = \
                otimizar_solucao(full_instance_filepath) # A função agora é autocontida e precisa apenas do caminho da instância
            
            # Abre o arquivo de saída no modo de escrita ('w') para salvar os resultados
            with open(full_output_filepath, 'w') as f:
                f.write(f"{int(total_cost)}\n")         # Escreve o custo total da solução (inteiro)
                f.write(f"{num_routes}\n")             # Escreve o número total de rotas
                f.write(f"{int(clocks_ref_exec)}\n")    # Escreve o tempo total de execução da Etapa 3 (em ms)
                f.write(f"{int(clocks_ref_find)}\n")    # Escreve o tempo gasto no cálculo do APSP (em ms)

                # Itera sobre cada rota na solução otimizada para formatar e escrever seus detalhes
                for route in routes_data:
                    total_visits_in_route = len(route['visits']) # Obtém o número de visitas na rota
                    # Constrói a linha da rota no formato específico: "0 1 route_id demand cost total_visits"
                    route_line = f"0 1 {route['route_id']} {int(route['demand'])} {int(route['cost'])} {total_visits_in_route}" 

                    # Adiciona os detalhes de cada visita (Depósito 'D' ou Serviço 'S')
                    for visit_type, service_id, from_node, to_node in route['visits']:
                        if visit_type == 'D':
                            route_line += f" (D {service_id},{from_node},{to_node})" # Formato para visita ao Depósito
                        elif visit_type == 'S':
                            route_line += f" (S {service_id},{from_node},{to_node})" # Formato para visita a Serviço
                    f.write(route_line + "\n") # Escreve a linha completa da rota no arquivo
            
            # Calcula e imprime o tempo que levou para processar o arquivo atual
            elapsed_time_file = (time.perf_counter() - current_file_start_time) * 1000 # Tempo em milissegundos
            print(f"  Concluído: '{os.path.basename(full_output_filepath)}' em {elapsed_time_file:.2f} ms")

        except Exception as e:
            # Em caso de qualquer erro durante o processamento de um arquivo,
            # imprime a mensagem de erro detalhada.
            print(f"  ERRO ao processar '{dat_file}': {type(e).__name__}: {e}")
            print(f"  Saída para '{os.path.basename(full_output_filepath)}' pode estar incompleta ou ausente.")
        print("-" * 50) # Imprime um separador visual para melhor legibilidade no console

    end_time_batch = time.perf_counter() # Marca o tempo final do processamento de todos os arquivos
    total_elapsed_batch_time = (end_time_batch - start_time_batch) # Calcula o tempo total de execução em segundos

    # Mensagens finais de resumo do processamento
    print(f"\n--- Processamento de todos os arquivos da ETAPA 3 concluído ---")
    print(f"Total de arquivos processados: {processed_count}")
    print(f"Tempo total de execução: {total_elapsed_batch_time:.2f} segundos")
    print(f"Todos os arquivos de saída melhorados foram gerados em: '{output_directory_improved}'")

# Este bloco garante que o código abaixo só será executado quando o script for chamado diretamente
if __name__ == "__main__":
    # CONFIGURAÇÃO DOS DIRETÓRIOS DE TRABALHO
    # Define a pasta onde as instâncias de problema (.dat) estão localizadas.
    input_directory = "instancias" 
    # Define a pasta onde as soluções melhoradas da Etapa 3 serão salvas.
    output_directory_improved = "saidas_Melhoradas" 
    
    # Chama a função principal para iniciar o processamento de todos os arquivos
    processar_arquivos_etapa3(input_directory, output_directory_improved)