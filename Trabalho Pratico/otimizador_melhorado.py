# otimizador_melhorado.py (Versão Final Otimizada - Etapa 3 Autocontida)
import time # Importa o módulo time para medir o tempo de execução
import heapq # Importa heapq, uma implementação de fila de prioridade para Dijkstra
from collections import defaultdict, deque # Importa defaultdict para listas de adjacência e deque para otimizações de fila
import copy # Importa copy para cópias de objetos, especialmente listas aninhadas
from copy import deepcopy # Importa deepcopy para criar cópias independentes de objetos complexos
from concurrent.futures import ThreadPoolExecutor # Para paralelizar tarefas em threads
import os # Importa os para interagir com o sistema operacional (ex: obter número de CPUs)

# Importa módulos base necessários para carregar dados e construir o grafo.
# NOTA: Este módulo é autocontido para a Etapa 3, portanto, não importa o 'otimizador.py' da Etapa 2
# para evitar dependências e recálculos duplicados do APSP.
from leitor_dados import carregar_dados_arquivo
from grafo_estatisticas import construir_grafo, contar_vertices

# --- Funções Auxiliares Comuns (Dijkstra, Cálculo de Custo/Demanda) ---

def dijkstra_optimized(start_node, graph_adj, traversal_costs, all_nodes):
    """
    Calcula as distâncias dos caminhos mais curtos de um nó inicial para todos os outros nós.
    Implementação otimizada do algoritmo de Dijkstra usando uma fila de prioridade (heap).
    
    Args:
        start_node (int): O nó de origem.
        graph_adj (defaultdict): Lista de adjacência do grafo.
        traversal_costs (dict): Dicionário de custos de travessia (chave: (u, v), valor: custo).
        all_nodes (list): Lista de todos os nós no grafo.
        
    Returns:
        dict: Dicionário onde as chaves são os nós e os valores são as distâncias mais curtas de start_node.
    """
    distances = {node: float('inf') for node in all_nodes} # Inicializa distâncias com infinito
    distances[start_node] = 0 # Distância do nó inicial para si mesmo é 0
    pq = [(0, start_node)] # Fila de prioridade: (custo_acumulado, nó)

    while pq:
        dist, current_node = heapq.heappop(pq) # Extrai o nó com menor custo
        if dist > distances[current_node]: # Se já encontrou um caminho melhor, ignora
            continue
        for neighbor in graph_adj.get(current_node, []): # Itera sobre os vizinhos do nó atual
            cost_to_neighbor = traversal_costs.get((current_node, neighbor), float('inf')) # Custo da aresta/arco
            if cost_to_neighbor == float('inf'): # Se o caminho não existe ou é inválido, pula
                continue
            if distances[current_node] + cost_to_neighbor < distances[neighbor]: # Se encontrou um caminho mais curto
                distances[neighbor] = distances[current_node] + cost_to_neighbor # Atualiza a distância
                heapq.heappush(pq, (distances[neighbor], neighbor)) # Adiciona/atualiza na fila de prioridade
    return distances

def calculate_route_cost_from_segments(services_segment, sp_matrix, depot, id_map):
    """
    Calcula o custo total de uma rota dada uma sequência de segmentos de serviço.
    Considera os custos de travessia (da matriz APSP) e os custos de serviço.
    
    Args:
        services_segment (list): Lista de tuplas de serviços na rota (excluindo 'D' de depósito).
        sp_matrix (dict): Matriz de caminhos mais curtos (All-Pairs Shortest Path).
        depot (int): O nó do depósito.
        id_map (dict): Dicionário mapeando service_id para o objeto de serviço completo.
        
    Returns:
        float: O custo total calculado para a rota. Retorna float('inf') se alguma travessia for inacessível.
    """
    cost = 0
    current_location = depot # O veículo sempre começa no depósito

    # Custo do depósito para o primeiro serviço
    if services_segment:
        first_service_id = services_segment[0][1]
        first_service_obj = id_map[first_service_id]
        
        travel_cost = sp_matrix.get((current_location, first_service_obj['from']), float('inf'))
        if travel_cost == float('inf'): return float('inf') # Caminho inacessível
        cost += travel_cost # Adiciona custo de travessia
        cost += first_service_obj['service_cost'] # Adiciona custo do serviço
        current_location = first_service_obj['to'] # Atualiza localização do veículo
    
    # Custo entre serviços consecutivos na rota
    for i in range(1, len(services_segment)):
        prev_service_id = services_segment[i-1][1]
        current_service_id = services_segment[i][1]

        prev_service_obj = id_map[prev_service_id]
        current_service_obj = id_map[current_service_id]
        
        travel_cost = sp_matrix.get((prev_service_obj['to'], current_service_obj['from']), float('inf'))
        if travel_cost == float('inf'): return float('inf') # Caminho inacessível
        cost += travel_cost # Adiciona custo de travessia entre serviços
        cost += current_service_obj['service_cost'] # Adiciona custo do serviço
        current_location = current_service_obj['to'] # Atualiza localização do veículo

    # Custo de retorno ao depósito a partir do último serviço
    if services_segment:
        cost_to_depot = sp_matrix.get((current_location, depot), float('inf'))
        if cost_to_depot == float('inf'): return float('inf') # Caminho inacessível
        cost += cost_to_depot
    else:
        return 0 # Rota vazia (apenas Depot -> Depot) tem custo zero

    return cost

