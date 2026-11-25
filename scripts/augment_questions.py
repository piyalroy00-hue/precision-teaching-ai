"""Augment the base question dataset with reproducible, answer-safe variations.

Implements 7 augmentation techniques (each individually safe, i.e. never able to
desynchronize `correct_answer` from the options):

1. paraphrase_stem        - reword the question's opening phrase
2. rename_code_variables   - consistently rename a variable identifier in code blocks
3. restyle_code_block      - cosmetic code formatting change (adds a step comment)
4. shuffle_options         - reorders the option columns (correct_answer text is unaffected)
5. vary_difficulty         - shifts the difficulty tag by one band with a marks adjustment
6. vary_context            - wraps the question stem with a neutral framing sentence
7. template_variation      - generates brand-new parameterized questions whose
                             correct answer is computed programmatically, guaranteeing
                             correctness by construction

Every produced row (base + augmented) is re-validated with
scripts.validate_questions.validate_question_row before being written out, per the
"never change the correct answer accidentally" requirement.
"""
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from app.config.settings import AUGMENTED_DATA_DIR, GENERATED_DATA_DIR, RANDOM_SEED, SUBJECT_NAME
from app.database.seed import TOPIC_TREE
from scripts.validate_questions import OPTION_COLUMNS, validate_question_row

PARAPHRASE_MAP = {
    "What is the result of": ["What does the following expression evaluate to:", "Which value results from"],
    "What is printed by": ["What output is produced by", "What will the following code display when run"],
    "What is the data type of": ["Which data type best describes", "What type results from"],
    "Which of the following": ["Select the option that", "Choose the statement that"],
    "What does": ["What is the outcome of", "Which result comes from"],
    "Which keyword": ["Which reserved word", "What keyword"],
    "Which mode": ["Which file mode", "What mode"],
    "What is the main benefit of": ["What key advantage does", "Why is it preferable to use"],
    "What best describes": ["Which statement best defines", "How would you best describe"],
}

CONTEXT_PREFIXES = [
    "Consider the following Python question. ",
    "As part of a diagnostic quiz on Python programming: ",
    "In the context of core Python concepts: ",
]

CODE_VAR_POOL = ["p", "q", "r", "s", "u", "v", "w"]
CODE_VAR_CANDIDATES = ["x", "y", "z", "n", "i", "j", "k", "m", "a", "b", "c"]

DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]


def _has_code_block(text: str) -> bool:
    return "```" in text or "print(" in text or "def " in text


def paraphrase_stem(text: str, rng: random.Random) -> str | None:
    for stem, alternatives in PARAPHRASE_MAP.items():
        if text.startswith(stem):
            return rng.choice(alternatives) + text[len(stem):]
    return None


def vary_context(text: str, rng: random.Random) -> str:
    return rng.choice(CONTEXT_PREFIXES) + text


def restyle_code_block(text: str) -> str | None:
    if "```" not in text:
        return None
    # Cosmetic-only change: insert a step marker comment right after the fence, no
    # executable code is altered so behaviour/output is unaffected.
    return text.replace("```\n", "```\n# step through carefully\n", 1)


def rename_code_variables(text: str, explanation: str, rng: random.Random) -> tuple[str, str] | None:
    if not _has_code_block(text):
        return None
    present = [v for v in CODE_VAR_CANDIDATES if re.search(rf"\b{v}\b", text)]
    if not present:
        return None
    old = rng.choice(present)
    unused_pool = [p for p in CODE_VAR_POOL if not re.search(rf"\b{p}\b", text)]
    if not unused_pool:
        return None
    new = rng.choice(unused_pool)
    pattern = re.compile(rf"\b{old}\b")
    return pattern.sub(new, text), pattern.sub(new, explanation)


def shuffle_options(row: dict, rng: random.Random) -> dict:
    options = [row.get(col, "") for col in OPTION_COLUMNS]
    non_empty = [o for o in options if str(o).strip() != ""]
    empty_count = len(options) - len(non_empty)
    rng.shuffle(non_empty)
    new_options = non_empty + [""] * empty_count
    new_row = dict(row)
    for col, value in zip(OPTION_COLUMNS, new_options):
        new_row[col] = value
    return new_row


