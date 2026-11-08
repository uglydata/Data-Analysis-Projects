"""
Real (inflation-adjusted) wages by industry in Latvia, 2015-2025.

Question: which industries' pay actually grew faster than prices, and by how much?

Data (Central Statistical Bureau of Latvia, data.stat.gov.lv, CC BY 4.0), pulled live:
  DSV030  average monthly wages and salaries by industry (NACE Rev. 2), annual
  PCI021  consumer price index, all goods and services, 2015 = 100, annual average
  DSR020  CSP's own real-wage series (net wages), used only as a cross-check

Method:
  real_index[y]   = (wage[y] / wage[2015]) / (cpi[y] / cpi[2015]) * 100
  real_2015_eur[y] = wage[y] * cpi[2015] / cpi[y]       (wage in 2015 prices)
The industry list is read from the table's metadata (every NACE section + total),
not hardcoded. Gross wages are used for industries; the cross-check uses net wages
because that is what CSP's real-wage series is based on.

    python real_wages.py               # pull, compute, write results/, print summary
"""

import csv
import io
import sys
from pathlib import Path

from csp_client import CspClient
from svg_chart import line_chart

BASE_YEAR = "2015"
END_YEAR = "2025"
HIGHLIGHT = ["TOTAL", "J62", "K", "O", "P", "Q", "I"]   # drawn in colour; the rest in grey
RESULTS = Path(__file__).parent / "results"


def years_between(first, last):
    return [str(y) for y in range(int(first), int(last) + 1)]


def industries(meta):
    """NACE sections (single letters) + total + J62 (computer programming), with labels, from metadata."""
    nace = next(v for v in meta["variables"] if v["code"] == "NACE")
    keep = {"TOTAL", "J62"}
    return {c: t for c, t in zip(nace["values"], nace["valueTexts"]) if len(c) == 1 or c in keep}


def real_index(wages, cpi, base=BASE_YEAR):
    """wages, cpi: {year: value}. Returns {year: (real_2015_eur, real_index)} for years with both values."""
    if wages.get(base) is None or cpi.get(base) is None:
        return {}
    out = {}
    for y, w in wages.items():
        if w is None or cpi.get(y) is None:
            continue
        real_eur = w * cpi[base] / cpi[y]
        out[y] = (round(real_eur, 1), round(real_eur / wages[base] * 100, 1))
    return out


def yoy_real(net, cpi):
    """Real net wage, % of previous year (CSP's DSR020 definition), from net wages and a CPI index."""
    ys = sorted(y for y in net if net[y] is not None and cpi.get(y) is not None)
    return {y: round(net[y] / net[p] / (cpi[y] / cpi[p]) * 100, 1) for p, y in zip(ys, ys[1:])}


def pull(client):
    years = years_between(BASE_YEAR, END_YEAR)
    labels = industries(client.metadata("DSV030"))
    wages = client.fetch("DSV030", {"GRS_NET": ["GRS", "NET"], "SECTOR": ["TOTAL"], "NACE": list(labels), "TIME": years})
    cpi = client.fetch("PCI021", {"ECOICOP_V2": ["0"], "ContentsCode": ["PCI0213"], "TIME": years})
    official = client.fetch("DSR020", {"TIME": years})
    for r in (wages, cpi, official):
        if r.eliminated:
            raise RuntimeError(f"{r.table}: unfiltered dimensions {r.eliminated} would be silently aggregated")
    return labels, wages.rows, cpi.rows, official.rows


