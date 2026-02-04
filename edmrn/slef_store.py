import json
from pathlib import Path
from edmrn.utils import atomic_write_json

SLEF_STORE_PATH = str(Path.home() / ".edmrn_slef_store.json")

def load_slef_store():
    try:
        path = Path(SLEF_STORE_PATH)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception:
        return []

def save_slef_store(slef_list):
    return atomic_write_json(SLEF_STORE_PATH, slef_list)

def add_slef_entry(name, code):
    slef_list = load_slef_store()
    slef_list = [entry for entry in slef_list if entry.get("name") != name]
    slef_list.append({"name": name, "code": code})
    save_slef_store(slef_list)
    return slef_list

def remove_slef_entry(name):
    slef_list = load_slef_store()
    slef_list = [entry for entry in slef_list if entry.get("name") != name]
    save_slef_store(slef_list)
    return slef_list
