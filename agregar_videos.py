#!/usr/bin/env python3
"""
Script para agregar videos iniciales a la base de datos
Extrae información desde YouTube usando la API
"""
import sqlite3
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

# Configuración
DB_PATH = 'videos.db'
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', 'TU_API_KEY_AQUI')

def get_video_info(youtube_id):
    """Obtener información de un video desde YouTube API"""
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
        request = youtube.videos().list(
            part='snippet,contentDetails',
            id=youtube_id
        )
        response = request.execute()
        
        if not response['items']:
            return None
        
        item = response['items'][0]
        snippet = item['snippet']
        
        return {
            'youtube_id': youtube_id,
            'titulo': snippet['title'],
            'canal': snippet['channelTitle'],
            'descripcion': snippet['description'][:500],  # Limitar descripción
            'thumbnail': snippet['thumbnails']['high']['url'],
            'duracion': item['contentDetails']['duration']
        }
    except HttpError as e:
        print(f"Error API: {e}")
        return None

def agregar_video(youtube_id, categoria, conn):
    """Agregar un video a la base de datos"""
    info = get_video_info(youtube_id)
    
    if not info:
        print(f"❌ No se pudo obtener info del video: {youtube_id}")
        return False
    
    try:
        conn.execute('''
            INSERT INTO videos (youtube_id, titulo, canal, thumbnail, duracion, descripcion, categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            info['youtube_id'],
            info['titulo'],
            info['canal'],
            info['thumbnail'],
            info['duracion'],
            info['descripcion'],
            categoria
        ))
        conn.commit()
        print(f"✅ Agregado: {info['titulo']}")
        return True
    except sqlite3.IntegrityError:
        print(f"⚠️  Ya existe: {info['titulo']}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Lista de 80 videos iniciales
VIDEOS_INICIALES = {
    'Religion': [
        'v4QcFJEFPZE',  # Santo Rosario - EWTN
        'Jx7YBFzYsz4',  # Misa de Hoy - EWTN
        # Agregar más IDs de videos...
    ],
    'Recetas': [
        'q8qZnLQ4FJg',  # Pozole Rojo - Jauja Cocina
        'WjHvPTT1qfA',  # Tamales - Jauja Cocina
        # Agregar más IDs de videos...
    ],
    'Plantas': [
        'XqW2LTUqLJs',  # Cuidado de Suculentas
        # Agregar más IDs de videos...
    ],
    'Musica': [
        'c7VJaqqDVzY',  # Vicente Fernández
        # Agregar más IDs de videos...
    ]
}

def main():
    """Agregar todos los videos iniciales"""
    conn = sqlite3.connect(DB_PATH)
    
    total_agregados = 0
    
    for categoria, videos in VIDEOS_INICIALES.items():
        print(f"\n📂 Categoría: {categoria}")
        print("=" * 50)
        
        for youtube_id in videos:
            if agregar_video(youtube_id, categoria, conn):
                total_agregados += 1
    
    conn.close()
    
    print(f"\n🎉 Total de videos agregados: {total_agregados}")

if __name__ == '__main__':
    main()
