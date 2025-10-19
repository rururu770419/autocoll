// 顧客情報設定タブのJavaScript

// グローバル変数
let customerFieldData = {
    categories: [],
    options: {}
};

let editingOptionId = null;
let editingCategoryKey = null;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    // 顧客情報タブのイベントリスナー設定
    const customerInfoTab = document.getElementById('customer-info-tab');
    if (customerInfoTab) {
        customerInfoTab.addEventListener('click', function() {
            setTimeout(loadCustomerFieldSettings, 100);
        });
    }
    
    // switchTab関数に顧客情報の読み込みを追加
    const originalSwitchTab = window.switchTab;
    if (originalSwitchTab) {
        window.switchTab = function(tabName) {
            originalSwitchTab(tabName);
            if (tabName === 'customer_info') {
                setTimeout(loadCustomerFieldSettings, 100);
            }
        };
    }
    
    // 初期表示が顧客情報タブの場合は読み込み
    const customerInfoContent = document.getElementById('customer_info');
    if (customerInfoContent && customerInfoContent.classList.contains('active')) {
        setTimeout(loadCustomerFieldSettings, 300);
    }
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// データ読み込み
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function loadCustomerFieldSettings() {
    try {
        const store = getStoreCode();
        
        const url = `/${store}/api/customer_fields`;
        
        const response = await fetch(url);
        
        const result = await response.json();
        
        if (result.success) {
            customerFieldData = result.data;
            renderCustomerFields();
        } else {
            showMessage('設定の読み込みに失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error loading customer fields:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// UI描画
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function renderCustomerFields() {
    const container = document.getElementById('customerFieldsContainer');
    if (!container) return;

    let html = '';

    customerFieldData.categories.forEach(category => {
        const options = customerFieldData.options[category.field_key] || [];

        html += `
            <div class="customer-field-section">
                <div class="customer-field-header">
                    <h4 class="customer-field-category-title">【${escapeHtml(category.field_label)}】</h4>
                    <button type="button" class="settings-btn settings-btn-link"
                            onclick="showCategoryEditModal('${category.field_key}', '${escapeHtml(category.field_label)}')">
                        名前を変更
                    </button>
                </div>

                <div class="customer-field-options-list">
                    ${options.map((option, index) => renderOptionItem(category.field_key, option, index, options.length)).join('')}
                </div>

                <button type="button" class="settings-btn settings-btn-secondary"
                        onclick="showAddOptionModal('${category.field_key}')">
                    項目を追加
                </button>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderOptionItem(fieldKey, option, index, totalCount) {
    const isVisible = !option.is_hidden;
    const isFirst = index === 0;
    const isLast = index === totalCount - 1;

    return `
        <div class="customer-field-item">
            <div class="customer-field-checkbox">
                <input type="checkbox"
                       class="customer-field-checkbox-input"
                       ${isVisible ? 'checked' : ''}
                       onchange="toggleOptionVisibility(${option.id}, this.checked)"
                       title="チェックON=表示、OFF=非表示">
            </div>

            <div class="customer-field-color-box" style="background-color: ${option.display_color}"></div>

            <span class="customer-field-name">${escapeHtml(option.option_value)}</span>

            <div class="customer-field-sort-buttons">
                <button type="button"
                        class="customer-field-sort-btn ${isFirst ? 'customer-field-sort-btn-disabled' : ''}"
                        onclick="moveOptionUp('${fieldKey}', ${option.id})"
                        ${isFirst ? 'disabled' : ''}
                        title="上に移動">
                    <i class="fas fa-chevron-up"></i>
                </button>
                <button type="button"
                        class="customer-field-sort-btn ${isLast ? 'customer-field-sort-btn-disabled' : ''}"
                        onclick="moveOptionDown('${fieldKey}', ${option.id})"
                        ${isLast ? 'disabled' : ''}
                        title="下に移動">
                    <i class="fas fa-chevron-down"></i>
                </button>
            </div>

            <div class="customer-field-actions">
                <button type="button" class="settings-action-btn"
                        onclick="showEditOptionModal(${option.id}, '${escapeHtml(option.option_value)}', '${option.display_color}')"
                        title="編集">
                    <i class="fas fa-pencil-alt settings-edit-icon"></i>
                </button>
                <button type="button" class="settings-action-btn"
                        onclick="deleteOption(${option.id})"
                        title="削除">
                    <i class="fas fa-trash-alt settings-delete-icon"></i>
                </button>
            </div>
        </div>
    `;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// カテゴリ名編集
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function showCategoryEditModal(fieldKey, currentLabel) {
    editingCategoryKey = fieldKey;
    
    const modal = document.getElementById('categoryEditModal');
    const input = document.getElementById('categoryLabelInput');
    
    input.value = currentLabel;
    modal.style.display = 'block';
}

async function saveCategoryLabel() {
    const newLabel = document.getElementById('categoryLabelInput').value.trim();
    
    if (!newLabel) {
        alert('カテゴリ名を入力してください');
        return;
    }
    
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/category`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                field_key: editingCategoryKey,
                field_label: newLabel
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('カテゴリ名を更新しました', 'success');
            closeCategoryEditModal();
            loadCustomerFieldSettings();
        } else {
            alert(result.message || '更新に失敗しました');
        }
    } catch (error) {
        console.error('Error saving category label:', error);
        alert('エラーが発生しました');
    }
}

function closeCategoryEditModal() {
    document.getElementById('categoryEditModal').style.display = 'none';
    editingCategoryKey = null;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 選択肢追加
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function showAddOptionModal(fieldKey) {
    editingCategoryKey = fieldKey;
    
    const modal = document.getElementById('optionAddModal');
    const input = document.getElementById('optionValueInput');
    const colorInput = document.getElementById('optionColorInput');
    
    input.value = '';
    colorInput.value = '#f0f0f0';
    updateColorPreview('optionColorInput', 'optionColorPreview');
    
    modal.style.display = 'block';
}

async function saveNewOption() {
    const optionValue = document.getElementById('optionValueInput').value.trim();
    const displayColor = document.getElementById('optionColorInput').value;
    
    if (!optionValue) {
        alert('項目名を入力してください');
        return;
    }
    
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                field_key: editingCategoryKey,
                option_value: optionValue,
                display_color: displayColor
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('項目を追加しました', 'success');
            closeOptionAddModal();
            loadCustomerFieldSettings();
        } else {
            alert(result.message || '追加に失敗しました');
        }
    } catch (error) {
        console.error('Error adding option:', error);
        alert('エラーが発生しました');
    }
}

function closeOptionAddModal() {
    document.getElementById('optionAddModal').style.display = 'none';
    editingCategoryKey = null;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 項目編集モーダル
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function showEditOptionModal(optionId, optionValue, displayColor) {
    editingOptionId = optionId;

    const modal = document.getElementById('customerFieldEditModal');
    const nameInput = document.getElementById('customerFieldNameInput');
    const colorInput = document.getElementById('customerFieldColorInput');
    const colorText = document.getElementById('customerFieldColorText');

    nameInput.value = optionValue;
    colorInput.value = displayColor;
    colorText.value = displayColor;

    modal.style.display = 'block';

    // 色ピッカーの連動を設定
    initCustomerFieldColorPicker();
}

function closeCustomerFieldEditModal() {
    document.getElementById('customerFieldEditModal').style.display = 'none';
    editingOptionId = null;
}

async function saveCustomerFieldEdit() {
    const optionValue = document.getElementById('customerFieldNameInput').value.trim();
    const displayColor = document.getElementById('customerFieldColorInput').value;

    if (!optionValue) {
        alert('項目名を入力してください');
        return;
    }

    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${editingOptionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                option_value: optionValue,
                display_color: displayColor
            })
        });

        const result = await response.json();

        if (result.success) {
            showMessage('項目を更新しました', 'success');
            closeCustomerFieldEditModal();
            loadCustomerFieldSettings();
        } else {
            alert(result.message || '更新に失敗しました');
        }
    } catch (error) {
        console.error('Error updating option:', error);
        alert('エラーが発生しました');
    }
}

