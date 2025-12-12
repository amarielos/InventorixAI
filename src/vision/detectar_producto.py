import cv2
import json
from ultralytics import YOLO

def detectar_producto():
    # 1. Cargar inventario
    with open("data/inventario.json", "r") as file:
        inventario = json.load(file)

    # Crear un set con los nombres de productos del inventario
    nombres_inventario = {item["name"].lower(): item for item in inventario}

    # 2. Cargar modelo YOLO
    model = YOLO("yolov8n.pt")

    # 3. Inicializar cámara
    cap = cv2.VideoCapture(0)

    print("Iniciando cámara... Presiona 'q' para salir manualmente.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        results = model(frame)

        # Dibujar anotaciones en pantalla
        anotaciones = results[0].plot()
        cv2.imshow("Detección", anotaciones)

        # 4. Extraer detecciones
        detecciones = results[0].boxes

        if len(detecciones) > 0:
            # Tomar la primera detección
            clase_id = int(detecciones[0].cls[0])
            nombre_detectado = model.names[clase_id].lower()

            print(f"Objeto detectado: {nombre_detectado}")

            # 5. Verificar si está en el inventario
            if nombre_detectado in nombres_inventario:
                print("Producto encontrado en inventario.")
                producto = nombres_inventario[nombre_detectado]

                # Cerrar cámara y ventanas
                cap.release()
                cv2.destroyAllWindows()

                return producto  # ← devuelve todo el objeto

        # Salida manual
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cerrar cámara si se sale sin coincidencias
    cap.release()
    cv2.destroyAllWindows()
    return None
