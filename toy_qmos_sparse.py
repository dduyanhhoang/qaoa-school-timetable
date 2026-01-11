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
    # Updated to point to the Toy (Easy) datasets provided in your tree
    skills = pd.read_csv(base_path + 'QAOA_Data_Fall_2025 - InstructorSkill_easy.csv', index_col=0)
    slots = pd.read_csv(base_path + 'QAOA_Data_Fall_2025 - InstructorSlot_easy.csv', index_col=0)
    quotas = pd.read_csv(base_path + 'QAOA_Data_Fall_2025 - InstructorQuota_easy.csv', index_col=0)
    return skills, slots, quotas


DF_SKILLS, DF_SLOTS, DF_QUOTAS = load_rules()

# --------------------------
# LOAD GRAPH METADATA
# --------------------------
# Load the Toy graph you generated with graph_toy.py
with open('dataset/toy_graph_sparse.pickle', 'rb') as f:
    G_METADATA = pickle.load(f)

# --------------------------
# TEACHER MAPPING
# --------------------------
TEACHERS = list(DF_SKILLS.index)
TEACHER_MAP = {i: name for i, name in enumerate(TEACHERS)}
NUM_TEACHERS = len(TEACHERS)

print(f"Loaded {NUM_TEACHERS} Teachers: {TEACHER_MAP}")


def cost_function_toy(G_Candidate):
    """
    Constraints adaptation.
    """
    C = 0

    # Track teacher usage for quotas
    teacher_counts = {t: 0 for t in TEACHERS}

    for node in G_Candidate.nodes:
        # 1. Get Assignment (Color)
        color = G_Candidate.nodes[node]['color']

        # 2. Get Metadata (Subject/Slot) from the Global Graph
        subject = G_METADATA.nodes[node]['subject']
        slot = G_METADATA.nodes[node]['slot']

        teacher = TEACHER_MAP[color]

        # Increment quota count
        teacher_counts[teacher] += 1

        # 3. Check Skill (Must be 5)
        try:
            skill_val = DF_SKILLS.loc[teacher, subject]
            if skill_val < 5:
                C += 100  # Penalty for unskilled teacher
        except KeyError:
            C += 100

        # 4. Check Slot Availability (Must be 5)
        try:
            if slot not in DF_SLOTS.columns:
                avail_val = DF_SLOTS.loc[teacher, str(slot)]
            else:
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
    print("\nStarting program for sparse version of Toy dataset\n")
    school = "Toy_Sparse"
    G = G_METADATA

    print("--------------------------")
    print("Graph information\n")
    print("Nodes = ", G.nodes(data=True))
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")

    # --------------------------
    #  Initial Coloring (Stage 1)
    # --------------------------
    print("Running Greedy Coloring to find valid starting state...")
    try:
        color_graph_greedy(G)

        current_coloring = [G.nodes[node]['color'] for node in G.nodes]
        used_colors = set(current_coloring)
        num_used = len(used_colors)

        print(f"Greedy Algorithm found a valid coloring using {num_used} colors: {current_coloring}")
    except Exception as e:
        print(f"Greedy coloring failed: {e}")
        return

    initial_function_value = cost_function_toy(G)
    print(f"\nInitial Function Value (Soft Violations): {initial_function_value}")

    # ----------------------------
    # Running QAOA (Stage 2)
    # ----------------------------
    print("----------------------------")
    print("Running QAOA")

    print(f"\nNumber of colors (Teachers): {NUM_TEACHERS}")

    num_nodes = G.number_of_nodes()
    num_qubits = num_nodes * NUM_TEACHERS + num_nodes
    print("Estimated qubits required: ", num_qubits)

    goal_p = 1

    # Run Solver
    # minimization_process_cobyla(goal_p, G, NUM_TEACHERS, school, cost_function_toy)

    print("Program End")
    print("----------------------------")


if __name__ == '__main__':
    main()
