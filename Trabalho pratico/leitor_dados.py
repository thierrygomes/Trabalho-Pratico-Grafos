import re # Importa o módulo 're' para usar expressões regulares (útil para lstrip se necessário, ou para re.search)

def carregar_dados_arquivo(arquivo):
    """
    Carrega os dados de um arquivo .dat e os organiza em dicionários e listas.
    Esta função lê o arquivo linha por linha, identifica seções e parseia os dados.
    
    Args:
        arquivo (str): O caminho completo para o arquivo .dat a ser lido.
        
    Returns:
        tuple: Uma tupla contendo 5 listas e 1 dicionário com os dados carregados:
               - dados_gerais (dict): Informações gerais da instância.
               - required_nodes (list): Lista de nós que requerem serviço.
               - required_edges (list): Lista de arestas requeridas.
               - non_required_edges (list): Lista de arestas não requeridas.
               - required_arcs (list): Lista de arcos requeridos.
               - non_required_arcs (list): Lista de arcos não requeridos.
    """
    # Inicialização das estruturas de dados para armazenar as informações
    dados_gerais = {}          # Armazena informações como Capacidade, Depósito, etc.
    required_nodes = []        # Nós que devem ser visitados
    required_edges = []        # Arestas não direcionadas que devem ser percorridas
    non_required_edges = []    # Arestas não direcionadas opcionais
    required_arcs = []         # Arcos direcionados que devem ser percorridos
    non_required_arcs = []     # Arcos direcionados opcionais

    # Mapeia os cabeçalhos das seções do arquivo para nomes de seções internos
    section_map = {
        "ReN.": "ReN",   # Seção de Nós Requeridos
        "ReE.": "ReE",   # Seção de Arestas Requeridas
        "ReA.": "ReA",   # Seção de Arcos Requeridos
        "ARC": "NrA",    # Seção de Arcos Não Requeridos (linha 'ARC' sozinha)
        "EDGE": "NrE"    # Seção de Arestas Não Requeridas (linha 'EDGE' sozinha)
    }

    current_section = 'meta' # Começa lendo a seção de metadados/dados gerais do arquivo

    # Abre e lê o arquivo linha por linha
    with open(arquivo, 'r') as f:
        for line_num, linha in enumerate(f, 1): # line_num para rastrear o número da linha
            linha = linha.strip() # Remove espaços em branco do início e fim da linha
            if not linha:
                continue # Pula linhas vazias

            # Verifica se a linha atual é um cabeçalho de nova seção
            found_section_header = False
            for header_prefix, section_name in section_map.items():
                if linha.startswith(header_prefix):
                    # Evita confundir 'EDGE' (não requerida) com 'ReE.' (requerida)
                    if header_prefix == "EDGE" and "ReE." in linha:
                        continue 
                    current_section = section_name # Atualiza a seção atual
                    found_section_header = True
                    break
            
            if found_section_header:
                continue # Se encontrou um cabeçalho de seção, vai para a próxima linha para ler os dados da nova seção

            # Processa os dados com base na seção atual
            parts = linha.split() # Divide a linha em partes usando espaços como delimitador

            if current_section == 'meta':
                # Processa linhas de metadados no formato "Chave: Valor"
                if ':' in linha:
                    chave, valor = linha.split(':', 1) # Divide em no máximo 2 partes no primeiro ':'
                    dados_gerais[chave.strip()] = valor.strip() # Armazena no dicionário geral
            
            elif current_section == 'ReN' and len(parts) >= 3:
                # Processa Nós Requeridos: Node Demand Service_Cost
                try:
                    required_nodes.append({
                        'node': parts[0],
                        'demand': int(parts[1]),
                        'service_cost': int(parts[2])
                    })
                except ValueError:
                    # Captura erros de conversão de tipo (ex: texto onde esperava número)
                    # print(f"AVISO: Erro de valor na linha {line_num} (ReN): '{linha}' - Ignorando.") # Descomente para depuração
                    pass # Silencia o erro, mas poderia logar ou levantar uma exceção
            
            elif current_section == 'ReE' and len(parts) >= 6:
                # Processa Arestas Requeridas: Edge_ID From To Traversal_Cost Demand Service_Cost
                try:
                    required_edges.append({
                        'edge': parts[0],
                        'from': int(parts[1]),
                        'to': int(parts[2]),
                        'traversal_cost': int(parts[3]),
                        'demand': int(parts[4]),
                        'service_cost': int(parts[5])
                    })
                except ValueError:
                    pass
            
            elif current_section == 'ReA' and len(parts) >= 6:
                # Processa Arcos Requeridos: Arc_ID From To Traversal_Cost Demand Service_Cost
                try:
                    required_arcs.append({
                        'arc': parts[0],
                        'from': int(parts[1]),
                        'to': int(parts[2]),
                        'traversal_cost': int(parts[3]),
                        'demand': int(parts[4]),
                        'service_cost': int(parts[5])
                    })
                except ValueError:
                    pass
            
            elif current_section == 'NrA' and len(parts) >= 4:
                # Processa Arcos Não Requeridos: Arc_ID From To Traversal_Cost
                try:
                    non_required_arcs.append({
                        'arc': parts[0],
                        'from': int(parts[1]),
                        'to': int(parts[2]),
                        'traversal_cost': int(parts[3])
                    })
                except ValueError:
                    pass
            
            elif current_section == 'NrE' and len(parts) >= 4:
                # Processa Arestas Não Requeridas: Edge_ID From To Traversal_Cost
                try:
                    non_required_edges.append({
                        'edge': parts[0],
                        'from': int(parts[1]),
                        'to': int(parts[2]),
                        'traversal_cost': int(parts[3])
                    })
                except ValueError:
                    pass

    # Retorna todas as estruturas de dados populadas
    return dados_gerais, required_nodes, required_edges, non_required_edges, required_arcs, non_required_arcs