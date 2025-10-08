// ==========================================
// settings_ng.js - キャストNG項目設定タブ（独立ファイル）
// ==========================================

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', function() {
    initializeNgItemsTab();
});

function initializeNgItemsTab() {
    // NG項目タブがクリックされたときにデータを読み込む
    const ngItemsTab = document.querySelector('[onclick*="ng_items"]');
    if (ngItemsTab) {
        ngItemsTab.addEventListener('click', function() {
            loadNgAreas();
            loadNgAges();
        });
    }
    
    // モーダル初期化
    initializeNgModals();
    
    // フォーム初期化
    initializeNgForms();
}

// ==========================================
// NGエリア管理
// ==========================================

function loadNgAreas() {
    fetch('/api/ng-areas')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('ng-areas-tbody');
            
            if (data.areas && data.areas.length > 0) {
                tbody.innerHTML = data.areas.map(area => `
                    <tr>
                        <td>${escapeHtml(area.area_name)}</td>
                        <td>
                            <button type="button" class="settings-table-action-btn settings-table-action-btn-edit" 
                                    onclick="editNgArea(${area.ng_area_id}, '${escapeHtml(area.area_name)}')">
                                編集
                            </button>
                            <button type="button" class="settings-table-action-btn settings-table-action-btn-delete" 
                                    onclick="deleteNgArea(${area.ng_area_id}, '${escapeHtml(area.area_name)}')">
                                削除
                            </button>
                        </td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="2" class="settings-table-empty">登録されているエリアはありません</td></tr>';
            }
        })
        .catch(error => {
            console.error('NGエリア取得エラー:', error);
            showNgMessage('NGエリアの取得に失敗しました', 'error');
        });
}

function editNgArea(areaId, areaName) {
    document.getElementById('ng-area-modal-title').textContent = 'エリア編集';
    document.getElementById('ng-area-id').value = areaId;
    document.getElementById('ng-area-name').value = areaName;
    openNgModal('ng-area-modal');
}

function deleteNgArea(areaId, areaName) {
    if (!confirm(`「${areaName}」を削除してもよろしいですか？\n\nこのエリアをNG設定しているキャストから紐付けも削除されます。`)) {
        return;
    }

    fetch(`/api/ng-areas/${areaId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNgMessage('エリアを削除しました', 'success');
            loadNgAreas();
        } else {
            showNgMessage(data.error || 'エリアの削除に失敗しました', 'error');
        }
    })
    .catch(error => {
        console.error('エリア削除エラー:', error);
        showNgMessage('エリアの削除に失敗しました', 'error');
    });
}

// ==========================================
// 年齢NG管理
// ==========================================

function loadNgAges() {
    fetch('/api/ng-ages')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('ng-ages-tbody');
            
            if (data.ages && data.ages.length > 0) {
                tbody.innerHTML = data.ages.map(age => `
                    <tr>
                        <td>${escapeHtml(age.pattern_name)}</td>
                        <td>${escapeHtml(age.description || '-')}</td>
                        <td>
                            <button type="button" class="settings-table-action-btn settings-table-action-btn-edit" 
                                    onclick="editNgAge(${age.ng_age_id}, '${escapeHtml(age.pattern_name)}', '${escapeHtml(age.description || '')}')">
                                編集
                            </button>
                            <button type="button" class="settings-table-action-btn settings-table-action-btn-delete" 
                                    onclick="deleteNgAge(${age.ng_age_id}, '${escapeHtml(age.pattern_name)}')">
                                削除
                            </button>
                        </td>
                    </tr>
                `).join('');
            } else {
                tbody.innerHTML = '<tr><td colspan="3" class="settings-table-empty">登録されている年齢NGはありません</td></tr>';
            }
        })
        .catch(error => {
            console.error('年齢NG取得エラー:', error);
            showNgMessage('年齢NGの取得に失敗しました', 'error');
        });
}

function editNgAge(ageId, patternName, description) {
    document.getElementById('ng-age-modal-title').textContent = '年齢NG編集';
    document.getElementById('ng-age-id').value = ageId;
    document.getElementById('ng-age-pattern-name').value = patternName;
    document.getElementById('ng-age-description').value = description;
    openNgModal('ng-age-modal');
}

