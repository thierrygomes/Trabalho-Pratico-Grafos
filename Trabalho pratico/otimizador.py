import time # Importa o módulo time para medir o tempo de execução
import heapq # Importa heapq, uma implementação de fila de prioridade, essencial para o algoritmo de Dijkstra
from collections import defaultdict, deque # Importa defaultdict para lista de adjacência e deque (fila dupla)

# Importações dos módulos desacoplados para carregar dados e construir o grafo
from leitor_dados import carregar_dados_arquivo
from grafo_estatisticas import construir_grafo, contar_vertices

def dijkstra(start_node, graph_adj, traversal_costs, all_nodes):
    """
    Calcula as distâncias dos caminhos mais curtos de um nó inicial (start_node)
    para todos os outros nós no grafo, usando o algoritmo de Dijkstra.

    Args:
        start_node (int): O nó de origem a partir do qual os caminhos mais curtos serão calculados.
        graph_adj (defaultdict): Lista de adjacência do grafo, representando as conexões entre os nós.
                                 Ex: graph_adj[u] retorna uma lista de nós vizinhos a u.
        traversal_costs (dict): Dicionário que armazena o custo de travessia entre dois nós.
                                Ex: traversal_costs[(u, v)] retorna o custo para ir de u para v.
        all_nodes (list): Lista de todos os nós presentes no grafo.

    Returns:
        dict: Um dicionário onde as chaves são os nós e os valores são as distâncias mais curtas
              do start_node para cada um desses nós.
    """
    # Inicializa todas as distâncias como infinito, exceto a do nó inicial que é 0
    distances = {node: float('inf') for node in all_nodes}
    distances[start_node] = 0
    
    # Fila de prioridade (min-heap): armazena tuplas (custo_atual, nó_atual)
    # A fila prioriza o nó com o menor custo_atual
    pq = [(0, start_node)] # (custo, nó)

    # Continua enquanto houver nós na fila de prioridade para processar
    while pq:
        # Extrai o nó com o menor custo atual da fila de prioridade
        dist, current_node = heapq.heappop(pq)

        # Se já encontramos um caminho mais curto para current_node anteriormente,
        # e este caminho atual é maior, ignoramos (já processamos este nó de forma mais eficiente)
        if dist > distances[current_node]:
            continue

        # Itera sobre todos os vizinhos do nó atual
        for neighbor in graph_adj.get(current_node, []): # .get(current_node, []) lida com nós sem vizinhos
            # Obtém o custo para ir do nó atual para o vizinho
            cost_to_neighbor = traversal_costs.get((current_node, neighbor), float('inf'))
            
            # Se o custo for infinito (caminho não existe ou não é permitido), pula para o próximo vizinho
            if cost_to_neighbor == float('inf'):
                continue

            # Se encontrou um caminho mais curto para o vizinho através do nó atual
            if distances[current_node] + cost_to_neighbor < distances[neighbor]:
                distances[neighbor] = distances[current_node] + cost_to_neighbor # Atualiza a distância
                heapq.heappush(pq, (distances[neighbor], neighbor)) # Adiciona o vizinho à fila de prioridade com o novo custo
                
    return distances # Retorna as distâncias mais curtas encontradas

# A função reconstruct_path não é usada na lógica principal, mas mantida por clareza.
# def reconstruct_path(predecessor_matrix, start_node, end_node):
#     path = deque()
#     curr = end_node
#     while curr is not None and curr != start_node:
#         path.appendleft(curr)
#         curr = predecessor_matrix.get((start_node, curr))
#     if curr == start_node:
#         path.appendleft(start_node)
#         return list(path)
#     return None

