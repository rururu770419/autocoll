// オプション管理JavaScript

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 オプション管理ページ初期化');
    
    // フォームバリデーションを設定
    setupFormValidation();
    
    // トグルスイッチの連動を設定
    setupToggleSwitches();
});

// フォームバリデーション設定
function setupFormValidation() {
    const form = document.getElementById('optionForm');
    const priceInput = document.getElementById('price');
    const castBackAmountInput = document.getElementById('cast_back_amount');
    
    if (!form || !priceInput || !castBackAmountInput) {
        console.warn('⚠️ フォーム要素が見つかりません');
        return;
    }
    
    // リアルタイムバリデーション
    function validateAmounts() {
        const price = parseInt(priceInput.value) || 0;
        const castBackAmount = parseInt(castBackAmountInput.value) || 0;
        
        if (castBackAmount > price) {
            castBackAmountInput.setCustomValidity('バック金額は金額以下で入力してください');
            return false;
        } else {
            castBackAmountInput.setCustomValidity('');
            return true;
        }
    }
    
    priceInput.addEventListener('input', validateAmounts);
    castBackAmountInput.addEventListener('input', validateAmounts);
    
    // フォーム送信時のバリデーション
    form.addEventListener('submit', function(e) {
        if (!validateAmounts()) {
            e.preventDefault();
            alert('バック金額は金額以下で入力してください');
            return false;
        }
    });
    
    console.log('✅ フォームバリデーション設定完了');
}

// トグルスイッチの連動設定
function setupToggleSwitches() {
    // 登録フォームのトグル
    const formToggle = document.getElementById('is_active');
    if (formToggle) {
        // デフォルトで有効（チェック済み）
        formToggle.checked = true;
    }
    
    // 編集モーダルのトグル
    const editToggle = document.getElementById('edit_is_active');
    const editHidden = document.getElementById('edit_is_active_hidden');
    
    if (editToggle && editHidden) {
        editToggle.addEventListener('change', function() {
            editHidden.value = this.checked ? 'true' : 'false';
        });
    }
    
    console.log('✅ トグルスイッチ設定完了');
}

// フォームリセット
function resetForm() {
    const form = document.getElementById('optionForm');
    if (form) {
        form.reset();
        
        // トグルスイッチをデフォルト（有効）に戻す
        const toggle = document.getElementById('is_active');
        if (toggle) {
            toggle.checked = true;
        }
        
        console.log('🔄 フォームをリセットしました');
    }
}

// 編集モーダルを開く
function openEditModal(optionId, name, price, castBackAmount, isActive) {
    console.log('📝 編集モーダルを開く:', { optionId, name, price, castBackAmount, isActive });
    
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    
    if (!modal || !form) {
        console.error('❌ モーダル要素が見つかりません');
        return;
    }
    
    // フォームのactionを設定
    const store = getStoreFromPath();
    form.action = `/${store}/options/${optionId}/update`;
    
    // フォームに値を設定
    document.getElementById('edit_name').value = name;
    document.getElementById('edit_price').value = price;
    document.getElementById('edit_cast_back_amount').value = castBackAmount;
    
    // トグルスイッチの状態を設定
    const toggle = document.getElementById('edit_is_active');
    const hidden = document.getElementById('edit_is_active_hidden');
    
    if (toggle && hidden) {
        toggle.checked = isActive;
        hidden.value = isActive ? 'true' : 'false';
    }
    
    // モーダルを表示
    modal.classList.add('show');
    document.body.style.overflow = 'hidden'; // スクロール防止
    
    console.log('✅ 編集モーダルを開きました');
}

// 編集モーダルを閉じる
function closeEditModal() {
    const modal = document.getElementById('editModal');
    
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = ''; // スクロール復元
        console.log('✅ 編集モーダルを閉じました');
    }
}

// モーダル外クリックで閉じる
window.addEventListener('click', function(event) {
    const modal = document.getElementById('editModal');
    if (event.target === modal) {
        closeEditModal();
    }
});

// ESCキーでモーダルを閉じる
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('editModal');
        if (modal && modal.classList.contains('show')) {
            closeEditModal();
        }
    }
});

// URLから店舗コードを取得
function getStoreFromPath() {
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[1] || 'nagano';
}