# routes/cast_mypage.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from database.connection import get_db, get_store_id
from database.cast_db import (
    verify_cast_password,
    find_cast_by_login_id,
    update_last_login,
    find_cast_by_id
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
from database.cast_reservation_db import (
    get_cast_reservations_by_date,
    get_cast_monthly_reservation_counts,
    get_cast_reservation_detail,
    get_customer_visit_count
)
from database.cast_reward_db import (
    get_daily_rewards,
    get_cast_transportation_fee,
    get_total_change,
    get_daily_adjustments,
    save_daily_adjustments,
    get_monthly_summary,
    get_monthly_rewards
)
from database.customer_db import (
    get_customer_by_id,
    get_customer_usage_history
)
from database.rating_db import (
    get_all_rating_items
)
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
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
        store_id = get_store_id(store)
        cast_session = get_cast_session(db, cast_session_id, store_id)

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
        update_cast_session_activity(db, cast_session_id, store_id)

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
        store_id = get_store_id(store)

        # 認証
        cast_id = verify_cast_password(db, login_id, password)

        if not cast_id:
            flash('ログインIDまたはパスワードが間違っています。', 'error')
            return render_template('cast/cast_login.html', store=store)

        # セッション作成
        ip_address = request.remote_addr or '0.0.0.0'
        user_agent = request.headers.get('User-Agent', 'Unknown')
        cast_session_id = create_cast_session(db, cast_id, store_id, ip_address, user_agent)
        
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
        store_id = get_store_id(store)
        delete_cast_session(db, cast_session_id, store_id)

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
    store_id = get_store_id(store)
    cast_id = session.get('cast_id')
    cast_name = session.get('cast_name', 'ゲスト')

    # 下書き一覧取得
    drafts = get_cast_blog_drafts(db, cast_id, store_id, limit=50)
    
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
            store_id = get_store_id(store)
            cast_id = session.get('cast_id')

            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()

            print(f"[DEBUG] 新規下書き作成: title='{title[:50]}...', content length={len(content)}")

            # タイトルが空の場合はデフォルト値を設定
            if not title:
                title = '(無題)'

            # 下書き作成
            draft_id = create_cast_blog_draft(db, cast_id, store_id, title, content)
            
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
        store_id = get_store_id(store)
        cast_id = session.get('cast_id')

        print(f"[DEBUG] 下書き編集ページアクセス: draft_id={draft_id}, cast_id={cast_id}, method={request.method}")

        # 下書き取得
        draft = get_cast_blog_draft_by_id(db, draft_id, cast_id, store_id)
        
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
                success = update_cast_blog_draft(db, draft_id, cast_id, store_id, title, content)

                if success:
                    print(f"[SUCCESS] 下書き更新成功: draft_id={draft_id}")

                    # 更新後のデータを確認
                    updated_draft = get_cast_blog_draft_by_id(db, draft_id, cast_id, store_id)
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
        store_id = get_store_id(store)
        cast_id = session.get('cast_id')

        print(f"[DEBUG] 下書き削除リクエスト: draft_id={draft_id}, cast_id={cast_id}")

        # 下書き取得
        draft = get_cast_blog_draft_by_id(db, draft_id, cast_id, store_id)
        
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
        success = delete_cast_blog_draft(db, draft_id, cast_id, store_id)
        
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
        store_id = get_store_id(store)
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
            draft_id = create_cast_blog_draft(db, cast_id, store_id, title, content)
            if draft_id:
                print(f"[SUCCESS] 自動保存（新規作成）成功: draft_id={draft_id}")
                return jsonify({'success': True, 'draft_id': draft_id, 'message': '自動保存しました'})
            else:
                print(f"[ERROR] 自動保存（新規作成）失敗")
                return jsonify({'success': False, 'error': '保存に失敗しました'}), 500

        # 既存の下書きを更新
        draft = get_cast_blog_draft_by_id(db, draft_id, cast_id, store_id)

        if not draft or draft.get('cast_id') != cast_id:
            print(f"[ERROR] 自動保存の権限エラー: draft_id={draft_id}")
            return jsonify({'success': False, 'error': 'アクセス権限がありません'}), 403

        success = update_cast_blog_draft(db, draft_id, cast_id, store_id, title, content)
        
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


# ==== 予約一覧 ====

@cast_mypage_bp.route('/reservation_list')
@login_required
def reservation_list(store):
    """キャスト予約一覧"""

    db = get_db(store)
    store_id = get_store_id(store)
    cast_id = session.get('cast_id')
    cast_name = session.get('cast_name', 'ゲスト')

    # 日付パラメータ取得（デフォルトは今日）
    date_str = request.args.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()

    # 指定日の予約一覧を取得
    reservations = get_cast_reservations_by_date(db, cast_id, store_id, selected_date)

    # お釣り機能の設定を取得
    from database.settings_db import get_change_feature_setting
    use_change_feature = get_change_feature_setting(store_id)

    print(f"[DEBUG] 予約一覧取得: {len(reservations)}件（{selected_date}）")

    return render_template(
        'cast/reservation_list.html',
        store=store,
        cast_name=cast_name,
        reservations=reservations,
        selected_date=selected_date,
        active_page='reservation_list',
        use_change_feature=use_change_feature
    )


@cast_mypage_bp.route('/api/update_amount_received', methods=['POST'])
@login_required
def update_amount_received_api(store):
    """お預かり金額を更新"""
    try:
        from database.cast_reservation_db import update_reservation_amount_received

        db = get_db(store)
        store_id = get_store_id(store)
        cast_id = session.get('cast_id')

        data = request.get_json()
        reservation_id = data.get('reservation_id')
        amount_received = data.get('amount_received', 0)

        if not reservation_id:
            return jsonify({'success': False, 'error': '予約IDが指定されていません'}), 400

        # お預かり金額を更新
        success = update_reservation_amount_received(
            db, reservation_id, cast_id, store_id, amount_received
        )

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '更新に失敗しました'}), 500

    except Exception as e:
        print(f"[ERROR] update_amount_received_api: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'サーバーエラー'}), 500


@cast_mypage_bp.route('/api/reservation_counts')
@login_required
def reservation_list_api(store):
    """月間予約件数API（カレンダー表示用）"""

    try:
        db = get_db(store)
        store_id = get_store_id(store)
        cast_id = session.get('cast_id')

        # 年月パラメータ取得
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)

        if not year or not month:
            now = datetime.now()
            year = now.year
            month = now.month

        # 月間予約件数を取得
        counts = get_cast_monthly_reservation_counts(db, cast_id, store_id, year, month)

        print(f"[DEBUG] 月間予約件数取得: {year}年{month}月 → {len(counts)}日分")

        return jsonify({'success': True, 'counts': counts})

    except Exception as e:
        print(f"[ERROR] 月間予約件数取得エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cast_mypage_bp.route('/api/reservation_detail')
@login_required
def reservation_detail_api(store):
    """予約詳細API（キャスト本人の予約のみ）"""

    try:
        db = get_db(store)
        store_id = get_store_id(store)
        cast_id = session.get('cast_id')

        # 予約IDを取得
        reservation_id = request.args.get('reservation_id', type=int)
        if not reservation_id:
            return jsonify({'success': False, 'error': '予約IDが指定されていません'}), 400

        # 予約詳細を取得（キャスト本人の予約のみ）
        detail = get_cast_reservation_detail(db, reservation_id, cast_id, store_id)

        if not detail:
            return jsonify({'success': False, 'error': '予約が見つかりません'}), 404

        # datetime型をISO形式文字列に変換
        for key, value in detail.items():
            if isinstance(value, datetime):
                detail[key] = value.isoformat()

        # 接客回数を取得
        visit_count = get_customer_visit_count(db, detail['customer_id'], cast_id, store_id)

        print(f"[DEBUG] 予約詳細取得: ID={reservation_id}, 顧客={detail['customer_name']}, 接客回数={visit_count}")

        return jsonify({
            'success': True,
            'detail': detail,
            'visit_count': visit_count
        })

    except Exception as e:
        print(f"[ERROR] 予約詳細取得エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cast_mypage_bp.route('/customer_info')
@login_required
def customer_info(store):
    """キャスト用：お客様情報ページ"""

    try:
        db = get_db(store)
        cast_id = session.get('cast_id')

        # キャスト情報を取得
        cast = find_cast_by_id(db, cast_id)
        cast_name = cast['name'] if cast else 'キャスト名なし'

        # customer_idを取得
        customer_id = request.args.get('customer_id', type=int)

        if not customer_id:
            return "顧客IDが指定されていません", 400

        # 顧客情報を取得
        customer = get_customer_by_id(store, customer_id)

        if not customer:
            return "顧客情報が見つかりません", 404

        # 利用履歴を取得（最新1件のみ）
        usage_history = get_customer_usage_history(store, customer_id, limit=1)

        # 最終利用日時を取得
        last_visit_date = None
        if usage_history and len(usage_history) > 0:
            last_visit_datetime = usage_history[0].get('reservation_datetime')
            if last_visit_datetime:
                # datetime型を日本語形式に変換
                if isinstance(last_visit_datetime, datetime):
                    last_visit_date = last_visit_datetime.strftime('%Y年%m月%d日')
                else:
                    # 文字列の場合はそのまま使用
                    last_visit_date = last_visit_datetime

        # 評価項目を取得（アクティブな項目のみ）
        all_rating_items = get_all_rating_items(db)
        active_rating_items = [item for item in all_rating_items if item.get('is_active')]

        # このキャストによる、この顧客への評価が既に登録されているかチェック
        store_id = get_store_id(store)
        cursor = db.execute("""
            SELECT COUNT(*) as count
            FROM cast_customer_ratings
            WHERE cast_id = %s AND customer_id = %s AND store_id = %s
        """, (cast_id, customer_id, store_id))
        rating_count = cursor.fetchone()
        has_rating = rating_count['count'] > 0

        # 既存の評価データを取得
        cursor = db.execute("""
            SELECT item_id, rating_value
            FROM cast_customer_ratings
            WHERE cast_id = %s AND customer_id = %s AND store_id = %s
        """, (cast_id, customer_id, store_id))
        existing_ratings = cursor.fetchall()

        # 辞書形式に変換（item_id -> rating_value）
        existing_ratings_dict = {str(row['item_id']): row['rating_value'] for row in existing_ratings}

        # 皆の評価を集計（他のキャスト全員の評価）
        # ラジオボタン/セレクト項目の集計
        cursor = db.execute("""
            SELECT r.item_id, r.rating_value, COUNT(*) as count
            FROM cast_customer_ratings r
            JOIN rating_items ri ON r.item_id = ri.item_id
            WHERE r.customer_id = %s
            AND r.store_id = %s
            AND ri.item_type IN ('radio', 'select')
            GROUP BY r.item_id, r.rating_value
            ORDER BY r.item_id, r.rating_value
        """, (customer_id, store_id))
        everyone_ratings_raw = cursor.fetchall()


        # 項目IDごとにグループ化（値→カウントの辞書形式）
        everyone_ratings_dict = {}
        for row in everyone_ratings_raw:
            item_id = str(row['item_id'])
            if item_id not in everyone_ratings_dict:
                everyone_ratings_dict[item_id] = {}
            everyone_ratings_dict[item_id][row['rating_value']] = row['count']

        # 評価項目ごとに全選択肢のカウントを含む完全なデータを作成
        everyone_ratings = {}
        for item in active_rating_items:
            if item.get('item_type') in ('radio', 'select'):
                item_id = str(item.get('item_id'))
                options_json = item.get('options', '[]')

                try:
                    import json
                    options_list = json.loads(options_json)
                except:
                    options_list = []

                # 各選択肢のカウントを取得（0件も含む）
                item_counts = []
                for option in options_list:
                    if isinstance(option, dict):
                        option_value = option.get('value', '')
                    else:
                        option_value = option

                    count = everyone_ratings_dict.get(item_id, {}).get(option_value, 0)
                    item_counts.append({
                        'value': option_value,
                        'count': count
                    })

                everyone_ratings[item_id] = item_counts

        # テキストエリア（備考欄）の評価を取得（新しい順）
        cursor = db.execute("""
            SELECT r.rating_value, c.name as cast_name, r.created_at
            FROM cast_customer_ratings r
            JOIN rating_items ri ON r.item_id = ri.item_id
            JOIN casts c ON r.cast_id = c.cast_id
            WHERE r.customer_id = %s
            AND r.store_id = %s
            AND ri.item_type = 'textarea'
            AND r.rating_value != ''
            ORDER BY r.created_at DESC
        """, (customer_id, store_id))
        everyone_comments = cursor.fetchall()

        # テンプレートに渡すデータ
        customer_data = {
            'customer_id': customer['customer_id'],
            'name': customer.get('name', '名前なし'),
            'nickname': customer.get('nickname', ''),
            'last_visit_date': last_visit_date or '利用履歴なし'
        }

        return render_template(
            'cast/customer_info.html',
            store=store,
            cast_name=cast_name,
            customer=customer_data,
            rating_items=active_rating_items,
            has_rating=has_rating,
            existing_ratings=existing_ratings_dict,
            everyone_ratings=everyone_ratings,
            everyone_comments=everyone_comments
        )

    except Exception as e:
        print(f"[ERROR] お客様情報ページエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return "お客様情報の取得に失敗しました", 500


@cast_mypage_bp.route('/api/save_customer_rating', methods=['POST'])
@login_required
def save_customer_rating_api(store):
    """キャストの顧客評価を保存するAPI"""

    try:
        db = get_db(store)
        store_id = get_store_id(store)
        cast_id = session.get('cast_id')

        data = request.get_json()
        customer_id = data.get('customer_id')
        ratings = data.get('ratings', {})

        if not customer_id:
            return jsonify({'success': False, 'error': '顧客IDが指定されていません'}), 400

        if not ratings:
            return jsonify({'success': False, 'error': '評価データがありません'}), 400

        # 既存の評価を削除して新しく登録
        db.execute("""
            DELETE FROM cast_customer_ratings
            WHERE cast_id = %s AND customer_id = %s AND store_id = %s
        """, (cast_id, customer_id, store_id))

        # 各評価項目を保存
        for item_id, rating_value in ratings.items():
            db.execute("""
                INSERT INTO cast_customer_ratings
                (cast_id, customer_id, item_id, rating_value, store_id, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (cast_id, customer_id, int(item_id), rating_value, store_id))

        db.commit()

        return jsonify({'success': True, 'message': '評価を保存しました'})

    except Exception as e:
        print(f"[ERROR] 評価保存エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 顧客検索ページ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@cast_mypage_bp.route('/customer_search')
@login_required
def customer_search(store):
    """顧客検索ページ"""
    cast_name = session.get('cast_name', 'ゲスト')

    return render_template(
        'cast/customer_search.html',
        store=store,
        cast_name=cast_name,
        active_page='customer_search'
    )


@cast_mypage_bp.route('/api/customer_list', methods=['GET'])
@login_required
def api_customer_list(store):
    """
    キャストの接客履歴がある顧客一覧を取得するAPI

    Query Parameters:
        page: ページ番号（デフォルト1）
        per_page: 1ページあたりの件数（デフォルト20）
        nomination_type: 指名タイプフィルター（all, main, first）
        visit_period: 来店時期フィルター（all, 3months, 6months, 1year）
    """
    try:
        db = get_db(store)
        store_id = get_store_id(store)
        cast_id = session['cast_id']

        # クエリパラメータ取得
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        nomination_type = request.args.get('nomination_type', 'all')
        visit_period = request.args.get('visit_period', 'all')

        offset = (page - 1) * per_page

        # フィルター条件を構築
        where_conditions = []
        params = [cast_id, store_id]

        # 指名タイプフィルター
        if nomination_type == 'main':
            where_conditions.append("AND r.nomination_type_name LIKE %s")
            params.append('%本指名%')
        elif nomination_type == 'first':
            where_conditions.append("AND r.nomination_type_name LIKE %s")
            params.append('%初回%')

        # 来店時期フィルター
        if visit_period == '3months':
            where_conditions.append("AND r.reservation_datetime >= NOW() - INTERVAL '3 months'")
        elif visit_period == '6months':
            where_conditions.append("AND r.reservation_datetime >= NOW() - INTERVAL '6 months'")
        elif visit_period == '1year':
            where_conditions.append("AND r.reservation_datetime >= NOW() - INTERVAL '1 year'")

        where_clause = ' '.join(where_conditions)

        # 顧客一覧を取得
        cursor = db.execute(f"""
            WITH customer_visits AS (
                SELECT
                    r.customer_id,
                    c.name AS customer_name,
                    c.furigana,
                    COUNT(r.reservation_id) AS visit_count,
                    MAX(r.reservation_datetime) AS last_visit_datetime,
                    (SELECT r2.reservation_id FROM reservations r2
                     WHERE r2.customer_id = r.customer_id AND r2.store_id = r.store_id AND r2.cast_id = %s
                     ORDER BY r2.reservation_datetime DESC LIMIT 1) AS last_reservation_id,
                    (SELECT r2.hotel_name FROM reservations r2
                     WHERE r2.customer_id = r.customer_id AND r2.store_id = r.store_id AND r2.cast_id = %s
                     ORDER BY r2.reservation_datetime DESC LIMIT 1) AS last_hotel_name,
                    (SELECT r2.nomination_type_name FROM reservations r2
                     WHERE r2.customer_id = r.customer_id AND r2.store_id = r.store_id AND r2.cast_id = %s
                     ORDER BY r2.reservation_datetime DESC LIMIT 1) AS last_nomination_type
                FROM reservations r
                INNER JOIN customers c ON r.customer_id = c.customer_id AND r.store_id = c.store_id
                WHERE r.cast_id = %s
                    AND r.store_id = %s
                    {where_clause}
                GROUP BY r.customer_id, r.store_id, c.name, c.furigana
            )
            SELECT
                cv.*,
                ccr.rating_value AS memo
            FROM customer_visits cv
            LEFT JOIN LATERAL (
                SELECT rating_value
                FROM cast_customer_ratings ccr
                INNER JOIN rating_items cri ON ccr.item_id = cri.item_id
                WHERE ccr.cast_id = %s
                    AND ccr.customer_id = cv.customer_id
                    AND ccr.store_id = %s
                    AND cri.item_type = 'textarea'
                    AND cri.is_active = TRUE
                ORDER BY ccr.updated_at DESC
                LIMIT 1
            ) ccr ON TRUE
            ORDER BY cv.last_visit_datetime DESC
            LIMIT %s OFFSET %s
        """, [cast_id, cast_id, cast_id] + params + [cast_id, store_id, per_page, offset])

        customers = cursor.fetchall()

        # 総件数を取得
        cursor = db.execute(f"""
            SELECT COUNT(DISTINCT r.customer_id)
            FROM reservations r
            WHERE r.cast_id = %s
                AND r.store_id = %s
                {where_clause}
        """, params)

        total_count = cursor.fetchone()['count']

        # 結果を整形
        result_customers = []
        for customer in customers:
            result_customers.append({
                'customer_id': customer['customer_id'],
                'customer_name': customer['customer_name'],
                'furigana': customer['furigana'],
                'visit_count': customer['visit_count'],
                'last_visit_datetime': customer['last_visit_datetime'].isoformat() if customer['last_visit_datetime'] else None,
                'last_reservation_id': customer['last_reservation_id'],
                'last_hotel_name': customer['last_hotel_name'],
                'last_nomination_type': customer['last_nomination_type'],
                'memo': customer['memo'][:30] if customer['memo'] else None
            })

        return jsonify({
            'success': True,
            'customers': result_customers,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })

    except Exception as e:
        print(f"[ERROR] 顧客一覧取得エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cast_mypage_bp.route('/api/customer_search', methods=['GET'])
@login_required
def api_customer_search(store):
    """
    顧客検索API（リアルタイム検索）

    Query Parameters:
        keyword: 検索キーワード
        nomination_type: 指名タイプフィルター（all, main, first）
        visit_period: 来店時期フィルター（all, 3months, 6months, 1year）
    """
    try:
        db = get_db(store)
        store_id = get_store_id(store)
        cast_id = session['cast_id']

        # クエリパラメータ取得
        keyword = request.args.get('keyword', '').strip()
        nomination_type = request.args.get('nomination_type', 'all')
        visit_period = request.args.get('visit_period', 'all')

        if not keyword or len(keyword) < 2:
            return jsonify({'success': False, 'error': 'キーワードは2文字以上で入力してください'}), 400

        # フィルター条件を構築
        where_conditions = []
        params = [cast_id, store_id]
        search_keyword = f'%{keyword}%'

        # 指名タイプフィルター
        if nomination_type == 'main':
            where_conditions.append("AND r.nomination_type_name LIKE %s")
            params.append('%本指名%')
        elif nomination_type == 'first':
            where_conditions.append("AND r.nomination_type_name LIKE %s")
            params.append('%初回%')

        # 来店時期フィルター
        if visit_period == '3months':
            where_conditions.append("AND r.reservation_datetime >= NOW() - INTERVAL '3 months'")
        elif visit_period == '6months':
            where_conditions.append("AND r.reservation_datetime >= NOW() - INTERVAL '6 months'")
        elif visit_period == '1year':
            where_conditions.append("AND r.reservation_datetime >= NOW() - INTERVAL '1 year'")

        where_clause = ' '.join(where_conditions)

        # 検索実行（フリガナ、備考、ホテル名、メモで検索）
        cursor = db.execute(f"""
            WITH customer_visits AS (
                SELECT
                    r.customer_id,
                    c.name AS customer_name,
                    c.furigana,
                    c.comment AS customer_comment,
                    COUNT(r.reservation_id) AS visit_count,
                    MAX(r.reservation_datetime) AS last_visit_datetime,
                    (SELECT r2.reservation_id FROM reservations r2
                     WHERE r2.customer_id = r.customer_id AND r2.store_id = r.store_id AND r2.cast_id = %s
                     ORDER BY r2.reservation_datetime DESC LIMIT 1) AS last_reservation_id,
                    (SELECT r2.hotel_name FROM reservations r2
                     WHERE r2.customer_id = r.customer_id AND r2.store_id = r.store_id AND r2.cast_id = %s
                     ORDER BY r2.reservation_datetime DESC LIMIT 1) AS last_hotel_name,
                    (SELECT r2.nomination_type_name FROM reservations r2
                     WHERE r2.customer_id = r.customer_id AND r2.store_id = r.store_id AND r2.cast_id = %s
                     ORDER BY r2.reservation_datetime DESC LIMIT 1) AS last_nomination_type,
                    STRING_AGG(DISTINCT r.hotel_name, ', ') AS all_hotels
                FROM reservations r
                INNER JOIN customers c ON r.customer_id = c.customer_id AND r.store_id = c.store_id
                WHERE r.cast_id = %s
                    AND r.store_id = %s
                    {where_clause}
                GROUP BY r.customer_id, r.store_id, c.name, c.furigana, c.comment
            )
            SELECT
                cv.*,
                ccr.rating_value AS memo
            FROM customer_visits cv
            LEFT JOIN LATERAL (
                SELECT rating_value
                FROM cast_customer_ratings ccr
                INNER JOIN rating_items cri ON ccr.item_id = cri.item_id
                WHERE ccr.cast_id = %s
                    AND ccr.customer_id = cv.customer_id
                    AND ccr.store_id = %s
                    AND cri.item_type = 'textarea'
                    AND cri.is_active = TRUE
                ORDER BY ccr.updated_at DESC
                LIMIT 1
            ) ccr ON TRUE
            WHERE cv.furigana LIKE %s
                OR cv.customer_comment LIKE %s
                OR cv.all_hotels LIKE %s
                OR ccr.rating_value LIKE %s
            ORDER BY cv.last_visit_datetime DESC
            LIMIT 50
        """, [cast_id, cast_id, cast_id] + params + [cast_id, store_id, search_keyword, search_keyword, search_keyword, search_keyword])

        customers = cursor.fetchall()

        # 結果を整形
        result_customers = []
        for customer in customers:
            result_customers.append({
                'customer_id': customer['customer_id'],
                'customer_name': customer['customer_name'],
                'furigana': customer['furigana'],
                'visit_count': customer['visit_count'],
                'last_visit_datetime': customer['last_visit_datetime'].isoformat() if customer['last_visit_datetime'] else None,
                'last_reservation_id': customer['last_reservation_id'],
                'last_hotel_name': customer['last_hotel_name'],
                'last_nomination_type': customer['last_nomination_type'],
                'memo': customer['memo'][:30] if customer['memo'] else None
            })

        return jsonify({
            'success': True,
            'customers': result_customers,
            'count': len(result_customers)
        })

    except Exception as e:
        print(f"[ERROR] 顧客検索エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# キャスト報酬一覧
# ========================================

@cast_mypage_bp.route('/reward_list')
@login_required
def cast_reward_list(store):
    """キャスト報酬一覧ページ"""
    # キャストIDを取得
    cast_id = session.get('cast_id')
    cast_name = session.get('cast_name', 'ゲスト')

    # 店舗IDを取得
    store_id = get_store_id(store)
    if store_id is None:
        flash('店舗が見つかりません', 'error')
        return redirect(url_for('cast_routes.cast_login', store=store))

    # 日付パラメータを取得（なければ本日）
    from datetime import datetime, date
    date_param = request.args.get('date')

    if date_param:
        try:
            selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except:
            selected_date = date.today()
    else:
        selected_date = date.today()

    # 日別報酬詳細を取得
    rewards = get_daily_rewards(cast_id, store_id, selected_date)

    # 報酬合計を計算
    total_reward = sum(r['total_reward'] for r in rewards) if rewards else 0

    # 交通費を取得
    transportation_fee = get_cast_transportation_fee(cast_id, store_id)

    # お釣り合計を取得
    total_change = get_total_change(cast_id, store_id, selected_date)

    # 合計金額を計算（お釣りはキャストが立て替えているのでプラスする）
    final_total = total_reward + transportation_fee + total_change

    return render_template(
        'cast/reward_list.html',
        store=store,
        cast_name=cast_name,
        selected_date=selected_date,
        rewards=rewards,
        total_reward=total_reward,
        transportation_fee=transportation_fee,
        total_change=total_change,
        final_total=final_total,
        active_page='reward_list'
    )


@cast_mypage_bp.route('/reward_list/save_adjustments', methods=['POST'])
@login_required
def save_cast_adjustments(store):
    """調整金保存API"""
    # キャストIDを取得
    cast_id = session.get('cast_id')

    # 店舗IDを取得
    store_id = get_store_id(store)
    if store_id is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'}), 404

    try:
        data = request.get_json()

        business_date = data.get('business_date')
        dormitory_fee = int(data.get('dormitory_fee', 0))
        adjustment_amount = int(data.get('adjustment_amount', 0))
        memo = data.get('memo', '')

        # バリデーション
        if not business_date:
            return jsonify({'success': False, 'error': '日付が指定されていません'}), 400

        if dormitory_fee < 0 or adjustment_amount < 0:
            return jsonify({'success': False, 'error': '金額は0以上で入力してください'}), 400

        # 保存
        success = save_daily_adjustments(
            cast_id, store_id, business_date,
            dormitory_fee, adjustment_amount, memo
        )

        if success:
            return jsonify({'success': True, 'message': '登録しました'})
        else:
            return jsonify({'success': False, 'error': '登録に失敗しました'}), 500

    except Exception as e:
        print(f"[ERROR] 調整金保存エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@cast_mypage_bp.route('/api/monthly_rewards')
@login_required
def api_monthly_rewards(store):
    """月間報酬データ取得API（カレンダー用）"""
    # キャストIDを取得
    cast_id = session.get('cast_id')

    # 店舗IDを取得
    store_id = get_store_id(store)
    if store_id is None:
        return jsonify({'success': False, 'error': '店舗が見つかりません'}), 404

    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))

        # 月間サマリーを取得
        summary = get_monthly_summary(cast_id, store_id, year, month)

        # 日別報酬を取得
        daily_rewards = get_monthly_rewards(cast_id, store_id, year, month)

        return jsonify({
            'success': True,
            'summary': summary,
            'daily_rewards': daily_rewards
        })

    except Exception as e:
        print(f"[ERROR] 月間報酬取得エラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
