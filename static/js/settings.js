// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Settings.js - 設定管理メイン（デバッグ版）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// フラッシュメッセージの自動非表示と閉じるボタン
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.settings-flash').forEach(function(flash) {
        // 閉じるボタンのクリックイベント
        const closeBtn = flash.querySelector('.settings-flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                flash.style.display = 'none';
            });
        }

        // 5秒後に自動的に非表示
        setTimeout(function() {
            flash.style.opacity = '0';
            setTimeout(function() {
                flash.style.display = 'none';
            }, 300);
        }, 5000);
    });
});

(function() {
    'use strict';

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // グローバル変数（即時関数内のみ）
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    let currentParkingId = null;
    let currentShiftTypeId = null;
    let parkingLotsData = [];
    let shiftTypesData = [];
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // タブ切り替え（window に公開）
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    window.switchTab = function(tabName) {
        // すべてのタブコンテンツを非表示
        document.querySelectorAll('.settings-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // すべてのタブボタンの active クラスを削除
        document.querySelectorAll('.settings-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // 選択されたタブを表示
        const selectedTab = document.getElementById(tabName);
        if (selectedTab) {
            selectedTab.classList.add('active');
        }
        
        // 対応するボタンに active クラスを追加
        const buttons = document.querySelectorAll('.settings-tab-btn');
        buttons.forEach(btn => {
            if (btn.textContent.includes(getTabLabel(tabName))) {
                btn.classList.add('active');
            }
        });
        
        // タブに応じたデータ読み込み
        if (tabName === 'parking') {
            setTimeout(() => loadParkingLots(), 100);
        } else if (tabName === 'shift_types') {
            setTimeout(() => loadShiftTypes(), 100);
        }
    };
    
    function getTabLabel(tabName) {
        const labels = {
            'reservation_info': '予約情報',
            'notification': '通知設定',
            'auto_call': 'オートコール',
            'parking': '駐車場',
            'shift_types': 'シフト種別',
            'customer_info': '顧客情報',
            'ng_items': 'キャストNG項目'
        };
        return labels[tabName] || '';
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // パスワード表示切り替え（window に公開）
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    window.togglePassword = function(fieldId) {
        const field = document.getElementById(fieldId);
        const btn = field.nextElementSibling;
        
        if (field.type === 'password') {
            field.type = 'text';
            btn.textContent = '非表示';
        } else {
            field.type = 'password';
            btn.textContent = '表示';
        }
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 設定保存（タブ別）- デバッグ版
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    // 通知設定の保存
    window.saveNotificationSettings = async function() {
        const formData = new FormData();
        
        // 通知設定タブ内の要素のみ取得
        const notificationTab = document.getElementById('notification');
        if (!notificationTab) {
            console.error('❌ 通知設定タブが見つかりません');
            return;
        }
        
        console.log('🔍 通知設定を保存します');
        console.log('📋 通知設定タブの全input要素をチェック:');
        
        const inputs = notificationTab.querySelectorAll('input[type="checkbox"], input[type="text"], input[type="email"], textarea');
        console.log(`  見つかったinput数: ${inputs.length}`);
        
        inputs.forEach((input, index) => {
            console.log(`  [${index}] id="${input.id}" name="${input.name}" type="${input.type}"`);
            
            if (input.id && input.name) {
                if (input.type === 'checkbox') {
                    const value = input.checked ? 'true' : 'false';
                    formData.append(input.name, value);
                    console.log(`    ✅ チェックボックス追加: ${input.name} = ${value} (checked: ${input.checked})`);
                } else {
                    formData.append(input.name, input.value);
                    console.log(`    ✅ テキスト追加: ${input.name} = ${input.value}`);
                }
            } else {
                console.warn(`    ⚠️ スキップ (idまたはnameが無い): id="${input.id}" name="${input.name}"`);
            }
        });
        
        console.log('📤 送信するFormDataの内容:');
        let count = 0;
        for (let [key, value] of formData.entries()) {
            console.log(`  [${count++}] ${key}: ${value}`);
        }
        
        await saveFormData(formData, '通知設定');
    };
    
    // オートコール設定の保存
    window.saveAutoCallSettings = async function() {
        const formData = new FormData();
        
        // オートコールタブ内の要素のみ取得
        const autoCallTab = document.getElementById('auto_call');
        if (!autoCallTab) {
            console.error('❌ オートコールタブが見つかりません');
            return;
        }
        
        console.log('🔍 オートコール設定を保存します');
        console.log('📋 オートコールタブの全input要素をチェック:');
        
        const inputs = autoCallTab.querySelectorAll('input[type="checkbox"], input[type="text"], input[type="number"], input[type="password"], textarea');
        console.log(`  見つかったinput数: ${inputs.length}`);
        
        inputs.forEach((input, index) => {
            console.log(`  [${index}] id="${input.id}" name="${input.name}" type="${input.type}"`);
            
            if (input.id && input.name) {
                if (input.type === 'checkbox') {
                    const value = input.checked ? 'true' : 'false';
                    formData.append(input.name, value);
                    console.log(`    ✅ チェックボックス追加: ${input.name} = ${value} (checked: ${input.checked})`);
                } else {
                    formData.append(input.name, input.value);
                    console.log(`    ✅ その他追加: ${input.name} = ${input.value}`);
                }
            } else {
                console.warn(`    ⚠️ スキップ (idまたはnameが無い): id="${input.id}" name="${input.name}"`);
            }
        });
        
        console.log('📤 送信するFormDataの内容:');
        let count = 0;
        for (let [key, value] of formData.entries()) {
            console.log(`  [${count++}] ${key}: ${value}`);
        }
        
        await saveFormData(formData, 'オートコール設定');
    };
    
    // 予約情報設定の保存
    window.saveReservationSettings = async function() {
        const formData = new FormData();
        
        // 予約情報タブ内の要素のみ取得
        const reservationTab = document.getElementById('reservation_info');
        if (!reservationTab) return;
        
        reservationTab.querySelectorAll('input[type="checkbox"], input[type="text"], input[type="number"], textarea').forEach(input => {
            if (input.id && input.name) {
                if (input.type === 'checkbox') {
                    formData.append(input.name, input.checked ? 'true' : 'false');
                } else {
                    formData.append(input.name, input.value);
                }
            }
        });
        
        await saveFormData(formData, '予約情報設定');
    };
    
    // 共通保存処理
    async function saveFormData(formData, settingName) {
        try {
            console.log(`📡 ${settingName}をサーバーに送信中...`);
            
            const response = await fetch(window.settingsUrls.save, {
                method: 'POST',
                body: formData
            });
            
            console.log(`📥 サーバーからのレスポンス (status: ${response.status})`);
            
            const data = await response.json();
            console.log('📦 レスポンスデータ:', data);
            
            if (data.success) {
                showMessage(`${settingName}を保存しました`, 'success');
                console.log(`✅ ${settingName}の保存に成功`);
            } else {
                showMessage(`${settingName}の保存に失敗しました: ${data.message || ''}`, 'error');
                console.error(`❌ ${settingName}の保存に失敗:`, data);
            }
            
        } catch (error) {
            console.error(`❌ ${settingName}の保存中にエラー:`, error);
            showMessage(`${settingName}の保存中にエラーが発生しました`, 'error');
        }
    }
    
    // 互換性のため、旧関数名も残す
    window.saveSettings = window.saveNotificationSettings;
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // テストコール（window に公開）
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    window.testCall = async function() {
        const phoneNumber = document.getElementById('test_phone_number').value;
        const resultDiv = document.getElementById('testCallResult');
        
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
            resultDiv.innerHTML = '<div class="settings-alert settings-alert-error">テストコールに失敗しました</div>';
        }
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // メッセージ表示
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function showMessage(message, type) {
        // 既存のメッセージを削除
        const existingMessages = document.querySelectorAll('.settings-flash-dynamic');
        existingMessages.forEach(msg => msg.remove());

        // 新しいメッセージ要素を作成
        const flashDiv = document.createElement('div');
        flashDiv.className = `settings-flash settings-flash-${type === 'success' ? 'success' : 'error'} settings-flash-dynamic`;
        flashDiv.textContent = message;

        // 閉じるボタンを追加
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'settings-flash-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = function() {
            flashDiv.style.display = 'none';
        };
        flashDiv.appendChild(closeBtn);

        // ページに追加
        document.body.appendChild(flashDiv);

        // 5秒後に自動的に非表示
        setTimeout(function() {
            flashDiv.style.opacity = '0';
            setTimeout(function() {
                flashDiv.remove();
            }, 300);
        }, 5000);
    }

    // グローバルに公開
    window.showMessage = showMessage;
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 駐車場管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async function loadParkingLots() {
        try {
            const response = await fetch(`${window.settingsUrls.store}/settings/parking_lots`);
            const data = await response.json();
            
            if (data.success) {
                parkingLotsData = data.parking_lots || [];
                renderParkingLots();
            }
            
        } catch (error) {
        }
    }
    
    function renderParkingLots() {
        const listDiv = document.getElementById('parkingList');
        
        if (!parkingLotsData || parkingLotsData.length === 0) {
            listDiv.innerHTML = '<p class="settings-empty-message">登録されている駐車場がありません</p>';
            return;
        }
        
        listDiv.innerHTML = parkingLotsData.map(lot => `
            <div class="parking-item">
                <span class="parking-name">${escapeHtml(lot.parking_name)}</span>
                <div class="parking-actions">
                    <button type="button" class="settings-action-btn"
                            onclick="editParkingLot(${lot.parking_id})"
                            title="編集">
                        <i class="fas fa-pencil-alt settings-edit-icon"></i>
                    </button>
                    <button type="button" class="settings-action-btn"
                            onclick="deleteParkingLot(${lot.parking_id})"
                            title="削除">
                        <i class="fas fa-trash-alt settings-delete-icon"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    window.showAddParkingModal = function() {
        currentParkingId = null;
        document.getElementById('parkingModalTitle').textContent = '駐車場を追加';
        document.getElementById('parkingNameInput').value = '';
        document.getElementById('parkingModal').style.display = 'block';
    };
    
    window.editParkingLot = function(parkingId) {
        const lot = parkingLotsData.find(p => p.parking_id === parkingId);
        if (!lot) return;
        
        currentParkingId = parkingId;
        document.getElementById('parkingModalTitle').textContent = '駐車場を編集';
        document.getElementById('parkingNameInput').value = lot.parking_name;
        document.getElementById('parkingModal').style.display = 'block';
    };
    
    window.saveParkingLot = async function() {
        const name = document.getElementById('parkingNameInput').value.trim();
        
        if (!name) {
            showMessage('駐車場名を入力してください', 'error');
            return;
        }
        
        const url = currentParkingId 
            ? `${window.settingsUrls.store}/settings/parking_lots/${currentParkingId}`
            : `${window.settingsUrls.store}/settings/parking_lots`;
        
        const method = currentParkingId ? 'PUT' : 'POST';
        
        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ parking_name: name })
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
            showMessage('保存に失敗しました', 'error');
        }
    };
    
    window.deleteParkingLot = async function(parkingId) {
        const lot = parkingLotsData.find(p => p.parking_id === parkingId);
        
        if (!lot || !confirm(`「${lot.parking_name}」を削除してもよろしいですか？`)) {
            return;
        }
        
        try {
            const response = await fetch(`${window.settingsUrls.store}/settings/parking_lots/${parkingId}`, {
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
            showMessage('削除に失敗しました', 'error');
        }
    };
    
    window.closeParkingModal = function() {
        document.getElementById('parkingModal').style.display = 'none';
        currentParkingId = null;
    };
    
    window.toggleParkingFeature = async function(enabled) {
        
        const section = document.getElementById('parkingListSection');
        if (enabled) {
            section.style.display = 'block';
            loadParkingLots();
        } else {
            section.style.display = 'none';
        }
        
        // 駐車場設定を自動保存
        try {
            const formData = new FormData();
            formData.append('parking_enabled', enabled ? 'true' : 'false');
            
            
            const response = await fetch(window.settingsUrls.save, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('駐車場設定を保存しました', 'success');
            } else {
                showMessage('駐車場設定の保存に失敗しました', 'error');
            }
        } catch (error) {
            showMessage('駐車場設定の保存に失敗しました', 'error');
        }
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // シフト種別管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async function loadShiftTypes() {
        try {
            const response = await fetch(`${window.settingsUrls.store}/settings/shift_types`);
            const data = await response.json();
            
            if (data.success) {
                shiftTypesData = data.shift_types || [];
                renderShiftTypes();
            }
            
        } catch (error) {
        }
    }
    
    function renderShiftTypes() {
        const listDiv = document.getElementById('shiftTypeList');
        
        if (!shiftTypesData || shiftTypesData.length === 0) {
            listDiv.innerHTML = '<p class="settings-empty-message">登録されているシフト種別がありません</p>';
            return;
        }
        
        listDiv.innerHTML = shiftTypesData.map(type => `
            <div class="shift-type-item">
                <div class="shift-type-color" style="background-color: ${type.color}"></div>
                <span class="shift-type-name">${escapeHtml(type.shift_name)}</span>
                <span class="shift-type-badge ${type.is_work_day ? 'badge-work' : 'badge-off'}">
                    ${type.is_work_day ? '出勤' : '休日'}
                </span>
                <div class="shift-type-actions">
                    <button type="button" class="settings-action-btn"
                            onclick="editShiftType(${type.shift_type_id})"
                            title="編集">
                        <i class="fas fa-pencil-alt settings-edit-icon"></i>
                    </button>
                    <button type="button" class="settings-action-btn"
                            onclick="deleteShiftType(${type.shift_type_id})"
                            title="削除">
                        <i class="fas fa-trash-alt settings-delete-icon"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    window.showAddShiftTypeModal = function() {
        currentShiftTypeId = null;
        document.getElementById('shiftTypeModalTitle').textContent = 'シフト種別を追加';
        document.getElementById('shiftTypeNameInput').value = '';
        document.getElementById('shiftTypeIsWorkDay').checked = true;
        document.getElementById('shiftTypeColorInput').value = '#4CAF50';
        document.getElementById('shiftTypeColorText').value = '#4CAF50';
        document.getElementById('shiftTypeModal').style.display = 'block';
    };
    
    window.editShiftType = function(shiftTypeId) {
        const type = shiftTypesData.find(s => s.shift_type_id === shiftTypeId);
        if (!type) return;
        
        currentShiftTypeId = shiftTypeId;
        document.getElementById('shiftTypeModalTitle').textContent = 'シフト種別を編集';
        document.getElementById('shiftTypeNameInput').value = type.shift_name;
        document.getElementById('shiftTypeIsWorkDay').checked = type.is_work_day;
        document.getElementById('shiftTypeColorInput').value = type.color;
        document.getElementById('shiftTypeColorText').value = type.color;
        document.getElementById('shiftTypeModal').style.display = 'block';
    };
    
    window.saveShiftType = async function() {
        const name = document.getElementById('shiftTypeNameInput').value.trim();
        const isWorkDay = document.getElementById('shiftTypeIsWorkDay').checked;
        const color = document.getElementById('shiftTypeColorInput').value;
        
        if (!name) {
            showMessage('シフト名を入力してください', 'error');
            return;
        }
        
        const url = currentShiftTypeId 
            ? `${window.settingsUrls.store}/settings/shift_types/${currentShiftTypeId}`
            : `${window.settingsUrls.store}/settings/shift_types`;
        
        const method = currentShiftTypeId ? 'PUT' : 'POST';
        
        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    shift_name: name,
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
            showMessage('保存に失敗しました', 'error');
        }
    };
    
    window.deleteShiftType = async function(shiftTypeId) {
        const type = shiftTypesData.find(s => s.shift_type_id === shiftTypeId);
        
        if (!type || !confirm(`「${type.shift_name}」を削除してもよろしいですか？`)) {
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
            showMessage('削除に失敗しました', 'error');
        }
    };
    
    window.closeShiftTypeModal = function() {
        document.getElementById('shiftTypeModal').style.display = 'none';
        currentShiftTypeId = null;
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 色ピッカーの連動
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function initColorPicker() {
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
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // HTMLエスケープ
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 初期化
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    document.addEventListener('DOMContentLoaded', function() {
        console.log('⚙️ Settings.js 初期化開始');
        
        // 色ピッカー初期化
        initColorPicker();
        
        // 駐車場機能の初期表示チェック
        const parkingCheckbox = document.getElementById('parking_enabled');
        if (parkingCheckbox) {
            console.log(`🅿️ 駐車場チェックボックス: ${parkingCheckbox.checked}`);
            toggleParkingFeature(parkingCheckbox.checked);
        }
        
        console.log('✅ Settings.js 初期化完了');
    });
    
})();