def calculate_route_demand(services_segment, id_map, capacity):
    """
    Calcula a demanda total de uma rota (segmento de serviços) e verifica se excede a capacidade.
    
    Args:
        services_segment (list): Lista de tuplas de serviços na rota.
        id_map (dict): Dicionário mapeando service_id para o objeto de serviço completo.
        capacity (int): Capacidade máxima do veículo.
        
    Returns:
        tuple: (current_demand (int), is_feasible (bool)). Demanda total e se a rota é viável.
    """
    current_demand = 0
    for service_tuple in services_segment:
        service_id = service_tuple[1]
        service_obj = id_map[service_id]
        current_demand += service_obj['demand']
    
    return current_demand, current_demand <= capacity # Retorna a demanda e se ela é <= capacidade

# --- Lógica do Algoritmo Construtivo (Etapa 2), agora INTERNA a este módulo ---
def generate_initial_solution_internal(
    dados_gerais, required_nodes, required_edges, non_required_edges, 
    required_arcs, non_required_arcs, short_paths_matrix, id_to_service_obj):
    """
    Gera uma solução inicial para o problema de roteamento de veículos.
    Esta função replica a lógica construtiva da Etapa 2, usando a matriz APSP já calculada.
    Utiliza uma heurística gulosa de "Nearest Neighbor modificado".
    
    Args:
        dados_gerais (dict): Dados gerais da instância.
        required_nodes (list): Lista de nós requeridos.
        required_edges (list): Lista de arestas requeridas.
        non_required_edges (list): Lista de arestas não requeridas.
        required_arcs (list): Lista de arcos requeridos.
        non_required_arcs (list): Lista de arcos não requeridos.
        short_paths_matrix (dict): Matriz de caminhos mais curtos (APSP).
        id_to_service_obj (dict): Mapeamento de service_id para objeto de serviço completo.
        
    Returns:
        tuple: (total_solution_cost (float), num_routes (int), all_routes_output_data (list)).
               Custo total, número de rotas e dados detalhados das rotas.
    """
    capacidade_veiculo = int(dados_gerais['Capacity'])
    depot_node = int(dados_gerais['Depot Node'])

    all_routes_output_data = [] # Armazena todas as rotas geradas
    total_solution_cost = 0 # Custo acumulado de todas as rotas
    route_id_counter = 1 # ID para cada nova rota

    # Conjunto de IDs de serviços que ainda não foram atendidos
    uncovered_service_ids = {s_obj['id'] for s_obj in id_to_service_obj.values()}

    # Loop principal: continua criando novas rotas enquanto houver serviços não cobertos
    while uncovered_service_ids:
        current_route_demand = 0 # Demanda acumulada na rota atual
        current_route_cost = 0 # Custo acumulado na rota atual
        current_route_visits_triples = [] # Sequência de visitas (serviços) na rota atual
        current_vehicle_location = depot_node # Veículo sempre começa no depósito

        # Adiciona a visita inicial ao depósito no formato de saída
        current_route_visits_triples.append(('D', 0, depot_node, depot_node))
        
        best_first_service_for_route = None # Melhor serviço para iniciar esta nova rota
        min_cost_to_start_route = float('inf') # Custo mínimo de uma rota que contém apenas o primeiro serviço

        # Lista de serviços que ainda precisam ser cobertos
        current_uncovered_services_list = [s_obj for s_obj in id_to_service_obj.values() if s_obj['id'] in uncovered_service_ids]

        # --- Fase 1: Encontrar o melhor PRIMEIRO serviço para a rota atual ---
        for service_obj in current_uncovered_services_list:
            if current_route_demand + service_obj['demand'] > capacidade_veiculo:
                continue # Serviço muito grande para a capacidade do veículo

            # Custo de ir do depósito até o início do serviço
            cost_from_depot = short_paths_matrix.get((depot_node, service_obj['from']), float('inf'))
            if cost_from_depot == float('inf'):
                continue # Serviço inacessível do depósito

            # Custo de retornar ao depósito depois de realizar o serviço (se ele fosse o único)
            cost_to_depot_from_service = short_paths_matrix.get((service_obj['to'], depot_node), float('inf'))
            if cost_to_depot_from_service == float('inf'):
                continue # Não consegue retornar ao depósito

            # Custo potencial da rota se só este serviço for atendido
            potential_initial_route_cost = cost_from_depot + service_obj['service_cost'] + cost_to_depot_from_service
            
            if potential_initial_route_cost < min_cost_to_start_route:
                min_cost_to_start_route = potential_initial_route_cost
                best_first_service_for_route = service_obj

        if best_first_service_for_route is None:
            # Se não foi possível encontrar nenhum serviço para iniciar uma nova rota,
            # significa que os serviços restantes são inacessíveis ou excedem a capacidade individualmente.
            break # Quebra o loop principal, não há mais rotas viáveis a criar

        # Adiciona o primeiro serviço encontrado à rota atual
        service_to_add = best_first_service_for_route
        current_route_cost += short_paths_matrix[(depot_node, service_to_add['from'])] # Custo de ir do depósito ao serviço
        current_route_cost += service_to_add['service_cost'] # Custo de serviço em si
        current_route_demand += service_to_add['demand'] # Adiciona a demanda
        current_vehicle_location = service_to_add['to'] # Atualiza a localização do veículo
        
        current_route_visits_triples.append(('S', service_to_add['id'], service_to_add['from'], service_to_add['to']))
        uncovered_service_ids.remove(service_to_add['id']) # Marca o serviço como coberto

        # --- Fase 2: Adicionar serviços subsequentes à rota atual (Nearest Neighbor) ---
        while True:
            best_next_service_candidate = None # Melhor próximo serviço para adicionar a esta rota
            min_extended_cost_for_next_step = float('inf') # Custo incremental para o próximo serviço

            current_uncovered_services_list_inner = [s_obj for s_obj in id_to_service_obj.values() if s_obj['id'] in uncovered_service_ids]

            for service_obj in current_uncovered_services_list_inner:
                if current_route_demand + service_obj['demand'] > capacidade_veiculo:
                    continue # Serviço excede a capacidade remanescente da rota

                # Custo de ir da localização atual do veículo até o início do próximo serviço
                travel_cost_to_service_start = short_paths_matrix.get((current_vehicle_location, service_obj['from']), float('inf'))
                if travel_cost_to_service_start == float('inf'):
                    continue # Serviço inacessível da localização atual

                # Custo de retornar ao depósito SE este serviço for o ÚLTIMO da rota
                cost_to_depot_after_service = short_paths_matrix.get((service_obj['to'], depot_node), float('inf'))
                if cost_to_depot_after_service == float('inf'):
                    continue # Não consegue retornar ao depósito após este serviço

                # Critério de seleção: Minimiza (custo para chegar ao serviço + custo de serviço + custo de voltar ao depósito)
                potential_extended_cost = travel_cost_to_service_start + service_obj['service_cost'] + cost_to_depot_after_service

                if potential_extended_cost < min_extended_cost_for_next_step:
                    min_extended_cost_for_next_step = potential_extended_cost
                    best_next_service_candidate = service_obj
            
            if best_next_service_candidate:
                # Adiciona o serviço encontrado à rota
                service_to_add = best_next_service_candidate

                travel_cost_actual = short_paths_matrix[(current_vehicle_location, service_to_add['from'])]
                current_route_cost += travel_cost_actual # Custo de deslocamento
                current_route_cost += service_to_add['service_cost'] # Custo de serviço
                
                current_route_demand += service_to_add['demand'] # Atualiza demanda
                current_vehicle_location = service_to_add['to'] # Atualiza localização
                current_route_visits_triples.append(('S', service_to_add['id'], service_to_add['from'], service_to_add['to']))
                uncovered_service_ids.remove(service_to_add['id']) # Marca como coberto
            else:
                # Se nenhum serviço adicional pôde ser adicionado, a rota termina e retorna ao depósito.
                cost_to_depot = short_paths_matrix.get((current_vehicle_location, depot_node), 0)
                current_route_cost += cost_to_depot
                current_route_visits_triples.append(('D', 0, depot_node, depot_node))
                break # Sai do loop interno, rota completa

        # Armazena os dados da rota recém-criada
        total_solution_cost += current_route_cost
        all_routes_output_data.append({
            'route_id': route_id_counter,
            'demand': current_route_demand,
            'cost': current_route_cost,
            'visits': current_route_visits_triples
        })
        route_id_counter += 1 # Incrementa para a próxima rota

    return total_solution_cost, len(all_routes_output_data), all_routes_output_data

