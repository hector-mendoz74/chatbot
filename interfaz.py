import tkinter as tk
from tkinter import scrolledtext
import spacy
import json
import os
from difflib import SequenceMatcher
from PIL import Image, ImageTk

#Variable del presupuesto
awaiting_budget = False

# Cargar modelo de lenguaje de spaCy
nlp = spacy.load("es_core_news_sm")

# Cargar base de datos de productos desde JSON
PRODUCTS_FILE = "productos.json"

if not os.path.exists(PRODUCTS_FILE):
    # Crear archivo JSON de ejemplo si no existe
    sample_data = [
        {"nombre": "Vestido negro", "talla": "M", "color": "negro", "precio": 49.99},
        {"nombre": "Camiseta blanca", "talla": "L", "color": "blanco", "precio": 19.99},
        {"nombre": "Jeans azul", "talla": "32", "color": "azul", "precio": 39.99},
        {"nombre": "Falda roja", "talla": "S", "color": "rojo", "precio": 29.99}
    ]
    with open(PRODUCTS_FILE, "w") as file:
        json.dump(sample_data, file, indent=4)

with open(PRODUCTS_FILE, "r") as file:
    products = json.load(file)

def detect_kindness(query):
    """Detecta palabras amables y responde con mensajes apropiados."""
    kindness_words = ["gracias", "por favor", "amable", "genial", "excelente"]
    doc = nlp(query.lower())
    if any(token.text in kindness_words for token in doc):
        return True
    return False

def respond_to_kindness():
    """Responde a palabras amables con un mensaje positivo."""
    return "¡Gracias! Estoy aquí para ayudarte con lo que necesites."

def fuzzy_match(query, text, threshold=0.6):
    """Realiza una coincidencia difusa entre dos textos."""
    ratio = SequenceMatcher(None, query, text).ratio()
    return ratio >= threshold

def search_products(query):
    """Busca productos en la base de datos según el query."""
    doc = nlp(query.lower())
    keywords = {token.lemma_ for token in doc if token.is_alpha and not token.is_stop}

    results = []
    for product in products:
        product_text = f"{product['nombre']} {product['talla']} {product['color']} {product['precio']}"
        product_doc = nlp(product_text.lower())
        product_keywords = {token.lemma_ for token in product_doc if token.is_alpha}
        
        # Verificar si hay intersección significativa entre palabras clave o coincidencia difusa
        if keywords & product_keywords or fuzzy_match(query, product_text):
            results.append(product)

    return results

def filter_by_size(query):
    """Filtra productos según la talla mencionada en la consulta del usuario."""
    sizes = ["S", "M", "L", "XL", "U", "32", "34", "26", "27", "28"]  # Lista de tallas comunes
    doc = nlp(query.upper())  # Convertimos la consulta a mayúsculas para coincidir con las tallas
    detected_sizes = {token.text for token in doc if token.text in sizes}
    
    if detected_sizes:
        results = [p for p in products if p['talla'] in detected_sizes]
        if results:
            response = "Estos son los productos disponibles en las tallas consultadas:\n"
            for product in results:
                response += f"- {product['nombre']} (Talla: {product['talla']}, Color: {product['color']}, Precio: ${product['precio']:.2f})\n"
            return response
        return f"No se encontraron productos en las tallas mencionadas: {', '.join(detected_sizes)}."
    return "No se detectaron tallas válidas en tu consulta."


def show_catalog():
    """Muestra todos los productos disponibles en el catálogo."""
    response = "Estos son todos los productos disponibles:\n"
    for product in products:
        response += f"- {product['nombre']} (Talla: {product['talla']}, Color: {product['color']}, Precio: ${product['precio']})\n"
    return response

