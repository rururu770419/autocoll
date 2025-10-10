// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 予約情報管理（キャンセル理由・予約方法）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let cancellationReasons = [];
let reservationMethods = [];
let currentReasonId = null;
let currentMethodId = null;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    console.log('Settings Reservation loaded');
    
    // キャンセル理由を読み込み
    loadCancellationReasons();
    
    // 予約方法を読み込み
    loadReservationMethods();
    
    // イベントリスナー設定
    setupEventListeners();
});

function setupEventListeners() {
    // キャンセル理由追加ボタン
    const addReasonBtn = document.getElementById('add-cancellation-reason-btn');
    if (addReasonBtn) {
        addReasonBtn.addEventListener('click', showAddCancellationReasonModal);
    }
    
    // 予約方法追加ボタン
    const addMethodBtn = document.getElementById('add-reservation-method-btn');
    if (addMethodBtn) {
        addMethodBtn.addEventListener('click', showAddReservationMethodModal);
    }
    
    // キャンセル理由フォーム送信
    const reasonForm = document.getElementById('cancellation-reason-form');
    if (reasonForm) {
        reasonForm.addEventListener('submit', handleCancellationReasonSubmit);
    }
    
    // 予約方法フォーム送信
    const methodForm = document.getElementById('reservation-method-form');
    if (methodForm) {
        methodForm.addEventListener('submit', handleReservationMethodSubmit);
    }
    
    // モーダル閉じるボタン
    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-close');
            closeModal(modalId);
        });
    });
    
    // モーダルの×ボタン
    document.querySelectorAll('.settings-modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal');
            closeModal(modalId);
        });
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// キャンセル理由管理
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function loadCancellationReasons() {
    console.log('🔍 loadCancellationReasons() 開始');
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/cancellation_reasons`);
        const data = await response.json();
        
        console.log('📋 キャンセル理由データ:', data);
        console.log('🔍 Array.isArray(data):', Array.isArray(data));
        console.log('🔍 data.success:', data.success);
        
        // ✅ 配列とオブジェクトの両方に対応
        if (data.success && data.reasons) {
            // 新しい形式 {success: true, reasons: [...]}
            cancellationReasons = data.reasons;
            console.log('✅ 新形式でデータ取得:', cancellationReasons.length, '件');
        } else if (Array.isArray(data)) {
            // 古い形式（直接配列）
            cancellationReasons = data;
            console.log('✅ 配列形式でデータ取得:', cancellationReasons.length, '件');
        } else {
            console.error('❌ 予期しないデータ形式:', data);
            showMessage('キャンセル理由の読み込みに失敗しました', 'error');
            return;
        }
        
        renderCancellationReasons();
        
    } catch (error) {
        console.error('❌ キャンセル理由の読み込みエラー:', error);
        showMessage('キャンセル理由の読み込みに失敗しました', 'error');
    }
}

function renderCancellationReasons() {
    console.log('🎨 renderCancellationReasons() 開始');
    const tbody = document.getElementById('cancellation-reasons-tbody');
    
    if (!tbody) {
        console.error('❌ cancellation-reasons-tbody が見つかりません');
        return;
    }
    
    if (cancellationReasons.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" class="settings-table-empty">登録されているキャンセル理由はありません</td></tr>';
        console.log('📝 キャンセル理由なし');
        return;
    }
    
    let html = '';
    cancellationReasons.forEach((reason, index) => {
        console.log(`🔍 理由[${index}]:`, reason);
        
        html += `
            <tr>
                <td>${escapeHtml(reason.reason_name)}</td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="editCancellationReason(${reason.reason_id})">
                        編集
                    </button>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="deleteCancellationReason(${reason.reason_id})">
                        削除
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    console.log('✅ キャンセル理由を表示しました:', cancellationReasons.length, '件');
}

function showAddCancellationReasonModal() {
    currentReasonId = null;
    document.getElementById('cancellation-reason-modal-title').textContent = 'キャンセル理由を追加';
    document.getElementById('cancellation-reason-id').value = '';
    document.getElementById('cancellation-reason-name').value = '';
    openModal('cancellation-reason-modal');
}

function editCancellationReason(reasonId) {
    const reason = cancellationReasons.find(r => r.reason_id === reasonId);
    if (!reason) {
        console.error('❌ 理由が見つかりません:', reasonId);
        return;
    }
    
    currentReasonId = reasonId;
    document.getElementById('cancellation-reason-modal-title').textContent = 'キャンセル理由を編集';
    document.getElementById('cancellation-reason-id').value = reasonId;
    document.getElementById('cancellation-reason-name').value = reason.reason_name;
    openModal('cancellation-reason-modal');
}

