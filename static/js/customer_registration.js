// 顧客登録画面JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 生年月日から年齢を自動計算
    const birthdayInput = document.getElementById('birthday');
    if (birthdayInput) {
        birthdayInput.addEventListener('change', function() {
            calculateAge(this.value);
        });
    }
    
    // フォーム送信
    const customerForm = document.getElementById('customerForm');
    if (customerForm) {
        customerForm.addEventListener('submit', handleFormSubmit);
    }
});

// 年齢計算
function calculateAge(birthdayValue) {
    if (!birthdayValue) {
        document.getElementById('age').value = '';
        return;
    }
    
    const birthday = new Date(birthdayValue);
    const today = new Date();
    let age = today.getFullYear() - birthday.getFullYear();
    const monthDiff = today.getMonth() - birthday.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthday.getDate())) {
        age--;
    }
    
    document.getElementById('age').value = age >= 0 ? age + '歳' : '';
}

// フォーム送信処理
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // 住所を結合
    const prefecture = data.prefecture || '';
    const city = data.city || '';
    const addressDetail = data.address_detail || '';
    data.address = `${prefecture} ${city} ${addressDetail}`.trim();
    
    // 不要なフィールドを削除
    delete data.prefecture;
    delete data.city;
    delete data.address_detail;
    
    const store = getStoreCode();
    
    // バリデーション
    if (!data.name) {
        showMessage('名前は必須項目です', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/${store}/api/customers/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('顧客を登録しました', 'success');
            setTimeout(() => {
                location.href = `/${store}/customer_management`;
            }, 1500);
        } else {
            showMessage(result.message || '登録に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Form submit error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// メッセージ表示
function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    const alertClass = type === 'success' ? 'customer-alert-success' : 'customer-alert-error';
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