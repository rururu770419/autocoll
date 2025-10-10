/**
 * キャストマイページ用JavaScript
 * 共通機能（ハンバーガーメニュー、ユーティリティ関数など）
 */

// ============================================
// ハンバーガーメニュー
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initHamburgerMenu();
});

/**
 * ハンバーガーメニューの初期化
 */
function initHamburgerMenu() {
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    const sidebarClose = document.getElementById('sidebarClose');

    // メニューを開く
    function openMenu() {
        if (sidebar && overlay) {
            sidebar.classList.add('cm-sidebar-open');
            overlay.classList.add('cm-overlay-show');
            document.body.style.overflow = 'hidden'; // スクロール禁止
        }
    }

    // メニューを閉じる
    function closeMenu() {
        if (sidebar && overlay) {
            sidebar.classList.remove('cm-sidebar-open');
            overlay.classList.remove('cm-overlay-show');
            document.body.style.overflow = ''; // スクロール解除
        }
    }

    // ハンバーガーボタンクリック
    if (hamburger) {
        hamburger.addEventListener('click', openMenu);
    }

    // 閉じるボタンクリック
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeMenu);
    }

    // オーバーレイクリック
    if (overlay) {
        overlay.addEventListener('click', closeMenu);
    }

    // ESCキーで閉じる
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMenu();
        }
    });
}

// ============================================
// ユーティリティ関数
// ============================================

/**
 * フォーマット済みの日時文字列を取得
 * @param {Date} date - 日付オブジェクト
 * @param {string} format - フォーマット ('date', 'time', 'datetime')
 * @returns {string} フォーマット済み文字列
 */
function formatDateTime(date, format = 'datetime') {
    if (!date) return '';
    
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    
    switch (format) {
        case 'date':
            return `${year}/${month}/${day}`;
        case 'time':
            return `${hours}:${minutes}`;
        case 'datetime':
            return `${year}/${month}/${day} ${hours}:${minutes}`;
        default:
            return d.toLocaleString('ja-JP');
    }
}

/**
 * 確認ダイアログを表示
 * @param {string} message - 確認メッセージ
 * @param {Function} onConfirm - 確認時のコールバック
 * @param {Function} onCancel - キャンセル時のコールバック
 */
function showConfirmDialog(message, onConfirm, onCancel) {
    if (confirm(message)) {
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    } else {
        if (typeof onCancel === 'function') {
            onCancel();
        }
    }
}

/**
 * アラートメッセージを表示
 * @param {string} message - メッセージ
 * @param {string} type - タイプ ('success', 'error', 'info', 'warning')
 */
function showAlert(message, type = 'info') {
    // シンプルなalert（今後、トーストUIに置き換え可能）
    const icon = {
        'success': '✅',
        'error': '❌',
        'info': 'ℹ️',
        'warning': '⚠️'
    };
    
    alert((icon[type] || '') + ' ' + message);
}

/**
 * ローディング表示を制御
 * @param {boolean} show - 表示するかどうか
 */
function toggleLoading(show) {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = show ? 'flex' : 'none';
    }
}

/**
 * HTMLタグを除去してテキストのみ取得
 * @param {string} html - HTML文字列
 * @returns {string} テキストのみ
 */
function stripHtmlTags(html) {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
}

/**
 * 文字列を指定長に切り詰め
 * @param {string} str - 文字列
 * @param {number} length - 最大長
 * @param {string} suffix - 末尾に追加する文字（デフォルト: '...'）
 * @returns {string} 切り詰めた文字列
 */
function truncateString(str, length, suffix = '...') {
    if (!str) return '';
    if (str.length <= length) return str;
    return str.substring(0, length) + suffix;
}

// ============================================
// API通信ヘルパー
// ============================================

/**
 * POSTリクエストを送信
 * @param {string} url - リクエストURL
 * @param {Object} data - 送信データ
 * @returns {Promise} レスポンスPromise
 */
async function postJSON(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('POSTエラー:', error);
        throw error;
    }
}

/**
 * GETリクエストを送信
 * @param {string} url - リクエストURL
 * @returns {Promise} レスポンスPromise
 */
async function getJSON(url) {
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('GETエラー:', error);
        throw error;
    }
}

// ============================================
// エクスポート（グローバルに公開）
// ============================================

window.castMypage = {
    formatDateTime,
    showConfirmDialog,
    showAlert,
    toggleLoading,
    stripHtmlTags,
    truncateString,
    postJSON,
    getJSON
};