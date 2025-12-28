from qaoa import *
from qaoa.qaoa import qaoa_min_graph_coloring
import numpy as np
from qaoa.util import color_graph_greedy


def get_schedule_from_parameters(school_xml, parameters_string):
    events = parseXML(school_xml)
    G = create_graph_from_events(events)

    if "Toy" in school_xml:
        num_colors = 4
        color_graph_greedy(G)
    else:
        num_colors = 5

    num_nodes = G.number_of_nodes()

    cleaned_string = parameters_string.replace('[', '').replace(']', '').strip()
    par = [float(x) for x in cleaned_string.split()]

    beta0 = par[0]
    rest = par[1:]
    middle = int(len(rest) / 2)
    gamma = rest[:middle]
    beta = rest[middle:]
    p = len(gamma)  # Infer p from the number of gamma parameters

    print(f"Replaying Circuit with p={p}...")
    print(f"Beta0: {beta0:.4f}")
    print(f"Gamma: {[f'{g:.4f}' for g in gamma]}")
    print(f"Beta:  {[f'{b:.4f}' for b in beta]}")

    result = qaoa_min_graph_coloring(p, G, num_nodes, num_colors, beta0, gamma, beta, 1e-6)

    best_state_int = 0
    max_prob = -1

    for state_int in result.states:
        prob = result.probability(state_int)
        if prob > max_prob:
            max_prob = prob
            best_state_int = state_int

    print(f"\nMost probable state found with probability: {max_prob:.4f}")

    total_qubits = (num_nodes * num_colors) + num_nodes
    binary = f'{best_state_int:0{total_qubits}b}'

    x = [int(bit) for bit in binary]

    print("\n--- Final Schedule ---")
    node_list = list(G.nodes)

    for i in range(num_nodes):
        event_name = node_list[i]
        node_bits = x[i * num_colors: (i * num_colors + num_colors)]

        assigned_slot = -1
        for slot_idx, is_active in enumerate(node_bits):
            if is_active:
                assigned_slot = slot_idx
                break

        if assigned_slot != -1:
            print(f"{event_name}: Time Slot {assigned_slot}")
        else:
            print(f"{event_name}: NO VALID TIME ASSIGNED (Invalid State)")


csv_params = "[ 3.142e+00  5.413e+00  5.639e+00  7.852e-01  1.589e+00]"

get_schedule_from_parameters('dataset/Toy_Model.xml', csv_params)
