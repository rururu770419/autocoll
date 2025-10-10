"""
お知らせ管理 Blueprint
管理者がお知らせを作成・編集・削除する機能
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from database.connection import get_db
from database.cast_mypage_db import (
    get_cast_notices, 
    get_cast_notice_by_id,
    create_cast_notice,
    update_cast_notice,
    delete_cast_notice
)

notice_admin_bp = Blueprint('notice_admin', __name__, url_prefix='/nagano/admin/notices')

# 画像アップロード設定
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads/notices'

def allowed_file(filename):
    """許可された拡張子かチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """アップロードフォルダが存在することを確認"""
    upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        print(f"アップロードフォルダを作成しました: {upload_path}")
    else:
        print(f"アップロードフォルダ確認OK: {upload_path}")
    return upload_path

@notice_admin_bp.route('/')
def list_notices():
    """お知らせ一覧（管理者用）"""
    db = get_db()
    try:
        # すべてのお知らせを取得（公開・非公開問わず）
        cursor = db.cursor()
        cursor.execute("""
            SELECT notice_id, title, content, is_pinned, is_published, 
                   published_at, created_at, updated_at
            FROM cast_notices
            WHERE store_id = 1
            ORDER BY is_pinned DESC, published_at DESC, notice_id DESC
        """)
        
        notices = []
        for row in cursor.fetchall():
            notices.append({
                'notice_id': row['notice_id'],
                'title': row['title'],
                'content': row['content'],
                'is_pinned': row['is_pinned'],
                'is_published': row['is_published'],
                'published_at': row['published_at'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return render_template('admin/notice_list.html', notices=notices)
    finally:
        db.close()

@notice_admin_bp.route('/new', methods=['GET', 'POST'])
def new_notice():
    """お知らせ新規作成"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_pinned = request.form.get('is_pinned') == 'on'
        is_published = request.form.get('is_published') == 'on'
        published_at = request.form.get('published_at', '')
        
        # バリデーション
        if not title:
            flash('タイトルは必須です', 'error')
            return render_template('admin/notice_form.html', 
                                 notice=None, 
                                 form_data=request.form)
        
        if not content:
            flash('本文は必須です', 'error')
            return render_template('admin/notice_form.html', 
                                 notice=None, 
                                 form_data=request.form)
        
        # 公開日時の処理
        if published_at:
            try:
                published_at = datetime.fromisoformat(published_at)
            except ValueError:
                published_at = datetime.now()
        else:
            published_at = datetime.now()
        
        # データベースに保存
        db = get_db()
        try:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO cast_notices 
                (store_id, title, content, is_pinned, is_published, published_at, created_at, updated_at)
                VALUES (1, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING notice_id
            """, (title, content, is_pinned, is_published, published_at))
            
            notice_id = cursor.fetchone()['notice_id']
            db.commit()
            
            flash('お知らせを作成しました', 'success')
            return redirect(url_for('notice_admin.list_notices'))
        except Exception as e:
            db.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'error')
            return render_template('admin/notice_form.html', 
                                 notice=None, 
                                 form_data=request.form)
        finally:
            db.close()
    
    # GET: 新規作成フォーム表示
    return render_template('admin/notice_form.html', notice=None)

@notice_admin_bp.route('/edit/<int:notice_id>', methods=['GET', 'POST'])
def edit_notice(notice_id):
    """お知らせ編集"""
    db = get_db()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_pinned = request.form.get('is_pinned') == 'on'
        is_published = request.form.get('is_published') == 'on'
        published_at = request.form.get('published_at', '')
        
        # バリデーション
        if not title:
            flash('タイトルは必須です', 'error')
            notice = get_cast_notice_by_id(db, notice_id)
            return render_template('admin/notice_form.html', 
                                 notice=notice, 
                                 form_data=request.form)
        
        if not content:
            flash('本文は必須です', 'error')
            notice = get_cast_notice_by_id(db, notice_id)
            return render_template('admin/notice_form.html', 
                                 notice=notice, 
                                 form_data=request.form)
        
        # 公開日時の処理
        if published_at:
            try:
                published_at = datetime.fromisoformat(published_at)
            except ValueError:
                published_at = None
        else:
            published_at = None
        
        # データベース更新
        try:
            cursor = db.cursor()
            
            if published_at:
                cursor.execute("""
                    UPDATE cast_notices 
                    SET title = %s, content = %s, is_pinned = %s, 
                        is_published = %s, published_at = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE notice_id = %s
                """, (title, content, is_pinned, is_published, published_at, notice_id))
            else:
                cursor.execute("""
                    UPDATE cast_notices 
                    SET title = %s, content = %s, is_pinned = %s, 
                        is_published = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE notice_id = %s
                """, (title, content, is_pinned, is_published, notice_id))
            
            db.commit()
            
            flash('お知らせを更新しました', 'success')
            return redirect(url_for('notice_admin.list_notices'))
        except Exception as e:
            db.rollback()
            flash(f'エラーが発生しました: {str(e)}', 'error')
            notice = get_cast_notice_by_id(db, notice_id)
            return render_template('admin/notice_form.html', 
                                 notice=notice, 
                                 form_data=request.form)
        finally:
            db.close()
    
    # GET: 編集フォーム表示
    try:
        notice = get_cast_notice_by_id(db, notice_id)
        if not notice:
            flash('お知らせが見つかりません', 'error')
            return redirect(url_for('notice_admin.list_notices'))
        
        return render_template('admin/notice_form.html', notice=notice)
    finally:
        db.close()

@notice_admin_bp.route('/delete/<int:notice_id>', methods=['POST'])
def delete_notice_route(notice_id):
    """お知らせ削除"""
    db = get_db()
    try:
        result = delete_cast_notice(db, notice_id)
        if result:
            flash('お知らせを削除しました', 'success')
        else:
            flash('お知らせの削除に失敗しました', 'error')
    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'error')
    finally:
        db.close()
    
    return redirect(url_for('notice_admin.list_notices'))

@notice_admin_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """TinyMCE用の画像アップロード"""
    try:
        if 'file' not in request.files:
            return {'error': 'ファイルが選択されていません'}, 400
        
        file = request.files['file']
        
        if file.filename == '':
            return {'error': 'ファイル名が空です'}, 400
        
        if file and allowed_file(file.filename):
            # ファイル名を安全にする
            filename = secure_filename(file.filename)
            # タイムスタンプを追加してユニークにする
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            
            # アップロードフォルダを確認・作成
            upload_path = ensure_upload_folder()
            
            # ファイルを保存
            filepath = os.path.join(upload_path, filename)
            file.save(filepath)
            
            # URLを返す（TinyMCE用）
            file_url = url_for('static', filename=f'uploads/notices/{filename}')
            
            print(f"画像アップロード成功: {file_url}")
            return {'location': file_url}, 200
        
        return {'error': '許可されていないファイル形式です'}, 400
        
    except Exception as e:
        print(f"画像アップロードエラー: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'アップロード中にエラーが発生しました: {str(e)}'}, 500