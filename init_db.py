#!/usr/bin/env python3
"""
Inicializar base de datos para YouTube Seguro
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = 'videos.db'

def init_database():
    """Crear todas las tablas necesarias"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabla de videos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            youtube_id TEXT UNIQUE NOT NULL,
            titulo TEXT NOT NULL,
            canal TEXT,
            thumbnail TEXT,
            duracion TEXT,
            descripcion TEXT,
            categoria TEXT,
            fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    ''')
    
    # Tabla de palabras bloqueadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS palabras_bloqueadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palabra TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Insertar categorías por defecto
    categorias = [
        (1, 'Religion', '⛪', '#9C27B0'),
        (2, 'Recetas', '🍳', '#FF5722'),
        (3, 'Plantas', '🌿', '#4CAF50'),
        (4, 'Musica', '🎵', '#2196F3')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO categorias (id, nombre, icono, color) 
        VALUES (?, ?, ?, ?)
    ''', categorias)
    
    # Insertar palabras bloqueadas
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
            INSERT OR IGNORE INTO palabras_bloqueadas (palabra) 
            VALUES (?)
        ''', (palabra,))
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_database()