# --- Operadores de Busca Local ---

def perform_2opt(route_services_segment, sp_matrix, depot_node, id_to_service_obj, capacity, max_inner_iterations=50):
    """
    Aplica o operador 2-opt em uma única rota para tentar melhorar seu custo.
    A operação 2-opt inverte um segmento da rota.
    
    Args:
        route_services_segment (list): Lista de serviços na rota (sem os nós de depósito).
        sp_matrix (dict): Matriz de caminhos mais curtos.
        depot_node (int): Nó do depósito.
        id_to_service_obj (dict): Mapeamento de service_id para objeto de serviço.
        capacity (int): Capacidade do veículo (para verificações de viabilidade).
        max_inner_iterations (int): Número máximo de iterações do loop interno de melhoria.
        
    Returns:
        tuple: (best_segments (list), best_cost (float)). A melhor sequência de serviços e o custo.
    """
    if len(route_services_segment) < 2: # 2-opt requer pelo menos 2 serviços para trocar
        return route_services_segment, calculate_route_cost_from_segments(route_services_segment, sp_matrix, depot_node, id_to_service_obj)

    best_segments = deepcopy(route_services_segment) # Cria uma cópia para não modificar a original diretamente
    best_cost = calculate_route_cost_from_segments(best_segments, sp_matrix, depot_node, id_to_service_obj)
    
    # Loop para continuar buscando melhorias até que nenhuma seja encontrada ou atinja o limite
    for _ in range(max_inner_iterations):
        improved_in_iteration = False # Flag para saber se houve melhora nesta iteração
        
        # Itera sobre todos os pares de "pontos de corte" (i e j) na rota
        for i in range(len(best_segments)): # Início do segmento a ser invertido
            for j in range(i + 1, len(best_segments)): # Fim do segmento (inclusive)
                if j - i < 1: # Garante que há pelo menos 2 elementos no segmento para inverter
                    continue
                
                # --- NÓS ENVOLVIDOS NAS ARESTAS ANTIGAS QUE SERÃO REMOVIDAS ---
                # Aresta 1: Do nó ANTES do segmento invertido para o nó INICIAL do segmento
                node_before_segment_start_to = depot_node 
                if i > 0:
                    node_before_segment_start_to = id_to_service_obj[best_segments[i-1][1]]['to']
                node_segment_start_from = id_to_service_obj[best_segments[i][1]]['from']
                
                # Aresta 2: Do nó FINAL do segmento invertido para o nó DEPOIS do segmento
                node_segment_end_to = id_to_service_obj[best_segments[j][1]]['to']
                node_after_segment_end_from = depot_node 
                if j < len(best_segments) - 1:
                    node_after_segment_end_from = id_to_service_obj[best_segments[j+1][1]]['from']

                # Custos das duas arestas antigas que serão "removidas" virtualmente
                cost_old_1 = sp_matrix.get((node_before_segment_start_to, node_segment_start_from), float('inf'))
                cost_old_2 = sp_matrix.get((node_segment_end_to, node_after_segment_end_from), float('inf'))

                if cost_old_1 == float('inf') or cost_old_2 == float('inf'): 
                    continue # Se a rota original já tem caminhos inválidos, não otimiza

                # --- Cria o novo segmento de rota com a parte entre i e j invertida ---
                temp_segments = best_segments[:i] + \
                                best_segments[i:j+1][::-1] + \
                                best_segments[j+1:]
                
                # --- NÓS ENVOLVIDOS NAS ARESTAS NOVAS QUE SERÃO ADICIONADAS ---
                # As novas arestas são criadas a partir da nova ordem dos serviços
                new_node_before_segment_start_to = node_before_segment_start_to 
                new_node_segment_start_from = id_to_service_obj[temp_segments[i][1]]['from']
                
                new_node_segment_end_to = id_to_service_obj[temp_segments[j][1]]['to']
                new_node_after_segment_end_from = node_after_segment_end_from
                
                # Custos das duas arestas novas que serão "adicionadas" virtualmente
                cost_new_1 = sp_matrix.get((new_node_before_segment_start_to, new_node_segment_start_from), float('inf'))
                cost_new_2 = sp_matrix.get((new_node_segment_end_to, new_node_after_segment_end_from), float('inf'))

                if cost_new_1 == float('inf') or cost_new_2 == float('inf'): 
                    continue # Se a nova rota criaria caminhos inválidos, ignora

                # Calcula a mudança líquida no custo total da rota (custo das novas arestas - custo das antigas)
                cost_change = (cost_new_1 + cost_new_2) - (cost_old_1 + cost_old_2)
                
                if cost_change < 0: # Se a troca resulta em uma melhoria de custo
                    # A demanda da rota não muda com um 2-opt, mas a viabilidade é reconfirmada
                    demand, feasible = calculate_route_demand(temp_segments, id_to_service_obj, capacity)
                    if not feasible: 
                        continue # Rota se tornou inviável (não deveria ocorrer com 2-opt simples)

                    best_segments = temp_segments # Aplica a melhoria na rota
                    best_cost += cost_change     # Atualiza o custo da rota com a mudança
                    improved_in_iteration = True # Marca que uma melhoria foi encontrada
                    break # Quebra o loop 'j' e recomeça o loop externo (para '_') para esta rota
            if improved_in_iteration:
                continue # Se houve melhoria, continua o loop externo para tentar mais melhorias nesta rota
            else:
                break # Se nenhuma melhoria foi encontrada em todos os pares (i,j) nesta iteração, sai do 2-opt

    return best_segments, best_cost # Retorna a melhor versão da rota e seu custo