// 色ピッカーの連動を初期化
function initCustomerFieldColorPicker() {
    const colorInput = document.getElementById('customerFieldColorInput');
    const colorText = document.getElementById('customerFieldColorText');

    if (colorInput && colorText) {
        // イベントリスナーを削除してから追加（重複防止）
        const newColorInput = colorInput.cloneNode(true);
        const newColorText = colorText.cloneNode(true);
        colorInput.parentNode.replaceChild(newColorInput, colorInput);
        colorText.parentNode.replaceChild(newColorText, colorText);

        newColorInput.addEventListener('change', function() {
            newColorText.value = this.value;
        });

        newColorText.addEventListener('input', function() {
            if (/^#[0-9A-Fa-f]{6}$/.test(this.value)) {
                newColorInput.value = this.value;
            }
        });
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 表示/非表示切り替え
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function toggleOptionVisibility(optionId, isChecked) {
    // チェックON = 表示 = is_hidden は false
    // チェックOFF = 非表示 = is_hidden は true
    const isHidden = !isChecked;

    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${optionId}/visibility`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_hidden: isHidden })
        });

        const result = await response.json();

        if (result.success) {
            showMessage(isChecked ? '表示しました' : '非表示にしました', 'success');
            loadCustomerFieldSettings();
        } else {
            alert(result.message || '更新に失敗しました');
        }
    } catch (error) {
        console.error('Error toggling visibility:', error);
        alert('エラーが発生しました');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 並び替え
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function moveOptionUp(fieldKey, optionId) {
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${optionId}/move`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction: 'up' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            loadCustomerFieldSettings();
        } else {
            alert(result.message || '移動に失敗しました');
        }
    } catch (error) {
        console.error('Error moving option up:', error);
        alert('エラーが発生しました');
    }
}

