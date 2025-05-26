import time
import sys
import importlib.util
import heapq
from collections import defaultdict, deque
import os
import re

# --- Funções auxiliares ---

# A função dijkstra original não será mais usada para o cálculo de APSP com Floyd-Warshall.
# Mas a deixamos aqui para referência, caso queira reverter ou usar em outro contexto.
# def dijkstra(start_node, graph_adj, traversal_costs, all_nodes):
#     distances = {node: float('inf') for node in all_nodes}
#     distances[start_node] = 0
#     pq = [(0, start_node)]
#     predecessors = {node: None for node in all_nodes}

#     while pq:
#         dist, current_node = heapq.heappop(pq)
#         if dist > distances[current_node]:
#             continue
#         for neighbor in graph_adj.get(current_node, []):
#             cost = traversal_costs.get((current_node, neighbor), float('inf'))
#             if distances[current_node] + cost < distances[neighbor]:
#                 distances[neighbor] = distances[current_node] + cost
#                 predecessors[neighbor] = current_node
#                 heapq.heappush(pq, (distances[neighbor], neighbor))
#     return distances, predecessors

# A função reconstruct_path pode ser útil para depuração, mas não é chamada na lógica principal.
def reconstruct_path(predecessors, start_node, end_node):
    path = []
    current = end_node
    while current is not None:
        path.insert(0, current)
        current = predecessors[current]
        if current == start_node:
            path.insert(0, start_node)
            break
    if path and path[0] == start_node:
        return path
    return None

# --- Função Principal para a Etapa 2 ---