def vary_difficulty(row: dict, rng: random.Random) -> dict:
    new_row = dict(row)
    idx = DIFFICULTY_ORDER.index(row["difficulty"])
    direction = rng.choice([-1, 1])
    new_idx = min(max(idx + direction, 0), len(DIFFICULTY_ORDER) - 1)
    new_row["difficulty"] = DIFFICULTY_ORDER[new_idx]
    new_row["marks"] = max(1, row["marks"] + (new_idx - idx))
    return new_row


def _leaf_topic_subtopic_map() -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}
    for node in TOPIC_TREE:
        children = node.get("children")
        if children:
            for child in children:
                mapping[child["name"]] = (node["name"], child["name"])
        else:
            mapping[node["name"]] = (node["name"], "")
    return mapping


def augment_row(row: dict, rng: random.Random) -> dict | None:
    """Apply a random subset of safe augmentation techniques to one base question."""
    new_row = dict(row)
    techniques: list[str] = []

    paraphrased = paraphrase_stem(new_row["question_text"], rng)
    if paraphrased and rng.random() < 0.7:
        new_row["question_text"] = paraphrased
        techniques.append("paraphrase_stem")

    renamed = rename_code_variables(new_row["question_text"], new_row["explanation"], rng)
    if renamed and rng.random() < 0.5:
        new_row["question_text"], new_row["explanation"] = renamed
        techniques.append("rename_code_variables")

    if "rename_code_variables" not in techniques:
        restyled = restyle_code_block(new_row["question_text"])
        if restyled and rng.random() < 0.4:
            new_row["question_text"] = restyled
            techniques.append("restyle_code_block")

    if rng.random() < 0.6:
        new_row = shuffle_options(new_row, rng)
        techniques.append("shuffle_options")

    if rng.random() < 0.3:
        new_row = vary_difficulty(new_row, rng)
        techniques.append("vary_difficulty")

    if rng.random() < 0.5:
        new_row["question_text"] = vary_context(new_row["question_text"], rng)
        techniques.append("vary_context")

    if not techniques:
        return None  # nothing changed, skip to avoid an exact duplicate

    new_row["source"] = "augmented"
    new_row["parent_question_id"] = row["question_id"]
    new_row["augmentation_techniques"] = ",".join(techniques)
    return new_row


# --- Technique 7: question-template variation (new, programmatically-verified questions) ---

def _mcq_from_correct(correct_value: str, distractors: list[str], rng: random.Random) -> tuple[dict, str]:
    options = [correct_value] + distractors[:3]
    rng.shuffle(options)
    return {col: val for col, val in zip(OPTION_COLUMNS, options)}, correct_value


def template_arithmetic(rng: random.Random) -> dict:
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    op = rng.choice(["+", "-", "*", "%", "//"])
    expr = f"{a} {op} {b}"
    correct = eval(expr)  # noqa: S307 - internally constructed, trusted arithmetic only
    distractors = {str(correct + 1), str(correct - 1), str(correct * 2 if correct != 0 else correct + 3)}
    distractors.discard(str(correct))
    options, correct_str = _mcq_from_correct(str(correct), list(distractors), rng)
    return {
        "leaf_topic": "Operators",
        "difficulty": rng.choice(["Easy", "Medium"]),
        "question_type": "MCQ",
        "question_text": f"What is the result of `{expr}`?",
        **options,
        "correct_answer": correct_str,
        "explanation": f"`{expr}` evaluates to {correct}.",
        "marks": 1,
    }


def template_range_sum(rng: random.Random) -> dict:
    start, stop, step = rng.randint(0, 3), rng.randint(6, 12), rng.choice([1, 2, 3])
    values = list(range(start, stop, step))
    correct = sum(values)
    distractors = {str(correct + step), str(max(correct - step, 0)), str(correct + len(values))}
    distractors.discard(str(correct))
    options, correct_str = _mcq_from_correct(str(correct), list(distractors), rng)
    return {
        "leaf_topic": "for Loop",
        "difficulty": "Medium",
        "question_type": "MCQ",
        "question_text": f"What is the sum of all values produced by `range({start}, {stop}, {step})`?",
        **options,
        "correct_answer": correct_str,
        "explanation": f"`range({start}, {stop}, {step})` yields {values}, which sum to {correct}.",
        "marks": 2,
    }


