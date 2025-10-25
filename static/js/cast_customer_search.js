/**
 * キャスト顧客検索ページ用JavaScript
 * タブ切り替え、検索、フィルター、ページネーション
 */

// ============================================
// グローバル変数
// ============================================

let currentTab = 'search'; // 現在のタブ（search / list）
let currentPage = 1;
let totalPages = 1;
let searchDebounceTimer = null;
let listSearchDebounceTimer = null;
let currentFilters = {
    nomination_type: 'all',
    visit_period: 'all'
};

// ============================================
// タブ切り替え
// ============================================

/**
 * タブを切り替える
 * @param {string} tab - タブ名（search / list）
 */
function switchTab(tab) {
    currentTab = tab;

    // タブボタンの状態を更新
    document.getElementById('searchTab').classList.toggle('ccs-tab-active', tab === 'search');
    document.getElementById('listTab').classList.toggle('ccs-tab-active', tab === 'list');

    // タブコンテンツの表示を切り替え
    document.getElementById('searchContent').classList.toggle('ccs-tab-content-active', tab === 'search');
    document.getElementById('listContent').classList.toggle('ccs-tab-content-active', tab === 'list');

    // 一覧タブの場合はデータを読み込む
    if (tab === 'list') {
        loadCustomerList(1);
    }
}

// ============================================
// 顧客一覧の読み込み（一覧タブ）
// ============================================

/**
 * 顧客一覧を読み込む
 * @param {number} page - ページ番号
 */
async function loadCustomerList(page = 1) {
    try {
        currentPage = page;

        const params = new URLSearchParams({
            page: page,
            per_page: 20,
            nomination_type: currentFilters.nomination_type,
            visit_period: currentFilters.visit_period
        });

        const response = await fetch(`/${store}/cast/api/customer_list?${params}`);
        const data = await response.json();

        if (!data.success) {
            console.error('[ERROR] 顧客一覧取得失敗:', data.error);
            showEmptyState('customerList', 'データの取得に失敗しました');
            return;
        }

        // 総件数を更新
        document.getElementById('totalCustomerCount').textContent = data.total_count;

        // 顧客一覧を表示
        renderCustomerList(data.customers, 'customerList');

        // ページネーションを表示
        totalPages = data.total_pages;
        renderPagination();

    } catch (error) {
        console.error('[ERROR] 顧客一覧取得エラー:', error);
        showEmptyState('customerList', 'データの取得に失敗しました');
    }
}

// ============================================
// 検索機能
// ============================================

/**
 * 検索を実行（デバウンス処理あり）
 * @param {string} keyword - 検索キーワード
 */
function searchCustomers(keyword) {
    // デバウンス処理（300ms）
    if (searchDebounceTimer) {
        clearTimeout(searchDebounceTimer);
    }

    // クリアボタンの表示制御
    const clearBtn = document.getElementById('clearSearchBtn');
    clearBtn.style.display = keyword.length > 0 ? 'flex' : 'none';

    // キーワードが2文字未満の場合は検索しない
    if (keyword.length < 2) {
        document.getElementById('searchResultInfo').style.display = 'none';
        showEmptyState('searchResultList', 'キーワードを入力して検索してください');
        return;
    }

    searchDebounceTimer = setTimeout(async () => {
        try {
            const params = new URLSearchParams({
                keyword: keyword,
                nomination_type: currentFilters.nomination_type,
                visit_period: currentFilters.visit_period
            });

            const response = await fetch(`/${store}/cast/api/customer_search?${params}`);
            const data = await response.json();

            if (!data.success) {
                console.error('[ERROR] 検索失敗:', data.error);
                showEmptyState('searchResultList', data.error || '検索に失敗しました');
                return;
            }

            // 検索結果件数を表示
            const resultInfo = document.getElementById('searchResultInfo');
            const resultCount = document.getElementById('searchResultCount');
            resultCount.textContent = data.count;
            resultInfo.style.display = 'block';

            // 検索結果を表示
            if (data.customers.length === 0) {
                showEmptyState('searchResultList', '該当する顧客が見つかりませんでした');
            } else {
                renderCustomerList(data.customers, 'searchResultList');
            }

        } catch (error) {
            console.error('[ERROR] 検索エラー:', error);
            showEmptyState('searchResultList', 'データの取得に失敗しました');
        }
    }, 300);
}

/**
 * 検索をクリア
 */
function clearSearch() {
    document.getElementById('searchInput').value = '';
    document.getElementById('clearSearchBtn').style.display = 'none';
    document.getElementById('searchResultInfo').style.display = 'none';
    showEmptyState('searchResultList', 'キーワードを入力して検索してください');
}

/**
 * 一覧タブの検索（デバウンス処理あり）
 * @param {string} keyword - 検索キーワード
 */
