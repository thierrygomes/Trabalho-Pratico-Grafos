import heapq
from collections import defaultdict, deque
import sys # Importa o módulo sys

#leitura do arquivo.
# O arquivo deve estar no mesmo diretório do script ou fornecer o caminho completo.
# O arquivo deve conter as informações no formato especificado.
# O nome do arquivo será passado como argumento na linha de comando.
# lembre-se de digitar o caminho completo do arquivo, caso não esteja no mesmo diretório do script.

if len(sys.argv) < 2:
    print("Uso: python teste_uso.py <nome_do_arquivo.dat>")
    sys.exit(1)

arquivo = sys.argv[1] # Pega o nome do arquivo do primeiro argumento da linha de comando

dados_gerais = {}
required_nodes = []
required_edges = []
non_required_edges = []
required_arcs = []
non_required_arcs = []


estado = 'meta'

with open(arquivo, 'r') as f:
    for linha in f:
        linha = linha.strip()
        if not linha:
            continue

        if linha.startswith('ReN.'):
            estado = 'ReN'
            continue
        elif linha.startswith('ReE.'):
            estado = 'ReE'
            continue
        elif linha.startswith('ReA.'):
            estado = 'ReA'
            continue
        elif linha.startswith('ARC'):
            estado = 'ARC'
            continue
        elif linha.startswith('EDGE') and 'FROM' in linha:
            estado = 'non_required_edge'
            continue
        elif ':' in linha and estado == 'meta':
            chave, valor = linha.split(':', 1)
            dados_gerais[chave.strip()] = valor.strip()
        elif estado == 'ReN':
            partes = linha.split()
            if len(partes) < 3:
                continue
            try:
                required_nodes.append({
                    'node': partes[0],
                    'demand': int(partes[1]),
                    'service_cost': int(partes[2])
                })
            except ValueError:
                continue
        elif estado == 'ReE':
            partes = linha.split()
            if len(partes) < 6:
                continue
            try:
                required_edges.append({
                    'edge': partes[0],
                    'from': int(partes[1]),
                    'to': int(partes[2]),
                    'traversal_cost': int(partes[3]),
                    'demand': int(partes[4]),
                    'service_cost': int(partes[5])
                })
            except ValueError:
                continue
        elif estado == 'ReA':
            partes = linha.split()
            if len(partes) < 6:
                continue
            try:
                required_arcs.append({
                    'arc': partes[0],
                    'from': int(partes[1]),
                    'to': int(partes[2]),
                    'traversal_cost': int(partes[3]),
                    'demand': int(partes[4]),
                    'service_cost': int(partes[5])
                })
            except ValueError:
                continue
        elif estado == 'ARC':
            partes = linha.split()
            if len(partes) < 4:
                continue
            try:
                non_required_arcs.append({
                    'arc': partes[0],
                    'from': int(partes[1]),
                    'to': int(partes[2]),
                    'traversal_cost': int(partes[3])
                })
            except ValueError:
                continue
        elif estado == 'non_required_edge':
            partes = linha.split()
            if len(partes) < 4:
                continue
            try:
                non_required_edges.append({
                    'edge': partes[0],
                    'from': int(partes[1]),
                    'to': int(partes[2]),
                    'traversal_cost': int(partes[3])
                })
            except ValueError:
                continue

# Exemplo de uso:
print('\n=== DADOS GERAIS ===')
for chave, valor in dados_gerais.items():
    print(f'{chave}: {valor}')

print('\n=== REQUIRED NODES ===')
for node in required_nodes:
    print(node)

print('\n=== REQUIRED EDGES ===')
for edge in required_edges:
    print(edge)

print('\n=== NON-REQUIRED EDGES ===')
for edge in non_required_edges:
    print(edge)

print('\n=== REQUIRED ARCS ===')
for arc in required_arcs:
    print(arc)

print('\n=== NON-REQUIRED ARCS ===')
for arc in non_required_arcs:
    print(arc)

#FUNÇÃO: quantidade de vertices
def contar_vertices(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes):
    vertices = set()

    for item in required_edges:
        vertices.add(item['from'])
        vertices.add(item['to'])

    for item in non_required_edges:
        vertices.add(item['from'])
        vertices.add(item['to'])

    for item in required_arcs:
        vertices.add(item['from'])
        vertices.add(item['to'])

    for item in non_required_arcs:
        vertices.add(item['from'])
        vertices.add(item['to'])

    for item in required_nodes:
        vertices.add(int(item['node'].lstrip("N")))

    return len(vertices)


#IMPRESSÃO: quantidade de vertices
qtd_vertices = contar_vertices(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes)
print(f'\n=== ESTATÍSTICA DO GRAFO ===')
print(f'Quantidade de vértices: {qtd_vertices}')

