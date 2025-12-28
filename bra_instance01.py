from qaoa import *


def cost_function_bra(G):
    C = 0

    # Find times for each teacher
    times_T1 = []
    times_T2 = []
    times_T3 = []
    times_T4 = []
    times_T5 = []
    times_T6 = []
    times_T7 = []
    times_T8 = []

    for node in G.nodes:
        if node.find("T1") != -1:
            times_T1.append(G.nodes[node]['color'])
        if node.find("T2") != -1:
            times_T2.append(G.nodes[node]['color'])
        if node.find("T3") != -1:
            times_T3.append(G.nodes[node]['color'])
        if node.find("T4") != -1:
            times_T4.append(G.nodes[node]['color'])
        if node.find("T5") != -1:
            times_T5.append(G.nodes[node]['color'])
        if node.find("T6") != -1:
            times_T6.append(G.nodes[node]['color'])
        if node.find("T7") != -1:
            times_T7.append(G.nodes[node]['color'])
        if node.find("T8") != -1:
            times_T8.append(G.nodes[node]['color'])

    # No IDLE time for teachers constraint Soft 3
    # Counting IDLE time
    for i in times_T1[:-1]:
        for ii in times_T1[i:]:
            # Check if in same day (Integer division by 5) and gap is 2 slots
            if int(i / 5) == int(ii / 5) and abs(i - ii) == 2:
                C += 3

    # Not more than 2 days with lessons for teacher Soft 9
    # Not more than 3 days with lessons for teacher Soft 9 - only T6
    # Count number of days from teacher
    days_T1 = len(set([int(time / 5) for time in times_T1]))  # <--- Changed 3 to 5
    days_T2 = len(set([int(time / 5) for time in times_T2]))
    days_T3 = len(set([int(time / 5) for time in times_T3]))
    days_T4 = len(set([int(time / 5) for time in times_T4]))
    days_T5 = len(set([int(time / 5) for time in times_T5]))
    days_T6 = len(set([int(time / 5) for time in times_T6]))
    days_T7 = len(set([int(time / 5) for time in times_T7]))
    days_T8 = len(set([int(time / 5) for time in times_T8]))

    days_list = [days_T1, days_T2, days_T3, days_T4, days_T5, days_T7, days_T8]
    for days in days_list:
        if days > 2:
            C += 9
    if days_T6 > 3:
        C += 9

    return C


def create_graph_from_events(events):
    import networkx as nx
    from itertools import combinations

    G = nx.Graph()

    # --- FIX 1: Update Week to have 5 slots per day ---
    week = [
        "Mo_1", "Mo_2", "Mo_3", "Mo_4", "Mo_5",
        "Tu_1", "Tu_2", "Tu_3", "Tu_4", "Tu_5",
        "We_1", "We_2", "We_3", "We_4", "We_5",
        "Th_1", "Th_2", "Th_3", "Th_4", "Th_5",
        "Fr_1", "Fr_2", "Fr_3", "Fr_4", "Fr_5",
    ]

    # Add Time Nodes and Edges between them
    comb = combinations(week, 2)
    G.add_nodes_from(week)
    G.add_nodes_from([(day, {'color': c}) for c, day in enumerate(week)])
    for i in comb:
        G.add_edge(i[0], i[1])

    # Adding events to graph
    # No clash constraints Hard 1
    G.add_nodes_from([(event['Id'], {'color': None}) for event in events])
    comb = combinations(events, 2)
    for i in comb:
        res0 = set(i[0]['Resources'])
        res1 = i[1]['Resources']
        intersection = [value for value in res0 if value in res1]
        if intersection:
            G.add_edge(i[0]['Id'], i[1]['Id'])

    # --- FIX 2: Update Forbidden Times (Hard Constraints) ---
    # The XML defines specific days unavailable for specific teachers.
    # We must forbid slots 1-5 for those days.

    # T1: Unavailable on Wednesday
    for slot in ["We_1", "We_2", "We_3", "We_4", "We_5"]:
        G.add_edge("T1-S1", slot)
        G.add_edge("T1-S2", slot)
        G.add_edge("T1-S3", slot)

    # T2: Unavailable on Friday
    for slot in ["Fr_1", "Fr_2", "Fr_3", "Fr_4", "Fr_5"]:
        G.add_edge("T2-S1", slot)
        G.add_edge("T2-S2", slot)

    # T3: Unavailable on Thursday
    for slot in ["Th_1", "Th_2", "Th_3", "Th_4", "Th_5"]:
        G.add_edge("T3-S1", slot)
        G.add_edge("T3-S2", slot)
        G.add_edge("T3-S3", slot)

    # T4: Unavailable on Tuesday
    for slot in ["Tu_1", "Tu_2", "Tu_3", "Tu_4", "Tu_5"]:
        G.add_edge("T4-S1", slot)
        G.add_edge("T4-S2", slot)
        G.add_edge("T4-S3", slot)

    # T5: Unavailable on Monday
    for slot in ["Mo_1", "Mo_2", "Mo_3", "Mo_4", "Mo_5"]:
        G.add_edge("T5-S2", slot)
        G.add_edge("T5-S3", slot)

    # T6: Unavailable on Wednesday
    for slot in ["We_1", "We_2", "We_3", "We_4", "We_5"]:
        G.add_edge("T6-S1", slot)
        G.add_edge("T6-S2", slot)
        G.add_edge("T6-S3", slot)

    # T7: Unavailable on Tuesday
    for slot in ["Tu_1", "Tu_2", "Tu_3", "Tu_4", "Tu_5"]:
        G.add_edge("T7-S1", slot)
        G.add_edge("T7-S3", slot)

    # T8: Unavailable on Thursday
    for slot in ["Th_1", "Th_2", "Th_3", "Th_4", "Th_5"]:
        G.add_edge("T8-S1", slot)
        G.add_edge("T8-S2", slot)
        G.add_edge("T8-S3", slot)

    return G


