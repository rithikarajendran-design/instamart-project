import sqlite3
from pathlib import Path


def split_sql_statements(sql_script):
    statements = []
    current_statement = []

    for line in sql_script.splitlines(keepends=True):
        current_statement.append(line)
        if sqlite3.complete_statement("".join(current_statement)):
            statement = "".join(current_statement).strip()
            if statement:
                statements.append(statement)
            current_statement = []

    remainder = "".join(current_statement).strip()
    if remainder:
        statements.append(remainder)

    return statements


def print_query_results(cursor, limit=5):
    if cursor.description is None:
        print("Query completed; no result set.")
        return

    column_names = [column[0] for column in cursor.description]
    print(" | ".join(column_names))
    for row in cursor.fetchmany(limit):
        print(" | ".join("" if value is None else str(value) for value in row))


def main():
    project_dir = Path(__file__).resolve().parent
    database_path = project_dir / "data" / "instamart.db"
    sql_path = project_dir / "sql" / "queries.sql"

    if not database_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {database_path}")
    if not sql_path.is_file():
        raise FileNotFoundError(f"SQL query file not found: {sql_path}")

    sql_script = sql_path.read_text(encoding="utf-8")
    queries = split_sql_statements(sql_script)
    if not queries:
        raise ValueError(f"No SQL queries found in {sql_path}")

    failures = 0
    with sqlite3.connect(database_path) as conn:
        for index, query in enumerate(queries, 1):
            print(f"\n--- Running Query Q{index} ---")
            try:
                cursor = conn.execute(query)
                print_query_results(cursor)
            except sqlite3.Error as error:
                failures += 1
                print(f"Error in Query Q{index}: {error}")

    if failures:
        raise SystemExit(f"{failures} SQL quer{'y' if failures == 1 else 'ies'} failed.")


if __name__ == "__main__":
    main()
