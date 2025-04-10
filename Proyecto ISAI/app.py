
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

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
        response = requests.get("http://127.0.0.1:8000/clientes")
        clientes = response.json()

        # Mostramos cada objeto recibido para revisar su formato
        print("📦 CLIENTES DESDE API:")
        for c in clientes:
            print(" ->", c, type(c))
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

if __name__ == '__main__':
    app.run(debug=True, port=15000)
