from qaoa import *
import pandas as pd
import pickle
import networkx as nx
from qaoa.util import color_graph_greedy


# --------------------------
# LOAD RULE DATAFRAMES
# --------------------------
def load_rules():
    base_path = 'dataset/'
    skills = pd.read_csv(base_path + 'InstructorSkill_tiny.csv', index_col=0)
    slots = pd.read_csv(base_path + 'InstructorSlot_tiny.csv', index_col=0)
    quotas = pd.read_csv(base_path + 'InstructorQuota_tiny.csv', index_col=0)
    return skills, slots, quotas


DF_SKILLS, DF_SLOTS, DF_QUOTAS = load_rules()

# --------------------------
# LOAD GRAPH METADATA
# --------------------------
# 'cost_function_tiny' need to access the 'subject' and 'slot'
# metadata, Pires qaoa might drop it.
with open('dataset/tiny_graph.pickle', 'rb') as f:
    G_METADATA = pickle.load(f)

# Map Integer Colors to Teacher Names
TEACHER_MAP = {0: "T_A", 1: "T_B"}


def cost_function_tiny(G_Candidate):
    """
    Soft and hard-constraints, which could not hard-coded into the mixers
    Args:
        G_Candidate: colored graph
    """
    C = 0

    # Track teacher usage for quotas
    teacher_counts = {t: 0 for t in TEACHER_MAP.values()}

    for node in G_Candidate.nodes:
        # 1. Get Assignment (Color) from the Candidate Graph
        # This changes every iteration of the optimizer
        color = G_Candidate.nodes[node]['color']

        # 2. Get Metadata (Subject/Slot) from the Global Graph
        # We use the Node ID to look up the static details
        subject = G_METADATA.nodes[node]['subject']
        slot = G_METADATA.nodes[node]['slot']

        teacher = TEACHER_MAP[color]

        # Increment quota count
        teacher_counts[teacher] += 1

        # 3. Check Skill (Must be 5)
        try:
            skill_val = DF_SKILLS.loc[teacher, subject]
            if skill_val < 5:
                C += 100  # Large penalty for unskilled teacher
        except KeyError:
            C += 100

        # 4. Check Slot Availability (Must be 5)
        try:
            avail_val = DF_SLOTS.loc[teacher, slot]
            if avail_val < 5:
                C += 10  # Penalty for unavailable teacher
        except KeyError:
            C += 10

    # 5. Check Quotas
    for teacher, count in teacher_counts.items():
        try:
            min_q = DF_QUOTAS.loc[teacher, 'Min quota']
            max_q = DF_QUOTAS.loc[teacher, 'Max quota']

            if count < min_q:
                C += 5 * (min_q - count)
            elif count > max_q:
                C += 5 * (count - max_q)
        except KeyError:
            pass  # Should not happen if data is consistent

    return C


def main():
    print("Starting program for Tiny Model\n")
    school = "Tiny"

    # Use the globally loaded graph for initialization
    G = G_METADATA

    print("--------------------------")
    print("Graph information\n")
    print("Nodes = ", G.nodes(data=True))

    degree = [deg for (node, deg) in G.degree()]
    print("\nDegree of each node", degree)

    # --------------------------
    #  Initial Coloring
    # --------------------------
    try:
        print("Attempting to color graph automatically...")
        color_graph_greedy(G)

        current_coloring = [G.nodes[node]['color'] for node in G.nodes]
        used_colors = set(current_coloring)
        num_used = len(used_colors)

        print(f"Greedy Algorithm found a valid coloring using {num_used} colors: {current_coloring}")
    except:
        # SAFETY CHECK
        # We only have 2 Teachers (T_A, T_B). If greedy used 3 colors (a.k.a. 3 teachers needed),
        # we cannot proceed.
        if num_used > 2:
            print(f"\n[!] CRITICAL ERROR: The graph is too complex for {2} teachers!")
            print(f"The greedy solver needed {num_used} colors (Teachers).")
            print("Try increasing the number of teachers in your dataset or fixing the manual coloring.")
            return  # Stop execution

    # Valid Hard Constraints: [T_A, T_B, T_A, T_B, T_A]
    # initial_coloring = [0, 1, 0, 1, 0]  # hard-coded
    # color_graph_from_coloring(G, initial_coloring)
    # print("\nInitial coloring (Valid Hard Constraints):", initial_coloring)

    # Check the initial cost
    initial_function_value = cost_function_tiny(G)
    print("\nInitial Function Value (Soft Violations):", initial_function_value)

    # ---------------------------
    # Verifying Graph consistency
    # ----------------------------
    print("----------------------------")
    print("Verifying Graph consistency (Time Conflicts)")
    for i in G.nodes:
        color_and_neighbour = [(neighbour, G.nodes[neighbour]['color']) for neighbour in G[i]]
        for neighbour, color in color_and_neighbour:
            if color == G.nodes[i]['color']:
                print(f"ERROR: Hard Constraint Violation! Node {i} and {neighbour} have same teacher.")

    # ----------------------------
    # Starting QAOA
    # ----------------------------
    print("----------------------------")
    print("Running QAOA")

    num_colors = 2
    print("\nNumber of colors (Teachers):", num_colors)

    num_nodes = G.number_of_nodes()
    number_of_qubits = num_nodes * num_colors + num_nodes
    print("Necessary number of qubits: ", number_of_qubits)

    goal_p = 8

    # Run Solver
    minimization_process_cobyla(goal_p, G, num_colors, school, cost_function_tiny)

    print("Program End")
    print("----------------------------")


if __name__ == '__main__':
    main()
