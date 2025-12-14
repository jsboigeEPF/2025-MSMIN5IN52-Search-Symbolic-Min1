import argparse
import random
import numpy as np
from tqdm import tqdm

from src.pattern import get_pattern
from src.prior import get_word_list
from src.llm_solver import LLMSolver

def simulate_llm_games(model_name="llama3"):
    """
    Runs simulated Wordle games using an LLM to make guesses.
    """
    game_name = "wordle"
    first_guess = "raise"
    test_set = get_word_list(game_name, short=True)
    
    # Initialize the LLM solver
    llm_solver = LLMSolver(model_name=model_name, game_name=game_name)

    scores = np.zeros(0, dtype=int)
    game_results = []
    total_guesses = 0

    print(f"--- Running Wordle simulations with model: {model_name} ---")

    for answer in tqdm(test_set, leave=False, desc=f"Simulating games with {model_name}"):
        history = []
        
        score = 1
        guess = first_guess

        while guess != answer:
            pattern = get_pattern(guess, answer, game_name)
            history.append((guess, pattern))

            score += 1
            # Use the LLM to get the next guess
            guess = llm_solver.get_best_guess(history)

        # Accumulate stats
        scores = np.append(scores, [score])
        guesses_made = [h[0] for h in history]
        game_results.append({
            "score": int(score),
            "answer": answer,
            "guesses": guesses_made,
        })

    average_score = scores.mean()
    score_dist = [int((scores == i).sum()) for i in range(1, scores.max(initial=0) + 1)]
    total_guesses = scores.sum()

    final_result = {
        "score_distribution": score_dist,
        "total_guesses": int(total_guesses),
        "average_score": float(average_score),
        "game_results": game_results,
    }

    print(f"\n--- LLM Simulation Complete ---")
    print(f"Model: {model_name}")
    print(f"Average Score: {average_score:.2f}")
    print(f"Score Distribution: {score_dist}")
    print("---------------------------------")

    return final_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Wordle simulations using a local LLM.")
    parser.add_argument(
        "--model",
        type=str,
        default="llama3",
        help="The name of the Ollama model to use (e.g., 'llama3', 'codellama').",
    )
    args = parser.parse_args()

    simulate_llm_games(model_name=args.model)