import sqlite3
from pathlib import Path


def validate_data():
    database_path = Path(__file__).resolve().parent / "data" / "instamart.db"
    with sqlite3.connect(database_path) as conn:
        (
            order_count,
            completed_count,
            cancelled_count,
            pending_count,
            missing_amount,
            completed_sum,
            completed_missing_delivery,
        ) = conn.execute(
            """
            SELECT
                COUNT(*),
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END),
                SUM(CASE WHEN order_amount IS NULL THEN 1 ELSE 0 END),
                ROUND(SUM(CASE WHEN status = 'completed' THEN order_amount ELSE 0 END), 2),
                SUM(
                    CASE
                        WHEN status = 'completed' AND delivery_minutes IS NULL THEN 1
                        ELSE 0
                    END
                )
            FROM orders
            """
        ).fetchone()
        missing_ages = conn.execute(
            "SELECT COUNT(*) FROM customers WHERE age IS NULL"
        ).fetchone()[0]

    assert order_count == 12309, f"Order rows mismatch: {order_count}"
    assert completed_count == 11110, f"Completed orders mismatch: {completed_count}"
    assert cancelled_count == 1199, f"Cancelled orders mismatch: {cancelled_count}"
    assert pending_count == 0, f"Pending orders mismatch: {pending_count}"
    assert missing_amount == 0, f"Missing order amount mismatch: {missing_amount}"
    assert abs(completed_sum - 2998668.80) < 1e-2, (
        f"Total amount mismatch: {completed_sum}"
    )
    assert completed_missing_delivery == 0, (
        f"Completed missing delivery mismatch: {completed_missing_delivery}"
    )
    assert missing_ages == 0, f"Missing ages mismatch: {missing_ages}"

    print("ALL CHECKPOINTS PASSED")


if __name__ == "__main__":
    validate_data()