function searchListCustomers(keyword) {
    // デバウンス処理（300ms）
    if (listSearchDebounceTimer) {
        clearTimeout(listSearchDebounceTimer);
    }

    // クリアボタンの表示制御
    const clearBtn = document.getElementById('clearListSearchBtn');
    clearBtn.style.display = keyword.length > 0 ? 'flex' : 'none';

    // キーワードが空の場合は通常の一覧を表示
    if (keyword.length === 0) {
        loadCustomerList(1);
        return;
    }

    // キーワードが2文字未満の場合は検索しない
    if (keyword.length < 2) {
        return;
    }

    listSearchDebounceTimer = setTimeout(async () => {
        try {
            const params = new URLSearchParams({
                keyword: keyword,
                nomination_type: currentFilters.nomination_type,
                visit_period: currentFilters.visit_period
            });

            const response = await fetch(`/${store}/cast/api/customer_search?${params}`);
            const data = await response.json();

            if (!data.success) {
                console.error('[ERROR] 検索失敗:', data.error);
                showEmptyState('customerList', data.error || '検索に失敗しました');
                return;
            }

            // 総件数を更新
            document.getElementById('totalCustomerCount').textContent = data.count;

            // 検索結果を表示
            if (data.customers.length === 0) {
                showEmptyState('customerList', '該当する顧客が見つかりませんでした');
                // ページネーションを非表示
                document.getElementById('pagination').innerHTML = '';
            } else {
                renderCustomerList(data.customers, 'customerList');
                // 検索時はページネーションを非表示
                document.getElementById('pagination').innerHTML = '';
            }

        } catch (error) {
            console.error('[ERROR] 検索エラー:', error);
            showEmptyState('customerList', 'データの取得に失敗しました');
        }
    }, 300);
}

/**
 * 一覧タブの検索をクリア
 */
function clearListSearch() {
    document.getElementById('listSearchInput').value = '';
    document.getElementById('clearListSearchBtn').style.display = 'none';
    loadCustomerList(1);
}

// ============================================
// 顧客カードの表示
// ============================================

/**
 * 顧客一覧を描画
 * @param {Array} customers - 顧客データ配列
 * @param {string} containerId - 表示先のコンテナID
 */
