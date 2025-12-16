import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def _preparar_features(df_hist: pd.DataFrame):
    """
    Convierte el historial (JSON->DF) a un DF con features numéricas para IA.
    Espera columnas: date, time, quantity, movement_type, product_id, product_name
    movement_type esperado: 'Ingreso' o 'Salida'
    """
    df = df_hist.copy()

    # datetime
    df["Fecha_Hora"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
    df = df.dropna(subset=["Fecha_Hora"]).sort_values("Fecha_Hora")

    # features tiempo
    df["hora"] = df["Fecha_Hora"].dt.hour
    df["dia_semana"] = df["Fecha_Hora"].dt.dayofweek  # 0=Lunes

    # tipo movimiento -> binario
    df["es_salida"] = (df["movement_type"].astype(str).str.lower() == "salida").astype(int)

    # cantidad (aseguramos numérico)
    df["cantidad"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)

    feats = df[["cantidad", "es_salida", "hora", "dia_semana"]].copy()
    return df, feats


def _interpretar_y_accion(row: pd.Series) -> tuple[str, str]:
    """
    Genera interpretación (explicación) + acción sugerida por anomalía.
    """
    prod = str(row.get("product_name", "Producto"))
    movimiento = str(row.get("movement_type", "")).strip()
    motivo = str(row.get("motivo", "")).strip()
    q = row.get("quantity", None)

    interpretacion = (
        f"El movimiento de **{prod}** fue marcado como anómalo porque el patrón no coincide con el comportamiento "
        f"habitual registrado. {motivo}".strip()
    )

    if movimiento.lower() == "salida":
        accion = (
            "Verificar si fue una venta grande, merma o error de digitación. "
            "Confirmar con ticket/factura o control de bodega. "
            "Si fue error, corregir el movimiento para evitar quiebres de stock."
        )
    else:
        accion = (
            "Verificar si fue una recepción/compra real o un ajuste de inventario. "
            "Confirmar con factura/recepción. "
            "Si fue error, corregir para no inflar el stock."
        )

    if q is not None and isinstance(q, (int, float)) and q > 0:
        accion += " Validar unidades y que la cantidad esté en la unidad correcta."

    return interpretacion, accion


def detectar_movimientos_extranos(
    df_historial: pd.DataFrame,
    contamination: float = 0.15,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Devuelve el historial con columnas nuevas:
    - anomaly: 1 si es anómalo, 0 si normal
    - anomaly_score: score (más bajo suele ser más anómalo)
    - motivo: explicación corta del porqué
    - interpretacion: explicación más humana (qué podría estar pasando)
    - accion_sugerida: qué revisar/hacer
    """
    if df_historial is None or len(df_historial) == 0:
        return pd.DataFrame()

    df, X = _preparar_features(df_historial)

    # Si hay muy pocos datos, no entrenamos IA
    if len(X) < 8:
        df["anomaly"] = 0
        df["anomaly_score"] = 0.0
        df["motivo"] = "Datos insuficientes para IA (mínimo 8 registros)."
        df["interpretacion"] = "No hay suficientes datos para que el modelo aprenda el patrón normal."
        df["accion_sugerida"] = "Registrar más movimientos y volver a ejecutar."
        return df

    model = IsolationForest(
        n_estimators=200,
        contamination=min(max(contamination, 0.01), 0.4),
        random_state=random_state
    )
    model.fit(X)

    pred = model.predict(X)  # -1 anómalo, 1 normal
    score = model.decision_function(X)

    df["anomaly"] = (pred == -1).astype(int)
    df["anomaly_score"] = score

    # Motivos (explicabilidad ligera)
    df["motivo"] = ""

    # Reglas explicativas por producto (solo para dar “por qué”)
    if "product_id" in df.columns:
        for pid, grp in df.groupby("product_id"):
            cantidades = grp["cantidad"].values
            if len(cantidades) < 3:
                continue
            mu = float(np.mean(cantidades))
            sigma = float(np.std(cantidades)) if float(np.std(cantidades)) > 0 else 1.0

            for i in grp.index:
                if int(df.at[i, "anomaly"]) == 1:
                    q = float(df.at[i, "cantidad"])
                    tipo = str(df.at[i, "movement_type"]).lower().strip()

                    if q > mu + 2 * sigma:
                        df.at[i, "motivo"] = f"Cantidad inusual vs histórico del producto (q={q:.0f})."
                    elif tipo == "salida" and q > mu + 1.5 * sigma:
                        df.at[i, "motivo"] = f"Salida inusual vs histórico (q={q:.0f})."
                    else:
                        df.at[i, "motivo"] = "Patrón inusual detectado por IA."
    else:
        df.loc[df["anomaly"] == 1, "motivo"] = "Patrón inusual detectado por IA."
        df.loc[df["anomaly"] == 0, "motivo"] = "Normal"

    # Interpretación + acción
    df["interpretacion"] = ""
    df["accion_sugerida"] = ""

    for i in df.index:
        if int(df.at[i, "anomaly"]) == 1:
            interp, acc = _interpretar_y_accion(df.loc[i])
            df.at[i, "interpretacion"] = interp
            df.at[i, "accion_sugerida"] = acc
        else:
            df.at[i, "interpretacion"] = "Movimiento dentro del patrón esperado."
            df.at[i, "accion_sugerida"] = "Sin acción."

    return df


def resumen_anomalias(df_anom: pd.DataFrame) -> dict:
    """
    KPIs rápidos para mostrar en la UI.
    """
    if df_anom is None or len(df_anom) == 0:
        return {"total": 0, "anomalias": 0, "porcentaje": 0.0}

    total = len(df_anom)
    anom = int(df_anom["anomaly"].sum()) if "anomaly" in df_anom.columns else 0
    pct = (anom / total) * 100 if total > 0 else 0.0
    return {"total": total, "anomalias": anom, "porcentaje": pct}