def gerar_solucao_inicial_aprimorada(instance_filepath):
    start_time_total_algorithm = time.perf_counter()

    # 1. Carregar os dados e as estatísticas da Etapa 1
    original_sys_argv = sys.argv
    original_stdout = sys.stdout # Salva o stdout original para silenciar teste_uso.py
    sys.stdout = open(os.devnull, 'w') # Redireciona stdout para um "buraco negro" (silencia)

    sys.argv = ["teste_uso.py", instance_filepath]

    try:
        spec = importlib.util.spec_from_file_location("estatisticas_grafo", "teste_uso.py")
        estatisticas_grafo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(estatisticas_grafo)
    finally:
        sys.argv = original_sys_argv
        sys.stdout = original_stdout # Restaura o stdout para o console

    # Obter dados carregados da instância
    capacidade_veiculo = int(estatisticas_grafo.dados_gerais['Capacity'])
    depot_node = int(estatisticas_grafo.dados_gerais['Depot Node'])
    total_nodes_count = estatisticas_grafo.qtd_vertices
    # Garante que os nós sejam uma lista ordenada para as iterações do Floyd-Warshall
    all_graph_nodes = sorted(list(set(range(1, total_nodes_count + 1))))

    # Construir a estrutura do grafo para os custos diretos para Floyd-Warshall
    # graph_adj não é estritamente necessário para o Floyd-Warshall em si,
    # mas mantido para consistência se você usar em outra parte ou para depuração.
    graph_adj = defaultdict(list)
    traversal_costs_direct = {} # Armazena apenas os custos diretos entre u e v

    # Processa arestas não direcionadas (Edges)
    for item_list in [estatisticas_grafo.required_edges, estatisticas_grafo.non_required_edges]:
        for item in item_list:
            u, v, cost = item['from'], item['to'], item['traversal_cost']
            graph_adj[u].append(v)
            graph_adj[v].append(u) # Adiciona a aresta no sentido inverso para não direcionadas
            traversal_costs_direct[(u, v)] = cost
            traversal_costs_direct[(v, u)] = cost # Custo de volta também

    # Processa arcos direcionados (Arcs)
    for item_list in [estatisticas_grafo.required_arcs, estatisticas_grafo.non_required_arcs]:
        for item in item_list:
            u, v, cost = item['from'], item['to'], item['traversal_cost']
            graph_adj[u].append(v) # Apenas um sentido para arcos
            traversal_costs_direct[(u, v)] = cost # Custo apenas no sentido de u para v
    
    # Calcular todas as distâncias de caminhos mais curtos (All-Pairs Shortest Path)
    # usando FLOYD-WARSHALL
    short_paths_matrix = {}
    predecessor_matrix = {}
    
    # Inicialização das matrizes para Floyd-Warshall
    # short_paths_matrix[(i, j)] = distância de i para j
    # predecessor_matrix[(i, j)] = predecessor de j no caminho mais curto de i para j
    
    for i_node in all_graph_nodes:
        for j_node in all_graph_nodes:
            if i_node == j_node:
                short_paths_matrix[(i_node, j_node)] = 0 # Distância de um nó para ele mesmo é 0
                predecessor_matrix[(i_node, j_node)] = i_node # O predecessor é ele mesmo ou None
            else:
                cost = traversal_costs_direct.get((i_node, j_node), float('inf'))
                short_paths_matrix[(i_node, j_node)] = cost
                if cost != float('inf'):
                    predecessor_matrix[(i_node, j_node)] = i_node # O predecessor é o nó de origem se há uma aresta direta
                else:
                    predecessor_matrix[(i_node, j_node)] = None # Não há caminho direto conhecido inicialmente

    # Algoritmo de Floyd-Warshall
    # K é o nó intermediário
    # I é o nó de origem
    # J é o nó de destino
    for k_node in all_graph_nodes:
        for i_node in all_graph_nodes:
            for j_node in all_graph_nodes:
                # Se há um caminho de i para k E de k para j (não infinito)
                if short_paths_matrix[(i_node, k_node)] != float('inf') and \
                   short_paths_matrix[(k_node, j_node)] != float('inf'):
                    
                    new_dist = short_paths_matrix[(i_node, k_node)] + short_paths_matrix[(k_node, j_node)]
                    
                    # Se o novo caminho via K é mais curto que o caminho atual de i para j
                    if new_dist < short_paths_matrix[(i_node, j_node)]:
                        short_paths_matrix[(i_node, j_node)] = new_dist
                        # O predecessor de J no caminho mais curto de I para J, passando por K,
                        # é o predecessor de J no caminho mais curto de K para J.
                        predecessor_matrix[(i_node, j_node)] = predecessor_matrix[(k_node, j_node)]

    # 2. Mapeamento de Serviços Requeridos com IDs globais (mantido igual)
    all_required_services = []
    service_id_counter = 1
    uncovered_service_ids = set()

    for rn in estatisticas_grafo.required_nodes:
        node_val = int(rn['node'].lstrip('N'))
        service_obj = {
            'id': service_id_counter,
            'type': 'node',
            'node_val': node_val,
            'demand': rn['demand'],
            'service_cost': rn['service_cost'],
            'from': node_val,
            'to': node_val,
            'original_data': rn
        }
        all_required_services.append(service_obj)
        uncovered_service_ids.add(service_id_counter)
        service_id_counter += 1

    for re in estatisticas_grafo.required_edges:
        service_obj = {
            'id': service_id_counter,
            'type': 'edge',
            'from': re['from'],
            'to': re['to'],
            'traversal_cost': re['traversal_cost'],
            'demand': re['demand'],
            'service_cost': re['service_cost'],
            'original_data': re
        }
        all_required_services.append(service_obj)
        uncovered_service_ids.add(service_id_counter)
        service_id_counter += 1

    for ra in estatisticas_grafo.required_arcs:
        service_obj = {
            'id': service_id_counter,
            'type': 'arc',
            'from': ra['from'],
            'to': ra['to'],
            'traversal_cost': ra['traversal_cost'],
            'demand': ra['demand'],
            'service_cost': ra['service_cost'],
            'original_data': ra
        }
        all_required_services.append(service_obj)
        uncovered_service_ids.add(service_id_counter)
        service_id_counter += 1

    # 3. Algoritmo Construtivo Aprimorado (mantido igual)
    all_routes_output_data = []
    total_solution_cost = 0
    route_id_counter = 1

    services_pool = list(all_required_services)

    while uncovered_service_ids:
        current_route_demand = 0
        current_route_cost = 0
        current_route_visits_triples = []
        current_vehicle_location = depot_node

        current_route_visits_triples.append(('D', 0, depot_node, depot_node))
        services_visited_in_current_route = set()

        best_first_service_for_route = None
        min_cost_to_start_route = float('inf')

        for service_obj in services_pool:
            if service_obj['id'] not in uncovered_service_ids:
                continue

            cost_from_depot = short_paths_matrix.get((depot_node, service_obj['from']), float('inf'))

            if cost_from_depot == float('inf'):
                continue

            if current_route_demand + service_obj['demand'] > capacidade_veiculo:
                continue

            cost_to_depot_from_service = short_paths_matrix.get((service_obj['to'], depot_node), float('inf'))
            
            if cost_to_depot_from_service == float('inf'):
                continue

            potential_initial_route_cost = cost_from_depot + service_obj['service_cost'] + cost_to_depot_from_service
            
            if potential_initial_route_cost < min_cost_to_start_route:
                min_cost_to_start_route = potential_initial_route_cost
                best_first_service_for_route = service_obj

        if best_first_service_for_route is None:
            break

        service_to_add = best_first_service_for_route
        current_route_cost += short_paths_matrix[(depot_node, service_to_add['from'])]
        current_route_cost += service_to_add['service_cost']
        current_route_demand += service_to_add['demand']
        current_vehicle_location = service_to_add['to']
        current_route_visits_triples.append(('S', service_to_add['id'], service_to_add['from'], service_to_add['to']))
        services_visited_in_current_route.add(service_to_add['id'])
        uncovered_service_ids.remove(service_to_add['id'])
        
        while True:
            best_next_service_candidate = None
            min_extended_cost_for_next_step = float('inf')
            
            for service_obj in services_pool:
                if service_obj['id'] not in uncovered_service_ids:
                    continue

                travel_cost_to_service_start = short_paths_matrix.get((current_vehicle_location, service_obj['from']), float('inf'))

                if travel_cost_to_service_start == float('inf'):
                    continue

                if current_route_demand + service_obj['demand'] > capacidade_veiculo:
                    continue

                service_cost_for_step = 0
                if service_obj['id'] not in services_visited_in_current_route:
                    service_cost_for_step = service_obj['service_cost']

                cost_to_depot_after_service = short_paths_matrix.get((service_obj['to'], depot_node), float('inf'))
                if cost_to_depot_after_service == float('inf'):
                    continue

                potential_extended_cost = travel_cost_to_service_start + service_cost_for_step + cost_to_depot_after_service

                if potential_extended_cost < min_extended_cost_for_next_step:
                    min_extended_cost_for_next_step = potential_extended_cost
                    best_next_service_candidate = service_obj
            
            if best_next_service_candidate:
                service_to_add = best_next_service_candidate

                travel_cost_actual = short_paths_matrix[(current_vehicle_location, service_to_add['from'])]
                current_route_cost += travel_cost_actual

                if service_to_add['id'] not in services_visited_in_current_route:
                    current_route_cost += service_to_add['service_cost']
                    services_visited_in_current_route.add(service_to_add['id'])
                    uncovered_service_ids.remove(service_to_add['id'])

                current_route_demand += service_to_add['demand']
                current_vehicle_location = service_to_add['to']
                current_route_visits_triples.append(('S', service_to_add['id'], service_to_add['from'], service_to_add['to']))
            else:
                cost_to_depot = short_paths_matrix.get((current_vehicle_location, depot_node), 0)
                current_route_cost += cost_to_depot
                current_route_visits_triples.append(('D', 0, depot_node, depot_node))
                break

        total_solution_cost += current_route_cost
        all_routes_output_data.append({
            'route_id': route_id_counter,
            'demand': current_route_demand,
            'cost': current_route_cost,
            'visits': current_route_visits_triples
        })
        route_id_counter += 1

    end_time_total_algorithm = time.perf_counter()
    total_clocks_solution = (end_time_total_algorithm - start_time_total_algorithm) * 1000

    total_clocks_reference_execution = total_clocks_solution
    total_clocks_reference_finding = total_clocks_solution

    return (total_solution_cost, len(all_routes_output_data),
            total_clocks_reference_execution, total_clocks_reference_finding,
            all_routes_output_data)

