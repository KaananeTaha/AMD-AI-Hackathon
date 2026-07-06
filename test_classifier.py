"""Stress test for the heuristic classifier.

Each case is (prompt, expected_category). Includes plain cases, varied phrasings,
and deliberate traps (e.g. summarization prompts containing "what is", factual
prompts containing the word "function"). Run:  python test_classifier.py
"""

from __future__ import annotations

from collections import defaultdict

from classifier import Category, classify

C = Category

CASES: list[tuple[str, Category]] = [
    # ---- FACTUAL -----------------------------------------------------------
    ("What is photosynthesis?", C.FACTUAL),
    ("Explain how a transformer neural network works.", C.FACTUAL),
    ("Define entropy in thermodynamics.", C.FACTUAL),
    ("Who was the first president of the United States?", C.FACTUAL),
    ("Why is the sky blue?", C.FACTUAL),
    ("Describe the water cycle.", C.FACTUAL),
    ("How does a vaccine train the immune system?", C.FACTUAL),
    ("What does the term 'inflation' mean in economics?", C.FACTUAL),
    ("Tell me about the causes of World War I.", C.FACTUAL),
    ("What is the function of the mitochondria in a cell?", C.FACTUAL),  # trap: "function"
    ("Give an overview of how blockchain achieves consensus.", C.FACTUAL),

    # ---- MATH --------------------------------------------------------------
    ("A shirt costs $40 and is discounted by 25%. What is the final price?", C.MATH),
    ("Calculate the sum of the first 100 positive integers.", C.MATH),
    ("If a train travels 60 miles in 1.5 hours, what is its average speed?", C.MATH),
    ("What is 17 * 23?", C.MATH),
    ("A population grows 3% per year. Project its size after 5 years from 10000.", C.MATH),
    ("How many minutes are there in 3.5 days?", C.MATH),
    ("Round 3.14159 to two decimal places.", C.MATH),
    ("What percent of 250 is 45?", C.MATH),
    ("Compute the total cost of 12 items at $7.50 each.", C.MATH),
    ("Solve for x: 2x + 5 = 17.", C.MATH),

    # ---- SENTIMENT ---------------------------------------------------------
    ("Classify the sentiment of this review: 'The food was cold and the service was terrible.'", C.SENTIMENT),
    ("Is the following tweet positive or negative? 'Best day of my life!'", C.SENTIMENT),
    ("Label the sentiment and justify: 'I guess it was okay, nothing special.'", C.SENTIMENT),
    ("Determine the emotional tone of this comment.", C.SENTIMENT),
    ("What is the sentiment of: 'This product exceeded all my expectations.'", C.SENTIMENT),  # trap: "what is"
    ("Classify the tone of this message as positive, negative, or neutral.", C.SENTIMENT),

    # ---- SUMMARIZATION -----------------------------------------------------
    ("Summarise the following text in one sentence: ...", C.SUMMARIZATION),
    ("Give me a TL;DR of this article.", C.SUMMARIZATION),
    ("Condense this paragraph into 20 words.", C.SUMMARIZATION),
    ("Provide a summary of the key points below.", C.SUMMARIZATION),
    ("Shorten this passage to three sentences.", C.SUMMARIZATION),
    ("What is the main idea of the following text? Summarise it briefly.", C.SUMMARIZATION),  # trap: "what is"
    ("In two sentences, describe what this report is about.", C.SUMMARIZATION),

    # ---- NER ---------------------------------------------------------------
    ("Extract all named entities from: Tim Cook visited Paris in June 2021.", C.NER),
    ("Identify the person, organization, and location in this sentence.", C.NER),
    ("List all the people and organizations mentioned in the passage.", C.NER),
    ("Extract the dates and locations from the following text.", C.NER),
    ("Find all named entities and label them person/org/location/date.", C.NER),

    # ---- CODE_DEBUG --------------------------------------------------------
    ("Fix this code:\n```python\ndef add(a, b):\n    return a - b\n```", C.CODE_DEBUG),
    ("Why doesn't this function return the right value?", C.CODE_DEBUG),
    ("There is a bug in the following snippet. Find and fix it.", C.CODE_DEBUG),
    ("This code throws an exception. What's wrong with it?", C.CODE_DEBUG),
    ("Debug my program:\nfor i in range(10) print(i)", C.CODE_DEBUG),
    ("Provide a corrected implementation of the sort function below.", C.CODE_DEBUG),
    ("Here is a traceback and the code that caused it. Fix the error.", C.CODE_DEBUG),

    # ---- LOGIC -------------------------------------------------------------
    ("Three friends sit in a row. Alice is not next to Bob. Carol is on the left end. Who sits in the middle?", C.LOGIC),
    ("Solve this logic puzzle using the clues below.", C.LOGIC),
    ("Five houses in a row, each a different color. Deduce who owns the fish.", C.LOGIC),
    ("Given the following constraints, determine the correct ordering.", C.LOGIC),
    ("Exactly one of the three statements is true. Who is lying?", C.LOGIC),

    # ---- CODE_GEN ----------------------------------------------------------
    ("Write a function that returns the nth Fibonacci number.", C.CODE_GEN),
    ("Implement a binary search over a sorted list.", C.CODE_GEN),
    ("Create a program that reverses a string.", C.CODE_GEN),
    ("Write a Python function that checks if a number is prime.", C.CODE_GEN),
    ("Generate code to parse a CSV file into a list of dicts.", C.CODE_GEN),
    ("Write a function that takes two integers and returns their GCD.", C.CODE_GEN),
]

