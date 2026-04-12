"""Create a labeled 10-segment insert image for Logikus lamps."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TypedDict

import pygame

TARGET_SIZE = (1050, 150)
TEXT_COUNT = 10
RGB = tuple[int, int, int]


class InsertRow(TypedDict):
    in_file: str
    out_file: str
    texts: list[str]
    size: int
    color: RGB


# ---------------------------------- Parse color strings --------------------

def parse_color(color_text: str) -> RGB:
    """Parse an RGB color from a string like "0-0-0" or "(0, 0, 0)"."""
    cleaned = color_text.strip().replace("(", "").replace(")", "")
    parts = [part.strip() for part in cleaned.split("-")]
    if len(parts) != 3:
        raise ValueError(f"Invalid color value: {color_text}")

    values = tuple(int(part) for part in parts)
    if any(value < 0 or value > 255 for value in values):
        raise ValueError(f"Color values must be in range 0..255: {color_text}")
    return values


def load_insert_csv(csv_path: str | Path = "insert.csv") -> list[InsertRow]:
    """Read insert.csv (comma separated) and map rows to insert dictionaries."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    rows: list[InsertRow] = []
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=",")
        for line_number, row in enumerate(reader, start=1):
            if line_number == 1 or not row or row[0][0] == '#' or all(cell.strip() == "" for cell in row):
                continue

            if len(row) != 14:
                raise ValueError(
                    f"Line {line_number}: expected 14 columns, got {len(row)}"
                )
            texts = [text.replace("|", "\n") for text in row[2:12]]

            print(texts)
            rows.append(
                {
                    "in_file": row[0].strip(),
                    "out_file": row[1].strip(),
                    "texts": texts,
                    "size": int(row[12].strip()),
                    "color": parse_color(row[13]),
                }
            )

    return rows


# ------------------------------------------ Clean-up directory --------------------

def cleanup(directory: str | Path) -> int:
    """Delete all files with a leading underscore in the given directory."""
    target_dir = Path(directory)
    if not target_dir.is_dir():
        raise NotADirectoryError(f"Directory not found: {target_dir}")

    deleted_count = 0
    for file_path in target_dir.iterdir():
        if file_path.is_file() and file_path.name.startswith("_"):
            file_path.unlink()
            deleted_count += 1

    return deleted_count


# ------------------------------------ Create the insert --------------------------------

def create_insert(
        input_png: str | Path,
        output_png: str | Path,
        text: str,
        font_size: int = 72,
        text_color: tuple[int, int, int] = (0, 0, 0),
        font_name: str | None = None,
) -> Path:
    texts = text.split(';')
    if len(texts) != TEXT_COUNT:
        raise ValueError(f"Expected exactly {TEXT_COUNT} texts, got {len(texts)}")

    input_path = Path(input_png)
    output_path = Path(output_png)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    pygame.init()
    pygame.font.init()
    try:
        surface = pygame.image.load(str(input_path))
        if surface.get_size() != TARGET_SIZE:
            raise ValueError(
                f"Input image must be {TARGET_SIZE[0]}x{TARGET_SIZE[1]} px, got {surface.get_width()}x{surface.get_height()} px"
            )

        font = pygame.font.SysFont(font_name, font_size)
        segment_width = TARGET_SIZE[0] // TEXT_COUNT

        for index, segment_text in enumerate(texts):
            lines = segment_text.split("\n")
            line_height = font.get_linesize()
            block_height = line_height * len(lines)
            start_y = (TARGET_SIZE[1] - block_height) // 2

            for row, line in enumerate(lines):
                rendered = font.render(line, True, text_color)
                x = index * segment_width + (segment_width - rendered.get_width()) // 2
                y = start_y + row * line_height + (line_height - rendered.get_height()) // 2
                surface.blit(rendered, (x, y))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surface, str(output_path))
    finally:
        pygame.font.quit()
        pygame.quit()

    return output_path


# ------------------------------------- main ------------------------------

INSERT_DIR = "inserts"


def main() -> None:
    inserts = load_insert_csv("inserts.csv")
    for insert in inserts:
        create_insert(input_png=f"{INSERT_DIR}/{insert[f'in_file']}",
                      output_png=f"{INSERT_DIR}/{insert[f'out_file']}",
                      text=';'.join(insert["texts"]),
                      font_size=insert["size"],
                      text_color=insert["color"],
                      )
    cleanup(INSERT_DIR)


# -----------------------------------------------------------------

if __name__ == "__main__":
    main()
