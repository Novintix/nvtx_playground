# test_multihop.py

from MedLink_AI.multihop_rag import MultiHopRAG

query = "How do lifestyle factors influence insulin resistance through inflammatory pathways?"

rag = MultiHopRAG()

answer, papers = rag.run(query)

print("\n🧠 MULTI-HOP ANSWER:\n")
print(answer)

print("\n📚 Evidence papers:\n")
for i, p in enumerate(papers[:5], start=1):
    print(f"{i}. {p['title']}")
