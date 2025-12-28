from qaoa import *
from qaoa.util import color_graph_greedy


# Define the Cost Function for the Toy Model
# Based on the Soft Constraints in Toy_Model.xml:
# - Event0 prefers Time 0 (13.30)
# - Event1 prefers Time 1 (14.40)
# - Event2 prefers Time 2 (15.50)
# - Event3 prefers Time 3 (17.00)
def cost_function_toy(G):
    C = 0

    # Check if Event0 is NOT in color 0
    if G.nodes["Event0"]['color'] != 0:
        C += 1

    # Check if Event1 is NOT in color 1
    if G.nodes["Event1"]['color'] != 1:
        C += 1

    # Check if Event2 is NOT in color 2
    if G.nodes["Event2"]['color'] != 2:
        C += 1

    # Check if Event3 is NOT in color 3
    if G.nodes["Event3"]['color'] != 3:
        C += 1

    return C


def main():
    print("Starting program for Toy Model\n")

    # For logging to ./results/
    school = "Toy"

    events = parseXML('dataset/Toy_Model.xml')
    G = create_graph_from_events(events)

    print("--------------------------")
    print("Graph information\n")
    print("Nodes = ", G.nodes)
    degree = [deg for (node, deg) in G.degree()]
    print("\nDegree of each node", degree)
    num_colors = 4
    print("\nNumber of colors set to:", num_colors)

    # Coloring
    color_graph_greedy(G)
    coloring = [G.nodes[node]['color'] for node in G.nodes]
    print("\nInitial coloring (Valid Hard Constraints):", coloring)

    # Check the initial cost (how many preferences are violated?)
    initial_function_value = cost_function_toy(G)
    print("\nInitial Function Value (Soft Constraint Violations):", initial_function_value)

    print("----------------------------")
    print("Verifying Graph consistency")
    for i in G.nodes:
        color_and_neighbour = [(neighbour, G.nodes[neighbour]['color']) for neighbour in G[i]]
        for neighbour, color in color_and_neighbour:
            if color == G.nodes[i]['color']:
                print(f"ERROR: CLASH DETECTED between {i} and {neighbour}")

    # ----------------------------
    # QAOA
    # ----------------------------
    print("----------------------------")
    print("Running QAOA")
    num_nodes = G.number_of_nodes()
    # Calculate qubits: (Events * Colors) + Events
    number_of_qubits = num_nodes * num_colors + num_nodes
    print("Necessary number of qubits: ", number_of_qubits)

    # QAOA parameter p (depth)
    goal_p = 8

    minimization_process_cobyla(goal_p, G, num_colors, school, cost_function_toy)

    print("Program End")
    print("----------------------------")


if __name__ == '__main__':
    main()
