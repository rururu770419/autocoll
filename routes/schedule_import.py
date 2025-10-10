# routes/schedule_import.py
from flask import Blueprint, jsonify, current_app
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from database.db_connection import get_db_connection
from datetime import datetime
import time
import re
import traceback

schedule_import_bp = Blueprint('schedule_import', __name__)

# シティヘブン設定
CITYHEAVEN_LOGIN_URL = "https://newmanager.cityheaven.net/"
CITYHEAVEN_ID = "23764"
CITYHEAVEN_PASSWORD = "2043hdmk"
CITYHEAVEN_SCHEDULE_URL = "https://newmanager.cityheaven.net/C9ShukkinShiftList.php?shopdir=n_precious_h"


def get_cast_id_by_name(cast_name):
    """
    キャスト名からcast_idを取得
    完全一致で検索
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cast_id FROM casts 
            WHERE name = %s
        """, (cast_name,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result[0] if result else None
    except Exception as e:
        current_app.logger.error(f"キャストID取得エラー: {e}")
        if conn:
            conn.close()
        return None


def parse_time_range(time_str):
    """
    時間文字列をパース
    例: '10:00～13:00' → ('10:00', '13:00')
    """
    if not time_str or time_str == '---' or time_str.strip() == '':
        return None, None
    
    # '～' または '~' で分割
    match = re.search(r'(\d{1,2}:\d{2})[～~](\d{1,2}:\d{2})', time_str)
    if match:
        return match.group(1), match.group(2)
    
    return None, None


def save_schedule_to_db(cast_id, work_date, start_time, end_time):
    """
    出勤情報をデータベースに保存
    既存データは上書き（UPSERT）
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 既存データがあれば更新、なければ挿入
        cursor.execute("""
            INSERT INTO cast_schedules (cast_id, work_date, start_time, end_time, source)
            VALUES (%s, %s, %s, %s, 'cityheaven')
            ON CONFLICT (cast_id, work_date, start_time) 
            DO UPDATE SET 
                end_time = EXCLUDED.end_time,
                updated_at = CURRENT_TIMESTAMP
        """, (cast_id, work_date, start_time, end_time))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        current_app.logger.error(f"スケジュール保存エラー: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


def scrape_cityheaven_schedule():
    """
    シティヘブンから出勤情報をスクレイピング
    """
    print("=" * 60)
    print("🚀 スクレイピング関数開始")
    print("=" * 60)
    
    # Chrome オプション設定
    chrome_options = Options()
    print("✅ Chromeオプション設定完了")
    chrome_options.add_argument('--headless')  # バックグラウンド実行
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = None
    
    try:
        # WebDriverの初期化
        current_app.logger.info("🚀 WebDriver初期化開始")
        try:
            service = Service(ChromeDriverManager().install())
            current_app.logger.info("✅ ChromeDriver取得完了")
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            current_app.logger.info("✅ WebDriver初期化完了")
        except Exception as e:
            current_app.logger.error(f"❌ WebDriver初期化エラー: {e}")
            raise
        
        current_app.logger.info("🔐 シティヘブンログイン開始")
        
        # ログインページにアクセス
        try:
            driver.get(CITYHEAVEN_LOGIN_URL)
            current_app.logger.info(f"✅ ページアクセス完了: {CITYHEAVEN_LOGIN_URL}")
        except Exception as e:
            current_app.logger.error(f"❌ ページアクセスエラー: {e}")
            raise
        
        # === デバッグ用：スクリーンショットとHTML保存 ===
        screenshot_path = 'cityheaven_debug.png'
        driver.save_screenshot(screenshot_path)
        current_app.logger.info(f"📸 スクリーンショット保存: {screenshot_path}")
        
        # ページのHTMLも保存
        with open('cityheaven_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        current_app.logger.info("📄 HTML保存: cityheaven_debug.html")
        
        # 現在のURLも確認
        current_app.logger.info(f"🔗 現在のURL: {driver.current_url}")
        current_app.logger.info(f"📋 ページタイトル: {driver.title}")
        # === ここまで ===
        
        # ログイン情報入力（表示されるまで待機）
        current_app.logger.info("🔍 ログインIDフィールドを探索中...")
        id_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "txt_account"))
        )
        current_app.logger.info("✅ ログインIDフィールド発見")
        
        password_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "txt_password"))
        )
        current_app.logger.info("✅ パスワードフィールド発見")
        
        current_app.logger.info("📝 フィールドに入力中...")
        id_input.clear()
        id_input.send_keys(CITYHEAVEN_ID)
        
        password_input.clear()
        password_input.send_keys(CITYHEAVEN_PASSWORD)
        current_app.logger.info("✅ 入力完了")
        
        # ログインボタンをクリック（JavaScript経由で確実に実行）
        current_app.logger.info("🔍 ログインボタンを探索中...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
        )
        current_app.logger.info("✅ ログインボタン発見")
        
        current_app.logger.info("👆 クリック実行中...")
        driver.execute_script("arguments[0].click();", login_button)
        current_app.logger.info("✅ ログイン完了")
        
        time.sleep(10)
        
        current_app.logger.info("📅 出勤情報ページにアクセス")
        
        # 出勤情報ページにアクセス
        driver.get(CITYHEAVEN_SCHEDULE_URL)
        time.sleep(10)
        
        # ページのHTMLを取得
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # テーブルを取得
        table = soup.find('table')
        if not table:
            current_app.logger.error("❌ 出勤情報テーブルが見つかりません")
            return {'success': False, 'error': 'テーブルが見つかりません'}
        
        current_app.logger.info("✅ 出勤情報テーブル発見")
        
        # ヘッダー行から日付を取得
        header_row = table.find('tr')
        date_cells = header_row.find_all('td')[1:]  # 最初のセル（女の子）をスキップ
        
        dates = []
        for cell in date_cells:
            date_text = cell.get_text(strip=True)
            # '10/8 (水)' のような形式から日付部分を抽出
            match = re.search(r'(\d{1,2})/(\d{1,2})', date_text)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                # 年は現在の年を使用（12月→1月の跨ぎは考慮が必要）
                year = datetime.now().year
                # 月が現在より小さい場合は翌年と判断
                if month < datetime.now().month:
                    year += 1
                dates.append(f"{year}-{month:02d}-{day:02d}")
        
        current_app.logger.info(f"📆 取得した日付: {dates}")
        
        # データ行を処理
        data_rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        i = 0
        while i < len(data_rows):
            # キャスト名の行
            name_row = data_rows[i]
            # 次の行がスケジュールの行
            if i + 1 < len(data_rows):
                schedule_row = data_rows[i + 1]
            else:
                break
            
            # キャスト名を取得
            name_cell = name_row.find('td')
            if not name_cell:
                i += 2
                continue
            
            cast_name = name_cell.get_text(strip=True)
            
            # キャストIDを取得
            cast_id = get_cast_id_by_name(cast_name)
            
            if not cast_id:
                current_app.logger.warning(f"⚠️ キャストが見つかりません: {cast_name}")
                skipped_count += 1
                i += 2
                continue
            
            # 出勤情報セルを取得
            schedule_cells = schedule_row.find_all('td')[1:]  # 最初のセルをスキップ
            
            # 各日付の出勤情報を処理
            for date_idx, cell in enumerate(schedule_cells):
                if date_idx >= len(dates):
                    break
                
                work_date = dates[date_idx]
                cell_text = cell.get_text(strip=True)
                
                # 時間情報をパース
                start_time, end_time = parse_time_range(cell_text)
                
                if start_time and end_time:
                    # データベースに保存
                    success = save_schedule_to_db(cast_id, work_date, start_time, end_time)
                    if success:
                        imported_count += 1
                        current_app.logger.info(f"💾 保存成功: {cast_name} {work_date} {start_time}-{end_time}")
                    else:
                        error_count += 1
            
            i += 2  # 次のキャストへ（名前行とスケジュール行をスキップ）
        
        current_app.logger.info(f"🎉 取り込み完了: {imported_count}件登録、{skipped_count}件スキップ、{error_count}件エラー")
        
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': error_count
        }
        
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"❌ スクレイピングエラー:\n{error_detail}")
        return {'success': False, 'error': str(e)}
    
    finally:
        if driver:
            driver.quit()
            current_app.logger.info("🛑 WebDriver終了")


@schedule_import_bp.route('/<store>/admin/import-schedule', methods=['POST'])
def import_schedule(store):
    """
    シティヘブンから出勤情報を取り込むエンドポイント
    """
    try:
        current_app.logger.info("=" * 60)
        current_app.logger.info("📥 シティヘブン取り込み開始")
        current_app.logger.info("=" * 60)
        
        result = scrape_cityheaven_schedule()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f"取り込み完了: {result['imported']}件登録、{result['skipped']}件スキップ、{result['errors']}件エラー"
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', '不明なエラー')
            }), 500
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"❌ 取り込みエラー:\n{error_detail}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@schedule_import_bp.route('/<store>/admin/test-cityheaven', methods=['GET'])
def test_cityheaven(store):
    """
    シティヘブン接続テスト用エンドポイント
    """
    return jsonify({
        'status': 'ok',
        'message': 'シティヘブン取り込み機能が有効です',
        'login_url': CITYHEAVEN_LOGIN_URL,
        'schedule_url': CITYHEAVEN_SCHEDULE_URL
    })