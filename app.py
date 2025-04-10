from flask import Flask, render_template, request, redirect, flash, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'hola1234'  # Cambia esto a una clave secreta más segura en producción

API_URL = "http://127.0.0.1:8000"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/productos')
def productos():
    try:
        response = requests.get(f"{API_URL}/productos")
        productos = response.json()
    except:
        productos = []
    return render_template('productos.html', productos=productos)

@app.route('/pedidos')
def pedidos():
    try:
        response = requests.get(f"{API_URL}/pedidos")
        pedidos = response.json()
    except:
        pedidos = []
    return render_template('pedidos.html', pedidos=pedidos)

@app.route('/empleados')
def empleados():
    try:
        response = requests.get(f"{API_URL}/empleados")
        empleados = response.json()
    except:
        empleados = []
    return render_template('empleados.html', empleados=empleados)


@app.route('/proveedores')
def proveedores():
    try:
        response = requests.get(f"{API_URL}/proveedores")
        proveedores = response.json()
    except:
        proveedores = []
    return render_template('proveedores_pedidos.html', proveedores=proveedores)


@app.route('/clientes')
def clientes():
    try:
        response = requests.get(f"{API_URL}/clientes")
        clientes = response.json()

        # Imprimir los datos para ver la estructura
        print("📦 CLIENTES DESDE API:", clientes)

    except Exception as e:
        print("❌ Error al obtener clientes:", e)
        clientes = []
    
    return render_template('clientes.html', clientes=clientes)




@app.route('/pos')
def pos():
    try:
        response = requests.get(f"{API_URL}/productos")
        productos = response.json()
    except:
        productos = []
    return render_template('POS.html', productos=productos)

@app.route('/inventario')
def inventario():
    try:
        # Obtener el token del header o de la sesión (esto tendría que implementarse)
        token = request.headers.get('Authorization')
        
        if not token:
            flash('Debe iniciar sesión para acceder a esta página', 'warning')
            return redirect('/')
            
        # Usar el token JWT para hacer la solicitud con autorización
        headers = {
            'Authorization': token if token.startswith('Bearer ') else f'Bearer {token}',
            'Accept': 'application/json'
        }

        # Realizar la solicitud GET a la API de movimientos de inventario
        response = requests.get(f"{API_URL}/inventario/movimientos", headers=headers)
        
        if response.status_code == 401:
            flash('Sesión expirada. Por favor inicie sesión nuevamente.', 'warning')
            return redirect('/')
            
        inventarios = response.json()  # Obtener los datos en formato JSON
        
        # Ordenar los datos por id_movimiento en orden ascendente (de primero a último)
        inventarios = sorted(inventarios, key=lambda x: x['id_movimiento'], reverse=False)

    except Exception as e:
        print(f"Error al obtener inventario: {e}")
        flash(f"Error: {str(e)}", "danger")
        inventarios = []  # Si hay algún error, asignar una lista vacía

    # Renderizar la plantilla 'Inventario.html' y pasar los datos de inventarios
    return render_template('Inventario.html', inventarios=inventarios)


if __name__ == '__main__':
    app.run(debug=True, port=15000)