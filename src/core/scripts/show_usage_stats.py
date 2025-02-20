import asyncio
from pathlib import Path
from tabulate import tabulate

from core.repositories.stats_repository import StatsRepository


async def main():
    # Assuming the database is in the project root
    db_path = Path(__file__).parent.parent.parent.parent / "db" / "stats.db"
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    repo = StatsRepository(db_path)
    stats = await repo.get_user_stats()

    if not stats:
        print("No usage statistics found")
        return

    # Prepare table headers and rows
    headers = [
        "User ID", "Requests", "Tokens In", "Tokens Out",
        "Cost In ($)", "Cost Out ($)", "Messages", "Models Used"
    ]

    # Format the data
    rows = [
        [
            user_id,
            requests,
            f"{tokens_in:,}",
            f"{tokens_out:,}",
            f"{dollars_in:.2f}",
            f"{dollars_out:.2f}",
            messages,
            models.replace(',', ', ')
        ]
        for (user_id, requests, tokens_in, tokens_out,
             dollars_in, dollars_out, messages, models) in stats
    ]

    # Add totals row
    totals = ["TOTAL"]
    for i in range(1, 7):  # Skip user_id and models columns
        total = sum(row[i] if isinstance(row[i], (int, float))
                    else float(row[i].replace(',', ''))
                    for row in stats)
        if i in [1]:  # Requests
            totals.append(f"{total:,}")
        elif i in [2, 3]:  # Tokens
            totals.append(f"{int(total):,}")
        elif i in [4, 5]:  # Dollars
            totals.append(f"{total:.2f}")
        else:  # Messages
            totals.append(f"{int(total):,}")
    totals.append("ALL")
    rows.append(totals)

    # Print the table
    print("\nLLM Usage Statistics per User")
    print("============================")
    print(tabulate(rows, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    asyncio.run(main())