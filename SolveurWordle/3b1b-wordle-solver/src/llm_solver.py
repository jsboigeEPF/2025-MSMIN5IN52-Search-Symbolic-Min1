import ollama
import re
from src.prior import get_word_list

class LLMSolver:
    def __init__(self, host=None, game_name="wordle", model_name="llama3"):
        """
        Initializes the LLMSolver using the ollama library.

        :param host: The host for the Ollama client, e.g., 'http://localhost:11434'.
        :param game_name: The name of the game, used to fetch the word lists.
        :param model_name: The name of the Ollama model to use.
        """
        self.client = ollama.Client(host=host)
        self.allowed_words = get_word_list(game_name)
        self.model_name = model_name

    def get_best_guess(self, history, max_retries=5):
        """
        Gets the best guess from the LLM based on the history of guesses.
        It parses the LLM response to find a valid 5-letter word.

        :param history: A list of tuples, where each tuple is (guess, pattern).
                        e.g., [('RAISE', 'bbyyg')]
        :param max_retries: The maximum number of times to ask the LLM for a valid word.
        :return: A valid 5-letter word as a string.
        """
        prompt = self._construct_prompt(history)

        for attempt in range(max_retries):
            try:
                response = self.client.chat(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': prompt}],
                )
                response_text = response['message']['content']
                
                # Find all 5-letter words in the response
                potential_words = re.findall(r'\b[a-zA-Z]{5}\b', response_text.lower())
                
                for word in potential_words:
                    if self._is_valid_guess(word):
                        return word # Return the first valid word found

                print(f"LLM proposed: '{response_text}'. No valid 5-letter word found. Retrying...")

            except ollama.ResponseError as e:
                print(f"Error calling Ollama API: {e.error}")
                if e.status_code == 404:
                    print(f"Model '{self.model_name}' not found. Make sure you have it running.")
                break
        
        print("LLM failed to provide a valid guess. Falling back to a simple strategy.")
        return self._fallback_guess(history)


    def _construct_prompt(self, history):
        """
        Constructs a prompt for the LLM based on the game history.
        'g' = green, 'y' = yellow, 'b' = black/gray.
        """
        prompt = (
            "You are a Wordle assistant. Your goal is to guess the secret 5-letter word.\n"
            "Based on the history of guesses and their results (patterns), suggest the best next 5-letter word.\n"
            "The pattern indicates the result for each letter:\n"
            "- 'g': The letter is in the correct position (green).\n"
            "- 'y': The letter is in the word but in the wrong position (yellow).\n"
            "- 'b': The letter is not in the word (black/gray).\n\n"
            "Here is the history of guesses so far:\n"
        )

        if not history:
            prompt += "No guesses have been made yet. Suggest a good starting word.\n"
        else:
            for guess, pattern in history:
                prompt += f"- Guess: '{guess}', Pattern: '{pattern}'\n"

        prompt += "\nYour response MUST be a single, valid 5-letter English word, and nothing else."
        return prompt

    def _is_valid_guess(self, word):
        """
        Checks if a word is a valid 5-letter word present in the allowed words list.
        """
        return len(word) == 5 and word in self.allowed_words

    def _fallback_guess(self, history):
        """
        A very simple fallback strategy if the LLM fails.
        """
        if not history:
            return "raise"
        # A real implementation would be more complex
        return self.allowed_words[0]

if __name__ == '__main__':
    # Example of how to use the LLMSolver
    # Make sure you have 'ollama' running with a model like 'llama3'
    # ollama run llama3
    solver = LLMSolver()
    
    history = [
        ('arise', 'ybbyb'),
        ('dough', 'bgybb'),
    ]
    
    next_guess = solver.get_best_guess(history)
    
    print(f"History: {history}")
    print(f"LLM's next guess: {next_guess}")
