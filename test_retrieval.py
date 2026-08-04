from retrieval.index import build_index, retrieve

documents = [
    "Python is a programming language.",
    "Machine Learning uses data.",
    "Transformers are deep learning models.",
    "Football is a sport.",
]

build_index(documents)

results = retrieve("Explain Machine Learning")

print(results)