def perform_relocate_intra(route_services_segment, sp_matrix, depot_node, id_to_service_obj, capacity, max_inner_iterations=50):
    """
    Aplica o operador Relocate (1-opt) intra-rota: move um único serviço para outra posição
    dentro da mesma rota.
    
    Args:
        route_services_segment (list): Lista de serviços na rota.
        sp_matrix (dict): Matriz de caminhos mais curtos.
        depot_node (int): Nó do depósito.
        id_to_service_obj (dict): Mapeamento de service_id para objeto de serviço.
        capacity (int): Capacidade do veículo.
        max_inner_iterations (int): Limite de iterações do loop de melhoria.
        
    Returns:
        tuple: (best_segments (list), best_cost (float)). A melhor sequência de serviços e o custo.
    """
    if len(route_services_segment) < 2: # Relocate intra requer pelo menos 2 serviços
        return route_services_segment, calculate_route_cost_from_segments(route_services_segment, sp_matrix, depot_node, id_to_service_obj)

    best_segments = deepcopy(route_services_segment)
    best_cost = calculate_route_cost_from_segments(best_segments, sp_matrix, depot_node, id_to_service_obj)
    
    for _ in range(max_inner_iterations):
        improved = False # Flag para indicar se houve melhoria nesta iteração
        
        for i in range(len(best_segments)): # Itera sobre cada serviço como o "serviço a ser movido"
            service_to_move = best_segments[i]
            
            # Cria uma rota temporária removendo o serviço atual
            temp_route_without_service = best_segments[:i] + best_segments[i+1:]
            
            # Tenta inserir o serviço em todas as outras posições possíveis na rota (inclusive no início/fim)
            for j in range(len(temp_route_without_service) + 1):
                if i == j: continue # Não tente inserir na mesma posição de onde removeu (seria trivial)
                
                new_segments_candidate = temp_route_without_service[:j] + [service_to_move] + temp_route_without_service[j:]
                
                # A demanda não muda para o Relocate Intra (o mesmo serviço está na rota), mas verifica viabilidade
                demand, feasible = calculate_route_demand(new_segments_candidate, id_to_service_obj, capacity)
                if not feasible:
                    continue # Nova rota inviável, pula
                
                new_cost = calculate_route_cost_from_segments(new_segments_candidate, sp_matrix, depot_node, id_to_service_obj)
                
                if new_cost < best_cost: # Se encontrou uma melhoria
                    best_segments = new_segments_candidate # Aplica a melhoria
                    best_cost = new_cost # Atualiza o custo
                    improved = True # Marca que houve melhoria
                    break # Quebra o loop 'j' e reinicia o loop externo (para '_') para esta rota
            if improved:
                continue # Se houve melhoria, continua o loop externo para mais otimizações nesta rota
            else:
                break # Se nenhuma melhoria foi encontrada em todas as posições, sai do relocate intra

    return best_segments, best_cost