function renderCustomerList(customers, containerId) {
    const container = document.getElementById(containerId);

    container.innerHTML = customers.map(customer => {
        // 日時のフォーマット
        const lastVisitDate = customer.last_visit_datetime
            ? formatDateTimeJP(customer.last_visit_datetime)
            : '利用履歴なし';

        // 日付部分のみを取得（YYYY-MM-DD形式）
        const lastVisitDateOnly = customer.last_visit_datetime
            ? customer.last_visit_datetime.split('T')[0]
            : null;

        // 指名タイプのアイコン
        let nominationIcon = '';
        let nominationText = '';
        if (customer.last_nomination_type && customer.last_nomination_type.includes('本指名')) {
            nominationIcon = '👑';
            nominationText = '本指名';
        } else if (customer.last_nomination_type && customer.last_nomination_type.includes('初回')) {
            nominationIcon = '🌟';
            nominationText = '初回利用';
        } else {
            nominationIcon = '👥';
            nominationText = customer.last_nomination_type || '指名なし';
        }

        return `
            <div class="ccs-customer-card">
                <!-- 情報ボタン（右上） -->
                <a href="/${store}/cast/customer_info?customer_id=${customer.customer_id}"
                   class="ccs-info-btn">情報</a>

                <!-- 顧客名 -->
                <div class="ccs-customer-name">${escapeHtml(customer.customer_name || '名前なし')}様</div>

                <!-- 来店回数 -->
                <div class="ccs-info-row">
                    <i class="fas fa-user"></i>
                    <span>来店 ${customer.visit_count}回目</span>
                </div>

                <!-- 最終利用日時 + 予約ボタン -->
                <div class="ccs-info-row-reservation">
                    <div class="ccs-info-row-reservation-left">
                        <i class="far fa-calendar-alt"></i>
                        <span>${lastVisitDate}</span>
                    </div>
                    ${customer.last_reservation_id && lastVisitDateOnly ? `
                        <a href="/${store}/cast/reservation_list?date=${lastVisitDateOnly}&reservation_id=${customer.last_reservation_id}"
                           class="ccs-reservation-btn">
                            予約詳細
                        </a>
                    ` : ''}
                </div>

                <!-- ホテル -->
                ${customer.last_hotel_name ? `
                <div class="ccs-info-row">
                    <i class="fas fa-hotel"></i>
                    <span>${escapeHtml(customer.last_hotel_name)}</span>
                </div>
                ` : ''}

                <!-- 指名タイプ -->
                <div class="ccs-info-row">
                    <span>${nominationIcon}</span>
                    <span>${nominationText}</span>
                </div>

                <!-- メモ -->
                ${customer.memo ? `
                <div class="ccs-memo-row">
                    <i class="fas fa-sticky-note"></i>
                    <div class="ccs-memo-text">${escapeHtml(customer.memo)}</div>
                </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

/**
 * 空状態を表示
 * @param {string} containerId - 表示先のコンテナID
 * @param {string} message - 表示メッセージ
 */
function showEmptyState(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="ccs-empty">
            <i class="fas fa-search ccs-empty-icon"></i>
            <p class="ccs-empty-text">${escapeHtml(message)}</p>
        </div>
    `;
}

// ============================================
// ページネーション
// ============================================

/**
 * ページネーションを描画
 */
function renderPagination() {
    const pagination = document.getElementById('pagination');

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    pagination.innerHTML = `
        <button class="ccs-page-btn"
                onclick="loadCustomerList(${currentPage - 1})"
                ${currentPage === 1 ? 'disabled' : ''}>
            ← 前へ
        </button>
        <span class="ccs-page-info">ページ ${currentPage} / ${totalPages}</span>
        <button class="ccs-page-btn"
                onclick="loadCustomerList(${currentPage + 1})"
                ${currentPage === totalPages ? 'disabled' : ''}>
            次へ →
        </button>
    `;
}

// ============================================
// フィルターアコーディオン
// ============================================

/**
 * フィルターエリアの開閉（アコーディオン）
 */
function toggleFilter() {
    const filterArea = document.getElementById('filterArea');
    const filterBtn = document.getElementById('filterBtn');

    if (filterArea.style.display === 'none' || !filterArea.style.display) {
        // 開く
        filterArea.style.display = 'block';
        filterBtn.style.background = 'linear-gradient(135deg, #ff7799 0%, #ff99bb 100%)';
    } else {
        // 閉じる
        filterArea.style.display = 'none';
        filterBtn.style.background = 'linear-gradient(135deg, #ff99bb 0%, #ffb3cc 100%)';
    }
}

/**
 * フィルターをクリア
 */
function clearFilter() {
    // すべてのラジオボタンをリセット
    document.querySelector('input[name="nominationType"][value="all"]').checked = true;
    document.querySelector('input[name="visitPeriod"][value="all"]').checked = true;

    // フィルターを適用
    applyFilter();
}

/**
 * フィルターを適用
 */
function applyFilter() {
    const nominationType = document.querySelector('input[name="nominationType"]:checked').value;
    const visitPeriod = document.querySelector('input[name="visitPeriod"]:checked').value;

    console.log('フィルター適用:', { nominationType, visitPeriod });

    // フィルターを保存
    currentFilters.nomination_type = nominationType;
    currentFilters.visit_period = visitPeriod;

    // フィルターエリアを閉じる
    const filterArea = document.getElementById('filterArea');
    const filterBtn = document.getElementById('filterBtn');
    filterArea.style.display = 'none';
    filterBtn.style.background = 'linear-gradient(135deg, #ff99bb 0%, #ffb3cc 100%)';

    // 現在のタブに応じてデータを再読み込み
    if (currentTab === 'list') {
        // 一覧タブの検索ボックスに値があれば検索、なければ通常の一覧
        const listKeyword = document.getElementById('listSearchInput').value.trim();
        if (listKeyword.length >= 2) {
            searchListCustomers(listKeyword);
        } else {
            loadCustomerList(1);
        }
    } else {
        // 検索タブの場合は現在の検索キーワードで再検索
        const keyword = document.getElementById('searchInput').value.trim();
        if (keyword.length >= 2) {
            searchCustomers(keyword);
        }
    }
}

// ============================================
// ユーティリティ関数
// ============================================

/**
 * 日時を日本語形式にフォーマット
 * @param {string} datetimeStr - 日時文字列（ISO形式）
 * @returns {string} YYYY/MM/DD HH:MM形式
 */
function formatDateTimeJP(datetimeStr) {
    const date = new Date(datetimeStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${year}/${month}/${day} ${hours}:${minutes}`;
}

/**
 * HTMLエスケープ
 * @param {string} text - エスケープするテキスト
 * @returns {string} エスケープされたテキスト
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

// ============================================
// 初期化
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] キャスト顧客検索ページ初期化');

    // 検索タブの検索入力のイベントリスナー
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            searchCustomers(this.value.trim());
        });
    }

    // 一覧タブの検索入力のイベントリスナー
    const listSearchInput = document.getElementById('listSearchInput');
    if (listSearchInput) {
        listSearchInput.addEventListener('input', function() {
            searchListCustomers(this.value.trim());
        });
    }

    // フィルターアコーディオンは特別なイベントリスナー不要
});