# --- BLOCÃO PARA PROCESSAR MÚLTIPLOS ARQUIVOS ---
if __name__ == "__main__":
    # 1. ***CONFIGURAÇÃO DO DIRETÓRIO DE ENTRADA***
    # Onde estão os seus arquivos .dat que o script vai ler.
    # Definido para o mesmo diretório do script.
    input_directory = "instancias" #

    # 2. ***CONFIGURAÇÃO DO DIRETÓRIO DE SAÍDA***
    # Onde os arquivos de saída serão salvos.
    # Definido para uma subpasta chamada "saidas" dentro do diretório do script.
    output_directory = "saidas" #

    # --- INÍCIO DA LÓGICA DE PROCESSAMENTO ---

    # Tenta criar o diretório de saída. Se já existir, não faz nada.
    try:
        os.makedirs(output_directory, exist_ok=True)
    except OSError as e:
        print(f"ERRO: Não foi possível criar o diretório de saída '{output_directory}': {e}")
        print("Verifique as permissões de escrita ou se o caminho é válido.")
        sys.exit(1)

    # Tenta listar os arquivos no diretório de entrada
    dat_files = []
    try:
        raw_dat_files = [f for f in os.listdir(input_directory) if f.endswith('.dat')]
        
        # Função para ordenar arquivos numericamente (para bhw1, bhw2, bhw10)
        def sort_key(filename):
            match = re.search(r'(\d+)', filename)
            if match:
                return int(match.group(1))
            return float('inf') # Coloca arquivos sem números no final

        dat_files = sorted(raw_dat_files, key=sort_key)

    except FileNotFoundError:
        print(f"ERRO CRÍTICO: O diretório de entrada '{input_directory}' NÃO FOI ENCONTRADO.")
        print("Certifique-se de que o caminho 'input_directory' no código esteja correto e que a pasta exista.")
        sys.exit(1) # Sai do script se a pasta de entrada não for encontrada

    if not dat_files:
        print(f"AVISO: Nenhum arquivo .dat encontrado no diretório: '{input_directory}'.")
        print("Verifique se os arquivos estão lá e se a extensão é '.dat'.")
        sys.exit(0) # Saímos sem erro se não houver arquivos para processar

    print(f"Iniciando processamento de {len(dat_files)} arquivos .dat...")
    print(f"Arquivos de entrada em: '{input_directory}'")
    print(f"Arquivos de saída serão salvos em: '{output_directory}'\n")

    processed_count = 0
    start_time_batch = time.perf_counter()

    for dat_file in dat_files:
        processed_count += 1
        current_file_start_time = time.perf_counter()

        # Constrói os caminhos completos para entrada e saída
        full_instance_filepath = os.path.join(input_directory, dat_file)
        
        # Formata o nome do arquivo de saída para sol-NOMEDOARQUIVO.dat
        output_filename_base = "sol-" + dat_file #
        full_output_filepath = os.path.join(output_directory, output_filename_base)

        print(f"[{processed_count}/{len(dat_files)}] Processando: '{dat_file}'...")

        try:
            with open(full_output_filepath, 'w') as f:
                total_cost, num_routes, clocks_ref_exec, clocks_ref_find, routes_data = \
                    gerar_solucao_inicial_aprimorada(full_instance_filepath)
                
                f.write(f"{int(total_cost)}\n")
                f.write(f"{num_routes}\n")
                f.write(f"{int(clocks_ref_exec)}\n")
                f.write(f"{int(clocks_ref_find)}\n")

                for route in routes_data:
                    total_visits_in_route = len(route['visits'])
                    # Adiciona um espaço antes do primeiro parêntese "(D 0,1,1)" para corresponder ao formato da imagem
                    route_line = f"0 1 {route['route_id']} {int(route['demand'])} {int(route['cost'])} {total_visits_in_route}" 

                    for visit_type, service_id, from_node, to_node in route['visits']:
                        if visit_type == 'D':
                            route_line += f" (D {service_id},{from_node},{to_node})"
                        elif visit_type == 'S':
                            route_line += f" (S {service_id},{from_node},{to_node})"
                    f.write(route_line + "\n")
            
            elapsed_time_file = (time.perf_counter() - current_file_start_time) * 1000 # em milissegundos
            print(f"  Concluído: '{os.path.basename(full_output_filepath)}' em {elapsed_time_file:.2f} ms")

        except Exception as e:
            print(f"  ERRO ao processar '{dat_file}': {type(e).__name__}: {e}")
            print(f"  Saída para '{os.path.basename(full_output_filepath)}' pode estar incompleta ou ausente.")
        print("-" * 50) # Separador visual

    end_time_batch = time.perf_counter()
    total_elapsed_batch_time = (end_time_batch - start_time_batch) # em segundos

    print(f"\n--- Processamento de todos os arquivos concluído ---")
    print(f"Total de arquivos processados: {processed_count}")
    print(f"Tempo total de execução: {total_elapsed_batch_time:.2f} segundos")
    print(f"Todos os arquivos de saída foram gerados em: '{output_directory}'")