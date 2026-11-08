"""
CSP (Central Statistical Bureau of Latvia) PX-Web API client - stdlib only.

API: https://data.stat.gov.lv/api/v1/{lang}/OSP_PUB  (public, no auth, CC BY 4.0)
CSP also publishes the same data through an MCP server (https://mcp-px.stat.gov.lv/) for AI assistants;
this client is for repeatable scripted pulls.

Main calls:
    c = CspClient(lang="en")
    c.search("average wages region")          -> [{id, path, title, published}]
    c.metadata("DSV052c")                     -> {title, variables: [...]}
    r = c.fetch("DSV052c", {"AREA": ["LV"], "NACE_21": ["K62"], "TIME": "top:2"})
    r.rows / r.to_csv(path) / r.eliminated

Gotchas:
- A dimension left out of the filters is ELIMINATED (silently summed/defaulted) by PX-Web.
  `fetch` records those in `result.eliminated`.
- Symbols in data: "." confidential, "…" not yet available, "-" no data. They become None.
- NACE Rev. 2.1 from 2026: IT is K62 (was J62), finance L64 (was K64), education Q85 (was P85).
"""

import csv
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

BASE = "https://data.stat.gov.lv/api/v1/{lang}/OSP_PUB"
WEB = "https://data.stat.gov.lv/pxweb/{lang}/OSP_PUB/START__{path}/{table}/"
USER_AGENT = "csp-stat/1.0 (python urllib)"
MISSING = {".", "…", "-", "..", ""}
CATALOGUE_MAX_AGE_S = 24 * 3600


class CspError(Exception):
    pass


def to_number(raw):
    """CSP cell text -> float/int, or None for the missing-value symbols."""
    s = (raw or "").strip()
    if s in MISSING:
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f.is_integer() and "." not in s else f


@dataclass
class Result:
    table: str
    title: str
    columns: list                      # output column names, in order
    rows: list = field(default_factory=list)
    eliminated: list = field(default_factory=list)   # dims not filtered -> aggregated by PX-Web

    def to_csv(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=self.columns)
            w.writeheader()
            w.writerows(self.rows)
        return path


class CspClient:
    def __init__(self, lang="en", cache_dir=None, delay=1.0, timeout=60):
        if lang not in ("en", "lv"):
            raise ValueError("lang must be 'en' or 'lv'")
        self.lang = lang
        self.base = BASE.format(lang=lang)
        self.delay = delay
        self.timeout = timeout
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent / ".cache"
        self._last = 0.0
        self._catalogue = None
        self._meta = {}

    # ---- HTTP -------------------------------------------------------------
    def _request(self, url, body=None):
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = resp.read().decode("utf-8-sig")
        except urllib.error.HTTPError as e:
            raise CspError(f"HTTP {e.code} for {url}: {e.read().decode('utf-8', 'replace')[:300]}") from None
        finally:
            self._last = time.monotonic()
        return json.loads(payload)

    # ---- catalogue / search -----------------------------------------------
    def catalogue(self, refresh=False):
        """All tables: [{id, path, title, published}]. Cached on disk for a day."""
        if self._catalogue is not None and not refresh:
            return self._catalogue
        cache = self.cache_dir / f"catalogue_{self.lang}.json"
        if not refresh and cache.exists() and time.time() - cache.stat().st_mtime < CATALOGUE_MAX_AGE_S:
            self._catalogue = json.loads(cache.read_text(encoding="utf-8"))
            return self._catalogue
        raw = self._request(f"{self.base}?query=*&filter=*")
        self._catalogue = [{"id": t["id"], "path": t["path"], "title": t["title"], "published": t.get("published", "")} for t in raw]
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(self._catalogue, ensure_ascii=False), encoding="utf-8")
        return self._catalogue

    def search(self, words, include_archive=False):
        """Tables whose title or id contains every word (case-insensitive). Archive (A_*) paths skipped by default."""
        terms = [w.lower() for w in (words.split() if isinstance(words, str) else words)]
        seen, out = set(), []
        for t in self.catalogue():
            if not include_archive and "/A_" in t["path"]:
                continue
            hay = f"{t['id']} {t['title']}".lower()
            if all(w in hay for w in terms) and t["id"] not in seen:
                seen.add(t["id"])
                out.append(t)
        return out

    def path_of(self, table):
        """Catalogue path of a table id, preferring a non-archive path."""
        hits = [t["path"] for t in self.catalogue() if t["id"] == table]
        if not hits:
            raise CspError(f"Table {table} not found in the {self.lang} catalogue")
        hits.sort(key=lambda p: "/A_" in p)
        return hits[0]

    def web_link(self, table):
        return WEB.format(lang=self.lang, path=self.path_of(table).strip("/").replace("/", "__"), table=table)

    # ---- metadata / data ---------------------------------------------------
    def _table_url(self, table):
        return f"{self.base}/START{self.path_of(table)}/{table}"

    def metadata(self, table):
        if table not in self._meta:
            self._meta[table] = self._request(self._table_url(table))
        return self._meta[table]

    @staticmethod
    def _selection(values):
        """['a','b'] -> item; '*' -> all; 'top:N' -> last N periods."""
        if values == "*" or values == ["*"]:
            return {"filter": "all", "values": ["*"]}
        if isinstance(values, str) and values.startswith("top:"):
            return {"filter": "top", "values": [values[4:]]}
        if isinstance(values, str):
            values = [values]
        return {"filter": "item", "values": list(values)}

    def fetch(self, table, filters=None):
        filters = dict(filters or {})
        meta = self.metadata(table)
        variables = {v["code"]: v for v in meta["variables"]}
        unknown = [k for k in filters if k not in variables]
        if unknown:
            raise CspError(f"{table}: unknown dimension(s) {unknown}; has {list(variables)}")
        for code, vals in filters.items():
            if isinstance(vals, list) and vals != ["*"]:
                bad = [v for v in vals if v not in variables[code]["values"]]
                if bad:
                    raise CspError(f"{table}.{code}: unknown value(s) {bad[:10]}")
        body = {"query": [{"code": k, "selection": self._selection(v)} for k, v in filters.items()],
                "response": {"format": "json"}}
        resp = self._request(self._table_url(table), body)
        return self._parse(table, meta, resp, filters)

    @staticmethod
    def _parse(table, meta, resp, filters):
        labels = {v["code"]: dict(zip(v["values"], v["valueTexts"])) for v in meta["variables"]}
        dims = [c for c in resp["columns"] if c["type"] != "c"]
        contents = [c for c in resp["columns"] if c["type"] == "c"]
        columns = []
        for d in dims:
            columns.append(d["code"])
            if d["type"] != "t":
                columns.append(d["code"] + "_label")
        content_names = [c["text"] if len(contents) > 1 else "value" for c in contents]
        columns += content_names
        rows = []
        for rec in resp["data"]:
            row = {}
            for d, key in zip(dims, rec["key"]):
                row[d["code"]] = key
                if d["type"] != "t":
                    row[d["code"] + "_label"] = labels.get(d["code"], {}).get(key, "")
            for name, raw in zip(content_names, rec["values"]):
                row[name] = to_number(raw)
            rows.append(row)
        returned = {d["code"] for d in dims} | {"ContentsCode"}
        eliminated = [v["code"] for v in meta["variables"] if v["code"] not in returned and v["code"] not in filters]
        return Result(table=table, title=meta.get("title", ""), columns=columns, rows=rows, eliminated=eliminated)
