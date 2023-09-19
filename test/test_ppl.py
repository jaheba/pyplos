from pyplos import ppl


def test_sort():
    xs = [2, 1, 3, 1]
    ys = [4, 6, 2, 1]

    table = [{"x": x, "y": y} for x, y in zip(xs, ys)]

    assert ppl("sort x", table) == sorted(table, key=lambda row: row["x"])
    assert ppl("sort + x", table) == sorted(table, key=lambda row: row["x"])
    assert ppl("sort - x", table) == sorted(
        table, key=lambda row: row["x"], reverse=True
    )

    assert ppl("sort x, y", table) == sorted(
        table, key=lambda row: (row["x"], row["y"])
    )