def template_list_index(rng: random.Random) -> dict:
    values = [rng.randint(1, 50) for _ in range(5)]
    idx = rng.randint(0, 4)
    correct = values[idx]
    distractors = {str(v) for v in values if v != correct}
    options, correct_str = _mcq_from_correct(str(correct), list(distractors), rng)
    return {
        "leaf_topic": "Lists",
        "difficulty": "Easy",
        "question_type": "MCQ",
        "question_text": f"What is printed by `print({values}[{idx}])`?",
        **options,
        "correct_answer": correct_str,
        "explanation": f"Index {idx} of the list {values} is {correct}.",
        "marks": 1,
    }


def template_dict_get(rng: random.Random) -> dict:
    keys = ["a", "b", "c"]
    values = [rng.randint(1, 20) for _ in keys]
    d = dict(zip(keys, values))
    default = rng.randint(90, 99)
    missing = rng.choice([True, False])
    key = "z" if missing else rng.choice(keys)
    correct = default if missing else d[key]
    distractors = {str(default), *[str(v) for v in values]}
    distractors.discard(str(correct))
    options, correct_str = _mcq_from_correct(str(correct), list(distractors), rng)
    return {
        "leaf_topic": "Dictionaries",
        "difficulty": "Medium",
        "question_type": "MCQ",
        "question_text": f'What is printed by:\n```\nd = {d}\nprint(d.get("{key}", {default}))\n```',
        **options,
        "correct_answer": correct_str,
        "explanation": (
            f'"{key}" is {"absent" if missing else "present"} in the dictionary, '
            f"so `.get()` returns {'the default ' + str(default) if missing else 'its value ' + str(correct)}."
        ),
        "marks": 2,
    }


TEMPLATE_GENERATORS = [template_arithmetic, template_range_sum, template_list_index, template_dict_get]


def generate_template_questions(rng: random.Random, count: int, start_id: int) -> list[dict]:
    topic_subtopic = _leaf_topic_subtopic_map()
    rows = []
    next_id = start_id
    for i in range(count):
        generator = TEMPLATE_GENERATORS[i % len(TEMPLATE_GENERATORS)]
        q = generator(rng)
        topic, subtopic = topic_subtopic[q.pop("leaf_topic")]
        row = {
            "question_id": next_id,
            "subject": SUBJECT_NAME,
            "topic": topic,
            "subtopic": subtopic,
            **q,
            "source": "augmented",
            "parent_question_id": None,
            "augmentation_techniques": "template_variation",
        }
        for col in OPTION_COLUMNS:
            row.setdefault(col, "")
        rows.append(row)
        next_id += 1
    return rows


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    input_path = GENERATED_DATA_DIR / "questions_generated.csv"
    base_df = pd.read_csv(input_path, keep_default_na=False)
    base_df["parent_question_id"] = None
    base_df["augmentation_techniques"] = ""

    augmented_rows = []
    next_id = int(base_df["question_id"].max()) + 1
    for _, row in base_df.iterrows():
        row_rng = random.Random(RANDOM_SEED + int(row["question_id"]))
        augmented = augment_row(row.to_dict(), row_rng)
        if augmented is not None:
            augmented["question_id"] = next_id
            augmented_rows.append(augmented)
            next_id += 1

    augmented_rows.extend(generate_template_questions(rng, count=20, start_id=next_id))

    all_rows = base_df.to_dict("records") + augmented_rows

    # Safety net: validate every row before writing; drop anything invalid and report it.
    kept, dropped = [], []
    for row in all_rows:
        errors = validate_question_row(row)
        if errors:
            dropped.append((row.get("question_id"), errors))
        else:
            kept.append(row)

    result_df = pd.DataFrame(kept)
    AUGMENTED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = AUGMENTED_DATA_DIR / "questions_augmented.csv"
    json_path = AUGMENTED_DATA_DIR / "questions_augmented.json"
    result_df.to_csv(csv_path, index=False)
    result_df.to_json(json_path, orient="records", indent=2)

    print(f"Base questions:      {len(base_df)}")
    print(f"Augmented variants:  {len(augmented_rows)}")
    print(f"Total valid written: {len(result_df)} -> {csv_path}")
    if dropped:
        print(f"Dropped {len(dropped)} invalid rows during augmentation:")
        for qid, errors in dropped:
            print(f"  question_id={qid}: {errors}")


if __name__ == "__main__":
    main()
