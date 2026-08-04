import json

from compare import similarity


def get_current_response(prompt):
    """
    Replace this function with your project's
    actual LLM call.
    """

    responses = {
        "What is AI?": "Artificial Intelligence is the simulation of human intelligence in machines.",
        "What is Machine Learning?": "Machine Learning is a subset of AI that enables computers to learn from data.",
        "Explain Python.": "Python is a high-level programming language.",
    }

    return responses.get(prompt, "")


# Load baseline prompts and expected outputs
with open("baseline.json") as f:
    tests = json.load(f)

threshold = 0.90

# Compare current responses with baseline
for test in tests:

    current = get_current_response(test["prompt"])

    score = similarity(test["expected"], current)

    status = "PASS"

    if score < threshold:
        status = "FAIL"

    print("=" * 40)
    print("Prompt:", test["prompt"])
    print("Similarity:", round(score, 2))
    print("Status:", status)