# Second batch: harder / more adversarial phrasings NOT used to tune the
# patterns. This is the honest generalisation check.
HARD_CASES: list[tuple[str, Category]] = [
    # Factual phrased without a wh-word
    ("Tell me the difference between TCP and UDP.", C.FACTUAL),
    ("Explain, in plain terms, what causes tides.", C.FACTUAL),
    ("Briefly, how do black holes form?", C.FACTUAL),

    # Math without obvious trigger words
    ("A recipe needs 2 cups of flour for 12 cookies. How many cups for 30 cookies?", C.MATH),
    ("If I invest $1000 at 5% annual interest, how much after 3 years?", C.MATH),
    ("The angles of a triangle are in ratio 2:3:4. Find the largest angle.", C.MATH),

    # Sentiment without the word 'sentiment'
    ("Would you say this customer message is happy or upset? 'Still waiting, three weeks now.'", C.SENTIMENT),
    ("Rate the overall mood of this feedback: 'Loved the design, hated the price.'", C.SENTIMENT),

    # Summarization phrased indirectly
    ("Boil the following report down to its three main takeaways.", C.SUMMARIZATION),
    ("Give me the gist of this email in a single line.", C.SUMMARIZATION),

    # NER phrased indirectly
    ("Who and what places are mentioned in this news snippet?", C.NER),
    ("Pull out every company name from the paragraph below.", C.NER),

    # Code debug without the word 'bug' or 'fix'
    ("This loop runs forever. Can you tell me why?\nwhile x > 0:\n    y += 1", C.CODE_DEBUG),
    ("The function below returns None instead of the sum. What did I do wrong?", C.CODE_DEBUG),

    # Logic phrased as a story
    ("Anna, Ben and Cara each have a different pet: cat, dog, fish. Anna hates cats. Ben's pet lives in water. What pet does Cara have?", C.LOGIC),
    ("If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies?", C.LOGIC),

    # Code gen phrased indirectly
    ("Give me a function to convert Celsius to Fahrenheit.", C.CODE_GEN),
    ("I need a script that renames all .txt files in a folder.", C.CODE_GEN),
    ("Produce a method that flattens a nested list.", C.CODE_GEN),
]


def evaluate(name: str, cases: list[tuple[str, Category]]) -> int:
    per_cat_total: dict[Category, int] = defaultdict(int)
    per_cat_correct: dict[Category, int] = defaultdict(int)
    failures: list[tuple[str, Category, Category]] = []

    for prompt, expected in cases:
        got = classify(prompt)
        per_cat_total[expected] += 1
        if got == expected:
            per_cat_correct[expected] += 1
        else:
            failures.append((prompt, expected, got))

    total = len(cases)
    correct = total - len(failures)

    print("=" * 70)
    print(f"{name}: {correct}/{total} correct  ({100 * correct / total:.1f}%)")
    print("=" * 70)
    print("Per-category accuracy:")
    for cat in Category:
        t = per_cat_total[cat]
        if not t:
            continue
        c = per_cat_correct[cat]
        flag = "" if c == t else "  <-- misses"
        print(f"  {cat.value:15s} {c}/{t}{flag}")

    if failures:
        print(f"\n{len(failures)} misclassification(s):")
        for prompt, expected, got in failures:
            snippet = prompt.replace("\n", " ")[:66]
            print(f"  expected {expected.value:13s} got {got.value:13s} | {snippet}")
    else:
        print("\nNo misclassifications.")
    print()
    return len(failures)


def main() -> int:
    tuned = evaluate("TUNED SET", CASES)
    held_out = evaluate("HELD-OUT SET (not tuned)", HARD_CASES)
    print(f"Total misclassifications: {tuned + held_out}")
    return 0 if (tuned + held_out) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