def respond_to_user():
    """Maneja la interacción con el usuario y muestra resultados."""
    user_input = user_entry.get().strip()
    if not user_input:
        chat_history.insert(tk.END, "Bot: Por favor, ingresa un mensaje antes de enviar.\n")
        return

    chat_history.insert(tk.END, f"Usuario: {user_input}\n")
    user_entry.delete(0, tk.END)

    response = None

    # Detectar tipo de consulta
    if detect_kindness(user_input):
        response = respond_to_kindness()
    elif "catálogo" in user_input.lower() or "catalogo" in user_input.lower():
        response = show_catalog()
    elif "precio" in user_input.lower() or "presupuesto" in user_input.lower():
        # Detectar presupuesto explícito
        detected_budget = extract_budget(user_input)
        if detected_budget:
            response = filter_by_budget(detected_budget)
        else:
            response = "Por favor, proporciona un presupuesto válido en tu consulta. Por ejemplo: 'Mostrarme productos por un precio de no más de $500'."
    elif "talla" in user_input.lower():
        # Detectar talla en la consulta
        sizes = ["S", "M", "L", "XL", "U", "32", "34", "26", "27", "28"]
        detected_size = next((size for size in sizes if size in user_input.upper()), None)
        if detected_size:
            response = filter_by_size(detected_size)
        else:
            response = "Por favor, especifica una talla válida (S, M, L, XL, etc.)."
    else:
        # Consulta general de productos
        results = search_products(user_input)
        if results:
            response = "Aquí tienes los productos que coinciden con tu búsqueda:\n"
            for product in results:
                response += f"- {product['nombre']} (Talla: {product['talla']}, Color: {product['color']}, Precio: ${product['precio']:.2f})\n"
        else:
            response = "Lo siento, no encontré productos que coincidan con tu búsqueda."

    # Mostrar la respuesta generada
    if response:
        root.bind('<Return>', lambda event: respond_to_user())
        chat_history.insert(tk.END, f"Bot: {response}\n")

        

def extract_budget(query):
    """Extrae el presupuesto del texto ingresado por el usuario."""
    words = query.split()
    for word in words:
        word_clean = word.replace("$", "").replace(",", "").strip()
        if word_clean.replace(".", "").isdigit():  # Verifica si es un número válido
            return float(word_clean)
    return None

        
def filter_by_budget(budget):
    """Devuelve los productos que están dentro del presupuesto dado."""
    affordable = [p for p in products if p['precio'] <= budget]
    if affordable:
        response = f"Estos son los productos que están dentro de tu presupuesto (${budget}):\n"
        for product in affordable:
            response += f"- {product['nombre']} (Talla: {product['talla']}, Color: {product['color']}, Precio: ${product['precio']})\n"
        return response
    return f"No se encontraron productos dentro de tu presupuesto de ${budget}."


# Crear interfaz gráfica
root = tk.Tk()
root.title("Chatbot - Tienda de Ropa")
root.geometry("600x600")

# Dimensiones de la ventana
window_width = 600
window_height = 600

# Obtener dimensiones de la pantalla
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calcular la posición para centrar la ventana
x_cordinate = int((screen_width / 2) - (window_width / 2))
y_cordinate = int((screen_height / 2) - (window_height / 2))

# Establecer tamaño y posición de la ventana
root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

# Historial de chat
chat_history = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=25, state='normal')
chat_history.pack(pady=10)
chat_history.insert(tk.END, "Bot: ¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?\n")

# Estilos de la interfaz
root.configure(bg="gray")

# Cambiar colores del historial
chat_history.configure(bg="#e0f7fa", fg="black")

# Entrada del usuario
user_entry = tk.Entry(root, width=60, bg="#bbdefb", fg="black", insertbackground="black")
user_entry.pack(pady=5)

# Cargar el logo
logo_path = "LogoH.png"  # Cambia esta ruta por la ubicación del logo
if os.path.exists(logo_path):
    logo_image = Image.open(logo_path).resize((100, 100))  # Ajusta el tamaño del logo
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(root, image=logo_photo, bg="white")
    logo_label.pack(pady=10)

# Botón de enviar
send_button = tk.Button(root, text="Enviar", command=respond_to_user)
send_button.pack(pady=1)

# Entrada del usuario
user_entry.configure(bg="#bbdefb", fg="black", insertbackground="black")  # Insertbackground cambia el cursor

# Botón de enviar
send_button.configure(bg="#1565c0", fg="white", activebackground="#1e88e5", activeforeground="white")


# Ejecutar la aplicación
root.mainloop()
