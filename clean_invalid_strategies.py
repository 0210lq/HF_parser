"""
Clean invalid strategy records from database
Invalid strategies are those with percentage-like names (e.g., "0.01%", "-3.06%")
"""
from src.database.connection import get_session
from src.database.models import Strategy, Fund
import re

def clean_invalid_strategies():
    """Remove invalid strategy records and update fund references"""
    sess = next(get_session())

    print("=" * 80)
    print("Cleaning Invalid Strategy Records")
    print("=" * 80)

    # Step 1: Identify invalid strategies
    strategies = sess.query(Strategy).all()
    percentage_pattern = re.compile(r'^-?\d+\.\d+%')

    invalid_strategies = []
    valid_strategies = []

    for s in strategies:
        # Check if contains Chinese characters (real strategies)
        if any('\u4e00' <= char <= '\u9fff' for char in s.strategy_name):
            valid_strategies.append(s)
        elif percentage_pattern.match(s.strategy_name):
            invalid_strategies.append(s)
        elif (len(s.strategy_name) < 5 or
              s.strategy_name.replace('.', '').replace('%', '').replace('-', '').replace(' ', '').isdigit()):
            invalid_strategies.append(s)
        else:
            # Other suspicious patterns
            if s.strategy_name.count('%') >= 2:  # e.g., "00% 2.69%"
                invalid_strategies.append(s)
            else:
                valid_strategies.append(s)

    print(f"\n1. Analysis:")
    print(f"   Total strategies: {len(strategies)}")
    print(f"   Valid strategies: {len(valid_strategies)}")
    print(f"   Invalid strategies: {len(invalid_strategies)}")

    if not invalid_strategies:
        print("\n✓ No invalid strategies found!")
        return

    invalid_ids = [s.strategy_id for s in invalid_strategies]

    # Step 2: Check fund references
    funds_with_invalid = sess.query(Fund).filter(Fund.strategy_id.in_(invalid_ids)).all()
    print(f"\n2. Funds affected: {len(funds_with_invalid)}")

    # Step 3: Set fund strategy_id to NULL for affected funds
    if funds_with_invalid:
        print(f"\n3. Updating {len(funds_with_invalid)} fund records...")
        for fund in funds_with_invalid:
            fund.strategy_id = None
        sess.commit()
        print("   ✓ Fund references cleared")

    # Step 4: Delete invalid strategies
    print(f"\n4. Deleting {len(invalid_strategies)} invalid strategy records...")
    for strategy in invalid_strategies:
        sess.delete(strategy)
    sess.commit()
    print("   ✓ Invalid strategies deleted")

    # Step 5: Verify
    remaining_strategies = sess.query(Strategy).count()
    print(f"\n5. Verification:")
    print(f"   Remaining strategies: {remaining_strategies}")
    print(f"   Expected: {len(valid_strategies)}")

    if remaining_strategies == len(valid_strategies):
        print("   ✓ Cleanup successful!")
    else:
        print("   ✗ Mismatch detected!")

    # Show sample of remaining strategies
    print(f"\n6. Sample of valid strategies:")
    sample_strategies = sess.query(Strategy).order_by(Strategy.strategy_name).limit(20).all()
    for s in sample_strategies:
        print(f"   - {s.strategy_name} (ID: {s.strategy_id})")

    print("\n" + "=" * 80)
    print("Cleanup Complete!")
    print("=" * 80)


if __name__ == "__main__":
    clean_invalid_strategies()
