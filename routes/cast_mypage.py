# routes/cast_mypage.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from database.connection import get_db, get_store_id
from database.cast_db import (
    verify_cast_password,
    find_cast_by_login_id,
    update_last_login
)
from database.cast_mypage_db import (
    create_cast_session,
    get_cast_session,
    update_cast_session_activity,
    delete_cast_session,
    get_cast_notices,
    get_cast_notice_by_id,
    # ブログ下書き関数
    get_cast_blog_drafts,
    get_cast_blog_draft_by_id,
    create_cast_blog_draft,
    update_cast_blog_draft,
    delete_cast_blog_draft
)
from werkzeug.utils import secure_filename
from datetime import datetime
import os

cast_mypage_bp = Blueprint('cast_mypage', __name__, url_prefix='/<store>/cast')

# 画像アップロード設定
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """許可されたファイル形式かチェック"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """アップロードフォルダの確認・作成"""
    upload_folder = os.path.join('static', 'uploads', 'blog')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder


# ==== ログイン認証デコレータ ====

def login_required(f):
    """キャストログイン必須デコレータ"""
    @wraps(f)
    def decorated_function(store, *args, **kwargs):
        cast_session_id = session.get('cast_session_id')
        
        if not cast_session_id:
            flash('ログインが必要です。', 'error')
            return redirect(url_for('cast_mypage.login', store=store))
        
        # セッション検証
        db = get_db(store)
        cast_session = get_cast_session(db, cast_session_id)
        
        # 辞書形式でアクセス
        if not cast_session or not cast_session['is_active']:
            flash('セッションが無効です。再度ログインしてください。', 'error')
            return redirect(url_for('cast_mypage.login', store=store))
        
        # キャストIDを取得
        cast_id = cast_session['cast_id']
        if not cast_id:
            flash('セッション情報が不正です。再度ログインしてください。', 'error')
            return redirect(url_for('cast_mypage.login', store=store))
        
        # セッションにcast_idを保存（念のため）
        session['cast_id'] = cast_id
        
        # 最終アクティビティ更新
        update_cast_session_activity(db, cast_session_id)
        
        return f(store, *args, **kwargs)
    
    return decorated_function


# ==== ログイン・ログアウト ====

@cast_mypage_bp.route('/login', methods=['GET', 'POST'])
def login(store):
    """キャストログイン"""
    
    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '').strip()
        
        if not login_id or not password:
            flash('ログインIDとパスワードを入力してください。', 'error')
            return render_template('cast/cast_login.html', store=store)
        
        db = get_db(store)
        
        # 認証
        cast_id = verify_cast_password(db, login_id, password)
        
        if not cast_id:
            flash('ログインIDまたはパスワードが間違っています。', 'error')
            return render_template('cast/cast_login.html', store=store)
        
        # セッション作成
        ip_address = request.remote_addr or '0.0.0.0'
        user_agent = request.headers.get('User-Agent', 'Unknown')
        cast_session_id = create_cast_session(db, cast_id, ip_address, user_agent)
        
        if not cast_session_id:
            flash('セッションの作成に失敗しました。', 'error')
            return render_template('cast/cast_login.html', store=store)
        
        # セッションに保存
        session['cast_session_id'] = cast_session_id
        
        # キャスト情報を取得して名前をセッションに保存
        cast = find_cast_by_login_id(db, login_id)
        # 辞書形式でアクセス
        if cast:
            session['cast_name'] = cast['name']
            session['cast_id'] = cast_id
        
        flash(f'ようこそ、{cast["name"]}さん！', 'success')
        return redirect(url_for('cast_mypage.dashboard', store=store))
    
    return render_template('cast/cast_login.html', store=store)


@cast_mypage_bp.route('/logout')
@login_required
def logout(store):
    """キャストログアウト"""
    
    cast_session_id = session.get('cast_session_id')
    
    if cast_session_id:
        db = get_db(store)
        delete_cast_session(db, cast_session_id)
    
    session.clear()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('cast_mypage.login', store=store))


# ==== トップページ（お知らせ一覧） ====

@cast_mypage_bp.route('/dashboard')
@login_required
def dashboard(store):
    """キャストマイページ - トップページ（お知らせ一覧）"""
    
    # ✅ store_id を動的取得
    store_id = get_store_id(store)
    
    db = get_db(store)
    cast_name = session.get('cast_name', 'ゲスト')
    
    # ✅ お知らせ一覧取得（動的 store_id 使用）
    notices = get_cast_notices(db, store_id=store_id, limit=20)
    
    return render_template(
        'cast/cast_dashboard.html',
        store=store,
        cast_name=cast_name,
        notices=notices,
        active_page='dashboard'
    )


# ==== お知らせ詳細 ====

@cast_mypage_bp.route('/notice/<int:notice_id>')
@login_required
def notice_detail(store, notice_id):
    """お知らせ詳細ページ"""
    
    db = get_db(store)
    cast_name = session.get('cast_name', 'ゲスト')
    
    # お知らせ詳細取得
    notice = get_cast_notice_by_id(db, notice_id)
    
    if not notice:
        flash('お知らせが見つかりません。', 'error')
        return redirect(url_for('cast_mypage.dashboard', store=store))
    
    return render_template(
        'cast/cast_notice_detail.html',
        store=store,
        cast_name=cast_name,
        notice=notice
    )


# ==== ブログ下書き一覧 ====

@cast_mypage_bp.route('/blog-drafts')
@login_required
def blog_drafts(store):
    """ブログ下書き一覧"""
    
    db = get_db(store)
    cast_id = session.get('cast_id')
    cast_name = session.get('cast_name', 'ゲスト')
    
    # 下書き一覧取得
    drafts = get_cast_blog_drafts(db, cast_id, limit=50)
    
    print(f"[DEBUG] 下書き一覧取得: {len(drafts)}件")
    
    return render_template(
        'cast/blog_drafts.html',
        store=store,
        cast_name=cast_name,
        drafts=drafts,
        active_page='blog_drafts'
    )


# ==== ブログ下書き作成 ====

@cast_mypage_bp.route('/blog-drafts/new', methods=['GET', 'POST'])
@login_required
def blog_draft_new(store):
    """ブログ下書き新規作成"""
    
    if request.method == 'POST':
        try:
            db = get_db(store)
            cast_id = session.get('cast_id')
            
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            
            print(f"[DEBUG] 新規下書き作成: title='{title[:50]}...', content length={len(content)}")
            
            # タイトルが空の場合はデフォルト値を設定
            if not title:
                title = '(無題)'
            
            # 下書き作成
            draft_id = create_cast_blog_draft(db, cast_id, title, content)
            
            if draft_id:
                print(f"[SUCCESS] ブログ下書き作成成功: draft_id={draft_id}")
                flash('下書きを作成しました。', 'success')
                # 一覧ページにリダイレクト
                return redirect(url_for('cast_mypage.blog_drafts', store=store))
            else:
                print(f"[ERROR] 下書きの作成に失敗")
                flash('下書きの作成に失敗しました。', 'error')
                
        except Exception as e:
            print(f"[ERROR] ブログ下書き作成エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('エラーが発生しました。', 'error')
    
    cast_name = session.get('cast_name', 'ゲスト')
    
    return render_template(
        'cast/blog_draft_form.html',
        store=store,
        cast_name=cast_name,
        draft=None,
        active_page='blog_drafts'
    )


# ==== ブログ下書き編集 ====

@cast_mypage_bp.route('/blog-drafts/<int:draft_id>/edit', methods=['GET', 'POST'])
@login_required
def blog_draft_edit(store, draft_id):
    """ブログ下書き編集"""
    
    try:
        db = get_db(store)
        cast_id = session.get('cast_id')
        
        print(f"[DEBUG] 下書き編集ページアクセス: draft_id={draft_id}, cast_id={cast_id}, method={request.method}")
        
        # 下書き取得
        draft = get_cast_blog_draft_by_id(db, draft_id, cast_id)
        
        # draftがNoneの場合のチェック
        if not draft:
            print(f"[ERROR] 下書きが見つかりません: draft_id={draft_id}")
            flash('下書きが見つかりません。', 'error')
            return redirect(url_for('cast_mypage.blog_drafts', store=store))
        
        # draftが辞書形式であることを確認
        if not isinstance(draft, dict):
            print(f"[ERROR] draftが辞書形式ではありません: type={type(draft)}")
            flash('データの取得に失敗しました。', 'error')
            return redirect(url_for('cast_mypage.blog_drafts', store=store))
        
        print(f"[DEBUG] 下書き取得成功: title='{draft.get('title', 'N/A')}', cast_id={draft.get('cast_id')}")
        
        # アクセス権限チェック
        if draft.get('cast_id') != cast_id:
            print(f"[ERROR] アクセス権限エラー: draft.cast_id={draft.get('cast_id')}, session.cast_id={cast_id}")
            flash('アクセス権限がありません。', 'error')
            return redirect(url_for('cast_mypage.blog_drafts', store=store))
        
        if request.method == 'POST':
            try:
                title = request.form.get('title', '').strip()
                content = request.form.get('content', '').strip()
                
                print(f"[DEBUG] 下書き更新リクエスト: draft_id={draft_id}")
                print(f"[DEBUG] 更新データ: title='{title[:50]}...', content length={len(content)}")
                print(f"[DEBUG] 更新前データ: title='{draft.get('title')}', content length={len(draft.get('content', ''))}")
                
                # タイトルが空の場合はデフォルト値を設定
                if not title:
                    title = '(無題)'
                
                # ★★★ 修正: cast_idを追加 ★★★
                success = update_cast_blog_draft(db, draft_id, cast_id, title, content)
                
                if success:
                    print(f"[SUCCESS] 下書き更新成功: draft_id={draft_id}")
                    
                    # 更新後のデータを確認
                    updated_draft = get_cast_blog_draft_by_id(db, draft_id, cast_id)
                    if updated_draft:
                        print(f"[DEBUG] 更新後データ確認: title='{updated_draft.get('title')}', content length={len(updated_draft.get('content', ''))}")
                    
                    flash('下書きを保存しました。', 'success')
                    # 同じページにリダイレクト（最新データを表示）
                    return redirect(url_for('cast_mypage.blog_draft_edit', store=store, draft_id=draft_id))
                else:
                    print(f"[ERROR] 下書き更新失敗: draft_id={draft_id}")
                    flash('下書きの保存に失敗しました。', 'error')
                    
            except Exception as e:
                print(f"[ERROR] 下書き更新中のエラー: {str(e)}")
                import traceback
                traceback.print_exc()
                flash('エラーが発生しました。', 'error')
        
        cast_name = session.get('cast_name', 'ゲスト')
        
        return render_template(
            'cast/blog_draft_form.html',
            store=store,
            cast_name=cast_name,
            draft=draft,
            active_page='blog_drafts'
        )
        
    except Exception as e:
        print(f"[ERROR] ブログ下書き編集ページエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('エラーが発生しました。', 'error')
        return redirect(url_for('cast_mypage.blog_drafts', store=store))


# ==== ブログ下書き削除 ====

@cast_mypage_bp.route('/blog-drafts/<int:draft_id>/delete', methods=['POST'])
@login_required
def blog_draft_delete(store, draft_id):
    """ブログ下書き削除"""
    
    try:
        db = get_db(store)
        cast_id = session.get('cast_id')
        
        print(f"[DEBUG] 下書き削除リクエスト: draft_id={draft_id}, cast_id={cast_id}")
        
        # 下書き取得
        draft = get_cast_blog_draft_by_id(db, draft_id, cast_id)
        
        if not draft:
            print(f"[ERROR] 削除対象の下書きが見つかりません: draft_id={draft_id}")
            flash('下書きが見つかりません。', 'error')
            return redirect(url_for('cast_mypage.blog_drafts', store=store))
        
        # アクセス権限チェック
        if draft.get('cast_id') != cast_id:
            print(f"[ERROR] 削除権限エラー: draft.cast_id={draft.get('cast_id')}, session.cast_id={cast_id}")
            flash('アクセス権限がありません。', 'error')
            return redirect(url_for('cast_mypage.blog_drafts', store=store))
        
        # 削除実行
        success = delete_cast_blog_draft(db, draft_id, cast_id)
        
        if success:
            print(f"[SUCCESS] 下書き削除成功: draft_id={draft_id}")
            flash('下書きを削除しました。', 'success')
            return redirect(url_for('cast_mypage.blog_drafts', store=store))
        else:
            print(f"[ERROR] 下書き削除失敗: draft_id={draft_id}")
            flash('削除に失敗しました。', 'error')
            return redirect(url_for('cast_mypage.blog_drafts', store=store))
            
    except Exception as e:
        print(f"[ERROR] 下書き削除エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('エラーが発生しました。', 'error')
        return redirect(url_for('cast_mypage.blog_drafts', store=store))


# ==== ブログ下書き自動保存 ====

@cast_mypage_bp.route('/blog-drafts/autosave', methods=['POST'])
@login_required
def blog_draft_autosave(store):
    """ブログ下書き自動保存（5秒ごと）"""
    
    try:
        db = get_db(store)
        cast_id = session.get('cast_id')
        
        data = request.get_json()
        draft_id = data.get('draft_id')
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        print(f"[DEBUG] 自動保存: draft_id={draft_id}, title='{title[:30]}...', content length={len(content)}")
        
        # タイトルが空の場合はデフォルト値を設定
        if not title:
            title = '(無題)'
        
        # 新規作成
        if not draft_id:
            draft_id = create_cast_blog_draft(db, cast_id, title, content)
            if draft_id:
                print(f"[SUCCESS] 自動保存（新規作成）成功: draft_id={draft_id}")
                return jsonify({'success': True, 'draft_id': draft_id, 'message': '自動保存しました'})
            else:
                print(f"[ERROR] 自動保存（新規作成）失敗")
                return jsonify({'success': False, 'error': '保存に失敗しました'}), 500
        
        # 既存の下書きを更新
        draft = get_cast_blog_draft_by_id(db, draft_id, cast_id)
        
        if not draft or draft.get('cast_id') != cast_id:
            print(f"[ERROR] 自動保存の権限エラー: draft_id={draft_id}")
            return jsonify({'success': False, 'error': 'アクセス権限がありません'}), 403
        
        success = update_cast_blog_draft(db, draft_id, cast_id, title, content)
        
        if success:
            print(f"[SUCCESS] 自動保存（更新）成功: draft_id={draft_id}")
            return jsonify({'success': True, 'message': '自動保存しました'})
        else:
            print(f"[ERROR] 自動保存（更新）失敗: draft_id={draft_id}")
            return jsonify({'success': False, 'error': '保存に失敗しました'}), 500
            
    except Exception as e:
        print(f"[ERROR] 自動保存エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==== 画像アップロード ====

@cast_mypage_bp.route('/blog/upload-image', methods=['POST'])
@login_required
def upload_blog_image(store):
    """ブログ用の画像アップロード"""
    
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
            file_url = url_for('static', filename=f'uploads/blog/{filename}')
            
            print(f"[SUCCESS] ブログ画像アップロード成功: {file_url}")
            return {'location': file_url}, 200
        
        return {'error': '許可されていないファイル形式です'}, 400
        
    except Exception as e:
        print(f"[ERROR] 画像アップロードエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': f'アップロード中にエラーが発生しました: {str(e)}'}, 500