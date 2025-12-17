import json
from datetime import datetime


def registrar_movimiento(product_id, cantidad, tipo_movimiento):
    inventario_path = "data/inventario.json"
    historial_path = "data/historial.json"

    # 1. Cargar inventario
    with open(inventario_path, "r") as file:
        inventario = json.load(file)

    # Buscar producto
    producto = next((p for p in inventario if p["product_id"] == product_id), None)

    if producto is None:
        return {"error": "Producto no encontrado"}

    # 🔹 GUARDAR STOCK ANTERIOR
    stock_anterior = producto["stock"]

    # 2. Actualizar stock
    if tipo_movimiento.lower() == "entrada":
        producto["stock"] += cantidad

    elif tipo_movimiento.lower() == "salida":
        if producto["stock"] < cantidad:
            return {"error": "Stock insuficiente para salida"}
        producto["stock"] -= cantidad

    else:
        return {"error": "Tipo de movimiento inválido. Use 'Entrada' o 'Salida'"}

    # Guardar nuevo inventario
    with open(inventario_path, "w") as file:
        json.dump(inventario, file, indent=4)

    # 3. Fecha y hora completas
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Cargar historial
    try:
        with open(historial_path, "r") as file:
            historial = json.load(file)
    except:
        historial = []

    # Generar ID consecutivo
    nuevo_id = historial[-1]["id"] + 1 if historial else 1

    nuevo_registro = {
        "id": nuevo_id,
        "datetime": fecha_hora,

        "product_id": producto["product_id"],
        "product_name": producto["name"],
        "minimum_stock": producto["minimum_stock"],
        "category": producto["category"],
        "price_per_unit": producto["price"],

        "movement_type": "Ingreso" if tipo_movimiento.lower() == "entrada" else "Salida",
        "quantity": cantidad,

        "stock_before": stock_anterior,
        "stock_after": producto["stock"]
    }

    historial.append(nuevo_registro)

    with open(historial_path, "w") as file:
        json.dump(historial, file, indent=4)

    return nuevo_registro