#FUNÇÃO: quantidade de arestas
def contar_arestas(required_edges, non_required_edges):
    arestas = set()

    for item in required_edges:
        u, v = sorted((item['from'], item['to']))
        arestas.add((u, v))

    for item in non_required_edges:
        u, v = sorted((item['from'], item['to']))
        arestas.add((u, v))

    return len(arestas)

#IMPRESSÃO: quantidade de arestas
qtd_arestas = contar_arestas(required_edges, non_required_edges)
print(f'Quantidade de arestas não direcionadas: {qtd_arestas}')

#FUNÇÃO: quantidade de arcos
def contar_arcos(required_arcs, non_required_arcs):
    return len(required_arcs) + len(non_required_arcs)

#IMPRESSÃO: quantidade de arcos
qtd_arcos = contar_arcos(required_arcs, non_required_arcs)
print(f'Quantidade de arcos (direcionados): {qtd_arcos}')

# FUNÇÃO: quantidade de vértices requeridos
def contar_vertices_requeridos(required_nodes):
    return len(required_nodes)

# IMPRESSÃO: quantidade de vértices requeridos
qtd_vertices_requeridos = contar_vertices_requeridos(required_nodes)
print(f'Quantidade de vértices requeridos: {qtd_vertices_requeridos}')

# FUNÇÃO: quantidade de arestas requeridas
def contar_arestas_requeridas(required_edges):
    return len(required_edges)

# IMPRESSÃO: quantidade de arestas requeridas
qtd_arestas_requeridas = contar_arestas_requeridas(required_edges)
print(f'Quantidade de arestas requeridas (não direcionadas): {qtd_arestas_requeridas}')

# FUNÇÃO: quantidade de arcos requeridos
def contar_arcos_requeridos(required_arcs):
    return len(required_arcs)

# IMPRESSÃO: quantidade de arcos requeridos
qtd_arcos_requeridos = contar_arcos_requeridos(required_arcs)
print(f'Quantidade de arcos requeridos (direcionados): {qtd_arcos_requeridos}')

# FUNÇÃO: Densidade do grafo (considerando arcos como direcionados)
def calcular_densidade_arcos(num_vertices, num_arcos):
    if num_vertices <= 1:
        return 0.0
    return num_arcos / (num_vertices * (num_vertices - 1))

# FUNÇÃO: Densidade do grafo (considerando arestas como não direcionadas)
def calcular_densidade_arestas(num_vertices, num_arestas):
    if num_vertices <= 1:
        return 0.0
    return num_arestas / (num_vertices * (num_vertices - 1) / 2)

# Cálculo e impressão da densidade considerando arcos
densidade_arcos = calcular_densidade_arcos(qtd_vertices, qtd_arcos)
print(f'\nDensidade do grafo (considerando arcos direcionados): {densidade_arcos:.4f}')

# Cálculo e impressão da densidade considerando arestas não direcionadas
qtd_arestas = contar_arestas(required_edges, non_required_edges)
densidade_arestas = calcular_densidade_arestas(qtd_vertices, qtd_arestas)
print(f'Densidade do grafo (considerando arestas não direcionadas): {densidade_arestas:.4f}')

print("\nObservação sobre 'Order Strength':")
print("'Order strength' geralmente se refere a grafos direcionados e mede a proporção de pares de nós")
print("que têm uma aresta direcionada entre eles (em qualquer direção). A 'densidade do grafo'")
print("para grafos direcionados, como calculado acima com os arcos, é uma métrica relacionada.")
print("Se você tiver informações específicas sobre como 'order strength' é definida para o seu contexto,")
print("pode ser necessário um cálculo ligeiramente diferente, talvez considerando a existência de uma")
print("conexão (em qualquer direção) entre pares de nós.")