def color_graph_from_num(graph, num_color):
    color_index = 0
    node_list = list(graph.nodes)
    not_allowed_color = []

    # Mark all the vertices as not visited
    visited = {x: False for x in graph.nodes}
    for node in graph.nodes:
        if graph.nodes[node]['color'] != None:
            visited[node] = True

    # Create a queue for BFS
    queue = []

    # Mark the source node as
    # visited and enqueue it
    for u in node_list:
        success = True
        queue.append(u)
        visited[u] = True

        while queue:
            # Dequeue a vertex from queue and color it
            source = queue.pop(0)
            not_allowed_color = {graph.nodes[neighbour]['color'] for neighbour in graph[source]
                                 if (graph.nodes[neighbour]['color'] != None)}
            if len(not_allowed_color) == num_color:
                success = False
                visited = {x: False for x in graph.nodes}
                break

            while color_index in not_allowed_color:
                color_index = (color_index + 1) % num_color
            graph.nodes[source]['color'] = color_index
            not_allowed_color = set()

            # Get all adjacent vertices of the
            # dequeued vertex s. If a adjacent
            # has not been visited, then mark it
            # visited and enqueue it
            for i in graph[source]:
                if visited[i] == False:
                    queue.append(i)
                    visited[i] = True
        if success:
            break

    return


def main():
    print("Starting program\n")

    # --------------------------
    # School Instances
    # --------------------------
    school = "Bra"

    # --------------------------
    # Parse XML file
    # --------------------------
    events = parseXML('dataset/bra-instance01.xml')

    # --------------------------
    #  Preparing Conflict Graph
    # --------------------------
    G = create_graph_from_events(events)

    print("--------------------------")
    print("Graph information\n")

    print("Nodes = ", G.nodes)
    coloring = [G.nodes[node]['color'] for node in G.nodes]
    print("\nPre-coloring", coloring)

    degree = [deg for (node, deg) in G.degree()]
    print("\nDegree of each node", degree)

    # --------------------------
    #  Coloring Conflict Graph
    # --------------------------
    num_colors = 25
    color_graph_from_num(G, num_colors)

    coloring = [G.nodes[node]['color'] for node in G.nodes]

    print("\nNumber of colors", num_colors)
    print("\nInitial coloring", coloring)

    initial_function_value = cost_function_bra(G)
    print("\nInitial Function Value", initial_function_value)

    # ---------------------------
    # Verifying Graph consistency
    # ----------------------------
    print("----------------------------")
    print("Verifying Graph consistency")
    for i in G.nodes:
        print("\nNode", i, "Color", G.nodes[i]['color'])
        color_and_neighbour = [(neighbour, G.nodes[neighbour]['color']) for neighbour in G[i]]
        print("Neighbours | Color")
        for pair in color_and_neighbour:
            print(pair)

    # ----------------------------
    # Starting QAOA
    # ----------------------------
    print("----------------------------")
    print("Running QAOA")
    num_nodes = G.number_of_nodes()
    number_of_qubits = num_nodes * num_colors + num_nodes
    print("Necessary number of qubits: ", number_of_qubits)

    # QAOA parameter
    goal_p = 8

    # Minimizing Example Bra
    minimization_process_cobyla(goal_p, G, num_colors, school, cost_function_bra)
    # minimization_process_cma(goal_p, G, num_colors, school)

    print("Program End")
    print("----------------------------")


if __name__ == '__main__':
    main()
