// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 設定管理メイン
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 予約管理（キャンセル理由・予約方法）は settings_reservation.js に移動

console.log('Settings.js loaded');

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// メッセージ表示関数（他のJSファイルから使用される）
function showMessage(message, type = 'info') {
    const messageDiv = document.getElementById('saveMessage');
    if (!messageDiv) {
        console.warn('saveMessage 要素が見つかりません');
        return;
    }
    
    messageDiv.textContent = message;
    messageDiv.className = `settings-message settings-message-${type}`;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 3000);
}

// HTMLエスケープ関数（他のJSファイルから使用される）
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

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// タブ切り替え
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function switchTab(tabName) {
    // すべてのタブを非表示
    document.querySelectorAll('.settings-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // すべてのタブボタンを非アクティブ
    document.querySelectorAll('.settings-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 選択されたタブを表示
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // 選択されたタブボタンをアクティブ
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 設定保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function saveSettings() {
    const form = document.getElementById('settingsForm');
    if (!form) {
        console.error('settingsForm が見つかりません');
        return;
    }
    
    const formData = new FormData(form);
    
    try {
        const response = await fetch(window.settingsUrls.save, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('保存エラー:', error);
        showMessage('保存に失敗しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// パスワード表示切替
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    const btn = field.nextElementSibling;
    
    if (field.type === 'password') {
        field.type = 'text';
        if (btn) btn.textContent = '非表示';
    } else {
        field.type = 'password';
        if (btn) btn.textContent = '表示';
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// テスト発信
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function testCall() {
    const phoneNumber = document.getElementById('test_phone_number')?.value;
    const resultDiv = document.getElementById('testCallResult');
    
    if (!resultDiv) {
        console.error('testCallResult が見つかりません');
        return;
    }
    
    if (!phoneNumber) {
        resultDiv.innerHTML = '<div class="settings-alert settings-alert-error">電話番号を入力してください</div>';
        return;
    }
    
    resultDiv.innerHTML = '<div class="settings-alert settings-alert-info">発信中...</div>';
    
    try {
        const response = await fetch(window.settingsUrls.testCall, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phone_number: phoneNumber })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `<div class="settings-alert settings-alert-success">${data.message}</div>`;
        } else {
            resultDiv.innerHTML = `<div class="settings-alert settings-alert-error">${data.message}</div>`;
        }
        
    } catch (error) {
        console.error('テスト発信エラー:', error);
        resultDiv.innerHTML = '<div class="settings-alert settings-alert-error">発信に失敗しました</div>';
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 駐車場管理
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let parkingLots = [];
let currentParkingId = null;

// 駐車場機能の有効/無効切り替え
function toggleParkingFeature(enabled) {
    const parkingListSection = document.getElementById('parkingListSection');
    if (parkingListSection) {
        parkingListSection.style.display = enabled ? 'block' : 'none';
    }
    
    if (enabled) {
        loadParkingLots();
    }
}

// 駐車場一覧を読み込み
async function loadParkingLots() {
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/parking`);
        const data = await response.json();
        
        if (data.success) {
            parkingLots = data.parking_lots;
            renderParkingLots();
            
            // 駐車場機能の状態を反映
            const parkingEnabled = data.parking_enabled;
            document.getElementById('parking_enabled').checked = parkingEnabled;
            toggleParkingFeature(parkingEnabled);
        }
    } catch (error) {
        console.error('駐車場の読み込みエラー:', error);
    }
}

// 駐車場一覧を表示
function renderParkingLots() {
    const container = document.getElementById('parkingList');
    if (!container) return;
    
    if (parkingLots.length === 0) {
        container.innerHTML = '<p class="settings-empty-message">登録されている駐車場はありません</p>';
        return;
    }
    
    let html = '<div class="parking-items">';
    parkingLots.forEach(lot => {
        html += `
            <div class="parking-item">
                <span class="parking-name">${escapeHtml(lot.parking_name)}</span>
                <div class="parking-actions">
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="editParkingLot(${lot.id})">編集</button>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="deleteParkingLot(${lot.id})">削除</button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// 駐車場追加モーダルを表示
function showAddParkingModal() {
    currentParkingId = null;
    document.getElementById('parkingModalTitle').textContent = '駐車場を追加';
    document.getElementById('parkingNameInput').value = '';
    document.getElementById('parkingModal').style.display = 'flex';
}

// 駐車場編集モーダルを表示
function editParkingLot(parkingId) {
    const lot = parkingLots.find(p => p.id === parkingId);
    if (!lot) return;
    
    currentParkingId = parkingId;
    document.getElementById('parkingModalTitle').textContent = '駐車場を編集';
    document.getElementById('parkingNameInput').value = lot.parking_name;
    document.getElementById('parkingModal').style.display = 'flex';
}

// 駐車場を保存
async function saveParkingLot() {
    const parkingName = document.getElementById('parkingNameInput').value.trim();
    
    if (!parkingName) {
        alert('駐車場名を入力してください');
        return;
    }
    
    try {
        let url, method;
        if (currentParkingId) {
            // 更新
            url = `${window.settingsUrls.store}/settings/parking/${currentParkingId}`;
            method = 'PUT';
        } else {
            // 新規作成
            url = `${window.settingsUrls.store}/settings/parking/create`;
            method = 'POST';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ parking_name: parkingName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            closeParkingModal();
            loadParkingLots();
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('保存エラー:', error);
        showMessage('保存に失敗しました', 'error');
    }
}

// 駐車場を削除
async function deleteParkingLot(parkingId) {
    const lot = parkingLots.find(p => p.id === parkingId);
    if (!lot) return;
    
    if (!confirm(`「${lot.parking_name}」を削除してもよろしいですか？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/parking/${parkingId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadParkingLots();
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('削除エラー:', error);
        showMessage('削除に失敗しました', 'error');
    }
}

// 駐車場モーダルを閉じる
function closeParkingModal() {
    document.getElementById('parkingModal').style.display = 'none';
    currentParkingId = null;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シフト種別管理
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let shiftTypes = [];
let currentShiftTypeId = null;

// シフト種別を読み込み
async function loadShiftTypes() {
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/shift_types`);
        const data = await response.json();
        
        if (data.success) {
            shiftTypes = data.shift_types;
            renderShiftTypes();
        }
    } catch (error) {
        console.error('シフト種別の読み込みエラー:', error);
    }
}

// シフト種別一覧を表示
function renderShiftTypes() {
    const container = document.getElementById('shiftTypeList');
    if (!container) return;
    
    if (shiftTypes.length === 0) {
        container.innerHTML = '<p class="settings-empty-message">登録されているシフト種別はありません</p>';
        return;
    }
    
    let html = '<div class="shift-type-items">';
    shiftTypes.forEach(type => {
        html += `
            <div class="shift-type-item" style="border-left: 4px solid ${type.color}">
                <div class="shift-type-info">
                    <span class="shift-type-name">${escapeHtml(type.shift_name)}</span>
                    <span class="shift-type-badge ${type.is_work_day ? 'badge-work' : 'badge-off'}">
                        ${type.is_work_day ? '出勤日' : '休日'}
                    </span>
                </div>
                <div class="shift-type-actions">
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="editShiftType(${type.shift_type_id})">編集</button>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="deleteShiftType(${type.shift_type_id})">削除</button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// シフト種別追加モーダルを表示
function showAddShiftTypeModal() {
    currentShiftTypeId = null;
    document.getElementById('shiftTypeModalTitle').textContent = 'シフト種別を追加';
    document.getElementById('shiftTypeNameInput').value = '';
    document.getElementById('shiftTypeIsWorkDay').checked = true;
    document.getElementById('shiftTypeColorInput').value = '#4CAF50';
    document.getElementById('shiftTypeColorText').value = '#4CAF50';
    document.getElementById('shiftTypeModal').style.display = 'flex';
}

// シフト種別編集モーダルを表示
function editShiftType(shiftTypeId) {
    const type = shiftTypes.find(t => t.shift_type_id === shiftTypeId);
    if (!type) return;
    
    currentShiftTypeId = shiftTypeId;
    document.getElementById('shiftTypeModalTitle').textContent = 'シフト種別を編集';
    document.getElementById('shiftTypeNameInput').value = type.shift_name;
    document.getElementById('shiftTypeIsWorkDay').checked = type.is_work_day;
    document.getElementById('shiftTypeColorInput').value = type.color;
    document.getElementById('shiftTypeColorText').value = type.color;
    document.getElementById('shiftTypeModal').style.display = 'flex';
}

// シフト種別を保存
async function saveShiftType() {
    const shiftName = document.getElementById('shiftTypeNameInput').value.trim();
    const isWorkDay = document.getElementById('shiftTypeIsWorkDay').checked;
    const color = document.getElementById('shiftTypeColorInput').value;
    
    if (!shiftName) {
        alert('シフト名を入力してください');
        return;
    }
    
    try {
        let url, method;
        if (currentShiftTypeId) {
            // 更新
            url = `${window.settingsUrls.store}/settings/shift_types/${currentShiftTypeId}`;
            method = 'PUT';
        } else {
            // 新規作成
            url = `${window.settingsUrls.store}/settings/shift_types/create`;
            method = 'POST';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                shift_name: shiftName,
                is_work_day: isWorkDay,
                color: color
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            closeShiftTypeModal();
            loadShiftTypes();
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('保存エラー:', error);
        showMessage('保存に失敗しました', 'error');
    }
}

// シフト種別を削除
async function deleteShiftType(shiftTypeId) {
    const type = shiftTypes.find(t => t.shift_type_id === shiftTypeId);
    if (!type) return;
    
    if (!confirm(`「${type.shift_name}」を削除してもよろしいですか？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/shift_types/${shiftTypeId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadShiftTypes();
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('削除エラー:', error);
        showMessage('削除に失敗しました', 'error');
    }
}

// シフト種別モーダルを閉じる
function closeShiftTypeModal() {
    document.getElementById('shiftTypeModal').style.display = 'none';
    currentShiftTypeId = null;
}

// 色ピッカーの連動
document.addEventListener('DOMContentLoaded', function() {
    const colorInput = document.getElementById('shiftTypeColorInput');
    const colorText = document.getElementById('shiftTypeColorText');
    
    if (colorInput && colorText) {
        colorInput.addEventListener('change', function() {
            colorText.value = this.value;
        });
        
        colorText.addEventListener('input', function() {
            if (/^#[0-9A-Fa-f]{6}$/.test(this.value)) {
                colorInput.value = this.value;
            }
        });
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    console.log('Settings initialized');
    
    // ❌ これをコメントアウトまたは削除
    // loadParkingLots();
    // loadShiftTypes();
    
    // ✅ タブ切り替え時に読み込むようにする
    document.querySelectorAll('.settings-tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.textContent.trim();
            
            // 駐車場設定タブがクリックされたときだけ読み込み
            if (tabName.includes('駐車場')) {
                setTimeout(() => loadParkingLots(), 100);
            }
            
            // シフト種別設定タブがクリックされたときだけ読み込み
            if (tabName.includes('シフト種別')) {
                setTimeout(() => loadShiftTypes(), 100);
            }
        });
    });
});