def encontrar_componentes_conectados(required_edges, non_required_edges, required_nodes):
    """
    Encontra os componentes conectados em um grafo não direcionado.

    Args:
        required_edges (list): Lista de dicionários representando as arestas requeridas.
        non_required_edges (list): Lista de dicionários representando as arestas não requeridas.
        required_nodes (list): Lista de dicionários representando os nós requeridos.

    Returns:
        list: Uma lista de sets, onde cada set contém os nós de um componente conectado.
    """
    adj = {}
    nodes = set()

    # Adiciona nós requeridos ao conjunto de nós
    for node_info in required_nodes:
        try:
            nodes.add(int(node_info['node'].lstrip("N")))
        except ValueError:
            pass

    # Cria a lista de adjacência a partir das arestas (tratando como não direcionadas)
    for edge in required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)

    for edge in non_required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)

    visited = set()
    components = []

    for node in nodes:
        if node not in visited:
            component = set()
            stack = [node]
            visited.add(node)
            component.add(node)
            while stack:
                current_node = stack.pop()
                for neighbor in adj.get(current_node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
            components.append(component)

    # Adiciona nós isolados (que não têm arestas conectadas) como componentes separados
    for node_info in required_nodes:
        try:
            node_id = int(node_info['node'].lstrip("N"))
            if node_id not in visited:
                components.append({node_id})
        except ValueError:
            pass

    return components

# Encontra e imprime os componentes conectados
componentes = encontrar_componentes_conectados(required_edges, non_required_edges, required_nodes)
print("\n=== COMPONENTES CONECTADOS ===")
for i, componente in enumerate(componentes):
    print(f"Componente {i+1}: {componente}")
print(f"Número total de componentes conectados: {len(componentes)}")

def calcular_graus(required_edges, non_required_edges, required_arcs, non_required_arcs):
    """
    Calcula o grau de cada vértice a partir das arestas e arcos.
    Considera que todas as conexões (arestas ou arcos) contam como +1 no grau.
    """
    graus = {}

    # Arestas (não direcionadas)
    for item in required_edges + non_required_edges:
        u, v = item['from'], item['to']
        graus[u] = graus.get(u, 0) + 1
        graus[v] = graus.get(v, 0) + 1

    # Arcos (direcionados, mas para grau não direcionado conta para os dois)
    for item in required_arcs + non_required_arcs:
        u, v = item['from'], item['to']
        graus[u] = graus.get(u, 0) + 1
        graus[v] = graus.get(v, 0) + 1

    return graus
graus = calcular_graus(required_edges, non_required_edges, required_arcs, non_required_arcs)

if graus:
    grau_minimo = min(graus.values())
    grau_maximo = max(graus.values())
    print(f"\nGrau mínimo dos vértices: {grau_minimo}")
    print(f"Grau máximo dos vértices: {grau_maximo}")
else:
    print("\nNão foi possível calcular o grau dos vértices.")


def calcular_intermediacao(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes):
    """
    Calcula a intermediação de cada nó no grafo.

    Args:
        required_edges (list): Lista de dicionários representando as arestas requeridas.
        non_required_edges (list): Lista de dicionários representando as arestas não requeridas.
        required_arcs (list): Lista de dicionários representando os arcos requeridos.
        non_required_arcs (list): Lista de dicionários representando os arcos não requeridos.
        required_nodes (list): Lista de dicionários representando os nós requeridos.

    Returns:
        dict: Um dicionário onde as chaves são os nós e os valores são suas pontuações de intermediação.
    """
    adj = defaultdict(list)
    nodes = set()

    # Adiciona nós requeridos
    for node_info in required_nodes:
        try:
            nodes.add(int(node_info['node'].lstrip("N")))
        except ValueError:
            pass

    # Adiciona arestas (não direcionadas) à lista de adjacência
    for edge in required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)
        adj[v].append(u)

    for edge in non_required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)
        adj[v].append(u)

    # Adiciona arcos (direcionados) à lista de adjacência
    for arc in required_arcs:
        u, v = arc['from'], arc['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)

    for arc in non_required_arcs:
        u, v = arc['from'], arc['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)

    intermediacao = defaultdict(float)
    num_nodes = len(nodes)
    node_list = list(nodes)

    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            start_node = node_list[i]
            end_node = node_list[j]

            # Calcular o caminho mais curto usando BFS
            queue = deque([(start_node, [start_node])])
            shortest_path = None

            while queue:
                current_node, path = queue.popleft()
                if current_node == end_node:
                    shortest_path = path
                    break
                for neighbor in adj[current_node]:
                    if neighbor not in path:
                        queue.append((neighbor, path + [neighbor]))

            if shortest_path:
                if len(shortest_path) > 2: # Intermediação só faz sentido para caminhos com mais de 2 nós
                    for node in shortest_path[1:-1]: # Exclui o nó inicial e final
                        intermediacao[node] += 1

    # Normalizar a intermediação pelo número de pares de nós (excluindo o nó em si)
    if num_nodes > 2:
        for node in intermediacao:
            intermediacao[node] /= ((num_nodes - 1) * (num_nodes - 2)) / 2

    return intermediacao

# Calcular e imprimir a intermediação dos nós
intermediacao_nodes = calcular_intermediacao(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes)

print("\n=== INTERMEDIAÇÃO DOS NÓS ===")
if intermediacao_nodes:
    for node, score in sorted(intermediacao_nodes.items()):
        print(f"Nó {node}: {score:.4f}")
else:
    print("Não há nós para calcular a intermediação.")

def calcular_caminho_medio(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes):
    """
    Calcula o comprimento médio dos caminhos mais curtos entre todos os pares de nós no grafo.

    Args:
        required_edges (list): Lista de dicionários representando as arestas requeridas.
        non_required_edges (list): Lista de dicionários representando as arestas não requeridas.
        required_arcs (list): Lista de dicionários representando os arcos requeridos.
        non_required_arcs (list): Lista de dicionários representando os arcos não requeridos.
        required_nodes (list): Lista de dicionários representando os nós requeridos.

    Returns:
        float: O comprimento médio dos caminhos mais curtos. Retorna 0.0 se não houver pares de nós.
    """
    adj = defaultdict(list)
    nodes = set()

    # Adiciona nós requeridos
    for node_info in required_nodes:
        try:
            nodes.add(int(node_info['node'].lstrip("N")))
        except ValueError:
            pass

    # Adiciona arestas (não direcionadas) à lista de adjacência
    for edge in required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)
        adj[v].append(u)

    for edge in non_required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)
        adj[v].append(u)

    # Adiciona arcos (direcionados) à lista de adjacência
    for arc in required_arcs:
        u, v = arc['from'], arc['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)

    for arc in non_required_arcs:
        u, v = arc['from'], arc['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)

    total_shortest_path_length = 0
    num_pairs = 0
    node_list = list(nodes)
    num_nodes = len(node_list)

    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            start_node = node_list[i]
            end_node = node_list[j]

            # Calcular o caminho mais curto usando BFS
            queue = deque([(start_node, [start_node])])
            shortest_path_length = float('inf')
            found_path = False

            while queue:
                current_node, path = queue.popleft()
                if current_node == end_node:
                    shortest_path_length = len(path) - 1
                    found_path = True
                    break
                for neighbor in adj[current_node]:
                    if neighbor not in path:
                        queue.append((neighbor, path + [neighbor]))

            if found_path:
                total_shortest_path_length += shortest_path_length
                num_pairs += 1

    if num_pairs > 0:
        return total_shortest_path_length / num_pairs
    else:
        return 0.0

# Calcular e imprimir o caminho médio
caminho_medio = calcular_caminho_medio(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes)

print("\n=== CAMINHO MÉDIO ===")
if caminho_medio > 0:
    print(f"O comprimento médio dos caminhos mais curtos é: {caminho_medio:.4f}")
else:
    print("Não há pares de nós para calcular o caminho médio.")


def calcular_diametro(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes):
    """
    Calcula o diâmetro do grafo, que é o comprimento do caminho mais longo entre todos os pares de nós.

    Args:
        required_edges (list): Lista de dicionários representando as arestas requeridas.
        non_required_edges (list): Lista de dicionários representando as arestas não requeridas.
        required_arcs (list): Lista de dicionários representando os arcos requeridos.
        non_required_arcs (list): Lista de dicionários representando os arcos não requeridos.
        required_nodes (list): Lista de dicionários representando os nós requeridos.

    Returns:
        int: O diâmetro do grafo. Retorna 0 se não houver nós ou se o grafo não for conexo.
    """
    adj = defaultdict(list)
    nodes = set()

    # Adiciona nós requeridos
    for node_info in required_nodes:
        try:
            nodes.add(int(node_info['node'].lstrip("N")))
        except ValueError:
            pass

    # Adiciona arestas (não direcionadas) à lista de adjacência
    for edge in required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)
        adj[v].append(u)

    for edge in non_required_edges:
        u, v = edge['from'], edge['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)
        adj[v].append(u)

    # Adiciona arcos (direcionados) à lista de adjacência
    for arc in required_arcs:
        u, v = arc['from'], arc['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)

    for arc in non_required_arcs:
        u, v = arc['from'], arc['to']
        nodes.add(u)
        nodes.add(v)
        adj[u].append(v)

    if not nodes:
        return 0

    max_dist = 0
    node_list = list(nodes)
    num_nodes = len(node_list)

    for i in range(num_nodes):
        start_node = node_list[i]
        distances = {node: float('inf') for node in nodes}
        distances[start_node] = 0
        queue = deque([start_node])

        while queue:
            current_node = queue.popleft()
            for neighbor in adj[current_node]:
                if distances[neighbor] == float('inf'):
                    distances[neighbor] = distances[current_node] + 1
                    max_dist = max(max_dist, distances[neighbor])
                    queue.append(neighbor)

        # Verificar se todos os nós são alcançáveis a partir do nó inicial
        if float('inf') in distances.values() and num_nodes > 1:
            return 0 # Grafo não é conexo
    return max_dist

# Calcular e imprimir o diâmetro
diametro = calcular_diametro(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes)

print("\n=== DIÂMETRO DO GRAFO ===")
if diametro > 0:
    print(f"O diâmetro do grafo é: {diametro}")
elif diametro == 0 and contar_vertices(required_edges, non_required_edges, required_arcs, non_required_arcs, required_nodes) > 0:
    print("O grafo não é conexo, portanto o diâmetro é considerado infinito (ou não definido).")
else:
    print("O grafo está vazio.")