async function moveOptionDown(fieldKey, optionId) {
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${optionId}/move`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction: 'down' })
        });
        
        const result = await response.json();
        
        if (result.success) {
            loadCustomerFieldSettings();
        } else {
            alert(result.message || '移動に失敗しました');
        }
    } catch (error) {
        console.error('Error moving option down:', error);
        alert('エラーが発生しました');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 削除
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function deleteOption(optionId) {
    if (!confirm('この項目を削除しますか？\n※使用中の場合は削除できません')) {
        return;
    }
    
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${optionId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('項目を削除しました', 'success');
            loadCustomerFieldSettings();
        } else {
            alert(result.message);
        }
    } catch (error) {
        console.error('Error deleting option:', error);
        alert('エラーが発生しました');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function getContrastColor(hexColor) {
    // 背景色の明度を計算して、読みやすい文字色を返す
    const r = parseInt(hexColor.substr(1, 2), 16);
    const g = parseInt(hexColor.substr(3, 2), 16);
    const b = parseInt(hexColor.substr(5, 2), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 155 ? '#000000' : '#ffffff';
}

function updateColorPreview(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (input && preview) {
        const color = input.value;
        const textColor = getContrastColor(color);
        preview.style.backgroundColor = color;
        preview.style.color = textColor;
        preview.textContent = color;
    }
}

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
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function showMessage(message, type) {
    const messageArea = document.getElementById('saveMessage');
    if (!messageArea) return;
    
    messageArea.className = `settings-message settings-message-${type}`;
    messageArea.textContent = message;
    messageArea.style.display = 'block';
    
    setTimeout(() => {
        messageArea.style.display = 'none';
    }, 3000);
}

// モーダルクリック時の処理
window.onclick = function(event) {
    const categoryModal = document.getElementById('categoryEditModal');
    const optionModal = document.getElementById('optionAddModal');
    const editModal = document.getElementById('customerFieldEditModal');

    if (event.target === categoryModal) {
        closeCategoryEditModal();
    }
    if (event.target === optionModal) {
        closeOptionAddModal();
    }
    if (event.target === editModal) {
        closeCustomerFieldEditModal();
    }
}