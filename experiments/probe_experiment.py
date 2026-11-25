"""Compare separate-chaining probe counts with their expected values."""

import csv
import random
import string
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from src.hash_table import HashTable

CAPACITY = 4093
ALPHA_STEPS = 16
FAILED_SEARCHES_PER_LOAD = 10_000
RANDOM_SEED = 20251125
ALPHANUMERIC = string.ascii_letters + string.digits


def random_url(generator: random.Random, index: int, missing: bool = False) -> str:
    token = "".join(generator.choices(ALPHANUMERIC, k=32))
    if missing:
        return f"https://missing-{token}.invalid/{index}"
    return f"https://{token}.example/{index}"


def count_node_comparisons(table: HashTable, key: str, should_exist: bool) -> int:
    node = table._buckets[table._bucket_index(key)]
    comparisons = 0
    while node is not None:
        comparisons += 1
        if node.key == key:
            if not should_exist:
                raise AssertionError("failed-search key unexpectedly exists")
            return comparisons
        node = node.next

    if should_exist:
        raise AssertionError("successful-search key was not found")
    return comparisons


def measure_load(
    generator: random.Random, target_alpha: float
) -> tuple[float, float, int, float, float, float, float]:
    entry_count = round(CAPACITY * target_alpha)
    table = HashTable(capacity=CAPACITY, max_load=None)
    urls = [random_url(generator, index) for index in range(entry_count)]

    for url in urls:
        table.put(url, url)

    actual_alpha = len(table) / table.capacity
    successful_comparisons = sum(
        count_node_comparisons(table, url, should_exist=True) for url in urls
    )
    successful_average = successful_comparisons / len(urls)

    failed_comparisons = sum(
        count_node_comparisons(
            table,
            random_url(generator, index, missing=True),
            should_exist=False,
        )
        for index in range(FAILED_SEARCHES_PER_LOAD)
    )
    failed_average = failed_comparisons / FAILED_SEARCHES_PER_LOAD

    return (
        target_alpha,
        actual_alpha,
        entry_count,
        successful_average,
        1 + actual_alpha / 2,
        failed_average,
        actual_alpha,
    )


def save_csv(
    rows: list[tuple[float, float, int, float, float, float, float]],
    output_path: Path,
) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(
            (
                "target_alpha",
                "actual_alpha",
                "entries",
                "successful_measured",
                "successful_theoretical",
                "failed_measured",
                "failed_theoretical",
            )
        )
        writer.writerows(
            (
                f"{target:.2f}",
                f"{actual:.6f}",
                entries,
                f"{success:.6f}",
                f"{success_theory:.6f}",
                f"{failed:.6f}",
                f"{failed_theory:.6f}",
            )
            for (
                target,
                actual,
                entries,
                success,
                success_theory,
                failed,
                failed_theory,
            ) in rows
        )


def create_svg(
    rows: list[tuple[float, float, int, float, float, float, float]],
) -> str:
    width = 1000
    height = 700
    left = 95
    right = 950
    plot_height = 175
    panels = (
        ("Successful searches", 45, 3.5, 3, 4),
        ("Failed searches", 375, 4.5, 5, 6),
    )
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="500" y="28" text-anchor="middle" font-family="sans-serif" '
        'font-size="20" font-weight="bold">Hash table node comparisons</text>',
        '<line x1="620" y1="53" x2="660" y2="53" stroke="#1769aa" stroke-width="3"/>',
        '<text x="668" y="58" font-family="sans-serif" font-size="13">Measured</text>',
        '<line x1="770" y1="53" x2="810" y2="53" stroke="#d1495b" stroke-width="3" '
        'stroke-dasharray="7 5"/>',
        '<text x="818" y="58" font-family="sans-serif" font-size="13">Theory</text>',
    ]

    for title, top, y_max, measured_index, theory_index in panels:
        plot_top = top + 28
        plot_bottom = plot_top + plot_height
        elements.append(
            f'<text x="{left}" y="{top + 17}" font-family="sans-serif" '
            f'font-size="16" font-weight="bold">{title}</text>'
        )
        for tick in range(int(y_max) + 1):
            y = plot_bottom - tick / y_max * plot_height
            elements.extend(
                (
                    f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" '
                    'stroke="#dddddd"/>',
                    f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" '
                    'font-family="sans-serif" font-size="12">'
                    f"{tick}</text>",
                )
            )
        for tick in range(5):
            x = left + tick / 4 * (right - left)
            elements.extend(
                (
                    f'<line x1="{x:.2f}" y1="{plot_top}" x2="{x:.2f}" '
                    f'y2="{plot_bottom}" stroke="#eeeeee"/>',
                    f'<text x="{x:.2f}" y="{plot_bottom + 20}" text-anchor="middle" '
                    f'font-family="sans-serif" font-size="12">{tick}</text>',
                )
            )

        for series_index, color, dash in (
            (measured_index, "#1769aa", ""),
            (theory_index, "#d1495b", ' stroke-dasharray="7 5"'),
        ):
            points = []
            for row in rows:
                alpha = row[1]
                value = row[series_index]
                x = left + alpha / 4 * (right - left)
                y = plot_bottom - value / y_max * plot_height
                points.append(f"{x:.2f},{y:.2f}")
            elements.append(
                f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
                f'stroke-width="2.5"{dash}/>'
            )
            if not dash:
                for point in points:
                    x, y = point.split(",")
                    elements.append(
                        f'<circle cx="{x}" cy="{y}" r="3" fill="{color}"/>'
                    )

        elements.extend(
            (
                f'<line x1="{left}" y1="{plot_bottom}" x2="{right}" '
                f'y2="{plot_bottom}" stroke="#333333"/>',
                f'<text x="{(left + right) / 2:.2f}" y="{plot_bottom + 42}" '
                'text-anchor="middle" font-family="sans-serif" font-size="13">'
                "Load factor (alpha)</text>",
                f'<text x="22" y="{plot_top + plot_height / 2:.2f}" '
                'transform="rotate(-90 22 '
                f'{plot_top + plot_height / 2:.2f})" text-anchor="middle" '
                'font-family="sans-serif" font-size="13">Average node comparisons</text>',
            )
        )

    elements.append("</svg>")
    return "\n".join(elements) + "\n"


def print_comparison_table(
    rows: list[tuple[float, float, int, float, float, float, float]],
) -> None:
    print(
        "| Target alpha | Actual alpha | Successful measured / theory "
        "| Failed measured / theory |"
    )
    print("|---:|---:|---:|---:|")
    for target, actual, _, success, success_theory, failed, failed_theory in rows:
        print(
            f"| {target:.2f} | {actual:.4f} | {success:.3f} / "
            f"{success_theory:.3f} | {failed:.3f} / {failed_theory:.3f} |"
        )


def main() -> None:
    generator = random.Random(RANDOM_SEED)
    rows = [
        measure_load(generator, step / 4)
        for step in range(1, ALPHA_STEPS + 1)
    ]

    experiment_directory = Path(__file__).resolve().parent
    save_csv(rows, experiment_directory / "results.csv")
    (experiment_directory / "results.svg").write_text(
        create_svg(rows), encoding="utf-8"
    )
    print_comparison_table(rows)
    print(f"\nSaved {experiment_directory / 'results.csv'}")
    print(f"Saved {experiment_directory / 'results.svg'}")


if __name__ == "__main__":
    main()
