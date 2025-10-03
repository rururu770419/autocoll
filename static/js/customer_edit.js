// 顧客編集画面JavaScript

let originalCustomer = null;

// ページ読み込み時の処理
document.addEventListener('DOMContentLoaded', function() {
    loadCustomerData();
    
    // フォーム送信
    const form = document.getElementById('customerForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            await updateCustomer();
        });
    }
    
    // 生年月日変更時に年齢を自動計算
    const birthdayInput = document.getElementById('birthday');
    if (birthdayInput) {
        birthdayInput.addEventListener('change', function() {
            calculateAge();
        });
    }
});

// 顧客データ読み込み
async function loadCustomerData() {
    const store = getStoreCode();
    const customerId = document.getElementById('customerId').value;
    
    try {
        const response = await fetch(`/${store}/api/customers/${customerId}`);
        const result = await response.json();
        
        console.log('API Response:', result);
        
        if (result.success) {
            originalCustomer = result.customer;
            fillForm(result.customer);
        } else {
            showMessage(result.message || '顧客情報の取得に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました: ' + error.message, 'error');
    }
}

// フォームに値を設定
function fillForm(customer) {
    console.log('Filling form with:', customer);
    
    // 安全な値設定関数
    const setValue = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.value = value || '';
        } else {
            console.warn(`Element not found: ${id}`);
        }
    };
    
    // 基本情報
    setValue('name', customer.name);
    setValue('furigana', customer.furigana);
    setValue('phone', customer.phone);
    setValue('email', customer.email);
    setValue('birthday', customer.birthday);
    setValue('age', customer.age);
    
    // セレクトボックス
    setValue('member_type', customer.member_type || '通常会員');
    setValue('status', customer.status || '普通');
    setValue('recruitment_source', customer.recruitment_source);
    
    // 住所（既存システムは1つのaddressフィールド）
    setValue('address_detail', customer.address);
    
    // マイページ情報
    setValue('mypage_id', customer.mypage_id);
    setValue('current_points', customer.current_points || 0);
    
    // 生年月日があれば年齢を計算
    if (customer.birthday) {
        calculateAge();
    }
}

// 年齢計算
function calculateAge() {
    const birthdayInput = document.getElementById('birthday');
    const ageInput = document.getElementById('age');
    
    if (!birthdayInput || !ageInput) return;
    
    const birthday = birthdayInput.value;
    if (!birthday) {
        ageInput.value = '';
        return;
    }
    
    const birthDate = new Date(birthday);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    ageInput.value = age;
}

// 更新
async function updateCustomer() {
    const store = getStoreCode();
    const customerId = document.getElementById('customerId').value;
    
    // 値を取得
    const getValue = (id) => {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    };
    
    // 住所を結合
    const prefecture = getValue('prefecture');
    const city = getValue('city');
    const addressDetail = getValue('address_detail');
    
    let fullAddress = '';
    if (prefecture) fullAddress += prefecture;
    if (city) fullAddress += city;
    if (addressDetail) fullAddress += addressDetail;
    
    const data = {
        name: getValue('name'),
        furigana: getValue('furigana'),
        phone: getValue('phone'),
        email: getValue('email'),
        birthday: getValue('birthday') || null,
        age: getValue('age') ? parseInt(getValue('age')) : null,
        address: fullAddress || null,
        member_type: getValue('member_type'),
        status: getValue('status'),
        current_points: parseInt(getValue('current_points')) || 0,
        recruitment_source: getValue('recruitment_source'),
        mypage_id: getValue('mypage_id'),
        mypage_password: getValue('mypage_password')
    };
    
    console.log('Update data:', data);
    
    // 必須チェック
    if (!data.name) {
        showMessage('名前は必須です', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/${store}/api/customers/${customerId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('顧客情報を更新しました', 'success');
            setTimeout(() => {
                window.location.href = `/${store}/customer_management`;
            }, 1500);
        } else {
            showMessage(result.message || '更新に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました: ' + error.message, 'error');
    }
}

// メッセージ表示
function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    if (!messageArea) return;
    
    const alertClass = type === 'success' ? 'customer-alert-success' : 
                      type === 'info' ? 'customer-alert-info' : 'customer-alert-error';
    messageArea.innerHTML = `<div class="customer-alert ${alertClass}">${escapeHtml(message)}</div>`;
    
    setTimeout(() => {
        if (type !== 'success') {
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
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}