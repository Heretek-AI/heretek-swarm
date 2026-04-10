# Fix MD5 -> SHA256 in strategies.py and hybrid_retriever.py

# Fix strategies.py
with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\rag\strategies.py', 'r') as f:
    content = f.read()
content = content.replace('hashlib.md5(query.lower().strip().encode()).hexdigest()', 'hashlib.sha256(query.lower().strip().encode()).hexdigest()')
with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\rag\strategies.py', 'w') as f:
    f.write(content)
print("strategies.py fixed!")

# Fix hybrid_retriever.py
with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\rag\hybrid_retriever.py', 'r') as f:
    content = f.read()
content = content.replace('hashlib.md5(query.lower().strip().encode()).hexdigest()', 'hashlib.sha256(query.lower().strip().encode()).hexdigest()')
with open(r'C:\Users\derek\Desktop\Heretek-AI\heretek-swarm\src\heretek_swarm\rag\hybrid_retriever.py', 'w') as f:
    f.write(content)
print("hybrid_retriever.py fixed!")
