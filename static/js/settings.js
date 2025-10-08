// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// タブ切り替え
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function switchTab(tabName) {
    // 全てのタブコンテンツを非表示
    const tabContents = document.querySelectorAll('.settings-tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // 全てのタブボタンを非アクティブ
    const tabButtons = document.querySelectorAll('.settings-tab-btn');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 選択されたタブを表示
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // 選択されたタブボタンをアクティブ
    event.target.classList.add('active');
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// パスワード表示/非表示
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const btn = event.target;
    
    if (field.type === 'password') {
        field.type = 'text';
        btn.textContent = '非表示';
    } else {
        field.type = 'password';
        btn.textContent = '表示';
    }
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 設定保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function saveSettings() {
    const form = document.getElementById('settingsForm');
    const formData = new FormData(form);
    
    // チェックボックスの処理
    const checkboxes = form.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        if (!checkbox.checked) {
            formData.set(checkbox.name, 'false');
        } else {
            formData.set(checkbox.name, 'true');
        }
    });
    
    // 保存中メッセージ
    showMessage('保存中...', 'info');
    
    // POSTリクエスト
    fetch(window.settingsUrls.save, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, 'success');
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('保存に失敗しました', 'error');
    });
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// テスト発信
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function testCall() {
    const phoneInput = document.getElementById('test_phone_number');
    const phoneNumber = phoneInput.value.trim();
    
    if (!phoneNumber) {
        showTestResult('電話番号を入力してください', 'error');
        return;
    }
    
    // 発信中メッセージ
    showTestResult('発信中...', 'info');
    
    // POSTリクエスト
    fetch(window.settingsUrls.testCall, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            phone_number: phoneNumber
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showTestResult(data.message, 'success');
        } else {
            showTestResult(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTestResult('発信に失敗しました', 'error');
    });
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// メッセージ表示
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function showMessage(message, type) {
    const messageDiv = document.getElementById('saveMessage');
    messageDiv.textContent = message;
    messageDiv.className = 'settings-message settings-message-' + type;
    messageDiv.style.display = 'block';
    
    // 3秒後に非表示
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 3000);
}

function showTestResult(message, type) {
    const resultDiv = document.getElementById('testCallResult');
    resultDiv.textContent = message;
    resultDiv.className = 'settings-test-result settings-test-result-' + type;
    resultDiv.style.display = 'block';
    
    // 5秒後に非表示
    setTimeout(() => {
        resultDiv.style.display = 'none';
    }, 5000);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 駐車場管理
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// 駐車場管理用の変数
let currentParkingId = null;
let parkingLots = [];

// 駐車場設定を読み込み
async function loadParkingSettings() {
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/parking`);
        const data = await response.json();
        
        if (data.success) {
            parkingLots = data.parking_lots;
            document.getElementById('parking_enabled').checked = data.parking_enabled;
            toggleParkingFeature(data.parking_enabled);
            renderParkingList();
        }
    } catch (error) {
        console.error('駐車場設定の読み込みエラー:', error);
    }
}

// 駐車場機能のON/OFF切り替え
function toggleParkingFeature(enabled) {
    const section = document.getElementById('parkingListSection');
    section.style.display = enabled ? 'block' : 'none';
    
    // チェックボックスの状態を設定に保存
    if (enabled !== document.getElementById('parking_enabled').checked) {
        return; // 初期化時はスキップ
    }
    
    saveParkingEnabled(enabled);
}

// 駐車場機能の有効/無効を保存
async function saveParkingEnabled(enabled) {
    try {
        // 🔧 現在の全ての設定値を取得
        const form = document.getElementById('settingsForm');
        const formData = new FormData(form);
        
        // 🔧 全てのチェックボックスを処理
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            if (!checkbox.checked) {
                formData.set(checkbox.name, 'false');
            } else {
                formData.set(checkbox.name, 'true');
            }
        });
        
        // 🔧 駐車場設定を上書き（最優先）
        formData.set('parking_enabled', enabled ? 'true' : 'false');
        
        const response = await fetch(`${window.settingsUrls.save}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            // メッセージは表示しない（自動保存だから）
        }
    } catch (error) {
        console.error('保存エラー:', error);
        showMessage('保存に失敗しました', 'error');
    }
}

// 駐車場一覧を表示
function renderParkingList() {
    const listContainer = document.getElementById('parkingList');
    
    if (parkingLots.length === 0) {
        listContainer.innerHTML = '<p class="no-parking-message">登録されている駐車場はありません</p>';
        return;
    }
    
    let html = '';
    parkingLots.forEach(parking => {
        html += `
            <div class="parking-item">
                <span class="parking-name">${escapeHtml(parking.parking_name)}</span>
                <div class="parking-actions">
                    <button type="button" class="settings-btn-small settings-btn-edit" onclick="editParking(${parking.parking_id})">編集</button>
                    <button type="button" class="settings-btn-small settings-btn-delete" onclick="deleteParking(${parking.parking_id})">削除</button>
                </div>
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
}

// 駐車場追加モーダルを表示
function showAddParkingModal() {
    currentParkingId = null;
    document.getElementById('parkingModalTitle').textContent = '駐車場を追加';
    document.getElementById('parkingNameInput').value = '';
    document.getElementById('parkingModal').style.display = 'flex';
}

// 駐車場編集モーダルを表示
function editParking(parkingId) {
    const parking = parkingLots.find(p => p.parking_id === parkingId);
    if (!parking) return;
    
    currentParkingId = parkingId;
    document.getElementById('parkingModalTitle').textContent = '駐車場を編集';
    document.getElementById('parkingNameInput').value = parking.parking_name;
    document.getElementById('parkingModal').style.display = 'flex';
}

// モーダルを閉じる
function closeParkingModal() {
    document.getElementById('parkingModal').style.display = 'none';
    currentParkingId = null;
}

// 駐車場を保存（追加または更新）
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
            loadParkingSettings(); // 再読み込み
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('保存エラー:', error);
        showMessage('保存に失敗しました', 'error');
    }
}

// 駐車場を削除
async function deleteParking(parkingId) {
    const parking = parkingLots.find(p => p.parking_id === parkingId);
    if (!parking) return;
    
    if (!confirm(`「${parking.parking_name}」を削除してもよろしいですか？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/parking/${parkingId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadParkingSettings(); // 再読み込み
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('削除エラー:', error);
        showMessage('削除に失敗しました', 'error');
    }
}

// HTMLエスケープ
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    console.log('Settings page loaded');
    
    // 駐車場設定を読み込み
    loadParkingSettings();
});


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シフト種別管理
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let currentShiftTypeId = null;
let shiftTypes = [];