def gerar_solucao_inicial_aprimorada(instance_filepath):
    """
    Gera uma solução inicial para o problema de roteamento de veículos,
    baseada em um algoritmo construtivo (Nearest Neighbor modificado) e
    cálculo de caminhos mais curtos (All-Pairs Shortest Path - APSP).
    Esta função representa a lógica principal da Etapa 2 do trabalho.

    Args:
        instance_filepath (str): Caminho completo para o arquivo de instância (.dat).

    Returns:
        tuple: Uma tupla contendo:
               - total_solution_cost (float): O custo total da solução encontrada.
               - num_routes (int): O número de rotas geradas.
               - total_clocks_reference_execution (float): Tempo total de execução da função (em milissegundos).
               - total_clocks_reference_finding (float): Tempo gasto no cálculo do APSP (em milissegundos).
               - all_routes_output_data (list): Uma lista de dicionários, cada um representando uma rota
                                                 com seus detalhes (ID, demanda, custo, visitas).
    """
    start_time_total_algorithm = time.perf_counter() # Marca o tempo de início total do algoritmo

    # 1. Carregar os dados da instância usando o módulo leitor_dados
    dados_gerais, required_nodes, required_edges, non_required_edges, required_arcs, non_required_arcs = carregar_dados_arquivo(instance_filepath)

    # Extrai informações gerais da instância
    capacidade_veiculo = int(dados_gerais['Capacity']) # Capacidade máxima de carga de um veículo
    depot_node = int(dados_gerais['Depot Node'])     # Nó do depósito (ponto de partida e chegada dos veículos)
    
    # Conta o número total de vértices e cria uma lista ordenada de todos os nós do grafo
    total_nodes_count = contar_vertices(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes)
    all_graph_nodes = sorted(list(set(range(1, total_nodes_count + 1)))) # Garante lista ordenada para iterações

    # Constrói a estrutura de adjacência do grafo e os custos de travessia diretos
    graph_adj, traversal_costs_direct = construir_grafo(required_edges, non_required_edges, required_arcs, non_required_arcs)
    
    # === Início do cálculo de All-Pairs Shortest Path (APSP) ===
    # Esta etapa calcula o caminho mais curto entre todos os pares de nós do grafo.
    start_time_path_finding = time.perf_counter() # Marca o tempo de início do cálculo do APSP

    short_paths_matrix = {} # Dicionário para armazenar as distâncias mais curtas: (u, v) -> distância

    # Executa Dijkstra a partir de CADA NÓ como origem para encontrar as distâncias para TODOS os outros nós
    for start_node in all_graph_nodes:
        distances_from_start = dijkstra(start_node, graph_adj, traversal_costs_direct, all_graph_nodes)
        # Armazena todas as distâncias calculadas a partir deste start_node na matriz APSP
        for end_node, dist in distances_from_start.items():
            short_paths_matrix[(start_node, end_node)] = dist
    
    end_time_path_finding = time.perf_counter() # Marca o tempo final do cálculo do APSP
    total_clocks_reference_finding = (end_time_path_finding - start_time_path_finding) * 1000 # Tempo em milissegundos
    # === Fim do cálculo de APSP ===

    # 2. Mapeamento de Serviços Requeridos com IDs globais
    # Cria uma lista unificada de todos os serviços requeridos (nós, arestas, arcos)
    # e atribui um ID global único a cada um.
    all_required_services = []
    service_id_counter = 1 # Contador para IDs únicos de serviço
    
    # Processa nós requeridos
    for rn in required_nodes:
        node_val = int(rn['node'].lstrip('N')) # Remove o prefixo 'N' do nome do nó (ex: 'N4' vira 4)
        service_obj = {
            'id': service_id_counter,
            'type': 'node',        # Tipo de serviço: nó
            'node_val': node_val,  # Valor numérico do nó
            'demand': rn['demand'], # Demanda associada ao serviço no nó
            'service_cost': rn['service_cost'], # Custo de serviço no nó
            'from': node_val,      # Para nós, 'from' e 'to' são o próprio nó
            'to': node_val,
            'original_data': rn    # Mantém os dados originais para referência
        }
        all_required_services.append(service_obj)
        service_id_counter += 1

    # Processa arestas requeridas
    for re_item in required_edges:
        service_obj = {
            'id': service_id_counter,
            'type': 'edge',        # Tipo de serviço: aresta
            'from': re_item['from'],
            'to': re_item['to'],
            'traversal_cost': re_item['traversal_cost'],
            'demand': re_item['demand'],
            'service_cost': re_item['service_cost'],
            'original_data': re_item
        }
        all_required_services.append(service_obj)
        service_id_counter += 1

    # Processa arcos requeridos
    for ra_item in required_arcs:
        service_obj = {
            'id': service_id_counter,
            'type': 'arc',         # Tipo de serviço: arco
            'from': ra_item['from'],
            'to': ra_item['to'],
            'traversal_cost': ra_item['traversal_cost'],
            'demand': ra_item['demand'],
            'service_cost': ra_item['service_cost'],
            'original_data': ra_item
        }
        all_required_services.append(service_obj)
        service_id_counter += 1

    # Cria um conjunto (set) com os IDs de todos os serviços requeridos.
    # Um set permite remoções e verificações de existência muito rápidas (O(1)).
    uncovered_service_ids = {s['id'] for s in all_required_services}

    # 3. Algoritmo Construtivo Aprimorado (Nearest Neighbor modificado)
    # Este é o coração da Etapa 2: constrói rotas sequencialmente até que todos os serviços sejam cobertos.
    start_time_constructive = time.perf_counter() # Marca o tempo de início da fase construtiva

    all_routes_output_data = [] # Lista para armazenar os dados de todas as rotas geradas
    total_solution_cost = 0     # Custo total da solução (soma dos custos de todas as rotas)
    route_id_counter = 1        # Contador para atribuir IDs únicos às rotas

    # O loop principal continua enquanto houver serviços não cobertos
    while uncovered_service_ids:
        current_route_demand = 0        # Demanda acumulada na rota atual
        current_route_cost = 0          # Custo acumulado na rota atual
        current_route_visits_triples = [] # Lista de tuplas de visitas para a rota atual (D para depósito, S para serviço)
        current_vehicle_location = depot_node # Localização atual do veículo (sempre começa no depósito)

        # Adiciona a visita inicial ao depósito no formato de saída
        current_route_visits_triples.append(('D', 0, depot_node, depot_node))
        
        best_first_service_for_route = None     # Armazena o melhor serviço para iniciar uma nova rota
        min_cost_to_start_route = float('inf') # Custo mínimo para iniciar uma rota com um serviço

        # Cria uma lista temporária dos serviços que ainda não foram cobertos
        current_uncovered_services_list = [s_obj for s_obj in all_required_services if s_obj['id'] in uncovered_service_ids]

        # --- Encontrar o melhor PRIMEIRO serviço para a rota atual ---
        # Itera sobre os serviços não cobertos para decidir qual iniciar a próxima rota
        for service_obj in current_uncovered_services_list:
            if current_route_demand + service_obj['demand'] > capacidade_veiculo:
                continue # Pula se a demanda do serviço excede a capacidade do veículo sozinho

            # Custo para ir do depósito até o início do serviço
            cost_from_depot = short_paths_matrix.get((depot_node, service_obj['from']), float('inf'))
            if cost_from_depot == float('inf'):
                continue # Pula se o serviço for inacessível a partir do depósito

            # Custo para retornar ao depósito após completar o serviço
            cost_to_depot_from_service = short_paths_matrix.get((service_obj['to'], depot_node), float('inf'))
            if cost_to_depot_from_service == float('inf'):
                continue # Pula se não for possível retornar ao depósito após o serviço

            # Calcula o custo potencial total da rota se este serviço fosse o ÚNICO na rota
            potential_initial_route_cost = cost_from_depot + service_obj['service_cost'] + cost_to_depot_from_service
            
            # Se este serviço resulta em um custo menor para iniciar a rota
            if potential_initial_route_cost < min_cost_to_start_route:
                min_cost_to_start_route = potential_initial_route_cost
                best_first_service_for_route = service_obj

        # Se nenhum serviço pôde ser encontrado para iniciar uma nova rota (todos inacessíveis ou muito grandes)
        if best_first_service_for_route is None:
            break # Quebra o loop principal, pois não há mais rotas viáveis a serem criadas

        # Adiciona o melhor primeiro serviço encontrado à rota atual
        service_to_add = best_first_service_for_route
        current_route_cost += short_paths_matrix[(depot_node, service_to_add['from'])] # Custo de ir do depósito ao serviço
        current_route_cost += service_to_add['service_cost'] # Custo de serviço em si
        current_route_demand += service_to_add['demand'] # Adiciona a demanda do serviço
        current_vehicle_location = service_to_add['to'] # Atualiza a localização do veículo para o "fim" do serviço
        
        # Adiciona o serviço à lista de visitas da rota
        current_route_visits_triples.append(('S', service_to_add['id'], service_to_add['from'], service_to_add['to']))
        uncovered_service_ids.remove(service_to_add['id']) # Marca o serviço como coberto

        # --- Loop para adicionar serviços subsequentes à rota atual (Nearest Neighbor) ---
        while True:
            best_next_service_candidate = None          # Armazena o melhor próximo serviço a ser adicionado
            min_extended_cost_for_next_step = float('inf') # Custo incremental mínimo para adicionar um próximo serviço

            # Cria uma lista temporária de serviços que ainda não foram cobertos
            current_uncovered_services_list_inner = [s_obj for s_obj in all_required_services if s_obj['id'] in uncovered_service_ids]

            # Itera sobre os serviços não cobertos para encontrar o melhor próximo
            for service_obj in current_uncovered_services_list_inner:
                # Verifica a capacidade
                if current_route_demand + service_obj['demand'] > capacidade_veiculo:
                    continue # Pula se o serviço exceder a capacidade da rota

                # Custo para ir da localização atual do veículo até o início do próximo serviço
                travel_cost_to_service_start = short_paths_matrix.get((current_vehicle_location, service_obj['from']), float('inf'))
                if travel_cost_to_service_start == float('inf'):
                    continue # Pula se o próximo serviço for inacessível da localização atual

                # Custo para retornar ao depósito SE este serviço fosse o ÚLTIMO da rota
                cost_to_depot_after_service = short_paths_matrix.get((service_obj['to'], depot_node), float('inf'))
                if cost_to_depot_after_service == float('inf'):
                    continue # Pula se não puder retornar ao depósito após este serviço

                # O "custo potencial estendido" é a soma do custo para chegar a este serviço,
                # o custo de serviço, e o custo de retornar ao depósito depois dele.
                # Isso guia a escolha do próximo "vizinho" que minimize o impacto no retorno ao depósito.
                potential_extended_cost = travel_cost_to_service_start + service_obj['service_cost'] + cost_to_depot_after_service

                # Compara com o custo mínimo encontrado até agora para um próximo serviço
                if potential_extended_cost < min_extended_cost_for_next_step:
                    min_extended_cost_for_next_step = potential_extended_cost
                    best_next_service_candidate = service_obj
            
            # Se um melhor próximo serviço foi encontrado
            if best_next_service_candidate:
                service_to_add = best_next_service_candidate

                # Adiciona o custo de deslocamento real (da localização atual até o início do serviço)
                travel_cost_actual = short_paths_matrix[(current_vehicle_location, service_to_add['from'])]
                current_route_cost += travel_cost_actual 
                current_route_cost += service_to_add['service_cost'] # Adiciona o custo de serviço
                
                current_route_demand += service_to_add['demand'] # Atualiza a demanda da rota
                current_vehicle_location = service_to_add['to'] # Atualiza a localização do veículo
                
                # Adiciona o serviço à lista de visitas da rota
                current_route_visits_triples.append(('S', service_to_add['id'], service_to_add['from'], service_to_add['to']))
                uncovered_service_ids.remove(service_to_add['id']) # Marca o serviço como coberto
            else:
                # Se nenhum serviço adicional pôde ser adicionado a esta rota (capacidade cheia, sem vizinhos acessíveis, etc.)
                # A rota é finalizada e o veículo retorna ao depósito.
                cost_to_depot = short_paths_matrix.get((current_vehicle_location, depot_node), 0) # Custo do último nó para o depósito
                current_route_cost += cost_to_depot # Adiciona o custo de retorno
                current_route_visits_triples.append(('D', 0, depot_node, depot_node)) # Adiciona a visita final ao depósito
                break # Sai do loop de adição de serviços na rota atual (rota está completa)

        # Após a conclusão da rota, adiciona os dados da rota à lista de todas as rotas
        total_solution_cost += current_route_cost
        all_routes_output_data.append({
            'route_id': route_id_counter,
            'demand': current_route_demand,
            'cost': current_route_cost,
            'visits': current_route_visits_triples
        })
        route_id_counter += 1 # Incrementa o ID para a próxima rota

    end_time_constructive = time.perf_counter() # Marca o tempo final da fase construtiva
    total_clocks_constructive = (end_time_constructive - start_time_constructive) * 1000 # Tempo construtivo em milissegundos
    
    end_time_total_algorithm = time.perf_counter() # Marca o tempo final de todo o algoritmo da Etapa 2
    total_clocks_solution = (end_time_total_algorithm - start_time_total_algorithm) * 1000 # Tempo total em milissegundos

    # Os valores de tempo são retornados para corresponder ao formato de saída.
    # 'total_clocks_reference_execution' é o tempo total da Etapa 2.
    # 'total_clocks_reference_finding' é o tempo do cálculo do APSP.
    total_clocks_reference_execution = total_clocks_solution # Tempo total para a Etapa 2

    return (total_solution_cost, len(all_routes_output_data),
            total_clocks_reference_execution, total_clocks_reference_finding,
            all_routes_output_data)