import json
import re
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass
class PgConfig:
    host: str
    port: int
    user: str
    password: str


@dataclass
class CompareConfig:
    pg: PgConfig
    db_a: str
    db_b: str
    mode: str  # all | selected | config
    selected_models: List[str]
    exclude_models_like: List[str]
    max_rows_per_model: int
    sample_diff_rows: int
    diff_cells_limit: int
    output_xlsx: str


def load_config(path: str = "config.json") -> CompareConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    pg = raw["pg"]
    return CompareConfig(
        pg=PgConfig(
            host=pg["host"],
            port=int(pg["port"]),
            user=pg["user"],
            password=pg["password"],
        ),
        db_a=raw["db_a"],
        db_b=raw["db_b"],
        mode=raw.get("mode", "selected"),
        selected_models=raw.get("selected_models", []),
        exclude_models_like=raw.get("exclude_models_like", []),
        max_rows_per_model=int(raw.get("max_rows_per_model", 20000)),
        sample_diff_rows=int(raw.get("sample_diff_rows", 200)),
        diff_cells_limit=int(raw.get("diff_cells_limit", 5000)),
        output_xlsx=raw.get("output_xlsx", "odoo_db_diff.xlsx"),
    )


def pg_connect(pg: PgConfig, dbname: str):
    return psycopg2.connect(
        host=pg.host,
        port=pg.port,
        user=pg.user,
        password=pg.password,
        dbname=dbname,
    )


