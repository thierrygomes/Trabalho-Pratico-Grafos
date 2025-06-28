from collections import defaultdict, deque # Importa defaultdict para listas de adjacência e deque (não usado diretamente neste arquivo, mas útil para grafos)

def construir_grafo(required_edges, non_required_edges, required_arcs, non_required_arcs):
    """
    Constrói a lista de adjacência e o dicionário de custos de travessia do grafo.
    Considera arestas não direcionadas (bidirecionais) e arcos direcionados.
    
    Args:
        required_edges (list): Lista de arestas requeridas.
        non_required_edges (list): Lista de arestas não requeridas.
        required_arcs (list): Lista de arcos requeridos.
        non_required_arcs (list): Lista de arcos não requeridos.
        
    Returns:
        tuple: graph_adj (defaultdict): Lista de adjacência do grafo.
               traversal_costs (dict): Dicionário de custos de travessia (chave: (u, v), valor: custo).
    """
    graph_adj = defaultdict(list) # Dicionário para armazenar vizinhos de cada nó
    traversal_costs = {} # Dicionário para armazenar o custo de travessia entre dois nós

    # Processa arestas não direcionadas (Edges)
    # Arestas podem ser percorridas em ambos os sentidos com o mesmo custo
    for item in required_edges + non_required_edges:
        u, v, cost = item['from'], item['to'], item['traversal_cost']
        graph_adj[u].append(v) # Adiciona v como vizinho de u
        graph_adj[v].append(u) # Adiciona u como vizinho de v (bidirecional)
        traversal_costs[(u, v)] = cost # Armazena o custo de u para v
        traversal_costs[(v, u)] = cost # Armazena o custo de v para u
        
    # Processa arcos direcionados (Arcs)
    # Arcos podem ser percorridos apenas em um sentido
    for item in required_arcs + non_required_arcs:
        u, v, cost = item['from'], item['to'], item['traversal_cost']
        graph_adj[u].append(v) # Adiciona v como vizinho de u (apenas um sentido)
        traversal_costs[(u, v)] = cost # Armazena o custo de u para v

    return graph_adj, traversal_costs

def contar_vertices(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes):
    """
    Conta o número total de vértices únicos no grafo a partir de todos os tipos de elementos.
    
    Args:
        required_edges (list): Lista de arestas requeridas.
        non_required_edges (list): Lista de arestas não requeridas.
        required_arcs (list): Lista de arcos requeridos.
        non_required_arcs (list): Lista de arcos não requeridos.
        required_nodes (list): Lista de nós requeridos.
        
    Returns:
        int: Quantidade total de vértices únicos no grafo.
    """
    vertices = set() # Usa um conjunto para armazenar vértices únicos automaticamente
    
    # Adiciona os vértices 'from' e 'to' de todas as arestas e arcos
    for item in required_edges + non_required_edges + required_arcs + non_required_arcs:
        vertices.add(item['from'])
        vertices.add(item['to'])
        
    # Adiciona os nós requeridos
    for item in required_nodes:
        try:
            # Remove 'N' do prefixo (ex: 'N4' vira 4) e converte para int
            vertices.add(int(item['node'].lstrip("N")))
        except ValueError:
            # Em caso de erro na conversão (e.g., 'N' ausente ou formato inválido), ignora o item
            pass 
            
    return len(vertices) # Retorna o número de elementos únicos no conjunto