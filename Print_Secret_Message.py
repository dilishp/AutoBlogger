from bs4 import BeautifulSoup
import requests
import re


def print_secret_message(url):
    # 1. Download the published Google Doc.
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 2. Extract the coordinate table.
    entries = []
    found_table = False

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        # Read the column headings.
        headers = [
            cell.get_text(" ", strip=True).lower()
            for cell in rows[0].find_all(["th", "td"])
        ]

        # Identify the columns by their header names.
        x_col = next(
            (i for i, h in enumerate(headers)
             if "x" in h and ("coordinate" in h or h == "x")),
            None
        )
        y_col = next(
            (i for i, h in enumerate(headers)
             if "y" in h and ("coordinate" in h or h == "y")),
            None
        )
        char_col = next(
            (i for i, h in enumerate(headers)
             if any(word in h for word in
                    ("character", "unicode", "symbol", "char"))),
            None
        )

        # Skip tables that do not contain the required headers.
        if None in (x_col, y_col, char_col):
            continue

        found_table = True

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if max(x_col, y_col, char_col) >= len(cells):
                continue

            x_text = cells[x_col].get_text(strip=True)
            y_text = cells[y_col].get_text(strip=True)
            char = cells[char_col].get_text(strip=True)

            # Ignore malformed rows.
            if not re.fullmatch(r"\d+", x_text):
                continue
            if not re.fullmatch(r"\d+", y_text):
                continue
            if not char:
                continue

            entries.append((int(x_text), int(y_text), char))

        if entries:
            break

    if not found_table or not entries:
        raise ValueError(
            "Could not find a valid coordinate table in the document."
        )

    # 3. Determine the grid dimensions.
    max_x = max(x for x, y, char in entries)
    max_y = max(y for x, y, char in entries)

    # 4. Fill unspecified positions with spaces.
    grid = [
        [" "] * (max_x + 1)
        for _ in range(max_y + 1)
    ]

    for x, y, char in entries:
        grid[y][x] = char

    # 5. Print from top to bottom.
    # The origin (0, 0) is the bottom-left corner.
    for y in range(max_y, -1, -1):
        print("".join(grid[y]))


url = "https://docs.google.com/document/d/e/2PACX-1vSvM5gDlNvt7npYHhp_XfsJvuntUhq184By5xO_pA4b_gCWeXb6dM6ZxwN8rE6S4ghUsCj2VKR21oEP/pub"
print_secret_message(url)