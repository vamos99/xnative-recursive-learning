import random


def epsilon_greedy(options: list[str], scores: dict[str, float], epsilon: float = 0.1) -> str:
    if not options:
        return ""
    if random.random() < epsilon:
        return random.choice(options)
    return max(options, key=lambda o: scores.get(o, 0.0))