def compute(labels, wage_rows, cpi_rows, official_rows):
    cpi = {r["TIME"]: r["value"] for r in cpi_rows}
    gross = {c: {} for c in labels}
    net_total = {}
    for r in wage_rows:
        if r["GRS_NET"] == "GRS":
            gross[r["NACE"]][r["TIME"]] = r["value"]
        elif r["NACE"] == "TOTAL":
            net_total[r["TIME"]] = r["value"]

    long_rows, summary = [], []
    for code, label in labels.items():
        idx = real_index(gross[code], cpi)
        if BASE_YEAR not in idx or END_YEAR not in idx:
            continue   # confidential or missing in the base or end year
        for y in sorted(idx):
            long_rows.append({"nace": code, "industry": label, "year": y, "nominal_gross_eur": gross[code][y],
                              "cpi_2015_100": cpi[y], "real_gross_2015_eur": idx[y][0], "real_index_2015_100": idx[y][1]})
        n0, n1 = gross[code][BASE_YEAR], gross[code][END_YEAR]
        real_change = idx[END_YEAR][1] - 100
        n_years = int(END_YEAR) - int(BASE_YEAR)
        summary.append({"nace": code, "industry": label, f"gross_{BASE_YEAR}": n0, f"gross_{END_YEAR}": n1,
                        "nominal_change_pct": round((n1 / n0 - 1) * 100, 1), "real_change_pct": round(real_change, 1),
                        "real_cagr_pct": round(((idx[END_YEAR][1] / 100) ** (1 / n_years) - 1) * 100, 2)})
    summary.sort(key=lambda r: r["real_change_pct"], reverse=True)

    ours = yoy_real(net_total, cpi)
    official = {r["TIME"]: r for r in official_rows}
    real_col = "Real wages and salaries of the employees"
    check = [{"year": y, "computed_real_net_pct_prev": v, "csp_real_net_pct_prev": official[y][real_col],
              "diff_pp": round(v - official[y][real_col], 1)} for y, v in ours.items() if y in official]
    return long_rows, summary, check


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def chart(long_rows, summary):
    names = {r["nace"]: r["industry"] for r in summary}
    series = {}
    for r in long_rows:
        series.setdefault(r["nace"], []).append((int(r["year"]), r["real_index_2015_100"]))
    short = {"TOTAL": "All industries", "J62": "Computer programming", "K": "Finance & insurance",
             "O": "Public administration", "P": "Education", "Q": "Health & social work", "I": "Accommodation & food"}
    lines = [{"name": short.get(c, names[c]), "points": pts, "highlight": c in HIGHLIGHT, "bold": c == "TOTAL"}
             for c, pts in series.items()]
    return line_chart(lines, title=f"Real gross wages by industry, Latvia ({BASE_YEAR} = 100)",
                      subtitle="Average monthly gross wage deflated by CPI. Grey: other NACE sections.",
                      source="Source: Central Statistical Bureau of Latvia (CSP), tables DSV030 and PCI021, CC BY 4.0",
                      baseline=100)


def main():
    labels, wage_rows, cpi_rows, official_rows = pull(CspClient(lang="en"))
    long_rows, summary, check = compute(labels, wage_rows, cpi_rows, official_rows)
    write_csv(RESULTS / "real_wages_by_industry.csv", long_rows)
    write_csv(RESULTS / "summary_by_industry.csv", summary)
    write_csv(RESULTS / "check_vs_csp_real_wages.csv", check)
    (RESULTS / "real_wage_index.svg").write_text(chart(long_rows, summary), encoding="utf-8")

    print(f"Real gross wage change {BASE_YEAR}-{END_YEAR}, by industry (CPI {BASE_YEAR}=100)")
    print(f"{'':<6}{'industry':<62}{'nominal':>9}{'real':>8}{'real/yr':>9}")
    for r in summary:
        print(f"{r['nace']:<6}{r['industry'][:60]:<62}{r['nominal_change_pct']:>8}%{r['real_change_pct']:>7}%{r['real_cagr_pct']:>8}%")
    worst = max(abs(c["diff_pp"]) for c in check)
    print(f"\nCross-check vs CSP real-wage series (net, % of previous year): max difference {worst} pp over {len(check)} years")
    print(f"Results written to {RESULTS}")


if __name__ == "__main__":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