def fetch_all(conn, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cr:
        cr.execute(query, params)
        return cr.fetchall()


def fetch_one(conn, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
    rows = fetch_all(conn, query, params)
    return rows[0] if rows else None


def normalize_value(v: Any) -> Any:
    # Normalizaciones sencillas para comparación
    if isinstance(v, str):
        return v.strip()
    return v


def md5_of_row(row: Dict[str, Any], cols: List[str]) -> str:
    parts = []
    for c in cols:
        v = normalize_value(row.get(c))
        parts.append("" if v is None else str(v))
    raw = "\u001f".join(parts).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def model_to_table(model_name: str) -> str:
    # Odoo por defecto usa: model.name -> model_name con puntos a guiones bajos
    return model_name.replace(".", "_")


def list_models(conn) -> List[str]:
    # Modelos registrados en la DB (no depende de código)
    rows = fetch_all(conn, "SELECT model FROM ir_model ORDER BY model")
    return [r["model"] for r in rows]


def get_table_columns(conn, table_name: str) -> List[str]:
    q = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """
    rows = fetch_all(conn, q, (table_name,))
    return [r["column_name"] for r in rows]


def get_model_fields(conn, model_name: str) -> List[str]:
    # Campos almacenados (store=True) suelen tener columna real
    # Nota: hay campos compute store, related store, etc. Odoo maneja columnas.
    # Aquí usamos information_schema para columnas reales de la tabla.
    table = model_to_table(model_name)
    q = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """
    rows = fetch_all(conn, q, (table,))
    return [r["column_name"] for r in rows]


def table_exists(conn, table_name: str) -> bool:
    q = """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema='public' AND table_name=%s
        LIMIT 1
    """
    return fetch_one(conn, q, (table_name,)) is not None


def should_exclude_model(model_name: str, exclude_patterns: List[str]) -> bool:
    # Excluir transients + modelos técnicos comunes (puedes ajustar)
    transient_prefixes = ("ir.attachment", "ir.logging", "mail.", "bus.", "digest.", "iap.")
    if model_name.startswith(transient_prefixes):
        return True

    for pat in exclude_patterns:
        # pat puede ser "mail.message" o regex simple; si contiene caracteres regex, se respeta
        if pat == model_name:
            return True
        if pat.endswith(".*") and model_name.startswith(pat[:-2]):
            return True
        try:
            if re.search(pat, model_name):
                return True
        except re.error:
            pass

    return False


def compare_simple_kv(conn_a, conn_b, title: str, query: str, key_col: str, val_cols: List[str], params: Tuple = ()) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Regresa:
    - left_only (en A no en B)
    - right_only (en B no en A)
    - different (en ambos pero distinto)
    """
    a_rows = fetch_all(conn_a, query, params)
    b_rows = fetch_all(conn_b, query, params)

    a_map = {r[key_col]: r for r in a_rows}
    b_map = {r[key_col]: r for r in b_rows}

    left_only = []
    right_only = []
    different = []

    all_keys = set(a_map.keys()) | set(b_map.keys())
    for k in sorted(all_keys, key=lambda x: str(x)):
        ra = a_map.get(k)
        rb = b_map.get(k)
        if ra and not rb:
            left_only.append({"section": title, key_col: k, **{c: ra.get(c) for c in val_cols}})
        elif rb and not ra:
            right_only.append({"section": title, key_col: k, **{c: rb.get(c) for c in val_cols}})
        else:
            diffs = {}
            for c in val_cols:
                va = normalize_value(ra.get(c))
                vb = normalize_value(rb.get(c))
                if va != vb:
                    diffs[f"{c}_a"] = ra.get(c)
                    diffs[f"{c}_b"] = rb.get(c)
            if diffs:
                different.append({"section": title, key_col: k, **diffs})

    return (
        pd.DataFrame(left_only),
        pd.DataFrame(right_only),
        pd.DataFrame(different),
    )


def compare_config(conn_a, conn_b) -> Dict[str, pd.DataFrame]:
    outputs: Dict[str, pd.DataFrame] = {}

    # Modules state
    q_modules = """
        SELECT name, state, latest_version
        FROM ir_module_module
        WHERE name IS NOT NULL
        ORDER BY name
    """
    a_only, b_only, diff = compare_simple_kv(
        conn_a, conn_b, "modules", q_modules, "name", ["state", "latest_version"]
    )
    outputs["config_modules_only_in_a"] = a_only
    outputs["config_modules_only_in_b"] = b_only
    outputs["config_modules_different"] = diff

    # System parameters (ojo: puede contener secretos; filtramos algunos)
    q_params = """
        SELECT key, value
        FROM ir_config_parameter
        WHERE key IS NOT NULL
        ORDER BY key
    """
    a_rows = fetch_all(conn_a, q_params)
    b_rows = fetch_all(conn_b, q_params)

    def is_sensitive(k: str) -> bool:
        k = (k or "").lower()
        sensitive_markers = ("password", "secret", "token", "api_key", "apikey", "smtp", "oauth")
        return any(m in k for m in sensitive_markers)

    a_map = {r["key"]: r["value"] for r in a_rows if not is_sensitive(r["key"])}
    b_map = {r["key"]: r["value"] for r in b_rows if not is_sensitive(r["key"])}

    a_only_list = []
    b_only_list = []
    diff_list = []
    all_keys = set(a_map.keys()) | set(b_map.keys())
    for k in sorted(all_keys):
        va = a_map.get(k)
        vb = b_map.get(k)
        if va is None and vb is not None:
            b_only_list.append({"key": k, "value": vb})
        elif vb is None and va is not None:
            a_only_list.append({"key": k, "value": va})
        elif normalize_value(va) != normalize_value(vb):
            diff_list.append({"key": k, "value_a": va, "value_b": vb})

    outputs["config_params_only_in_a"] = pd.DataFrame(a_only_list)
    outputs["config_params_only_in_b"] = pd.DataFrame(b_only_list)
    outputs["config_params_different"] = pd.DataFrame(diff_list)

    # Companies basic
    # Companies basic (tolerant to missing columns)
    table_company = "res_company"
    cols_a = set(get_table_columns(conn_a, table_company))
    cols_b = set(get_table_columns(conn_b, table_company))
    common_cols = cols_a & cols_b

    key_col = "id"
    wanted_cols = ["name", "currency_id", "country_id", "vat"]
    val_cols = [c for c in wanted_cols if c in common_cols]

    if key_col in common_cols and val_cols:
        select_cols = ", ".join([key_col] + val_cols)
        q_company = f"SELECT {select_cols} FROM {table_company} ORDER BY {key_col}"
        a_only, b_only, diff = compare_simple_kv(conn_a, conn_b, "companies", q_company, key_col, val_cols)
        outputs["config_companies_only_in_a"] = a_only
        outputs["config_companies_only_in_b"] = b_only
        outputs["config_companies_different"] = diff
    else:
        outputs["config_companies_only_in_a"] = pd.DataFrame([{
            "info": "res_company comparison skipped: missing required columns",
            "common_cols": ", ".join(sorted(list(common_cols))[:50]),
        }])
        outputs["config_companies_only_in_b"] = pd.DataFrame()
        outputs["config_companies_different"] = pd.DataFrame()

    return outputs


def compare_model_data(conn_a, conn_b, model_name: str, max_rows: int, sample_diff_rows: int, diff_cells_limit: int) -> Dict[str, pd.DataFrame]:
    table = model_to_table(model_name)
    if not table_exists(conn_a, table) or not table_exists(conn_b, table):
        return {
            "model_summary": pd.DataFrame([{
                "model": model_name,
                "table": table,
                "status": "table_missing_in_one_db",
            }])
        }

    fields_a = get_model_fields(conn_a, model_name)
    fields_b = get_model_fields(conn_b, model_name)
    common_fields = [f for f in fields_a if f in fields_b]

    # Siempre necesitamos id
    if "id" not in common_fields:
        return {
            "model_summary": pd.DataFrame([{
                "model": model_name,
                "table": table,
                "status": "no_common_id",
            }])
        }

    # Evitar campos enormes/ruidosos por defecto
    skip_fields = {"create_date", "write_date", "write_uid", "create_uid", "__last_update", "message_main_attachment_id"}
    compare_fields = [f for f in common_fields if f not in skip_fields]

    # Conteos
    count_a = fetch_one(conn_a, f"SELECT COUNT(*) AS c FROM {table}")["c"]
    count_b = fetch_one(conn_b, f"SELECT COUNT(*) AS c FROM {table}")["c"]

    # IDs (muestreo si es enorme)
    ids_a = fetch_all(conn_a, f"SELECT id FROM {table} ORDER BY id LIMIT %s", (max_rows,))
    ids_b = fetch_all(conn_b, f"SELECT id FROM {table} ORDER BY id LIMIT %s", (max_rows,))
    ids_a_set = {r["id"] for r in ids_a}
    ids_b_set = {r["id"] for r in ids_b}

    only_in_a = sorted(list(ids_a_set - ids_b_set))[:diff_cells_limit]
    only_in_b = sorted(list(ids_b_set - ids_a_set))[:diff_cells_limit]

    # Intersección para comparar contenido
    common_ids = sorted(list(ids_a_set & ids_b_set))
    common_ids = common_ids[:max_rows]

    # Traer filas por ids (para no leer todo)
    # Importante: alinear columnas en ambos
    cols_sql = ", ".join([f'"{c}"' for c in compare_fields])

    def fetch_rows_by_ids(conn, ids: List[int]) -> Dict[int, Dict[str, Any]]:
        if not ids:
            return {}
        q = f"SELECT {cols_sql} FROM {table} WHERE id = ANY(%s)"
        rows = fetch_all(conn, q, (ids,))
        return {r["id"]: r for r in rows}

    rows_a = fetch_rows_by_ids(conn_a, common_ids)
    rows_b = fetch_rows_by_ids(conn_b, common_ids)

    # Comparación por hash para detectar filas diferentes rápido
    diffs = []
    diff_count = 0
    for rid in common_ids:
        ra = rows_a.get(rid)
        rb = rows_b.get(rid)
        if not ra or not rb:
            continue
        ha = md5_of_row(ra, compare_fields)
        hb = md5_of_row(rb, compare_fields)
        if ha != hb:
            diffs.append(rid)
            diff_count += 1
            if len(diffs) >= sample_diff_rows:
                break

    # Diferencias por celda (solo para ids distintos muestreados)
    cell_diffs = []
    for rid in diffs:
        ra = rows_a[rid]
        rb = rows_b[rid]
        for c in compare_fields:
            va = normalize_value(ra.get(c))
            vb = normalize_value(rb.get(c))
            if va != vb:
                cell_diffs.append({
                    "model": model_name,
                    "table": table,
                    "id": rid,
                    "field": c,
                    "value_a": ra.get(c),
                    "value_b": rb.get(c),
                })
                if len(cell_diffs) >= diff_cells_limit:
                    break
        if len(cell_diffs) >= diff_cells_limit:
            break

    summary = pd.DataFrame([{
        "model": model_name,
        "table": table,
        "count_a": count_a,
        "count_b": count_b,
        "ids_only_in_a_sample": len(only_in_a),
        "ids_only_in_b_sample": len(only_in_b),
        "different_rows_sample": diff_count,
        "compared_ids": len(common_ids),
        "compared_fields": len(compare_fields),
        "status": "ok",
    }])

    out = {
        "model_summary": summary,
        "ids_only_in_a": pd.DataFrame([{"model": model_name, "id": i} for i in only_in_a]),
        "ids_only_in_b": pd.DataFrame([{"model": model_name, "id": i} for i in only_in_b]),
        "cell_differences": pd.DataFrame(cell_diffs),
    }
    return out


def sanitize_sheet_name(name: str) -> str:
    # Excel sheet limit is 31 chars
    name = re.sub(r"[\[\]\:\*\?\/\\]", "_", name)
    return name[:31]


def write_excel(output_path: str, sheets: Dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe = sanitize_sheet_name(sheet_name)
            if df is None or df.empty:
                # Aún así crear hoja con encabezado
                pd.DataFrame([{"info": "no_data"}]).to_excel(writer, index=False, sheet_name=safe)
            else:
                df.to_excel(writer, index=False, sheet_name=safe)


def build_model_list(cfg: CompareConfig, conn_a, conn_b) -> List[str]:
    if cfg.mode == "config":
        return []

    if cfg.mode == "selected":
        return cfg.selected_models

    # mode == all
    models_a = set(list_models(conn_a))
    models_b = set(list_models(conn_b))
    return sorted(list(models_a & models_b))


def main() -> None:
    cfg = load_config("config.json")

    conn_a = pg_connect(cfg.pg, cfg.db_a)
    conn_b = pg_connect(cfg.pg, cfg.db_b)

    try:
        sheets: Dict[str, pd.DataFrame] = {}

        # 1) Config diffs
        config_sheets = compare_config(conn_a, conn_b)
        sheets.update(config_sheets)

        # 2) Models
        models = build_model_list(cfg, conn_a, conn_b)
        models = [m for m in models if not should_exclude_model(m, cfg.exclude_models_like)]

        summaries = []
        for model in models:
            data = compare_model_data(
                conn_a=conn_a,
                conn_b=conn_b,
                model_name=model,
                max_rows=cfg.max_rows_per_model,
                sample_diff_rows=cfg.sample_diff_rows,
                diff_cells_limit=cfg.diff_cells_limit,
            )

            # Consolidar resumen global
            if "model_summary" in data and not data["model_summary"].empty:
                summaries.append(data["model_summary"])

            # Guardar hojas por modelo (solo si hay algo relevante)
            # Para no explotar el Excel, guardamos solo 3 hojas por modelo:
            # - ids only in a
            # - ids only in b
            # - cell diffs (muestreo)
            if cfg.mode != "config":
                sheets[f"{model}_only_in_a"] = data.get("ids_only_in_a", pd.DataFrame())
                sheets[f"{model}_only_in_b"] = data.get("ids_only_in_b", pd.DataFrame())
                sheets[f"{model}_cell_diff"] = data.get("cell_differences", pd.DataFrame())

        if summaries:
            sheets["models_summary"] = pd.concat(summaries, ignore_index=True)
        else:
            sheets["models_summary"] = pd.DataFrame([{"info": "no_models_compared"}])

        # Summary high-level
        sheets["run_info"] = pd.DataFrame([{
            "db_a": cfg.db_a,
            "db_b": cfg.db_b,
            "mode": cfg.mode,
            "selected_models_count": len(cfg.selected_models),
            "excluded_patterns": ", ".join(cfg.exclude_models_like),
            "max_rows_per_model": cfg.max_rows_per_model,
            "sample_diff_rows": cfg.sample_diff_rows,
            "diff_cells_limit": cfg.diff_cells_limit,
        }])

        write_excel(cfg.output_xlsx, sheets)
        print(f"Excel generated: {cfg.output_xlsx}")

    finally:
        conn_a.close()
        conn_b.close()


if __name__ == "__main__":
    main()
