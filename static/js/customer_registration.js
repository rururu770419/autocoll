// 顧客登録画面JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 生年月日から年齢を自動計算
    const birthdayInput = document.getElementById('birthday');
    if (birthdayInput) {
        birthdayInput.addEventListener('change', function() {
            calculateAge(this.value);
        });
    }
    
    // ========== リアルタイム入力制限 ==========
    
    // 電話番号：数字のみ、11桁まで
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            // 数字以外を削除
            this.value = this.value.replace(/[^0-9]/g, '');
            // 11桁を超える部分をカット
            if (this.value.length > 11) {
                this.value = this.value.slice(0, 11);
            }
        });
    }
    
    // 現在の所持PT：数字のみ
    const pointsInput = document.getElementById('current_points');
    if (pointsInput) {
        pointsInput.addEventListener('input', function() {
            // 数字以外を削除
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }
    
    // マイページID：半角英数字と記号のみ
    const mypageIdInput = document.getElementById('mypage_id');
    if (mypageIdInput) {
        mypageIdInput.addEventListener('input', function() {
            // 半角英数字と許可された記号のみ残す
            this.value = this.value.replace(/[^a-zA-Z0-9_\-@.]/g, '');
        });
    }
    
    // マイページパスワード：半角文字のみ
    const passwordInput = document.getElementById('mypage_password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            // 全角文字を削除（半角スペース~チルダの範囲のみ許可）
            this.value = this.value.replace(/[^\x20-\x7E]/g, '');
        });
    }
    
    // ========== リアルタイム入力制限ここまで ==========
    
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
    
    document.getElementById('age').value = age >= 0 ? age : '';
}

// フォーム送信処理
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // ニックネームが空なら名前をコピー
    if (!data.nickname) {
        data.nickname = data.name;
    }
    
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
            // 登録した顧客の編集ページにリダイレクト
            setTimeout(() => {
                window.location.href = `/${store}/customer_edit/${result.customer_id}`;
            }, 500);
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
        if (type === 'success') {
            messageArea.innerHTML = '';
        }
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