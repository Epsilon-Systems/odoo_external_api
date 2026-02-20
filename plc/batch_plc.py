import os
import json
import logging
import datetime
import xmlrpc.client
from typing import Any, Dict, List, Optional, Tuple


def get_project_root() -> str:
    # /.../odoo_external_api/plc/batch_plc.py -> /.../odoo_external_api
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def get_config(config_filename: str = "config.json") -> Dict[str, Any]:
    config_path = os.path.join(get_project_root(), "config", config_filename)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_logging() -> None:
    logs_dir = os.path.join(get_project_root(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "batch_plc.log")

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def get_odoo_clients(odoo_cfg: Dict[str, str]) -> Tuple[str, str, str, str, int, Any]:
    server_url = odoo_cfg["odoourl"].rstrip("/")
    db_name = odoo_cfg["odoodb"]
    username = odoo_cfg["odoouser"]
    password = odoo_cfg["odoopassword"]

    common = xmlrpc.client.ServerProxy(f"{server_url}/xmlrpc/2/common")
    uid = common.authenticate(db_name, username, password, {})
    if not uid:
        raise RuntimeError("Authentication failed: check database/user/password in config.json")

    models = xmlrpc.client.ServerProxy(f"{server_url}/xmlrpc/2/object")
    return server_url, db_name, username, password, uid, models


def detect_payload_field(db_name: str, uid: int, password: str, models: Any, model_name: str) -> str:
    fields_meta = models.execute_kw(db_name, uid, password, model_name, "fields_get", [], {"attributes": ["string", "type"]})

    # Candidate by technical name (best case)
    technical_candidates = [k for k in fields_meta.keys() if "payload" in k.lower()]
    if technical_candidates:
        # Prefer something like raw_payload if exists
        technical_candidates.sort(key=lambda x: (0 if "raw" in x.lower() else 1, len(x)))
        return technical_candidates[0]

    # Candidate by field label (string)
    label_candidates = []
    for field_name, meta in fields_meta.items():
        label = (meta.get("string") or "").lower()
        if "payload" in label:
            label_candidates.append(field_name)

    if label_candidates:
        label_candidates.sort(key=len)
        return label_candidates[0]

    raise RuntimeError(
        f"Could not detect payload field in model '{model_name}'. "
        f"Available fields count: {len(fields_meta)}"
    )


def fetch_raw_payload_records(db_name: str, uid: int, password: str, models: Any, limit: int = 10,) -> List[Dict[str, Any]]:
    model_name = "mrp.batch.plc.raw"
    payload_field = detect_payload_field(db_name, uid, password, models, model_name)

    # Try to include common useful fields if they exist
    fields_meta = models.execute_kw(db_name, uid, password, model_name, "fields_get", [], {"attributes": ["string", "type"]})

    wanted_fields = ["id", payload_field, "identifier", "source", "fetch_date", "processed_record"]
    read_fields = [f for f in wanted_fields if f in fields_meta]

    records = models.execute_kw(db_name, uid, password, model_name, "search_read", [[]],
                                {
                                    "fields": read_fields,
                                    "order": "id desc",
                                    "limit": limit,
                                })

    logging.info("Fetched %s record(s) from %s (payload field: %s)", len(records), model_name, payload_field)
    return records


def pretty_print_records(records: List[Dict[str, Any]]) -> None:
    if not records:
        print("No records found.")
        return

    print("================================================================")
    print("BATCH PLC - PHASE 1 (READ RAW PAYLOAD)")
    print("================================================================")
    for rec in records:
        rec_id = rec.get("id")
        identifier = rec.get("identifier")
        source = rec.get("source")
        fetch_date = rec.get("fetch_date")

        print("----------------------------------------------------------------")
        print(f"ID: {rec_id} | Identifier: {identifier} | Source: {source} | Fetch Date: {fetch_date}")

        # Find the payload field dynamically in the record
        payload_value = None
        for k, v in rec.items():
            if "payload" in k.lower():
                payload_value = v
                break

        if payload_value is None:
            print("Payload: <not found in returned fields>")
            continue

        # payload_value might already be a dict OR a JSON string depending on your custom field type
        if isinstance(payload_value, str):
            try:
                parsed = json.loads(payload_value)
                print("Raw Payload (parsed):")
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
            except Exception:
                print("Raw Payload (raw string):")
                print(payload_value)
        else:
            print("Raw Payload:")
            print(json.dumps(payload_value, indent=2, ensure_ascii=False))


def main() -> None:
    setup_logging()
    start_time = datetime.datetime.now()

    config = get_config("config.json")
    odoo_cfg = config["odoo"]

    print("Connecting to Odoo via XML-RPC...")
    server_url, db_name, username, password, uid, models = get_odoo_clients(odoo_cfg)
    print(f"Connected: {server_url} | DB: {db_name} | UID: {uid}")

    records = fetch_raw_payload_records(db_name, uid, password, models, limit=10)
    pretty_print_records(records)

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print("----------------------------------------------------------------")
    print(f"Script duration: {duration}")
    print("Done.")


if __name__ == "__main__":
    main()
