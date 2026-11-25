"""In-memory prerequisite graph for the Phase 2 Python curriculum.

Keeping this graph separate from ORM models makes it easy to replace with a
database-backed curriculum graph later without changing recommendation logic.
"""

PREREQUISITES = {
    "Conditional Statements": ["Variables and Data Types", "Operators"],
    "Loops": ["Conditional Statements"],
    "for Loop": ["Loops"],
    "while Loop": ["Loops"],
    "Function Definition": ["Variables and Data Types", "Conditional Statements"],
    "Parameters and Arguments": ["Function Definition"],
    "Return Values": ["Parameters and Arguments"],
    "Variable Scope": ["Function Definition"],
    "Lists": ["Variables and Data Types"],
    "Dictionaries": ["Lists", "Variables and Data Types"],
    "Exception Handling": ["Conditional Statements", "Functions"],
    "File Handling": ["Exception Handling"],
    "Recursion": ["Function Definition", "Parameters and Arguments", "Return Values"],
}


def prerequisites_for(topic_name: str, recursive: bool = True) -> list[str]:
    """Return direct or transitively required prerequisites in learning order."""
    result: list[str] = []
    visited: set[str] = set()

    def visit(name: str) -> None:
        for prerequisite in PREREQUISITES.get(name, []):
            if prerequisite in visited:
                continue
            visited.add(prerequisite)
            if recursive:
                visit(prerequisite)
            result.append(prerequisite)

    visit(topic_name)
    return result