// シフト種別を読み込み
async function loadShiftTypes() {
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/shift_types`);
        const data = await response.json();
        
        if (data.success) {
            shiftTypes = data.shift_types;
            renderShiftTypeList();
        }
    } catch (error) {
        console.error('シフト種別の読み込みエラー:', error);
    }
}

// シフト種別一覧を表示
function renderShiftTypeList() {
    const listContainer = document.getElementById('shiftTypeList');
    
    if (shiftTypes.length === 0) {
        listContainer.innerHTML = '<p class="no-data-message">登録されているシフト種別はありません</p>';
        return;
    }
    
    let html = '';
    shiftTypes.forEach(shiftType => {
        const workDayLabel = shiftType.is_work_day ? '出勤' : '休日';
        html += `
            <div class="shift-type-item">
                <div class="shift-type-info">
                    <span class="shift-type-color-box" style="background-color: ${shiftType.color}"></span>
                    <span class="shift-type-name">${escapeHtml(shiftType.shift_name)}</span>
                    <span class="shift-type-badge">${workDayLabel}</span>
                </div>
                <div class="shift-type-actions">
                    <button type="button" class="settings-btn-small settings-btn-move" onclick="moveShiftType(${shiftType.shift_type_id}, 'up')" title="上へ">↑</button>
                    <button type="button" class="settings-btn-small settings-btn-move" onclick="moveShiftType(${shiftType.shift_type_id}, 'down')" title="下へ">↓</button>
                    <button type="button" class="settings-btn-small settings-btn-edit" onclick="editShiftType(${shiftType.shift_type_id})">編集</button>
                    <button type="button" class="settings-btn-small settings-btn-delete" onclick="deleteShiftType(${shiftType.shift_type_id})">削除</button>
                </div>
            </div>
        `;
    });
    
    listContainer.innerHTML = html;
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
    const shiftType = shiftTypes.find(st => st.shift_type_id === shiftTypeId);
    if (!shiftType) return;
    
    currentShiftTypeId = shiftTypeId;
    document.getElementById('shiftTypeModalTitle').textContent = 'シフト種別を編集';
    document.getElementById('shiftTypeNameInput').value = shiftType.shift_name;
    document.getElementById('shiftTypeIsWorkDay').checked = shiftType.is_work_day;
    document.getElementById('shiftTypeColorInput').value = shiftType.color;
    document.getElementById('shiftTypeColorText').value = shiftType.color;
    document.getElementById('shiftTypeModal').style.display = 'flex';
}

// モーダルを閉じる
function closeShiftTypeModal() {
    document.getElementById('shiftTypeModal').style.display = 'none';
    currentShiftTypeId = null;
}

// シフト種別を保存（追加または更新）
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
            loadShiftTypes(); // 再読み込み
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
    const shiftType = shiftTypes.find(st => st.shift_type_id === shiftTypeId);
    if (!shiftType) return;
    
    if (!confirm(`「${shiftType.shift_name}」を削除してもよろしいですか？`)) {
        return;
    }
    
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/shift_types/${shiftTypeId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadShiftTypes(); // 再読み込み
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('削除エラー:', error);
        showMessage('削除に失敗しました', 'error');
    }
}

// シフト種別の並び順を変更
async function moveShiftType(shiftTypeId, direction) {
    try {
        const response = await fetch(`${window.settingsUrls.store}/settings/shift_types/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                shift_type_id: shiftTypeId,
                direction: direction
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadShiftTypes(); // 再読み込み（メッセージ不要）
        } else {
            showMessage(data.message, 'error');
        }
        
    } catch (error) {
        console.error('並び順変更エラー:', error);
        showMessage('並び順の変更に失敗しました', 'error');
    }
}

// カラーピッカーとテキスト入力の同期
document.addEventListener('DOMContentLoaded', function() {
    const colorInput = document.getElementById('shiftTypeColorInput');
    const colorText = document.getElementById('shiftTypeColorText');
    
    if (colorInput && colorText) {
        colorInput.addEventListener('input', function() {
            colorText.value = this.value;
        });
        
        colorText.addEventListener('input', function() {
            if (/^#[0-9A-Fa-f]{6}$/.test(this.value)) {
                colorInput.value = this.value;
            }
        });
    }
    
    // シフト種別を読み込み
    loadShiftTypes();
});