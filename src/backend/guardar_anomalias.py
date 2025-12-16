import json
from pathlib import Path
from datetime import datetime

ANOM_PATH = Path("data/anomalias.json")

def guardar_anomalias_historico(registros_anomalias: list[dict]) -> int:
    """
    Agrega anomalías al histórico.
    Devuelve cuántas guardó.
    """
    ANOM_PATH.parent.mkdir(parents=True, exist_ok=True)

    if ANOM_PATH.exists():
        try:
            prev = json.loads(ANOM_PATH.read_text(encoding="utf-8"))
            if not isinstance(prev, list):
                prev = []
        except:
            prev = []
    else:
        prev = []

    # Evitar duplicados básicos por (product_id, Fecha_Hora, movement, quantity)
    seen = set()
    for x in prev:
        key = (x.get("product_id"), x.get("Fecha_Hora"), x.get("movement_type"), x.get("quantity"))
        seen.add(key)

    nuevos = []
    for r in registros_anomalias:
        key = (r.get("product_id"), r.get("Fecha_Hora"), r.get("movement_type"), r.get("quantity"))
        if key in seen:
            continue
        nuevos.append(r)

    merged = prev + nuevos
    ANOM_PATH.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(nuevos)
