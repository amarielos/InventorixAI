from src.backend.detectar_producto import detectar_producto
from src.backend.registrar_movimiento import registrar_movimiento

# Flujo principal

#################################################
# FUNCIÓN 1
# Detectar producto usando la cámara
#################################################
producto = detectar_producto()

# Si se detecta un producto, registrar movimiento y actualizar inventario
if producto:
    print("Producto detectado:", producto)
    
    # Menu para pruebas en consola    
    print("""Ingresa el numero del tipo de movimiento 
1. Entrada  
2. Salida""")
    # La funcion recibe "Entrada" o "Salida", no el numero
    tipo_movimiento = "Entrada" if input() == "1" else "Salida"
    print("Ingresa la cantidad a registrar:")
    cantidad = int(input())
    
    ##############################################
    # FUNCIÓN 2
    # Registrar movimiento y actualizar inventario. recibe product_id, cantidad, tipo_movimiento
    ################################################
    resultado = registrar_movimiento(product_id=producto["product_id"], cantidad=cantidad, tipo_movimiento=tipo_movimiento)
    print(resultado)
    
# Final del flujo principal


########################################################
# FUNCION 3
# Obtener dataframe del historial de movimientos
########################################################
from src.backend.obtener_historial import obtener_historial

df_historial = obtener_historial()
print(df_historial)