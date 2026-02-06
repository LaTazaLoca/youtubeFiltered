from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Obtener URL de la base de datos desde variable de entorno
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """Obtener conexión a PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/', methods=['GET'])
def home():
    """Endpoint de verificación"""
    return jsonify({
        'status': 'online',
        'service': 'YouTube Seguro API',
        'version': '1.0',
        'database': 'PostgreSQL'
    })

@app.route('/videos', methods=['GET'])
def get_videos():
    """Obtener todos los videos"""
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT * FROM videos 
            ORDER BY orden DESC, fecha_agregado DESC
        ''')
        videos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'videos': videos
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Obtener un video específico"""
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM videos WHERE id = %s', (video_id,))
        video = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if video:
            return jsonify({
                'status': 'success',
                'video': video
            })
        return jsonify({'status': 'error', 'message': 'Video no encontrado'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/videos/categoria/<categoria>', methods=['GET'])
def get_videos_by_category(categoria):
    """Obtener videos por categoría"""
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT * FROM videos 
            WHERE LOWER(categoria) = LOWER(%s)
            ORDER BY vistas DESC, fecha_agregado DESC
        ''', (categoria,))
        videos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'categoria': categoria,
            'videos': videos
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_videos():
    """Buscar videos"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'status': 'error', 'message': 'Query parameter required'}), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT * FROM videos 
            WHERE titulo ILIKE %s OR descripcion ILIKE %s OR canal ILIKE %s
            ORDER BY vistas DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        videos = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'query': query,
            'resultados': len(videos),
            'videos': videos
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/view/<int:video_id>', methods=['POST'])
def register_view(video_id):
    """Registrar una vista de video"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verificar que el video existe
        cursor.execute('SELECT id FROM videos WHERE id = %s', (video_id,))
        video = cursor.fetchone()
        
        if not video:
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Video no encontrado'}), 404
        
        # Incrementar vistas
        cursor.execute('UPDATE videos SET vistas = vistas + 1 WHERE id = %s', (video_id,))
        
        # Registrar en historial
        cursor.execute('INSERT INTO historial (video_id) VALUES (%s)', (video_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Vista registrada'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas generales"""
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('SELECT COUNT(*) as count FROM videos')
        total_videos = cursor.fetchone()['count']
        
        cursor.execute('SELECT COALESCE(SUM(vistas), 0) as total FROM videos')
        total_vistas = cursor.fetchone()['total']
        
        cursor.execute('SELECT titulo, vistas, canal FROM videos ORDER BY vistas DESC LIMIT 1')
        mas_visto = cursor.fetchone()
        
        cursor.execute('''
            SELECT categoria, COUNT(*) as videos, COALESCE(SUM(vistas), 0) as vistas
            FROM videos
            GROUP BY categoria
        ''')
        vistas_categoria = cursor.fetchall()
        
        # Videos vistos hoy
        cursor.execute('''
            SELECT COUNT(*) as count FROM historial
            WHERE DATE(fecha) = CURRENT_DATE
        ''')
        vistas_hoy = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_videos': total_videos,
                'total_vistas': total_vistas,
                'vistas_hoy': vistas_hoy,
                'video_mas_visto': mas_visto,
                'por_categoria': vistas_categoria
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/categorias', methods=['GET'])
def get_categorias():
    """Obtener todas las categorías"""
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM categorias ORDER BY nombre')
        categorias = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'categorias': categorias
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/videos', methods=['POST'])
def add_video():
    """Agregar un nuevo video (admin)"""
    data = request.json
    
    required_fields = ['youtube_id', 'titulo', 'categoria']
    if not all(field in data for field in required_fields):
        return jsonify({
            'status': 'error', 
            'message': 'Campos requeridos: youtube_id, titulo, categoria'
        }), 400
    
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verificar si el video ya existe
        cursor.execute('SELECT id FROM videos WHERE youtube_id = %s', (data['youtube_id'],))
        exists = cursor.fetchone()
        
        if exists:
            cursor.close()
            conn.close()
            return jsonify({
                'status': 'error', 
                'message': 'Este video ya está agregado'
            }), 409
        
        # Insertar video
        cursor.execute('''
            INSERT INTO videos (youtube_id, titulo, canal, thumbnail, duracion, descripcion, categoria)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            data['youtube_id'],
            data['titulo'],
            data.get('canal', ''),
            data.get('thumbnail', ''),
            data.get('duracion', ''),
            data.get('descripcion', ''),
            data['categoria']
        ))
        
        video_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Video agregado correctamente',
            'video_id': video_id
        }), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/videos/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Eliminar un video (admin)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM videos WHERE id = %s', (video_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Video eliminado correctamente'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
