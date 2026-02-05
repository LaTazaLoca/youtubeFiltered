from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DB_PATH = 'videos.db'

def get_db():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def home():
    """Endpoint de verificación"""
    return jsonify({
        'status': 'online',
        'service': 'YouTube Seguro API',
        'version': '1.0'
    })

@app.route('/videos', methods=['GET'])
def get_videos():
    """Obtener todos los videos"""
    try:
        conn = get_db()
        videos = conn.execute('''
            SELECT * FROM videos 
            ORDER BY orden DESC, fecha_agregado DESC
        ''').fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'videos': [dict(v) for v in videos]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/videos/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Obtener un video específico"""
    try:
        conn = get_db()
        video = conn.execute(
            'SELECT * FROM videos WHERE id = ?', 
            (video_id,)
        ).fetchone()
        conn.close()
        
        if video:
            return jsonify({
                'status': 'success',
                'video': dict(video)
            })
        return jsonify({'status': 'error', 'message': 'Video no encontrado'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/videos/categoria/<categoria>', methods=['GET'])
def get_videos_by_category(categoria):
    """Obtener videos por categoría"""
    try:
        conn = get_db()
        videos = conn.execute('''
            SELECT * FROM videos 
            WHERE LOWER(categoria) = LOWER(?)
            ORDER BY vistas DESC, fecha_agregado DESC
        ''', (categoria,)).fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'categoria': categoria,
            'videos': [dict(v) for v in videos]
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
        videos = conn.execute('''
            SELECT * FROM videos 
            WHERE titulo LIKE ? OR descripcion LIKE ? OR canal LIKE ?
            ORDER BY vistas DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'query': query,
            'resultados': len(videos),
            'videos': [dict(v) for v in videos]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/view/<int:video_id>', methods=['POST'])
def register_view(video_id):
    """Registrar una vista de video"""
    try:
        conn = get_db()
        
        # Verificar que el video existe
        video = conn.execute('SELECT id FROM videos WHERE id = ?', (video_id,)).fetchone()
        if not video:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Video no encontrado'}), 404
        
        # Incrementar vistas
        conn.execute('UPDATE videos SET vistas = vistas + 1 WHERE id = ?', (video_id,))
        
        # Registrar en historial
        conn.execute('INSERT INTO historial (video_id) VALUES (?)', (video_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Vista registrada'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas generales"""
    try:
        conn = get_db()
        
        total_videos = conn.execute('SELECT COUNT(*) as count FROM videos').fetchone()['count']
        total_vistas = conn.execute('SELECT SUM(vistas) as total FROM videos').fetchone()['total']
        mas_visto = conn.execute('''
            SELECT titulo, vistas, canal FROM videos 
            ORDER BY vistas DESC LIMIT 1
        ''').fetchone()
        
        # Vistas por categoría
        vistas_categoria = conn.execute('''
            SELECT categoria, COUNT(*) as videos, SUM(vistas) as vistas
            FROM videos
            GROUP BY categoria
        ''').fetchall()
        
        # Videos vistos hoy
        hoy = datetime.now().strftime('%Y-%m-%d')
        vistas_hoy = conn.execute('''
            SELECT COUNT(*) as count FROM historial
            WHERE DATE(fecha) = ?
        ''', (hoy,)).fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_videos': total_videos,
                'total_vistas': total_vistas or 0,
                'vistas_hoy': vistas_hoy,
                'video_mas_visto': dict(mas_visto) if mas_visto else None,
                'por_categoria': [dict(c) for c in vistas_categoria]
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/categorias', methods=['GET'])
def get_categorias():
    """Obtener todas las categorías"""
    try:
        conn = get_db()
        categorias = conn.execute('SELECT * FROM categorias ORDER BY nombre').fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'categorias': [dict(c) for c in categorias]
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
        
        # Verificar si el video ya existe
        exists = conn.execute(
            'SELECT id FROM videos WHERE youtube_id = ?', 
            (data['youtube_id'],)
        ).fetchone()
        
        if exists:
            conn.close()
            return jsonify({
                'status': 'error', 
                'message': 'Este video ya está agregado'
            }), 409
        
        # Insertar video
        cursor = conn.execute('''
            INSERT INTO videos (youtube_id, titulo, canal, thumbnail, duracion, descripcion, categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['youtube_id'],
            data['titulo'],
            data.get('canal', ''),
            data.get('thumbnail', ''),
            data.get('duracion', ''),
            data.get('descripcion', ''),
            data['categoria']
        ))
        
        conn.commit()
        video_id = cursor.lastrowid
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
        conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        conn.commit()
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
