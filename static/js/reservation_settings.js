// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 予約設定ページ JavaScript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(function() {
    'use strict';
    
    console.log('Reservation Settings loaded');
    
    // ストアID
    let storeId = null;
    
    // 現在編集中のアイテム
    let currentEditItem = null;
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 初期化
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    document.addEventListener('DOMContentLoaded', function() {
        // 店舗IDを取得
        const pathParts = window.location.pathname.split('/');
        storeId = pathParts[1];
        
        console.log('Store ID:', storeId);
        
        // データを読み込み
        loadCancellationReasons();
        loadReservationMethods();
        loadCardFeeRate();
        loadNgAreas();
        loadNgAges();
        
        // イベントリスナーを設定
        setupEventListeners();
    });
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // イベントリスナー設定
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function setupEventListeners() {
        // キャンセル理由追加ボタン
        const addCancellationReasonBtn = document.getElementById('add-cancellation-reason-btn');
        if (addCancellationReasonBtn) {
            addCancellationReasonBtn.addEventListener('click', showAddCancellationReasonModal);
        }
        
        // 予約方法追加ボタン
        const addReservationMethodBtn = document.getElementById('add-reservation-method-btn');
        if (addReservationMethodBtn) {
            addReservationMethodBtn.addEventListener('click', showAddReservationMethodModal);
        }
        
        // カード手数料保存ボタン
        const saveCardFeeBtn = document.getElementById('save-card-fee-btn');
        if (saveCardFeeBtn) {
            saveCardFeeBtn.addEventListener('click', saveCardFeeRate);
        }
        
        // NGエリア追加ボタン
        const addNgAreaBtn = document.getElementById('add-ng-area-btn');
        if (addNgAreaBtn) {
            addNgAreaBtn.addEventListener('click', showAddNgAreaModal);
        }
        
        // 年齢NG追加ボタン
        const addNgAgeBtn = document.getElementById('add-ng-age-btn');
        if (addNgAgeBtn) {
            addNgAgeBtn.addEventListener('click', showAddNgAgeModal);
        }
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // タブ切り替え
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    window.switchTab = function(tabId) {
        // すべてのタブボタンとコンテンツを非アクティブに
        document.querySelectorAll('.settings-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelectorAll('.settings-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // 選択されたタブをアクティブに
        event.currentTarget.classList.add('active');
        document.getElementById(tabId).classList.add('active');
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // メッセージ表示
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function showMessage(message, type = 'success') {
        const messageDiv = document.getElementById('saveMessage');
        messageDiv.textContent = message;
        messageDiv.className = `settings-message settings-message-${type}`;
        messageDiv.style.display = 'block';
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // キャンセル理由管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadCancellationReasons() {
        fetch(`/${storeId}/reservation-settings/cancellation_reasons`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayCancellationReasons(data.data);
                } else {
                    console.error('Failed to load cancellation reasons');
                }
            })
            .catch(error => {
                console.error('Error loading cancellation reasons:', error);
            });
    }
    
    function displayCancellationReasons(reasons) {
        const tbody = document.getElementById('cancellation-reasons-tbody');
        
        if (!reasons || reasons.length === 0) {
            tbody.innerHTML = '<tr><td colspan=\"3\" class=\"settings-table-empty\">登録されているキャンセル理由はありません</td></tr>';
            return;
        }
        
        tbody.innerHTML = reasons.map(reason => `
            <tr>
                <td>${escapeHtml(reason.reason_name)}</td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="window.editCancellationReason(${reason.reason_id}, '${escapeHtml(reason.reason_name)}')">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="window.deleteCancellationReason(${reason.reason_id}, '${escapeHtml(reason.reason_name)}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    function showAddCancellationReasonModal() {
        currentEditItem = null;
        document.getElementById('cancellation-reason-modal-title').textContent = 'キャンセル理由を追加';
        document.getElementById('cancellation-reason-id').value = '';
        document.getElementById('cancellation-reason-name').value = '';
        document.getElementById('cancellation-reason-modal').style.display = 'flex';
    }
    
    window.editCancellationReason = function(id, name) {
        currentEditItem = { id, name };
        document.getElementById('cancellation-reason-modal-title').textContent = 'キャンセル理由を編集';
        document.getElementById('cancellation-reason-id').value = id;
        document.getElementById('cancellation-reason-name').value = name;
        document.getElementById('cancellation-reason-modal').style.display = 'flex';
    };
    
    window.closeCancellationReasonModal = function() {
        document.getElementById('cancellation-reason-modal').style.display = 'none';
        currentEditItem = null;
    };
    
    window.saveCancellationReason = function(event) {
        event.preventDefault();
        
        const id = document.getElementById('cancellation-reason-id').value;
        const name = document.getElementById('cancellation-reason-name').value;
        
        if (!name.trim()) {
            showMessage('理由名を入力してください', 'error');
            return;
        }
        
        const url = id 
            ? `/${storeId}/reservation-settings/cancellation_reasons/${id}`
            : `/${storeId}/reservation-settings/cancellation_reasons`;
        
        const method = id ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ reason_name: name })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                closeCancellationReasonModal();
                loadCancellationReasons();
            } else {
                showMessage(data.message || '保存に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving cancellation reason:', error);
            showMessage('保存中にエラーが発生しました', 'error');
        });
    };
    
    window.deleteCancellationReason = function(id, name) {
        if (!confirm(`「${name}」を削除してもよろしいですか？\n\n※ この理由が使用されている予約がある場合は削除できません。`)) {
            return;
        }
        
        fetch(`/${storeId}/reservation-settings/cancellation_reasons/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadCancellationReasons();
            } else {
                showMessage(data.message || '削除に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting cancellation reason:', error);
            showMessage('削除中にエラーが発生しました', 'error');
        });
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 予約方法管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadReservationMethods() {
        fetch(`/${storeId}/reservation-settings/reservation_methods`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayReservationMethods(data.data);
                } else {
                    console.error('Failed to load reservation methods');
                }
            })
            .catch(error => {
                console.error('Error loading reservation methods:', error);
            });
    }
    
    function displayReservationMethods(methods) {
        const tbody = document.getElementById('reservation-methods-tbody');
        
        if (!methods || methods.length === 0) {
            tbody.innerHTML = '<tr><td colspan=\"3\" class=\"settings-table-empty\">登録されている予約方法はありません</td></tr>';
            return;
        }
        
        tbody.innerHTML = methods.map(method => `
            <tr>
                <td>${escapeHtml(method.method_name)}</td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="window.editReservationMethod(${method.method_id}, '${escapeHtml(method.method_name)}')">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="window.deleteReservationMethod(${method.method_id}, '${escapeHtml(method.method_name)}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    function showAddReservationMethodModal() {
        currentEditItem = null;
        document.getElementById('reservation-method-modal-title').textContent = '予約方法を追加';
        document.getElementById('reservation-method-id').value = '';
        document.getElementById('reservation-method-name').value = '';
        document.getElementById('reservation-method-modal').style.display = 'flex';
    }
    
    window.editReservationMethod = function(id, name) {
        currentEditItem = { id, name };
        document.getElementById('reservation-method-modal-title').textContent = '予約方法を編集';
        document.getElementById('reservation-method-id').value = id;
        document.getElementById('reservation-method-name').value = name;
        document.getElementById('reservation-method-modal').style.display = 'flex';
    };
    
    window.closeReservationMethodModal = function() {
        document.getElementById('reservation-method-modal').style.display = 'none';
        currentEditItem = null;
    };
    
    window.saveReservationMethod = function(event) {
        event.preventDefault();
        
        const id = document.getElementById('reservation-method-id').value;
        const name = document.getElementById('reservation-method-name').value;
        
        if (!name.trim()) {
            showMessage('方法名を入力してください', 'error');
            return;
        }
        
        const url = id 
            ? `/${storeId}/reservation-settings/reservation_methods/${id}`
            : `/${storeId}/reservation-settings/reservation_methods`;
        
        const method = id ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ method_name: name })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                closeReservationMethodModal();
                loadReservationMethods();
            } else {
                showMessage(data.message || '保存に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving reservation method:', error);
            showMessage('保存中にエラーが発生しました', 'error');
        });
    };
    
    window.deleteReservationMethod = function(id, name) {
        if (!confirm(`「${name}」を削除してもよろしいですか？\n\n※ この方法が使用されている予約がある場合は削除できません。`)) {
            return;
        }
        
        fetch(`/${storeId}/reservation-settings/reservation_methods/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadReservationMethods();
            } else {
                showMessage(data.message || '削除に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting reservation method:', error);
            showMessage('削除中にエラーが発生しました', 'error');
        });
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // カード手数料管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadCardFeeRate() {
        fetch(`/${storeId}/reservation-settings/card_fee_rate`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const input = document.getElementById('card-fee-rate-input');
                    if (input) {
                        input.value = data.rate || 5.0;
                    }
                } else {
                    console.error('Failed to load card fee rate');
                }
            })
            .catch(error => {
                console.error('Error loading card fee rate:', error);
            });
    }
    
    function saveCardFeeRate() {
        const input = document.getElementById('card-fee-rate-input');
        const rate = parseFloat(input.value);
        
        if (isNaN(rate) || rate < 0 || rate > 100) {
            showMessage('カード手数料率は0〜100の範囲で入力してください', 'error');
            return;
        }
        
        fetch(`/${storeId}/reservation-settings/card_fee_rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ card_fee_rate: rate })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
            } else {
                showMessage(data.message || '保存に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving card fee rate:', error);
            showMessage('保存中にエラーが発生しました', 'error');
        });
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // NGエリア管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadNgAreas() {
        fetch(`/${storeId}/reservation-settings/ng_areas`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayNgAreas(data.data);
                } else {
                    console.error('Failed to load NG areas');
                }
            })
            .catch(error => {
                console.error('Error loading NG areas:', error);
            });
    }
    
    function displayNgAreas(areas) {
        const tbody = document.getElementById('ng-areas-tbody');
        
        if (!areas || areas.length === 0) {
            tbody.innerHTML = '<tr><td colspan=\"3\" class=\"settings-table-empty\">登録されているNGエリアはありません</td></tr>';
            return;
        }
        
        tbody.innerHTML = areas.map(area => `
            <tr>
                <td>${escapeHtml(area.area_name)}</td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="window.editNgArea(${area.ng_area_id}, '${escapeHtml(area.area_name)}')">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="window.deleteNgArea(${area.ng_area_id}, '${escapeHtml(area.area_name)}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    function showAddNgAreaModal() {
        currentEditItem = null;
        document.getElementById('ng-area-modal-title').textContent = '新規エリア追加';
        document.getElementById('ng-area-id').value = '';
        document.getElementById('ng-area-name').value = '';
        document.getElementById('ng-area-modal').style.display = 'flex';
    }
    
    window.editNgArea = function(id, name) {
        currentEditItem = { id, name };
        document.getElementById('ng-area-modal-title').textContent = 'エリアを編集';
        document.getElementById('ng-area-id').value = id;
        document.getElementById('ng-area-name').value = name;
        document.getElementById('ng-area-modal').style.display = 'flex';
    };
    
    window.closeNgAreaModal = function() {
        document.getElementById('ng-area-modal').style.display = 'none';
        currentEditItem = null;
    };
    
    window.saveNgArea = function(event) {
        event.preventDefault();
        
        const id = document.getElementById('ng-area-id').value;
        const name = document.getElementById('ng-area-name').value;
        
        if (!name.trim()) {
            showMessage('エリア名を入力してください', 'error');
            return;
        }
        
        const url = id 
            ? `/${storeId}/reservation-settings/ng_areas/${id}`
            : `/${storeId}/reservation-settings/ng_areas`;
        
        const method = id ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ area_name: name })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                closeNgAreaModal();
                loadNgAreas();
            } else {
                showMessage(data.message || '保存に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving NG area:', error);
            showMessage('保存中にエラーが発生しました', 'error');
        });
    };
    
    window.deleteNgArea = function(id, name) {
        if (!confirm(`「${name}」を削除してもよろしいですか？\n\n※ このエリアが使用されているキャストがいる場合は削除できません。`)) {
            return;
        }
        
        fetch(`/${storeId}/reservation-settings/ng_areas/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadNgAreas();
            } else {
                showMessage(data.message || '削除に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting NG area:', error);
            showMessage('削除中にエラーが発生しました', 'error');
        });
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 年齢NG管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadNgAges() {
        fetch(`/${storeId}/reservation-settings/ng_ages`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayNgAges(data.data);
                } else {
                    console.error('Failed to load NG ages');
                }
            })
            .catch(error => {
                console.error('Error loading NG ages:', error);
            });
    }
    
    function displayNgAges(ages) {
        const tbody = document.getElementById('ng-ages-tbody');
        
        if (!ages || ages.length === 0) {
            tbody.innerHTML = '<tr><td colspan=\"4\" class=\"settings-table-empty\">登録されている年齢NGはありません</td></tr>';
            return;
        }
        
        tbody.innerHTML = ages.map(age => `
            <tr>
                <td>${escapeHtml(age.pattern_name)}</td>
                <td>${age.description ? escapeHtml(age.description) : '-'}</td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-edit" 
                            onclick="window.editNgAge(${age.ng_age_id}, '${escapeHtml(age.pattern_name)}', '${escapeHtml(age.description || '')}')">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
                <td>
                    <button type="button" class="settings-btn-small settings-btn-delete" 
                            onclick="window.deleteNgAge(${age.ng_age_id}, '${escapeHtml(age.pattern_name)}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    function showAddNgAgeModal() {
        currentEditItem = null;
        document.getElementById('ng-age-modal-title').textContent = '新規年齢NG追加';
        document.getElementById('ng-age-id').value = '';
        document.getElementById('ng-age-pattern-name').value = '';
        document.getElementById('ng-age-description').value = '';
        document.getElementById('ng-age-modal').style.display = 'flex';
    }
    
    window.editNgAge = function(id, patternName, description) {
        currentEditItem = { id, patternName, description };
        document.getElementById('ng-age-modal-title').textContent = '年齢NGを編集';
        document.getElementById('ng-age-id').value = id;
        document.getElementById('ng-age-pattern-name').value = patternName;
        document.getElementById('ng-age-description').value = description || '';
        document.getElementById('ng-age-modal').style.display = 'flex';
    };
    
    window.closeNgAgeModal = function() {
        document.getElementById('ng-age-modal').style.display = 'none';
        currentEditItem = null;
    };
    
    window.saveNgAge = function(event) {
        event.preventDefault();
        
        const id = document.getElementById('ng-age-id').value;
        const patternName = document.getElementById('ng-age-pattern-name').value;
        const description = document.getElementById('ng-age-description').value;
        
        if (!patternName.trim()) {
            showMessage('パターン名を入力してください', 'error');
            return;
        }
        
        const url = id 
            ? `/${storeId}/reservation-settings/ng_ages/${id}`
            : `/${storeId}/reservation-settings/ng_ages`;
        
        const method = id ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                pattern_name: patternName,
                description: description
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                closeNgAgeModal();
                loadNgAges();
            } else {
                showMessage(data.message || '保存に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving NG age:', error);
            showMessage('保存中にエラーが発生しました', 'error');
        });
    };
    
    window.deleteNgAge = function(id, patternName) {
        if (!confirm(`「${patternName}」を削除してもよろしいですか？\n\n※ このパターンが使用されているキャストがいる場合は削除できません。`)) {
            return;
        }
        
        fetch(`/${storeId}/reservation-settings/ng_ages/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadNgAges();
            } else {
                showMessage(data.message || '削除に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting NG age:', error);
            showMessage('削除中にエラーが発生しました', 'error');
        });
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ユーティリティ関数
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
})();