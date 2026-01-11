from qaoa import *
import pandas as pd
import pickle
import networkx as nx
from qaoa.util import color_graph_greedy
import collections


# --------------------------
# LOAD RULE DATAFRAMES
# --------------------------
def load_rules():
    base_path = 'dataset/'
    skills = pd.read_csv(base_path + 'QAOA_Data_Fall_2025 - InstructorSkill_easy.csv', index_col=0)
    slots = pd.read_csv(base_path + 'QAOA_Data_Fall_2025 - InstructorSlot_easy.csv', index_col=0)
    quotas = pd.read_csv(base_path + 'QAOA_Data_Fall_2025 - InstructorQuota_easy.csv', index_col=0)
    return skills, slots, quotas


DF_SKILLS, DF_SLOTS, DF_QUOTAS = load_rules()

# --------------------------
# LOAD GRAPH METADATA
# --------------------------
with open('dataset/toy_graph_dense.pickle', 'rb') as f:
    G_METADATA = pickle.load(f)

# --------------------------
# TEACHER MAPPING
# --------------------------
REAL_TEACHERS = list(DF_SKILLS.index)
NUM_REAL = len(REAL_TEACHERS)


# Quick check number of required colors
greedy_strategy = nx.coloring.greedy_color(G_METADATA, strategy='largest_first')
required_colors = max(greedy_strategy.values()) + 1

TEACHER_MAP = {i: name for i, name in enumerate(REAL_TEACHERS)}

print(f"Loaded {NUM_REAL} Teachers: {TEACHER_MAP}")

if required_colors > NUM_REAL:
    diff = required_colors - NUM_REAL
    print(f"\n[!] DENSITY WARNING: Graph requires {diff} more teachers.")
    print("Creating dummy teachers:")

    for i in range(diff):
        dummy_id = NUM_REAL + i
        dummy_name = f"DUMMY_TEACHER_{i + 1}"
        TEACHER_MAP[dummy_id] = dummy_name
        print(f"  + Added {dummy_name} (ID: {dummy_id})")

NUM_TOTAL_COLORS = len(TEACHER_MAP)
print(f"Total Model Colors: {NUM_TOTAL_COLORS} (IDs: 0 to {NUM_TOTAL_COLORS - 1})")


def cost_function_dense(G_Candidate):
    """
    Constraints adaptation.
        * Dummy teachers: Set high penalty, force the circuit assign available real teachers as the first priority.
    """
    C = 0

    # Track usage for quotas
    teacher_counts = collections.defaultdict(int)

    for node in G_Candidate.nodes:
        color = G_Candidate.nodes[node]['color']

        # Safety Check
        if color not in TEACHER_MAP:
            C += 2000
            continue

        teacher_name = TEACHER_MAP[color]
        teacher_counts[teacher_name] += 1

        if "DUMMY" in teacher_name:
            C += 1000
            # if dummy, no need to check skills and quotas
            continue

        subject = G_METADATA.nodes[node]['subject']
        slot = G_METADATA.nodes[node]['slot']

        # 1. Skill Check
        try:
            skill_val = DF_SKILLS.loc[teacher_name, subject]
            if skill_val < 5:
                C += 100
        except KeyError:
            C += 100

        # 2. Slot Availability Check
        try:
            col_name = slot if slot in DF_SLOTS.columns else str(slot)
            avail_val = DF_SLOTS.loc[teacher_name, col_name]
            if avail_val < 5:
                C += 10
        except KeyError:
            C += 10

    # 5. Check Quotas
    for teacher_name in REAL_TEACHERS:
        count = teacher_counts[teacher_name]
        try:
            min_q = DF_QUOTAS.loc[teacher_name, 'Min quota']
            max_q = DF_QUOTAS.loc[teacher_name, 'Max quota']

            if count < min_q:
                C += 5 * (min_q - count)
            elif count > max_q:
                C += 5 * (count - max_q)
        except KeyError:
            pass

    return C


def main():
    print("\nStarting program for sparse version of Toy dataset\n")
    school = "Toy_Dense"
    G = G_METADATA

    print("--------------------------")
    print("Graph information\n")
    print("Nodes = ", G.nodes(data=True))
    print(f"Total Nodes: {G.number_of_nodes()}")
    print(f"Total Edges: {G.number_of_edges()}")

    # --------------------------
    # Initial Coloring (Stage 1)
    # --------------------------
    print("Running Greedy Coloring to find valid starting state...")
    try:
        color_graph_greedy(G)

        current_coloring = [G.nodes[node]['color'] for node in G.nodes]
        used_colors = set(current_coloring)
        num_used = len(used_colors)

        print(f"Greedy Algorithm found a valid coloring using {num_used} colors: {current_coloring}")
    except Exception as e:
        print(f"Initialization Failed: {e}")
        return

    initial_score = cost_function_dense(G)
    print(f"Initial Cost (Soft Violations): {initial_score}")

    # ----------------------------
    # Running QAOA (Stage 2)
    # ----------------------------
    print("\n----------------------------")
    print(f"Running QAOA")

    num_nodes = G.number_of_nodes()
    num_qubits = num_nodes * NUM_TOTAL_COLORS + num_nodes
    print(f"Estimated Qubits: {num_qubits}")

    goal_p = 1

    # Run the Solver
    # minimization_process_cobyla(goal_p, G, NUM_TOTAL_COLORS, school, cost_function_dense)

    print("Program End")
    print("----------------------------")


if __name__ == '__main__':
    main()
