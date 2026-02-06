import psycopg2
import os

DATABASE_URL = os.environ.get('DATABASE_URL')

def init_database():
    """Crear todas las tablas necesarias en PostgreSQL"""
    
    print("🔄 Conectando a PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("📊 Creando tablas...")
    
    # Tabla de videos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id SERIAL PRIMARY KEY,
            youtube_id TEXT UNIQUE NOT NULL,
            titulo TEXT NOT NULL,
            canal TEXT,
            thumbnail TEXT,
            duracion TEXT,
            descripcion TEXT,
            categoria TEXT,
            fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            vistas INTEGER DEFAULT 0,
            orden INTEGER DEFAULT 0
        )
    ''')
    
    # Tabla de categorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL,
            icono TEXT,
            color TEXT
        )
    ''')
    
    # Tabla de historial
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id SERIAL PRIMARY KEY,
            video_id INTEGER REFERENCES videos(id) ON DELETE CASCADE,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de palabras bloqueadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS palabras_bloqueadas (
            id SERIAL PRIMARY KEY,
            palabra TEXT UNIQUE NOT NULL
        )
    ''')
    
    print("✅ Tablas creadas")
    
    # Insertar categorías por defecto
    print("📝 Insertando categorías...")
    categorias = [
        (1, 'Religion', '⛪', '#9C27B0'),
        (2, 'Recetas', '🍳', '#FF5722'),
        (3, 'Plantas', '🌿', '#4CAF50'),
        (4, 'Musica', '🎵', '#2196F3')
    ]
    
    for cat in categorias:
        cursor.execute('''
            INSERT INTO categorias (id, nombre, icono, color) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        ''', cat)
    
    # Insertar palabras bloqueadas
    print("🚫 Insertando palabras bloqueadas...")
    palabras = [
        'brujeria', 'brujería', 'brujo', 'bruja',
        'hechizo', 'hechicería', 'hechiceria',
        'amarre', 'amarres', 'magia negra',
        'tarot', 'lectura de cartas', 'carta astral',
        'mal de ojo', 'ojo turco', 'limpia', 'limpias',
        'energía negativa', 'energias negativas', 'chakras',
        'horoscopo', 'horóscopo', 'prediccion', 'predicción',
        'ritual', 'rituales', 'hechizar',
        'santeria', 'santería', 'vudú', 'vudu',
        'espiritismo', 'médium', 'medium', 'ouija',
        'curandero', 'curandera', 'embrujar'
    ]
    
    for palabra in palabras:
        cursor.execute('''
            INSERT INTO palabras_bloqueadas (palabra) 
            VALUES (%s)
            ON CONFLICT (palabra) DO NOTHING
        ''', (palabra,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Base de datos PostgreSQL inicializada correctamente")
    print("🎉 Listo para usar!")

if __name__ == '__main__':
    init_database()
