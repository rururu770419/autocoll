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
                    <h3 class="customer-field-title">【${escapeHtml(category.field_label)}】</h3>
                    <button type="button" class="settings-btn settings-btn-link" 
                            onclick="showCategoryEditModal('${category.field_key}', '${escapeHtml(category.field_label)}')">
                        名前を変更
                    </button>
                </div>
                
                <div class="customer-field-options-list">
                    ${options.map(option => renderOptionItem(category.field_key, option)).join('')}
                </div>
                
                <button type="button" class="settings-btn settings-btn-secondary" 
                        onclick="showAddOptionModal('${category.field_key}')">
                    ➕ 項目を追加
                </button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function renderOptionItem(fieldKey, option) {
    const textColor = getContrastColor(option.display_color);
    const hiddenClass = option.is_hidden ? 'option-hidden' : '';
    const isVisible = !option.is_hidden;
    
    return `
        <div class="customer-field-option-item ${hiddenClass}">
            <label class="option-visibility-checkbox">
                <input type="checkbox" 
                       ${isVisible ? 'checked' : ''}
                       onchange="toggleOptionVisibility(${option.id}, ${isVisible})">
                <span class="checkbox-label">${isVisible ? '表示中' : '非表示'}</span>
            </label>
            
            <input type="text" 
                   class="option-name-input" 
                   value="${escapeHtml(option.option_value)}"
                   onchange="updateOptionValue(${option.id}, this.value)"
                   ${option.is_hidden ? 'disabled' : ''}>
            
            <div class="color-picker-group">
                <input type="color" 
                       class="color-input" 
                       value="${option.display_color}"
                       onchange="updateOptionColor(${option.id}, this.value)"
                       ${option.is_hidden ? 'disabled' : ''}>
                <span class="color-preview" 
                      style="background-color: ${option.display_color}; color: ${textColor};">
                    ${option.display_color}
                </span>
            </div>
            
            <div class="option-order-buttons">
                <button type="button" 
                        class="settings-btn settings-btn-order" 
                        onclick="moveOptionUp('${fieldKey}', ${option.id})"
                        title="上へ移動">
                    ↑
                </button>
                <button type="button" 
                        class="settings-btn settings-btn-order" 
                        onclick="moveOptionDown('${fieldKey}', ${option.id})"
                        title="下へ移動">
                    ↓
                </button>
            </div>
            
            <button type="button" 
                    class="settings-btn settings-btn-danger" 
                    onclick="deleteOption(${option.id})">
                削除
            </button>
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
// 選択肢更新
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function updateOptionValue(optionId, newValue) {
    if (!newValue.trim()) {
        alert('項目名を入力してください');
        loadCustomerFieldSettings();
        return;
    }
    
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${optionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ option_value: newValue })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('項目名を更新しました', 'success');
        } else {
            alert(result.message || '更新に失敗しました');
            loadCustomerFieldSettings();
        }
    } catch (error) {
        console.error('Error updating option value:', error);
        alert('エラーが発生しました');
        loadCustomerFieldSettings();
    }
}

async function updateOptionColor(optionId, newColor) {
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${optionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ display_color: newColor })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('色を更新しました', 'success');
            loadCustomerFieldSettings();
        } else {
            alert(result.message || '更新に失敗しました');
        }
    } catch (error) {
        console.error('Error updating option color:', error);
        alert('エラーが発生しました');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 表示/非表示切り替え
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function toggleOptionVisibility(optionId, isHidden) {
    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/api/customer_fields/option/${optionId}/visibility`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_hidden: isHidden })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(isHidden ? '非表示にしました' : '表示しました', 'success');
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
    
    if (event.target === categoryModal) {
        closeCategoryEditModal();
    }
    if (event.target === optionModal) {
        closeOptionAddModal();
    }
}