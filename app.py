from flask import Flask, render_template, request, redirect, flash
import requests
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'hola1234'  # Cambia esto a una clave secreta más segura en producción


API_URL = "http://127.0.0.1:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjIiLCJleHAiOjE3NDQzMTI5Mjd9.6s7iUb35N-9gwazkQkQiWIFhi232YJBQW_TNnA5sjJQ"

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
        response = requests.get(f"{API_URL}/proveedores")
        clientes = response.json()

        # Imprimir los datos para ver la estructura
        print("📦 CLIENTES DESDE API:", clientes)

    except Exception as e:
        print("❌ Error al obtener clientes:", e)
        clientes = []
    
    return render_template('clientes.html', clientes=clientes)


@app.route('/clientes/<int:cliente_id>/ver')
def ver_cliente(cliente_id):
    try:
        # Suponiendo que tu API requiere un token para acceder
        headers = {
            'Authorization': f'Bearer {TOKEN}',  # Usar el token JWT
            'Accept': 'application/json'
        }

        response = requests.get(f"{API_URL}/clientes/{cliente_id}", headers=headers)
        cliente = response.json()  # Obtener los datos en formato JSON
    except Exception as e:
        print(f"Error al obtener el cliente: {e}")
        cliente = None  # Si hay un error, asignar un valor None

    # Renderizar la plantilla 'ver_cliente.html' y pasar los datos del cliente
    return render_template('ver_cliente.html', cliente=cliente)

@app.route('/clientes/<int:id_cliente>/editar', methods=['GET', 'POST'])
def editar_cliente(id_cliente):
    try:
        # Incluir el token en las cabeceras para la solicitud GET
        headers = {
            'Authorization': f'Bearer {TOKEN}',  # Agregar el token JWT en la cabecera
            'Accept': 'application/json'
        }

        # Obtener los detalles actuales del cliente
        response = requests.get(f"{API_URL}/clientes/{id_cliente}", headers=headers)
        if response.status_code == 200:
            cliente = response.json()
        else:
            cliente = {}
            print(f"Error al obtener cliente: {response.status_code}")

        if request.method == 'POST':
            # Obtener los datos del formulario
            nombre = request.form['nombre']
            apellidos = request.form['apellidos']
            telefono = request.form['telefono']
            email = request.form['email']
            # Otros campos que quieres actualizar...

            # Realizar la actualización del cliente mediante un PUT
            update_data = {
                'nombre': nombre,
                'apellidos': apellidos,
                'telefono': telefono,
                'email': email,
                # Otros campos
            }

            # Realizar la solicitud PUT con el token en las cabeceras
            response = requests.put(f"{API_URL}/clientes/{id_cliente}", json=update_data, headers=headers)
            if response.status_code == 200:
                flash("Usuario actualizado exitosamente.", "success")  # Mostrar mensaje de éxito
                return redirect(f'/clientes/{id_cliente}')  # Redirigir a la página de detalles del cliente
            else:
                # Manejar error de la API
                flash("Error al actualizar el cliente.", "danger")  # Mostrar mensaje de error
                cliente = response.json()  # Mantener los datos previos en caso de error

    except Exception as e:
        print(f"Error: {e}")
        cliente = {}

    return render_template('editar_cliente.html', cliente=cliente)


@app.route('/clientes/<int:id_cliente>/eliminar', methods=['DELETE'])
def eliminar_cliente(id_cliente):
    try:
        token = request.headers.get('Authorization')  # Obtener el token de las cabeceras
        if not token:
            flash('Token de autenticación no encontrado', 'danger')
            return redirect('/clientes')

        response = requests.delete(f"{API_URL}/clientes/{id_cliente}", headers={'Authorization': token})

        if response.status_code == 204:
            flash('Cliente eliminado con éxito', 'success')
        else:
            flash(f'Error al eliminar cliente: {response.status_code}', 'danger')

    except Exception as e:
        flash(f'Hubo un error al intentar eliminar el cliente: {e}', 'danger')

    return redirect('/clientes')



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
        # Usar el token JWT para hacer la solicitud con autorización
        headers = {
            'Authorization': f'Bearer {TOKEN}',
            'Accept': 'application/json'
        }

        # Realizar la solicitud GET a la API de movimientos de inventario
        response = requests.get(f"{API_URL}/inventario/movimientos", headers=headers)
        inventarios = response.json()  # Obtener los datos en formato JSON
        
        # Ordenar los datos por id_movimiento en orden ascendente (de primero a último)
        inventarios = sorted(inventarios, key=lambda x: x['id_movimiento'], reverse=False)

    except Exception as e:
        print(f"Error al obtener inventario: {e}")
        inventarios = []  # Si hay algún error, asignar una lista vacía

    # Renderizar la plantilla 'Inventario.html' y pasar los datos de inventarios
    return render_template('Inventario.html', inventarios=inventarios)


if __name__ == '__main__':
    app.run(debug=True, port=15000)