function deleteNgAge(ageId, patternName) {
    if (!confirm(`「${patternName}」を削除してもよろしいですか？\n\nこの年齢NGを設定しているキャストから紐付けも削除されます。`)) {
        return;
    }

    fetch(`/api/ng-ages/${ageId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNgMessage('年齢NGを削除しました', 'success');
            loadNgAges();
        } else {
            showNgMessage(data.error || '年齢NGの削除に失敗しました', 'error');
        }
    })
    .catch(error => {
        console.error('年齢NG削除エラー:', error);
        showNgMessage('年齢NGの削除に失敗しました', 'error');
    });
}

// ==========================================
// モーダル管理
// ==========================================

function initializeNgModals() {
    // 新規追加ボタン
    const addAreaBtn = document.getElementById('add-ng-area-btn');
    if (addAreaBtn) {
        addAreaBtn.addEventListener('click', function() {
            document.getElementById('ng-area-modal-title').textContent = '新規エリア追加';
            document.getElementById('ng-area-form').reset();
            document.getElementById('ng-area-id').value = '';
            openNgModal('ng-area-modal');
        });
    }

    const addAgeBtn = document.getElementById('add-ng-age-btn');
    if (addAgeBtn) {
        addAgeBtn.addEventListener('click', function() {
            document.getElementById('ng-age-modal-title').textContent = '新規年齢NG追加';
            document.getElementById('ng-age-form').reset();
            document.getElementById('ng-age-id').value = '';
            openNgModal('ng-age-modal');
        });
    }

    // 閉じるボタン
    document.querySelectorAll('.settings-modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            closeNgModal(this.dataset.modal);
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', function() {
            closeNgModal(this.dataset.modalClose);
        });
    });

    // モーダル外クリックで閉じる
    document.querySelectorAll('.settings-modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeNgModal(this.id);
            }
        });
    });
}

function openNgModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
    }
}

function closeNgModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

// ==========================================
// フォーム送信
// ==========================================

function initializeNgForms() {
    // NGエリアフォーム
    const areaForm = document.getElementById('ng-area-form');
    if (areaForm) {
        areaForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const areaId = document.getElementById('ng-area-id').value;
            const areaName = document.getElementById('ng-area-name').value.trim();
            
            if (!areaName) {
                showNgMessage('エリア名を入力してください', 'error');
                return;
            }

            const url = areaId ? `/api/ng-areas/${areaId}` : '/api/ng-areas';
            const method = areaId ? 'PUT' : 'POST';

            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ area_name: areaName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNgMessage(areaId ? 'エリアを更新しました' : 'エリアを追加しました', 'success');
                    closeNgModal('ng-area-modal');
                    loadNgAreas();
                } else {
                    showNgMessage(data.error || 'エリアの保存に失敗しました', 'error');
                }
            })
            .catch(error => {
                console.error('エリア保存エラー:', error);
                showNgMessage('エリアの保存に失敗しました', 'error');
            });
        });
    }

    // 年齢NGフォーム
    const ageForm = document.getElementById('ng-age-form');
    if (ageForm) {
        ageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const ageId = document.getElementById('ng-age-id').value;
            const patternName = document.getElementById('ng-age-pattern-name').value.trim();
            const description = document.getElementById('ng-age-description').value.trim();
            
            if (!patternName) {
                showNgMessage('パターン名を入力してください', 'error');
                return;
            }

            const url = ageId ? `/api/ng-ages/${ageId}` : '/api/ng-ages';
            const method = ageId ? 'PUT' : 'POST';

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
                    showNgMessage(ageId ? '年齢NGを更新しました' : '年齢NGを追加しました', 'success');
                    closeNgModal('ng-age-modal');
                    loadNgAges();
                } else {
                    showNgMessage(data.error || '年齢NGの保存に失敗しました', 'error');
                }
            })
            .catch(error => {
                console.error('年齢NG保存エラー:', error);
                showNgMessage('年齢NGの保存に失敗しました', 'error');
            });
        });
    }
}

// ==========================================
// ユーティリティ関数
// ==========================================

function showNgMessage(message, type) {
    // settings.jsのshowMessage関数を使う（存在する場合）
    if (typeof showMessage === 'function') {
        showMessage(message, type);
        return;
    }
    
    // フォールバック: settings.jsがない場合
    const messageArea = document.getElementById('saveMessage');
    if (messageArea) {
        const alertClass = type === 'success' ? 'settings-alert-success' : 'settings-alert-error';
        
        messageArea.innerHTML = `
            <div class="settings-alert ${alertClass}">
                ${escapeHtml(message)}
            </div>
        `;
        
        messageArea.style.display = 'block';
        
        setTimeout(() => {
            messageArea.style.display = 'none';
            messageArea.innerHTML = '';
        }, 3000);
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
        alert(message);
    }
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}