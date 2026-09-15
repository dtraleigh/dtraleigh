"""Comparing scraped values without tripping over how they were typed.

City staff re-type the status strings we scrape, so the same fact reaches us
spelled differently from one scrape to the next - "City Council Public Hearing
10/6/26" one week, "City Council Public Hearing 10/06/26" the next. Comparing on
a canonical form keeps a re-typing from looking like news.
"""
import re

# Numeric dates as the city writes them inside status text: 10/6/26, 10/06/2026,
# 10-6-26. The leading \b\d{1,2} plus separator means a four-digit year cannot
# start a match, so ISO-ish substrings ("2025/10/06") and the blob storage paths
# in plan_url ("COR22/Z-050-25.pdf") are left alone.
DATE_RE = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b")


def _canonical_date(match):
    month, day, year = match.groups()
    year = int(year)

    if year < 100:
        year += 2000

    return f"{int(month):02d}/{int(day):02d}/{year:04d}"


def normalize_for_comparison(value):
    """Reduce a value to the form we compare on.

    Zero-pads embedded dates, collapses whitespace (including the &nbsp; the
    city's tables are full of), and folds case. None and "" both come back as "".
    """
    if value is None:
        return ""

    text = str(value).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()

    return DATE_RE.sub(_canonical_date, text).casefold()


def values_are_equivalent(old, new):
    """Return True if the two values mean the same thing."""
    return normalize_for_comparison(old) == normalize_for_comparison(new)


def is_cosmetic_change(old, new):
    """True when the two values differ literally but mean the same thing."""
    return old != new and values_are_equivalent(old, new)
