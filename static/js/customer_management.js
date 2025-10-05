// 顧客管理画面JavaScript

let allCustomers = [];
let currentPage = 1;
const itemsPerPage = 30;

// ページ読み込み時の処理
document.addEventListener('DOMContentLoaded', function() {
    // 初期表示で全件取得
    loadAllCustomers();
    
    // Enterキーで検索
    const searchInput = document.getElementById('searchKeyword');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchCustomers();
            }
        });
    }
});

// 全件取得関数を追加
async function loadAllCustomers() {
    const store = getStoreCode();
    
    try {
        const response = await fetch(`/${store}/api/customers`);
        const result = await response.json();
        
        if (result.success) {
            allCustomers = result.customers || [];
            currentPage = 1;
            displayCustomersWithPagination();
            
            if (allCustomers.length === 0) {
                showEmptyMessage();
            }
        } else {
            showMessage(result.message || '顧客の取得に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// 空メッセージ表示
function showEmptyMessage() {
    const tbody = document.getElementById('customerTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="10" class="customer-empty-message">
                検索条件を入力して検索してください
            </td>
        </tr>
    `;
    document.getElementById('paginationArea').innerHTML = '';
}

// 統合検索機能
async function searchCustomers() {
    const store = getStoreCode();
    const keyword = document.getElementById('searchKeyword').value.trim();
    
    if (!keyword) {
        showMessage('検索キーワードを入力してください', 'error');
        return;
    }
    
    // 検索キーワードの最小文字数チェック
    if (keyword.length < 2) {
        showMessage('検索キーワードは2文字以上で入力してください', 'error');
        return;
    }
    
    // 検索タイプの自動判定
    const searchType = detectSearchType(keyword);
    
    try {
        // 検索タイプに応じたパラメータを設定
        let url = `/${store}/api/customers/search?keyword=${encodeURIComponent(keyword)}`;
        
        // 検索タイプをクエリパラメータとして追加
        if (searchType) {
            url += `&type=${searchType}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            allCustomers = result.customers || [];
            currentPage = 1;
            displayCustomersWithPagination();
            
            if (allCustomers.length === 0) {
                showMessage('該当する顧客が見つかりませんでした', 'info');
            } else {
                const searchTypeText = searchType === 'phone' ? '電話番号' : 
                                      searchType === 'furigana' ? 'フリガナ' : 
                                      'フリガナ・電話番号';
                showMessage(`${allCustomers.length}件の顧客が見つかりました（${searchTypeText}検索）`, 'success');
            }
        } else {
            showMessage(result.message || '検索に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// 検索タイプの自動判定
function detectSearchType(keyword) {
    // ハイフンを除去
    const cleanKeyword = keyword.replace(/-/g, '');
    
    // 数字のみの場合は電話番号検索
    if (/^\d+$/.test(cleanKeyword)) {
        return 'phone';
    }
    
    // カタカナを含む場合はフリガナ検索
    if (/[ァ-ヴー]/.test(keyword)) {
        return 'furigana';
    }
    
    // ひらがなを含む場合もフリガナ検索として扱う（カタカナに変換）
    if (/[ぁ-ん]/.test(keyword)) {
        return 'furigana';
    }
    
    // どちらでもない場合は両方で検索（nullを返す）
    return null;
}

// ページネーション付き表示
function displayCustomersWithPagination() {
    const tbody = document.getElementById('customerTableBody');
    const store = getStoreCode();
    
    if (allCustomers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="customer-empty-message">
                    顧客データがありません
                </td>
            </tr>
        `;
        document.getElementById('paginationArea').innerHTML = '';
        return;
    }
    
    // 現在のページのデータを取得
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageCustomers = allCustomers.slice(startIndex, endIndex);
    
    // テーブル表示
    tbody.innerHTML = pageCustomers.map(customer => `
        <tr class="customer-table-row">
            <td class="customer-table-cell">
                <div class="customer-table-actions">
                    <a href="/${store}/customer_edit/${customer.customer_id}" 
                       class="customer-btn customer-btn-primary">詳細</a>
                </div>
            </td>
            <td class="customer-table-cell">${customer.customer_id}</td>
            <td class="customer-table-cell">${escapeHtml(customer.name || '')}</td>
            <td class="customer-table-cell">${escapeHtml(customer.furigana || '')}</td>
            <td class="customer-table-cell">${escapeHtml(customer.phone || '')}</td>
            <td class="customer-table-cell">${customer.age ? customer.age + '歳' : ''}</td>
            <td class="customer-table-cell">
                <span class="customer-badge ${getBadgeClass(customer.member_type)}">
                    ${escapeHtml(customer.member_type || '通常会員')}
                </span>
            </td>
            <td class="customer-table-cell">
                <span class="customer-badge ${getStatusBadgeClass(customer.status)}">
                    ${escapeHtml(customer.status || '普通')}
                </span>
            </td>
            <td class="customer-table-cell">${customer.current_points || 0} pt</td>
            <td class="customer-table-cell">${escapeHtml(customer.comment || '')}</td>
        </tr>
    `).join('');
    
    // ページネーション表示
    displayPagination();
}

// ページネーション表示
function displayPagination() {
    const totalPages = Math.ceil(allCustomers.length / itemsPerPage);
    const paginationArea = document.getElementById('paginationArea');
    
    if (totalPages <= 1) {
        paginationArea.innerHTML = '';
        return;
    }
    
    const startIndex = (currentPage - 1) * itemsPerPage + 1;
    const endIndex = Math.min(currentPage * itemsPerPage, allCustomers.length);
    
    let html = '<div class="customer-pagination">';
    html += `<div class="customer-pagination-info">${startIndex}～${endIndex}件 / 全${allCustomers.length}件</div>`;
    html += '<div class="customer-pagination-buttons">';
    
    // 前へボタン
    if (currentPage > 1) {
        html += `<button class="customer-pagination-btn" onclick="changePage(${currentPage - 1})">← 前へ</button>`;
    } else {
        html += `<button class="customer-pagination-btn customer-pagination-btn-disabled" disabled>← 前へ</button>`;
    }
    
    // ページ番号
    html += `<span class="customer-pagination-current">ページ ${currentPage} / ${totalPages}</span>`;
    
    // 次へボタン
    if (currentPage < totalPages) {
        html += `<button class="customer-pagination-btn" onclick="changePage(${currentPage + 1})">次へ →</button>`;
    } else {
        html += `<button class="customer-pagination-btn customer-pagination-btn-disabled" disabled>次へ →</button>`;
    }
    
    html += '</div></div>';
    paginationArea.innerHTML = html;
}

// ページ変更
function changePage(page) {
    currentPage = page;
    displayCustomersWithPagination();
    
    // テーブルの先頭にスクロール
    document.querySelector('.customer-table-wrapper').scrollIntoView({ behavior: 'smooth' });
}

// 会員種別バッジクラス
function getBadgeClass(memberType) {
    if (memberType === '本会員') return 'customer-badge-premium';
    return 'customer-badge-normal';
}

// ステータスバッジクラス
function getStatusBadgeClass(status) {
    switch(status) {
        case '優良': return 'customer-badge-excellent';
        case '要注意': return 'customer-badge-caution';
        case '出禁': return 'customer-badge-banned';
        default: return 'customer-badge-average';
    }
}

// メッセージ表示
function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    const alertClass = type === 'success' ? 'customer-alert-success' : 
                      type === 'info' ? 'customer-alert-info' : 'customer-alert-error';
    messageArea.innerHTML = `<div class="customer-alert ${alertClass}">${escapeHtml(message)}</div>`;
    
    setTimeout(() => {
        messageArea.innerHTML = '';
    }, 5000);
}

// ユーティリティ関数
function getStoreCode() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[1] || 'nagano';
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}