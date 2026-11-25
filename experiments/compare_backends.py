"""Compare separate chaining and linear probing under identical workloads."""

import csv
import random
import string
import sys
from pathlib import Path
from typing import NamedTuple

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable

CAPACITY = 4093
RANDOM_SEED = 20251125
QUERIES_PER_SEARCH = 10_000
ALPHANUMERIC = string.ascii_letters + string.digits


class ComparisonRow(NamedTuple):
    target_alpha: float
    actual_alpha: float
    entries: int
    chain_success_measured: float
    chain_success_theory: float
    chain_failed_measured: float
    chain_failed_theory: float
    linear_success_measured: float
    linear_success_theory: float
    linear_failed_measured: float
    linear_failed_theory: float


def random_url(generator: random.Random, index: int, missing: bool = False) -> str:
    token = "".join(generator.choices(ALPHANUMERIC, k=32))
    if missing:
        return f"https://missing-{token}.invalid/{index}"
    return f"https://{token}.example/{index}"


def average_probes(
    table: HashTable | LinearProbingHashTable,
    keys: list[str],
    should_exist: bool,
) -> float:
    total_probes = 0
    for key in keys:
        value, probes = table.find(key)
        if (value is not None) != should_exist:
            raise RuntimeError(f"search result did not match expected presence: {key}")
        total_probes += probes
    return total_probes / len(keys)


def measure(
    generator: random.Random, target_alpha: float
) -> ComparisonRow:
    entry_count = round(CAPACITY * target_alpha)
    urls = [random_url(generator, index) for index in range(entry_count)]
    successful_queries = generator.choices(urls, k=QUERIES_PER_SEARCH)
    failed_queries = [
        random_url(generator, index, missing=True)
        for index in range(QUERIES_PER_SEARCH)
    ]

    chaining = HashTable(capacity=CAPACITY, max_load=None)
    linear = LinearProbingHashTable(capacity=CAPACITY, max_load=None)
    for url in urls:
        chaining.put(url, url)
        linear.put(url, url)

    actual_alpha = len(chaining) / chaining.capacity
    chain_success = average_probes(chaining, successful_queries, should_exist=True)
    chain_failed = average_probes(chaining, failed_queries, should_exist=False)
    linear_success = average_probes(linear, successful_queries, should_exist=True)
    linear_failed = average_probes(linear, failed_queries, should_exist=False)

    return ComparisonRow(
        target_alpha=target_alpha,
        actual_alpha=actual_alpha,
        entries=entry_count,
        chain_success_measured=chain_success,
        chain_success_theory=1 + actual_alpha / 2,
        chain_failed_measured=chain_failed,
        chain_failed_theory=actual_alpha,
        linear_success_measured=linear_success,
        linear_success_theory=(1 + 1 / (1 - actual_alpha)) / 2,
        linear_failed_measured=linear_failed,
        linear_failed_theory=(1 + 1 / (1 - actual_alpha) ** 2) / 2,
    )


def save_csv(rows: list[ComparisonRow], output_path: Path) -> None:
    fieldnames = (
        "target_alpha",
        "actual_alpha",
        "entries",
        "successful_queries",
        "failed_queries",
        "chaining_success_measured",
        "chaining_success_theory",
        "chaining_failed_measured",
        "chaining_failed_theory",
        "linear_success_measured",
        "linear_success_theory",
        "linear_failed_measured",
        "linear_failed_theory",
    )
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(fieldnames)
        for row in rows:
            writer.writerow(
                (
                    f"{row.target_alpha:.1f}",
                    f"{row.actual_alpha:.6f}",
                    row.entries,
                    QUERIES_PER_SEARCH,
                    QUERIES_PER_SEARCH,
                    f"{row.chain_success_measured:.6f}",
                    f"{row.chain_success_theory:.6f}",
                    f"{row.chain_failed_measured:.6f}",
                    f"{row.chain_failed_theory:.6f}",
                    f"{row.linear_success_measured:.6f}",
                    f"{row.linear_success_theory:.6f}",
                    f"{row.linear_failed_measured:.6f}",
                    f"{row.linear_failed_theory:.6f}",
                )
            )


