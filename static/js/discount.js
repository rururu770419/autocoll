// ==========================================
// 割引マスタ管理 - JavaScript
// ==========================================

// ========== 初期化 ==========
document.addEventListener('DOMContentLoaded', function() {
    console.log('割引マスタ管理ページ初期化');
    updateRegisterValueLabel();
    initTypeButtons();
});

// ========== 種類ボタンの初期化 ==========
function initTypeButtons() {
    // 登録フォームの種類ボタン
    const registerTypeBtns = document.querySelectorAll('.discount-form-grid .discount-type-btn');
    registerTypeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                updateRegisterTypeButtons();
                updateRegisterValueLabel();
            }
        });
    });
    
    // 初期状態を設定
    updateRegisterTypeButtons();
}

// ========== 登録フォームの種類ボタンを更新 ==========
function updateRegisterTypeButtons() {
    const registerTypeBtns = document.querySelectorAll('.discount-form-grid .discount-type-btn');
    registerTypeBtns.forEach(btn => {
        const radio = btn.querySelector('input[type="radio"]');
        if (radio && radio.checked) {
            btn.classList.add('discount-type-btn-active');
        } else {
            btn.classList.remove('discount-type-btn-active');
        }
    });
}

// ========== 編集モーダルの種類ボタンを更新 ==========
function updateEditTypeButtons() {
    const editTypeBtns = document.querySelectorAll('.discount-modal-body .discount-type-btn');
    editTypeBtns.forEach(btn => {
        const radio = btn.querySelector('input[type="radio"]');
        if (radio && radio.checked) {
            btn.classList.add('discount-type-btn-active');
        } else {
            btn.classList.remove('discount-type-btn-active');
        }
    });
}

// ========== 登録フォーム操作 ==========

/**
 * 登録フォームの割引値ラベルを更新
 */
function updateRegisterValueLabel() {
    const discountType = document.querySelector('input[name="register_type"]:checked').value;
    const label = document.getElementById('register-value-label');
    const input = document.getElementById('register-value');
    const helpText = document.getElementById('register-help-text');
    const nameInput = document.getElementById('register-name');

    if (discountType === 'fixed') {
        label.innerHTML = '割引値 <span style="color: #dc3545;">*</span>';
        input.setAttribute('max', '999999');
        input.setAttribute('placeholder', '例）3000');
        helpText.textContent = '金額は円単位で入力してください';
        nameInput.setAttribute('placeholder', '例）イベント割引2000円OFF');
    } else {
        label.innerHTML = '割引値（%） <span style="color: #dc3545;">*</span>';
        input.setAttribute('max', '100');
        input.setAttribute('placeholder', '例）10');
        helpText.textContent = 'パーセント割引は100%以下で入力してください';
        nameInput.setAttribute('placeholder', '例）クーポン10％OFF');
    }
}

/**
 * 登録フォームをリセット
 */
function resetForm() {
    document.getElementById('discountForm').reset();
    document.querySelector('input[name="register_type"][value="fixed"]').checked = true;
    document.getElementById('register-is-active').checked = true;
    updateRegisterValueLabel();
    updateRegisterTypeButtons();
}

/**
 * 登録フォーム送信
 */
