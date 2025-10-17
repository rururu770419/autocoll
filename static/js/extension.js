// 延長管理JavaScript

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 延長管理ページ初期化');

    // フォームバリデーションを設定
    setupFormValidation();

    // トグルスイッチの連動を設定
    setupToggleSwitches();
});

// フォームバリデーション設定
function setupFormValidation() {
    const form = document.getElementById('extensionForm');
    const extensionFeeInput = document.getElementById('extension_fee');
    const backAmountInput = document.getElementById('back_amount');

    if (!form || !extensionFeeInput || !backAmountInput) {
        console.warn('⚠️ フォーム要素が見つかりません');
        return;
    }

    // リアルタイムバリデーション
    function validateAmounts() {
        const extensionFee = parseInt(extensionFeeInput.value) || 0;
        const backAmount = parseInt(backAmountInput.value) || 0;

        if (backAmount > extensionFee) {
            backAmountInput.setCustomValidity('バック金額は金額以下で入力してください');
            return false;
        } else {
            backAmountInput.setCustomValidity('');
            return true;
        }
    }

    extensionFeeInput.addEventListener('input', validateAmounts);
    backAmountInput.addEventListener('input', validateAmounts);

    // フォーム送信時のバリデーション
    form.addEventListener('submit', function(e) {
        if (!validateAmounts()) {
            e.preventDefault();
            alert('バック金額は金額以下で入力してください');
            return false;
        }
    });
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
}

// フォームリセット
function resetForm() {
    const form = document.getElementById('extensionForm');
    if (form) {
        form.reset();

        // トグルスイッチをデフォルト（有効）に戻す
        const toggle = document.getElementById('is_active');
        if (toggle) {
            toggle.checked = true;
        }
    }
}

// 編集モーダルを開く
function openEditModal(extensionId, extensionName, extensionFee, backAmount, extensionMinutes, isActive) {
    console.log('📝 編集モーダルを開く:', { extensionId, extensionName, extensionFee, backAmount, extensionMinutes, isActive });

    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');

    if (!modal || !form) {
        return;
    }

    // フォームのactionを設定
    const store = getStoreFromPath();
    form.action = `/${store}/extension/${extensionId}/update`;

    // フォームに値を設定
    document.getElementById('edit_extension_name').value = extensionName;
    document.getElementById('edit_extension_fee').value = extensionFee;
    document.getElementById('edit_back_amount').value = backAmount;
    document.getElementById('edit_extension_minutes').value = extensionMinutes;

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
}

// 編集モーダルを閉じる
function closeEditModal() {
    const modal = document.getElementById('editModal');

    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = ''; // スクロール復元
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