def _svg_panel(
    rows: list[ComparisonRow],
    title: str,
    top: int,
    y_max: float,
    y_tick: float,
    measured_attribute: str,
    theory_attribute: str,
) -> list[str]:
    left = 100
    right = 1040
    plot_top = top + 28
    plot_height = 205
    plot_bottom = plot_top + plot_height
    elements = [
        f'<text x="{left}" y="{top + 17}" font-family="sans-serif" '
        f'font-size="16" font-weight="bold">{title}</text>'
    ]

    tick = 0.0
    while tick <= y_max:
        y = plot_bottom - tick / y_max * plot_height
        elements.extend(
            (
                f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" '
                'stroke="#dddddd"/>',
                f'<text x="{left - 12}" y="{y + 4:.2f}" text-anchor="end" '
                f'font-family="sans-serif" font-size="12">{tick:g}</text>',
            )
        )
        tick += y_tick

    for tick in range(6):
        alpha = tick / 5
        x = left + alpha * (right - left)
        elements.extend(
            (
                f'<line x1="{x:.2f}" y1="{plot_top}" x2="{x:.2f}" '
                f'y2="{plot_bottom}" stroke="#eeeeee"/>',
                f'<text x="{x:.2f}" y="{plot_bottom + 20}" text-anchor="middle" '
                'font-family="sans-serif" font-size="12">'
                f"{alpha:.1f}</text>",
            )
        )

    for prefix, color in (("chain", "#1769aa"), ("linear", "#198754")):
        for attribute, dash in (
            (measured_attribute.format(prefix=prefix), ""),
            (theory_attribute.format(prefix=prefix), ' stroke-dasharray="7 5"'),
        ):
            points = []
            for row in rows:
                alpha = row.actual_alpha
                value = getattr(row, attribute)
                x = left + alpha * (right - left)
                y = plot_bottom - value / y_max * plot_height
                points.append(f"{x:.2f},{y:.2f}")
            elements.append(
                f'<polyline points="{" ".join(points)}" fill="none" '
                f'stroke="{color}" stroke-width="2.5"{dash}/>'
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
            f'transform="rotate(-90 22 {plot_top + plot_height / 2:.2f})" '
            'text-anchor="middle" font-family="sans-serif" font-size="13">'
            "Average probes</text>",
        )
    )
    return elements


def create_svg(rows: list[ComparisonRow]) -> str:
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" '
        'viewBox="0 0 1100 760">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="550" y="28" text-anchor="middle" font-family="sans-serif" '
        'font-size="20" font-weight="bold">'
        "Separate chaining vs. linear probing</text>",
    ]
    legend = (
        ("#1769aa", "", "Chaining measured"),
        ("#1769aa", ' stroke-dasharray="7 5"', "Chaining theory"),
        ("#198754", "", "Linear measured"),
        ("#198754", ' stroke-dasharray="7 5"', "Linear theory"),
    )
    for index, (color, dash, label) in enumerate(legend):
        x = 130 + index * 235
        elements.extend(
            (
                f'<line x1="{x}" y1="53" x2="{x + 35}" y2="53" '
                f'stroke="{color}" stroke-width="3"{dash}/>',
                f'<text x="{x + 42}" y="58" font-family="sans-serif" '
                f'font-size="12">{label}</text>',
            )
        )

    elements.extend(
        _svg_panel(
            rows,
            "Successful searches",
            70,
            6,
            1,
            "{prefix}_success_measured",
            "{prefix}_success_theory",
        )
    )
    elements.extend(
        _svg_panel(
            rows,
            "Failed searches",
            410,
            55,
            10,
            "{prefix}_failed_measured",
            "{prefix}_failed_theory",
        )
    )
    elements.append("</svg>")
    return "\n".join(elements) + "\n"


def print_results(rows: list[ComparisonRow]) -> None:
    print(
        "| alpha | chaining success M/T | chaining failed M/T "
        "| linear success M/T | linear failed M/T |"
    )
    print("|---:|---:|---:|---:|---:|")
    for row in rows:
        print(
            f"| {row.target_alpha:.1f} | "
            f"{row.chain_success_measured:.3f}/{row.chain_success_theory:.3f} | "
            f"{row.chain_failed_measured:.3f}/{row.chain_failed_theory:.3f} | "
            f"{row.linear_success_measured:.3f}/{row.linear_success_theory:.3f} | "
            f"{row.linear_failed_measured:.3f}/{row.linear_failed_theory:.3f} |"
        )


def main() -> None:
    generator = random.Random(RANDOM_SEED)
    rows = [measure(generator, step / 10) for step in range(1, 10)]
    experiments_directory = Path(__file__).resolve().parent
    save_csv(rows, experiments_directory / "comparison.csv")
    (experiments_directory / "comparison.svg").write_text(
        create_svg(rows), encoding="utf-8"
    )
    print(f"Seed: {RANDOM_SEED}")
    print(
        f"Queries per search type/backend/load factor: {QUERIES_PER_SEARCH}"
    )
    print_results(rows)
    print(f"\nSaved {experiments_directory / 'comparison.csv'}")
    print(f"Saved {experiments_directory / 'comparison.svg'}")


if __name__ == "__main__":
    main()