def perform_relocate_inter(all_routes_data, sp_matrix, depot_node, id_to_service_obj, capacity):
    """
    Aplica o operador Relocate inter-rotas: tenta mover um serviço de uma rota para outra rota existente.
    Modifica a lista `all_routes_data` (solução completa) in-place.
    
    Args:
        all_routes_data (list): Lista de dicionários representando todas as rotas da solução atual.
        sp_matrix (dict): Matriz de caminhos mais curtos.
        depot_node (int): Nó do depósito.
        id_to_service_obj (dict): Mapeamento de service_id para objeto de serviço.
        capacity (int): Capacidade do veículo.
        
    Returns:
        bool: True se alguma melhoria foi encontrada e aplicada, False caso contrário.
    """
    total_improved = False # Flag global para indicar se houve QUALQUER melhoria nesta função

    # Loop principal para continuar buscando melhorias enquanto elas forem encontradas
    while True:
        improved_in_iteration = False # Flag para indicar se houve melhoria nesta iteração completa de todos os pares de rotas
        
        # Itera sobre todas as rotas como rota de origem (r1)
        for r1_idx in range(len(all_routes_data)):
            r1 = all_routes_data[r1_idx]
            r1_services = [v for v in r1['visits'] if v[0] == 'S'] # Serviços da rota de origem
            if not r1_services: continue # Rota de origem vazia, não há serviços para mover

            # Itera sobre cada serviço na rota de origem (o serviço a ser movido)
            for s_idx in range(len(r1_services)):
                service_to_move = r1_services[s_idx]
                
                # Cria uma versão temporária da rota de origem sem o serviço
                r1_temp_services = r1_services[:s_idx] + r1_services[s_idx+1:]
                
                # Calcula o custo e demanda da rota de origem APÓS a remoção
                r1_cost_after_removal = calculate_route_cost_from_segments(r1_temp_services, sp_matrix, depot_node, id_to_service_obj)
                r1_demand_after_removal, r1_feasible_after_removal = calculate_route_demand(r1_temp_services, id_to_service_obj, capacity)
                
                if not r1_feasible_after_removal: # Se a rota de origem ficar inviável (improvável para remoção), pula
                    continue

                # Itera sobre todas as outras rotas como rota de destino (r2)
                for r2_idx in range(len(all_routes_data)):
                    if r1_idx == r2_idx: continue # Não tenta mover para a mesma rota

                    r2 = all_routes_data[r2_idx]
                    r2_services = [v for v in r2['visits'] if v[0] == 'S'] # Serviços da rota de destino
                    
                    # Tenta inserir o serviço em todas as posições possíveis na rota de destino
                    for insert_pos in range(len(r2_services) + 1):
                        r2_temp_services = r2_services[:insert_pos] + [service_to_move] + r2_services[insert_pos:]
                        
                        # Verifica a viabilidade da rota de destino com o novo serviço
                        r2_demand_after_insertion, r2_feasible_after_insertion = calculate_route_demand(r2_temp_services, id_to_service_obj, capacity)
                        
                        if not r2_feasible_after_insertion: # Se a rota de destino ficar inviável, pula
                            continue
                        
                        # Calcula o novo custo da rota de destino
                        r2_cost_after_insertion = calculate_route_cost_from_segments(r2_temp_services, sp_matrix, depot_node, id_to_service_obj)

                        # Calcula a mudança total de custo na solução (custo_novo_par - custo_antigo_par)
                        old_total_cost_pair = r1['cost'] + r2['cost']
                        new_total_cost_pair = r1_cost_after_removal + r2_cost_after_insertion
                        
                        if new_total_cost_pair < old_total_cost_pair: # Se encontrou uma melhoria global
                            # --- Aplica a melhoria (modifica as rotas in-place) ---
                            # Atualiza rota de origem (r1)
                            r1['visits'] = [('D', 0, depot_node, depot_node)] + r1_temp_services + [('D', 0, depot_node, depot_node)]
                            r1['demand'] = r1_demand_after_removal
                            r1['cost'] = r1_cost_after_removal

                            # Atualiza rota de destino (r2)
                            r2['visits'] = [('D', 0, depot_node, depot_node)] + r2_temp_services + [('D', 0, depot_node, depot_node)]
                            r2['demand'] = r2_demand_after_insertion
                            r2['cost'] = r2_cost_after_insertion
                            
                            improved_in_iteration = True # Marca que houve melhoria nesta iteração da função
                            total_improved = True # Marca que houve melhoria global na execução da função
                            # Retorna True imediatamente para reiniciar a busca local global,
                            # pois a estrutura das rotas mudou e pode abrir novas oportunidades.
                            return True 

        if not improved_in_iteration: # Se nenhuma melhoria foi encontrada após tentar todas as combinações
            break # Sai do loop de busca inter-rota

    return total_improved # Retorna True se houve alguma melhoria total na função perform_relocate_inter

