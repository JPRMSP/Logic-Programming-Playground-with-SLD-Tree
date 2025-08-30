import streamlit as st
import re
from collections import defaultdict
import graphviz

st.set_page_config(page_title="Logic Programming Playground", layout="wide")

st.title("🧠 Logic Programming Playground with SLD-Tree")
st.write("Interactive First-Order Logic, Resolution & SLD Derivation Tree (FI1946 - Anna University)")

# ------------------------------
# Logic Engine (Mini Prolog)
# ------------------------------

def parse_clause(clause):
    clause = clause.strip().rstrip(".")
    if ":-" in clause:
        head, body = clause.split(":-")
        head = head.strip()
        body = [b.strip() for b in body.split(",")]
        return ("rule", head, body)
    else:
        return ("fact", clause, [])

def parse_query(query):
    query = query.strip().lstrip("?-").rstrip(".").strip()
    return query

def is_variable(term):
    return term[0].isupper()

def tokenize(predicate):
    name, args = predicate.split("(", 1)
    args = args[:-1].split(",")
    return name.strip(), [a.strip() for a in args]

def unify(x, y, subst=None):
    if subst is None:
        subst = {}
    if x == y:
        return subst
    if is_variable(x):
        return unify_var(x, y, subst)
    if is_variable(y):
        return unify_var(y, x, subst)
    if "(" in x and "(" in y:
        name1, args1 = tokenize(x)
        name2, args2 = tokenize(y)
        if name1 != name2 or len(args1) != len(args2):
            return None
        for a1, a2 in zip(args1, args2):
            subst = unify(a1, a2, subst)
            if subst is None:
                return None
        return subst
    return None

def unify_var(var, x, subst):
    if var in subst:
        return unify(subst[var], x, subst)
    elif x in subst:
        return unify(var, subst[x], subst)
    else:
        subst[var] = x
        return subst

def substitute(term, subst):
    if "(" in term:
        name, args = tokenize(term)
        new_args = [substitute(a, subst) for a in args]
        return f"{name}({', '.join(new_args)})"
    else:
        return subst.get(term, term)

def resolve(query, kb):
    results = []
    for typ, head, body in kb:
        subst = unify(query, head, {})
        if subst is not None:
            if not body:  # fact
                results.append((subst, []))
            else:  # rule
                subgoals = [substitute(b, subst) for b in body]
                results.append((subst, subgoals))
    return results

def prove(goals, kb, subst=None, depth=0, tree=None, parent=None, node_id=[0]):
    if subst is None:
        subst = {}
    if tree is None:
        tree = graphviz.Digraph()
        tree.attr("node", shape="box", style="rounded,filled", color="lightblue2")

    node_id[0] += 1
    current_id = str(node_id[0])
    label = f"Goals: {goals}\\nSubst: {subst}"
    tree.node(current_id, label)

    if parent is not None:
        tree.edge(parent, current_id)

    if not goals:
        tree.node(current_id, label + "\\n✅ Success", color="lightgreen")
        return [subst], tree

    first, rest = goals[0], goals[1:]
    solutions = []
    for s, subgoals in resolve(first, kb):
        new_goals = subgoals + rest
        new_subst = subst.copy()
        new_subst.update(s)
        sols, tree = prove(new_goals, kb, new_subst, depth+1, tree, current_id, node_id)
        solutions.extend(sols)
    return solutions, tree

# ------------------------------
# Streamlit UI
# ------------------------------
st.subheader("1️⃣ Enter Knowledge Base (Facts & Rules)")
kb_text = st.text_area("Knowledge Base", 
"""parent(john, mary).
parent(mary, alice).
parent(alice, bob).
grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
""", height=200)

st.subheader("2️⃣ Enter Query")
query_text = st.text_input("Query", "?- grandparent(john, alice).")

if st.button("Run Logic Resolution"):
    kb = [parse_clause(line) for line in kb_text.splitlines() if line.strip()]
    query = parse_query(query_text)

    sols, tree = prove([query], kb)

    if sols:
        st.success(f"✅ Query proved! Solutions: {sols}")
    else:
        st.error("❌ Query failed (no solutions found).")

    st.subheader("3️⃣ SLD Derivation Tree")
    st.graphviz_chart(tree)