async function submitRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('register-name').value.trim();
    const discountType = document.querySelector('input[name="register_type"]:checked').value;
    const value = parseFloat(document.getElementById('register-value').value);
    const isActive = document.getElementById('register-is-active').checked;
    
    // バリデーション
    if (!name) {
        showMessage('割引名を入力してください', 'danger');
        return;
    }
    
    if (!value || value <= 0) {
        showMessage('割引値は0より大きい値を入力してください', 'danger');
        return;
    }
    
    if (discountType === 'percent' && value > 100) {
        showMessage('パーセント割引は100%以下で入力してください', 'danger');
        return;
    }
    
    const formData = {
        name: name,
        discount_type: discountType,
        value: value,
        is_active: isActive
    };
    
    try {
        const response = await fetch(`/${store}/discount_management/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            resetForm();
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showMessage(data.message || '登録に失敗しました', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('登録に失敗しました', 'danger');
    }
}

// ========== 編集モーダル操作 ==========

/**
 * 編集モーダルを表示
 */
async function openEditModal(discountId) {
    try {
        const response = await fetch(`/${store}/discount_management/api/get/${discountId}`);
        const data = await response.json();
        
        if (data.success) {
            const discount = data.discount;
            
            // フォームに値を設定
            document.getElementById('edit-discount-id').value = discount.discount_id;
            document.getElementById('edit-name').value = discount.name;
            document.querySelector(`input[name="edit_type"][value="${discount.discount_type}"]`).checked = true;
            document.getElementById('edit-value').value = Math.floor(discount.value);
            document.getElementById('edit-is-active').checked = discount.is_active;
            
            updateEditValueLabel();
            updateEditTypeButtons();
            
            // モーダルの種類ボタンにイベントリスナーを追加
            const editTypeBtns = document.querySelectorAll('.discount-modal-body .discount-type-btn');
            editTypeBtns.forEach(btn => {
                btn.onclick = function() {
                    const radio = this.querySelector('input[type="radio"]');
                    if (radio) {
                        radio.checked = true;
                        updateEditTypeButtons();
                        updateEditValueLabel();
                    }
                };
            });
            
            // モーダルを表示
            document.getElementById('editModal').classList.add('show');
        } else {
            showMessage(data.message || '割引の取得に失敗しました', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('割引の取得に失敗しました', 'danger');
    }
}

/**
 * 編集モーダルを閉じる
 */
function closeEditModal() {
    document.getElementById('editModal').classList.remove('show');
    document.getElementById('editForm').reset();
}

/**
 * 編集フォームの割引値ラベルを更新
 */
function updateEditValueLabel() {
    const discountType = document.querySelector('input[name="edit_type"]:checked').value;
    const label = document.getElementById('edit-value-label');
    const input = document.getElementById('edit-value');
    const nameInput = document.getElementById('edit-name');

    if (discountType === 'fixed') {
        label.innerHTML = '割引値 <span style="color: #dc3545;">*</span>';
        input.setAttribute('max', '999999');
        nameInput.setAttribute('placeholder', '例）イベント割引2000円OFF');
    } else {
        label.innerHTML = '割引値（%） <span style="color: #dc3545;">*</span>';
        input.setAttribute('max', '100');
        nameInput.setAttribute('placeholder', '例）クーポン10％OFF');
    }
}

/**
 * 編集フォーム送信
 */
async function submitEdit(event) {
    event.preventDefault();
    
    const discountId = document.getElementById('edit-discount-id').value;
    const name = document.getElementById('edit-name').value.trim();
    const discountType = document.querySelector('input[name="edit_type"]:checked').value;
    const value = parseFloat(document.getElementById('edit-value').value);
    const isActive = document.getElementById('edit-is-active').checked;
    
    // バリデーション
    if (!name) {
        showMessage('割引名を入力してください', 'danger');
        return;
    }
    
    if (!value || value <= 0) {
        showMessage('割引値は0より大きい値を入力してください', 'danger');
        return;
    }
    
    if (discountType === 'percent' && value > 100) {
        showMessage('パーセント割引は100%以下で入力してください', 'danger');
        return;
    }
    
    const formData = {
        name: name,
        discount_type: discountType,
        value: value,
        is_active: isActive
    };
    
    try {
        const response = await fetch(`/${store}/discount_management/api/update/${discountId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            closeEditModal();
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showMessage(data.message || '更新に失敗しました', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('更新に失敗しました', 'danger');
    }
}

// ========== 削除 ==========

/**
 * 割引を削除
 */
async function deleteDiscount(discountId, discountName) {
    if (!confirm(`「${discountName}」を削除してもよろしいですか？\n\n※予約で使用されている場合は削除できません。`)) {
        return;
    }
    
    try {
        const response = await fetch(`/${store}/discount_management/api/delete/${discountId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showMessage(data.message || '削除に失敗しました', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('削除に失敗しました', 'danger');
    }
}

// ========== 並び順変更 ==========

/**
 * 割引の並び順を変更
 */
async function moveDiscount(discountId, direction) {
    try {
        const response = await fetch(`/${store}/discount_management/api/move/${discountId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ direction: direction })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // ページをリロードして最新の順序を表示
            location.reload();
        } else {
            if (data.message && data.message.includes('移動できません')) {
                // 移動できない場合は何もしない（既に端）
            } else {
                showMessage(data.message || '移動に失敗しました', 'danger');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('移動に失敗しました', 'danger');
    }
}

// ========== メッセージ表示 ==========

/**
 * メッセージを表示
 */
function showMessage(message, type) {
    const messageArea = document.getElementById('discount-message-area');
    const alertClass = type === 'success' ? 'discount-alert-success' : 'discount-alert-danger';
    
    messageArea.innerHTML = `
        <div class="discount-alert ${alertClass}">
            ${message}
        </div>
    `;
    
    // 上部にスクロール
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // 3秒後に自動で消す
    setTimeout(() => {
        messageArea.innerHTML = '';
    }, 3000);
}