# --- Função Principal de Otimização (Etapa 3) ---
def otimizar_solucao(instance_filepath, initial_solution_threshold_factor=1.00, max_total_iterations=5, num_threads=None):
    """
    Função principal para a Etapa 3 do trabalho prático.
    Realiza a geração da solução inicial (internamente, replicando a Etapa 2) e aplica aprimoramentos
    usando heurísticas de busca local (2-opt, Relocate Intra/Inter-rotas).
    O All-Pairs Shortest Path (APSP) é calculado apenas uma vez e de forma paralelizada para eficiência.
    
    Args:
        instance_filepath (str): Caminho completo para o arquivo de instância (.dat).
        initial_solution_threshold_factor (float): Fator (ex: 1.05 para 5%) para decidir se uma rota
                                                    já é "boa o suficiente" e não precisa de otimização intra-rota.
        max_total_iterations (int): Número máximo de iterações do loop global de busca local (VND).
        num_threads (int, optional): Número de threads para paralelização. Se None, usa o número de CPUs.
        
    Returns:
        tuple: (final_total_cost (float), num_routes (int), total_clocks_optimization_stage (float),
                clocks_apsp (float), final_solution_routes_output (list)).
                Custo total final, número de rotas, tempo total da Etapa 3, tempo do APSP, e rotas detalhadas.
    """
    t0_total_optimization_process = time.perf_counter() # Marca o tempo de início total do processo da Etapa 3

    # 1. Carregar os dados da instância usando o módulo 'leitor_dados.py'
    dados_gerais, required_nodes, required_edges, non_required_edges, required_arcs, non_required_arcs = \
        carregar_dados_arquivo(instance_filepath)
    
    capacidade_veiculo = int(dados_gerais['Capacity']) # Capacidade dos veículos
    depot_node = int(dados_gerais['Depot Node'])     # Nó do depósito
    
    # Mapeamento de todos os Serviços Requeridos com IDs globais
    # Essencial para acessar facilmente os detalhes (demanda, custo, from/to) de cada serviço por seu ID.
    all_required_services = []
    service_id_counter = 1
    # Adiciona nós requeridos
    for rn in required_nodes:
        node_val = int(rn['node'].lstrip('N'))
        all_required_services.append({
            'id': service_id_counter, 'type': 'node', 'node_val': node_val,
            'demand': rn['demand'], 'service_cost': rn['service_cost'],
            'from': node_val, 'to': node_val
        })
        service_id_counter += 1
    # Adiciona arestas e arcos requeridos
    for re_or_ra in required_edges + required_arcs:
        s_type = 'edge' if 'edge' in re_or_ra else 'arc'
        all_required_services.append({
            'id': service_id_counter, 'type': s_type, 'from': re_or_ra['from'], 'to': re_or_ra['to'],
            'traversal_cost': re_or_ra['traversal_cost'], # Importante para construir o grafo
            'demand': re_or_ra['demand'], 'service_cost': re_or_ra['service_cost']
        })
        service_id_counter += 1
    
    id_to_service_obj = {s['id']: s for s in all_required_services}

    # === CÁLCULO ÚNICO DO ALL-PAIRS SHORTEST PATH (APSP) ===
    # Esta é a parte mais intensiva computacionalmente para grafos grandes.
    # O APSP é calculado apenas uma vez neste módulo.
    start_time_path_finding = time.perf_counter()
    
    # Conta o total de nós no grafo e os ordena
    total_nodes_count = contar_vertices(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes)
    all_graph_nodes = sorted(list(set(range(1, total_nodes_count + 1))))
    
    # Constrói o grafo (adjacência e custos) a partir dos dados carregados
    graph_adj, traversal_costs_direct = construir_grafo(required_edges, non_required_edges, required_arcs, non_required_arcs)
    
    short_paths_matrix = {} # Dicionário para armazenar as distâncias mais curtas entre todos os pares

    # Define o número de threads a serem usadas para paralelizar o cálculo do Dijkstra
    # Se 'num_threads' for None, usa o número de CPUs lógicas disponíveis no sistema.
    num_threads_apsp = os.cpu_count() if os.cpu_count() else 1 

    # Função auxiliar para ThreadPoolExecutor: executa Dijkstra para um nó de origem.
    def run_dijkstra_for_node(start_node_for_worker):
        return start_node_for_worker, dijkstra_optimized(start_node_for_worker, graph_adj, traversal_costs_direct, all_graph_nodes)

    # Paraleliza o cálculo do APSP
    if num_threads_apsp > 1 and len(all_graph_nodes) > 1:
        print(f"  Paralelizando cálculo APSP com {num_threads_apsp} threads...")
        with ThreadPoolExecutor(max_workers=num_threads_apsp) as executor:
            # 'executor.map' aplica a função 'run_dijkstra_for_node' a cada 'start_node' em 'all_graph_nodes'.
            # Os resultados são processados à medida que ficam prontos.
            for start_node_result, distances_from_start in executor.map(run_dijkstra_for_node, all_graph_nodes):
                for end_node, dist in distances_from_start.items():
                    short_paths_matrix[(start_node_result, end_node)] = dist
    else: 
        # Execução sequencial do APSP se não houver threads ou nós suficientes
        print("  Calculando APSP sequencialmente...")
        for start_node in all_graph_nodes:
            distances_from_start = dijkstra_optimized(start_node, graph_adj, traversal_costs_direct, all_graph_nodes)
            for end_node, dist in distances_from_start.items():
                short_paths_matrix[(start_node, end_node)] = dist
    
    end_time_path_finding = time.perf_counter()
    clocks_apsp = (end_time_path_finding - start_time_path_finding) * 1000 # Tempo total do cálculo APSP em milissegundos

    # 2. Gerar a solução inicial (replicando a Etapa 2)
    # Esta é a fase construtiva que gera um conjunto de rotas viáveis.
    start_time_constructive = time.perf_counter()
    total_cost_initial_internal, num_routes_initial_internal, all_routes_data = \
        generate_initial_solution_internal(
            dados_gerais, required_nodes, required_edges, non_required_edges, 
            required_arcs, non_required_arcs, short_paths_matrix, id_to_service_obj
        )
    end_time_constructive = time.perf_counter()
    clocks_constructive_internal = (end_time_constructive - start_time_constructive) * 1000 # Tempo da fase construtiva

    # === 3. Aplicar aprimoramentos de Busca Local (VND - Variable Neighborhood Descent) ===
    # A Busca Local tenta melhorar a solução inicial através de pequenas modificações (operadores).
    # O VND alterna entre diferentes operadores de vizinhança.
    current_total_cost_solution = total_cost_initial_internal # Custo inicial da solução antes da busca local
    
    # Cria uma cópia profunda das rotas iniciais para trabalhar (para não modificar o objeto original)
    best_solution_routes = deepcopy(all_routes_data) 
    
    # Define o número de threads a serem usadas para paralelizar operadores intra-rota.
    if num_threads is None:
        num_threads = os.cpu_count() if os.cpu_count() else 1

    total_improved_in_search = True # Flag para controlar o loop global de busca: True se alguma melhoria foi encontrada
    iteration_counter = 0 # Contador de iterações do VND

    # Loop principal do VND: continua enquanto houver melhorias e não exceder o número máximo de iterações
    while total_improved_in_search and iteration_counter < max_total_iterations:
        total_improved_in_search = False # Reseta a flag para esta iteração
        iteration_counter += 1
        print(f"  Iniciando Iteração Global de Busca Local {iteration_counter} (Custo Atual: {current_total_cost_solution:.2f})...")

        # --- Operador 1: 2-opt (Intra-rota) ---
        improved_2opt_pass = False # Flag para saber se o 2-opt melhorou nesta passagem
        
        # Prepara os dados de cada rota para serem processados em paralelo pelo 2-opt
        routes_for_intra_opt = []
        for route_initial_data in best_solution_routes:
            services_segment = [v for v in route_initial_data['visits'] if v[0] == 'S']
            routes_for_intra_opt.append({
                'services_segment': services_segment,
                'current_cost': calculate_route_cost_from_segments(services_segment, short_paths_matrix, depot_node, id_to_service_obj),
                'route_id': route_initial_data['route_id']
            })

        # Função wrapper para ThreadPoolExecutor: aplica 2-opt a uma única rota
        def wrapper_2opt_single_route(route_info):
            services = route_info['services_segment']
            initial_cost = route_info['current_cost']
            route_id = route_info['route_id']
            
            # Condição de early stopping / threshold: se a rota já está "boa o suficiente"
            # initial_solution_threshold_factor * initial_cost é para permitir uma margem de melhora.
            # Se a rota já está dentro dessa margem, não otimiza.
            if initial_cost < (initial_solution_threshold_factor * initial_cost) and initial_solution_threshold_factor >= 1.0: 
                return services, initial_cost, route_id, False # Retorna a rota original sem otimização

            # Aplica o operador 2-opt
            optimized_segments, optimized_cost = perform_2opt(services, short_paths_matrix, depot_node, id_to_service_obj, capacidade_veiculo)
            return optimized_segments, optimized_cost, route_id, optimized_cost < initial_cost # Retorna se houve melhora

        # Executa o 2-opt em paralelo para todas as rotas (se houver mais de 1 thread e rota)
        if num_threads > 1 and len(routes_for_intra_opt) > 0:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                results_2opt = list(executor.map(wrapper_2opt_single_route, routes_for_intra_opt))
        else: # Execução sequencial
            results_2opt = [wrapper_2opt_single_route(r) for r in routes_for_intra_opt]

        # Atualiza a melhor solução global com os resultados do 2-opt
        new_best_solution_routes = []
        new_total_cost_temp = 0
        
        for optimized_segments, optimized_cost, route_id, was_improved in results_2opt:
            if was_improved:
                improved_2opt_pass = True # Marca que pelo menos uma rota foi melhorada pelo 2-opt
            
            # Reconstroi o formato completo da rota para a saída
            final_demand, _ = calculate_route_demand(optimized_segments, id_to_service_obj, capacidade_veiculo)
            final_visits = [('D', 0, depot_node, depot_node)] + optimized_segments + [('D', 0, depot_node, depot_node)]
            
            new_best_solution_routes.append({
                'route_id': route_id,
                'demand': final_demand,
                'cost': optimized_cost,
                'visits': final_visits
            })
            new_total_cost_temp += optimized_cost # Acumula o custo das rotas otimizadas

        # Se o 2-opt intra-rota melhorou o custo total da solução
        if improved_2opt_pass and new_total_cost_temp < current_total_cost_solution:
            best_solution_routes = new_best_solution_routes # Atualiza a melhor solução encontrada
            current_total_cost_solution = new_total_cost_temp # Atualiza o custo total
            total_improved_in_search = True # Marca que houve melhoria global nesta iteração do VND
            print(f"    2-opt Intra melhorou. Novo Custo: {current_total_cost_solution:.2f}")
            
        # --- Operador 2: Relocate Intra-rota (1-opt intra) ---
        improved_relocate_intra_pass = False # Flag para Relocate Intra
        
        # Prepara dados para paralelização do Relocate Intra (similar ao 2-opt)
        routes_for_relocate_intra_opt = []
        for route_data in best_solution_routes:
            services_segment = [v for v in route_data['visits'] if v[0] == 'S']
            routes_for_relocate_intra_opt.append({
                'services_segment': services_segment,
                'current_cost': calculate_route_cost_from_segments(services_segment, short_paths_matrix, depot_node, id_to_service_obj),
                'route_id': route_data['route_id']
            })
        
        # Função wrapper para ThreadPoolExecutor: aplica Relocate Intra a uma única rota
        def wrapper_relocate_intra_single_route(route_info):
            services = route_info['services_segment']
            initial_cost = route_info['current_cost']
            route_id = route_info['route_id']
            
            if initial_cost < (initial_solution_threshold_factor * initial_cost):
                return services, initial_cost, route_id, False
            
            optimized_segments, optimized_cost = perform_relocate_intra(services, short_paths_matrix, depot_node, id_to_service_obj, capacidade_veiculo)
            return optimized_segments, optimized_cost, route_id, optimized_cost < initial_cost

        # Executa Relocate Intra em paralelo
        if num_threads > 1 and len(routes_for_relocate_intra_opt) > 0:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                results_relocate_intra = list(executor.map(wrapper_relocate_intra_single_route, routes_for_relocate_intra_opt))
        else:
            results_relocate_intra = [wrapper_relocate_intra_single_route(r) for r in routes_for_relocate_intra_opt]
            
        new_best_solution_routes = []
        new_total_cost_temp = 0
        
        for optimized_segments, optimized_cost, route_id, was_improved in results_relocate_intra:
            if was_improved:
                improved_relocate_intra_pass = True

            final_demand, _ = calculate_route_demand(optimized_segments, id_to_service_obj, capacidade_veiculo)
            final_visits = [('D', 0, depot_node, depot_node)] + optimized_segments + [('D', 0, depot_node, depot_node)]
            
            new_best_solution_routes.append({
                'route_id': route_id,
                'demand': final_demand,
                'cost': optimized_cost,
                'visits': final_visits
            })
            new_total_cost_temp += optimized_cost

        # Se o Relocate Intra melhorou o custo total
        if improved_relocate_intra_pass and new_total_cost_temp < current_total_cost_solution:
            best_solution_routes = new_best_solution_routes
            current_total_cost_solution = new_total_cost_temp
            total_improved_in_search = True
            print(f"    Relocate Intra melhorou. Novo Custo: {current_total_cost_solution:.2f}")

        # --- Operador 3: Relocate Inter-rota (Busca entre rotas) ---
        # Este operador é tipicamente executado sequencialmente devido à complexidade de gerenciar
        # modificações entre múltiplas rotas de forma paralela. Ele tenta mover um serviço de uma
        # rota para qualquer outra rota existente na solução.
        improved_inter_relocate_pass = perform_relocate_inter(best_solution_routes, short_paths_matrix, depot_node, id_to_service_obj, capacidade_veiculo)
        
        # Se o Relocate Inter melhorou o custo total
        if improved_inter_relocate_pass:
            # O perform_relocate_inter modifica as rotas in-place, então recalculamos o custo total aqui.
            current_total_cost_solution = sum(r['cost'] for r in best_solution_routes) 
            total_improved_in_search = True
            print(f"    Relocate Inter melhorou. Novo Custo: {current_total_cost_solution:.2f}")

    # === Fim da Busca Local (VND) ===
    
    final_solution_routes_output = best_solution_routes # A melhor solução de rotas encontrada
    final_total_cost = current_total_cost_solution # O custo total final da solução

    t1_total_optimization_process = time.perf_counter()
    # Tempo total de execução da função otimizar_solucao (Etapa 3)
    total_clocks_optimization_stage = (t1_total_optimization_process - t0_total_optimization_process) * 1000

    # Retorna os resultados conforme o formato esperado.
    # clocks_ref_exec: tempo total da Etapa 3 (APSP + Construtivo + Busca Local)
    # clocks_ref_find: tempo apenas do APSP
    return (final_total_cost, len(final_solution_routes_output),
            total_clocks_optimization_stage, clocks_apsp,
            final_solution_routes_output)