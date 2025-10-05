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
    
    // ========== ここから追加 ==========
    
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
    
    // ========== ここまで追加 ==========
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
    setValue('customer_number', customer.customer_id);
    setValue('name', customer.name);
    setValue('furigana', customer.furigana);
    setValue('phone', customer.phone);
    setValue('birthday', customer.birthday);
    setValue('age', customer.age);
    
    // セレクトボックス
    setValue('member_type', customer.member_type || '通常会員');
    setValue('status', customer.status || '普通');
    setValue('web_member', customer.web_member || 'web会員');
    setValue('recruitment_source', customer.recruitment_source);
    
    // 住所：都道府県を先に設定
setValue('prefecture', customer.prefecture);
setValue('address_detail', customer.address_detail);

// 市区町村は都道府県のchangeイベント後に設定
if (customer.prefecture && customer.city) {
    const prefectureSelect = document.getElementById('prefecture');
    const citySelect = document.getElementById('city');
    
    // 都道府県の変更イベントをリッスン
    const setCityValue = () => {
        // 市区町村リストが生成されるまで待つ
        const checkAndSet = () => {
            if (citySelect.options.length > 1) {
                // リストが生成された
                setValue('city', customer.city);
                console.log('市区町村を設定:', customer.city);
            } else {
                // まだ生成されていない場合は50ms後に再試行
                setTimeout(checkAndSet, 50);
            }
        };
        checkAndSet();
    };
    
    // 都道府県のchangeイベント発火
    if (prefectureSelect) {
        prefectureSelect.addEventListener('change', setCityValue, { once: true });
        prefectureSelect.dispatchEvent(new Event('change'));
    }
}
    
    // マイページ情報
    setValue('mypage_id', customer.mypage_id);
    setValue('mypage_password', customer.mypage_password);  // ← この行を追加
    setValue('current_points', customer.current_points || 0);
    
    // 新規フィールド
    setValue('comment', customer.comment);
    setValue('nickname', customer.nickname);
    
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
    
    // デバッグ：保存直前の値を確認
    console.log('保存直前のcity値:', document.getElementById('city').value);
    
    // 値を取得
    const getValue = (id) => {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    };
    
    const data = {
        name: getValue('name'),
        furigana: getValue('furigana'),
        phone: getValue('phone'),
        birthday: getValue('birthday') || null,
        age: getValue('age') ? parseInt(getValue('age')) : null,
        prefecture: getValue('prefecture'),
        city: getValue('city'),
        address_detail: getValue('address_detail'),
        member_type: getValue('member_type'),
        status: getValue('status'),
        web_member: getValue('web_member'),
        current_points: parseInt(getValue('current_points')) || 0,
        recruitment_source: getValue('recruitment_source'),
        mypage_id: getValue('mypage_id'),
        mypage_password: getValue('mypage_password'),
        comment: getValue('comment'),
        nickname: getValue('nickname')
    };

    // ニックネームが空なら名前をコピー
if (!data.nickname) {
    data.nickname = data.name;
}
    
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
            // リダイレクトを削除（そのままページに留まる）
            // データを再読み込み
            await loadCustomerData();
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
    
    // 成功メッセージは5秒後に消す
    if (type === 'success') {
        setTimeout(() => {
            messageArea.innerHTML = '';
        }, 5000);
    }
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

// 削除機能を追加（ファイルの最後に追加）

// 削除
async function deleteCustomer() {
    if (!confirm('本当にこの顧客を削除しますか？\nこの操作は取り消せません。')) {
        return;
    }
    
    const store = getStoreCode();
    const customerId = document.getElementById('customerId').value;
    
    try {
        const response = await fetch(`/${store}/api/customers/${customerId}/delete`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('顧客を削除しました', 'success');
            
            // 1秒後に一覧ページにリダイレクト
            setTimeout(() => {
                window.location.href = `/${store}/customer_management`;
            }, 1000);
        } else {
            showMessage(result.message || '削除に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました: ' + error.message, 'error');
    }
}