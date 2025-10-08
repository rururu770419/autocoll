# ng_routes.py - NG項目管理用API

from flask import Blueprint, jsonify, request
from database.connection import get_db

ng_bp = Blueprint('ng_api', __name__, url_prefix='/api')

# ==========================================
# NGエリア管理API
# ==========================================

@ng_bp.route('/ng-areas', methods=['GET'])
def get_ng_areas():
    """NGエリア一覧取得"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT ng_area_id, area_name, display_order
            FROM ng_areas
            WHERE is_active = TRUE
            ORDER BY display_order, area_name
        """)
        areas = cursor.fetchall()
        return jsonify({'success': True, 'areas': areas})
    except Exception as e:
        print(f"NGエリア取得エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ng_bp.route('/ng-areas', methods=['POST'])
def create_ng_area():
    """NGエリア新規作成"""
    try:
        data = request.get_json()
        area_name = data.get('area_name', '').strip()
        
        if not area_name:
            return jsonify({'success': False, 'error': 'エリア名を入力してください'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # 重複チェック
        cursor.execute("""
            SELECT ng_area_id FROM ng_areas
            WHERE area_name = %s AND is_active = TRUE
        """, (area_name,))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'このエリアは既に登録されています'}), 400
        
        # 挿入
        cursor.execute("""
            INSERT INTO ng_areas (area_name, display_order)
            VALUES (%s, COALESCE((SELECT MAX(display_order) + 1 FROM ng_areas), 1))
            RETURNING ng_area_id
        """, (area_name,))
        
        new_id = cursor.fetchone()['ng_area_id']
        db.commit()
        
        return jsonify({'success': True, 'ng_area_id': new_id})
    except Exception as e:
        print(f"NGエリア作成エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ng_bp.route('/ng-areas/<int:area_id>', methods=['PUT'])
def update_ng_area(area_id):
    """NGエリア更新"""
    try:
        data = request.get_json()
        area_name = data.get('area_name', '').strip()
        
        if not area_name:
            return jsonify({'success': False, 'error': 'エリア名を入力してください'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # 重複チェック（自分以外）
        cursor.execute("""
            SELECT ng_area_id FROM ng_areas
            WHERE area_name = %s AND ng_area_id != %s AND is_active = TRUE
        """, (area_name, area_id))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'このエリアは既に登録されています'}), 400
        
        # 更新
        cursor.execute("""
            UPDATE ng_areas
            SET area_name = %s, updated_at = CURRENT_TIMESTAMP
            WHERE ng_area_id = %s
        """, (area_name, area_id))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"NGエリア更新エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ng_bp.route('/ng-areas/<int:area_id>', methods=['DELETE'])
def delete_ng_area(area_id):
    """NGエリア削除（論理削除）"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 紐付けを削除
        cursor.execute("DELETE FROM cast_ng_custom_areas WHERE ng_area_id = %s", (area_id,))
        
        # 論理削除
        cursor.execute("""
            UPDATE ng_areas
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE ng_area_id = %s
        """, (area_id,))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"NGエリア削除エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# 年齢NG管理API
# ==========================================

@ng_bp.route('/ng-ages', methods=['GET'])
def get_ng_ages():
    """年齢NG一覧取得"""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT ng_age_id, pattern_name, description, display_order
            FROM ng_age_patterns
            WHERE is_active = TRUE
            ORDER BY display_order, pattern_name
        """)
        ages = cursor.fetchall()
        return jsonify({'success': True, 'ages': ages})
    except Exception as e:
        print(f"年齢NG取得エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ng_bp.route('/ng-ages', methods=['POST'])
def create_ng_age():
    """年齢NG新規作成"""
    try:
        data = request.get_json()
        pattern_name = data.get('pattern_name', '').strip()
        description = data.get('description', '').strip()
        
        if not pattern_name:
            return jsonify({'success': False, 'error': 'パターン名を入力してください'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # 重複チェック
        cursor.execute("""
            SELECT ng_age_id FROM ng_age_patterns
            WHERE pattern_name = %s AND is_active = TRUE
        """, (pattern_name,))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'このパターンは既に登録されています'}), 400
        
        # 挿入
        cursor.execute("""
            INSERT INTO ng_age_patterns (pattern_name, description, display_order)
            VALUES (%s, %s, COALESCE((SELECT MAX(display_order) + 1 FROM ng_age_patterns), 1))
            RETURNING ng_age_id
        """, (pattern_name, description))
        
        new_id = cursor.fetchone()['ng_age_id']
        db.commit()
        
        return jsonify({'success': True, 'ng_age_id': new_id})
    except Exception as e:
        print(f"年齢NG作成エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ng_bp.route('/ng-ages/<int:age_id>', methods=['PUT'])
def update_ng_age(age_id):
    """年齢NG更新"""
    try:
        data = request.get_json()
        pattern_name = data.get('pattern_name', '').strip()
        description = data.get('description', '').strip()
        
        if not pattern_name:
            return jsonify({'success': False, 'error': 'パターン名を入力してください'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        # 重複チェック（自分以外）
        cursor.execute("""
            SELECT ng_age_id FROM ng_age_patterns
            WHERE pattern_name = %s AND ng_age_id != %s AND is_active = TRUE
        """, (pattern_name, age_id))
        
        if cursor.fetchone():
            return jsonify({'success': False, 'error': 'このパターンは既に登録されています'}), 400
        
        # 更新
        cursor.execute("""
            UPDATE ng_age_patterns
            SET pattern_name = %s, description = %s, updated_at = CURRENT_TIMESTAMP
            WHERE ng_age_id = %s
        """, (pattern_name, description, age_id))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"年齢NG更新エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ng_bp.route('/ng-ages/<int:age_id>', methods=['DELETE'])
def delete_ng_age(age_id):
    """年齢NG削除（論理削除）"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 紐付けを削除
        cursor.execute("DELETE FROM cast_ng_ages WHERE ng_age_id = %s", (age_id,))
        
        # 論理削除
        cursor.execute("""
            UPDATE ng_age_patterns
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE ng_age_id = %s
        """, (age_id,))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"年齢NG削除エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==========================================
# キャスト個別NG設定API
# ==========================================

@ng_bp.route('/cast/<int:cast_id>/ng-settings', methods=['GET'])
def get_cast_ng_settings(cast_id):
    """キャストのNG設定取得"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # NGエリア
        cursor.execute("""
            SELECT ng_area_id FROM cast_ng_custom_areas
            WHERE cast_id = %s
        """, (cast_id,))
        ng_areas = [row['ng_area_id'] for row in cursor.fetchall()]
        
        # 年齢NG
        cursor.execute("""
            SELECT ng_age_id FROM cast_ng_ages
            WHERE cast_id = %s
        """, (cast_id,))
        ng_ages = [row['ng_age_id'] for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'ng_areas': ng_areas,
            'ng_ages': ng_ages
        })
    except Exception as e:
        print(f"キャストNG設定取得エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ng_bp.route('/cast/<int:cast_id>/ng-settings', methods=['POST'])
def update_cast_ng_settings(cast_id):
    """キャストのNG設定更新"""
    try:
        data = request.get_json()
        ng_areas = data.get('ng_areas', [])
        ng_ages = data.get('ng_ages', [])
        
        db = get_db()
        cursor = db.cursor()
        
        # NGエリアの更新
        cursor.execute("DELETE FROM cast_ng_custom_areas WHERE cast_id = %s", (cast_id,))
        for area_id in ng_areas:
            cursor.execute("""
                INSERT INTO cast_ng_custom_areas (cast_id, ng_area_id)
                VALUES (%s, %s)
            """, (cast_id, area_id))
        
        # 年齢NGの更新
        cursor.execute("DELETE FROM cast_ng_ages WHERE cast_id = %s", (cast_id,))
        for age_id in ng_ages:
            cursor.execute("""
                INSERT INTO cast_ng_ages (cast_id, ng_age_id)
                VALUES (%s, %s)
            """, (cast_id, age_id))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"キャストNG設定更新エラー: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500