async function handleCancellationReasonSubmit(e) {
    e.preventDefault();
    
    const reasonName = document.getElementById('cancellation-reason-name').value.trim();
    
    if (!reasonName) {
        alert('理由名を入力してください');
        return;
    }
    
    try {
        let url, method;
        if (currentReasonId) {
            // 更新
            url = `${window.settingsUrls.store}/settings/cancellation_reasons/${currentReasonId}`;
            method = 'PUT';
        } else {
            // 新規作成
            url = `${window.settingsUrls.store}/settings/cancellation_reasons/create`;
            method = 'POST';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason_name: reasonName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            closeModal('cancellation-reason-modal');
            loadCancellationReasons(); // 再読み込み
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('保存エラー:', error);
        showMessage('保存に失敗しました', 'error');
    }
}

async function deleteCancellationReason(reasonId) {
    console.log('🗑️ deleteCancellationReason:', reasonId);
    
    const reason = cancellationReasons.find(r => r.reason_id === reasonId);
    if (!reason) {
        console.error('❌ 理由が見つかりません:', reasonId);
        return;
    }
    
    if (!confirm(`「${reason.reason_name}」を削除してもよろしいですか？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/cancellation_reasons/${reasonId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadCancellationReasons(); // 再読み込み
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('削除エラー:', error);
        showMessage('削除に失敗しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 予約方法管理
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function loadReservationMethods() {
    console.log('🔍 loadReservationMethods() 開始');
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/reservation_methods`);
        const data = await response.json();
        
        console.log('📋 予約方法データ:', data);
        console.log('🔍 Array.isArray(data):', Array.isArray(data));
        console.log('🔍 data.success:', data.success);
        
        // ✅ 配列とオブジェクトの両方に対応
        if (data.success && data.methods) {
            // 新しい形式 {success: true, methods: [...]}
            reservationMethods = data.methods;
            console.log('✅ 新形式でデータ取得:', reservationMethods.length, '件');
        } else if (Array.isArray(data)) {
            // 古い形式（直接配列）
            reservationMethods = data;
            console.log('✅ 配列形式でデータ取得:', reservationMethods.length, '件');
        } else {
            console.error('❌ 予期しないデータ形式:', data);
            showMessage('予約方法の読み込みに失敗しました', 'error');
            return;
        }
        
        renderReservationMethods();
        
    } catch (error) {
        console.error('❌ 予約方法の読み込みエラー:', error);
        showMessage('予約方法の読み込みに失敗しました', 'error');
    }
}

function renderReservationMethods() {
    console.log('🎨 renderReservationMethods() 開始');
    const tbody = document.getElementById('reservation-methods-tbody');
    
    if (!tbody) {
        console.error('❌ reservation-methods-tbody が見つかりません');
        return;
    }
    
    if (reservationMethods.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" class="settings-table-empty">登録されている予約方法はありません</td></tr>';
        console.log('📝 予約方法なし');
        return;
    }
    
    let html = '';
    reservationMethods.forEach((method, index) => {
        console.log(`🔍 方法[${index}]:`, method);
        
        html += `
            <tr>
                <td>${escapeHtml(method.method_name)}</td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="editReservationMethod(${method.method_id})">
                        編集
                    </button>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="deleteReservationMethod(${method.method_id})">
                        削除
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    console.log('✅ 予約方法を表示しました:', reservationMethods.length, '件');
}

function showAddReservationMethodModal() {
    currentMethodId = null;
    document.getElementById('reservation-method-modal-title').textContent = '予約方法を追加';
    document.getElementById('reservation-method-id').value = '';
    document.getElementById('reservation-method-name').value = '';
    openModal('reservation-method-modal');
}

function editReservationMethod(methodId) {
    const method = reservationMethods.find(m => m.method_id === methodId);
    if (!method) {
        console.error('❌ 予約方法が見つかりません:', methodId);
        return;
    }
    
    currentMethodId = methodId;
    document.getElementById('reservation-method-modal-title').textContent = '予約方法を編集';
    document.getElementById('reservation-method-id').value = methodId;
    document.getElementById('reservation-method-name').value = method.method_name;
    openModal('reservation-method-modal');
}

async function handleReservationMethodSubmit(e) {
    e.preventDefault();
    
    const methodName = document.getElementById('reservation-method-name').value.trim();
    
    if (!methodName) {
        alert('方法名を入力してください');
        return;
    }
    
    try {
        let url, method;
        if (currentMethodId) {
            // 更新
            url = `${window.settingsUrls.store}/settings/reservation_methods/${currentMethodId}`;
            method = 'PUT';
        } else {
            // 新規作成
            url = `${window.settingsUrls.store}/settings/reservation_methods/create`;
            method = 'POST';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ method_name: methodName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            closeModal('reservation-method-modal');
            loadReservationMethods(); // 再読み込み
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('保存エラー:', error);
        showMessage('保存に失敗しました', 'error');
    }
}

async function deleteReservationMethod(methodId) {
    console.log('🗑️ deleteReservationMethod:', methodId);
    
    const method = reservationMethods.find(m => m.method_id === methodId);
    if (!method) {
        console.error('❌ 予約方法が見つかりません:', methodId);
        return;
    }
    
    if (!confirm(`「${method.method_name}」を削除してもよろしいですか？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/reservation_methods/${methodId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadReservationMethods(); // 再読み込み
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('削除エラー:', error);
        showMessage('削除に失敗しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// モーダル操作
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    } else {
        console.error('❌ モーダルが見つかりません:', modalId);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ユーティリティ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}