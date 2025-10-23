// =========================================
// キャストお客様情報ページ JavaScript
// =========================================

/**
 * アコーディオンの開閉を制御
 * @param {string} sectionId - アコーディオンセクションのID
 */
function toggleAccordion(sectionId) {
    const content = document.getElementById('content-' + sectionId);
    const icon = document.getElementById('icon-' + sectionId);

    if (content.classList.contains('active')) {
        // 閉じる
        content.classList.remove('active');
        icon.textContent = '▼';
    } else {
        // 開く
        content.classList.add('active');
        icon.textContent = '▲';
    }
}

/**
 * お客様メモを保存
 * ※現在はアラートのみ、データベース連携は後回し
 */
function saveCustomerMemo() {
    alert('保存機能は実装中です');
    return false;
}

/**
 * URLからstoreコードを取得
 */
function getStoreFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[1];
}

/**
 * URLからcustomer_idを取得
 */
function getCustomerIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('customer_id');
}

/**
 * 私の評価を保存
 */
async function saveMyRating() {
    const store = getStoreFromUrl();
    const customerId = getCustomerIdFromUrl();

    if (!customerId) {
        alert('顧客IDが取得できませんでした');
        return false;
    }

    // フォームデータを収集
    const form = document.querySelector('#content-my-rating form');
    const formData = new FormData(form);

    // 必須チェック：全てのラジオボタングループをチェック
    const radioGroups = form.querySelectorAll('.cci-radio-group');
    const uncheckedItems = [];

    radioGroups.forEach(group => {
        const radioInputs = group.querySelectorAll('input[type="radio"]');
        if (radioInputs.length > 0) {
            const groupName = radioInputs[0].name;
            const isChecked = Array.from(radioInputs).some(input => input.checked);

            if (!isChecked) {
                // グループ名から項目名を取得
                const labelElement = group.closest('.cci-form-group').querySelector('.cci-label');
                const itemName = labelElement ? labelElement.textContent : '項目';
                uncheckedItems.push(itemName);
            }
        }
    });

    // 未選択の項目がある場合はエラー
    if (uncheckedItems.length > 0) {
        alert('以下の項目を選択してください：\n\n' + uncheckedItems.join('\n'));
        return false;
    }

    const ratingData = {};
    for (const [key, value] of formData.entries()) {
        if (key.startsWith('rating_')) {
            const itemId = key.replace('rating_', '');
            if (value) {  // 空でない値のみ送信
                ratingData[itemId] = value;
            }
        }
    }

    if (Object.keys(ratingData).length === 0) {
        alert('評価項目を入力してください');
        return false;
    }

    try {
        const response = await fetch(`/${store}/cast/api/save_customer_rating`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                customer_id: customerId,
                ratings: ratingData
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('評価を登録しました');
            // ページをリロードして「※未登録」バッジを更新
            location.reload();
        } else {
            alert('評価の登録に失敗しました: ' + (result.error || ''));
        }
    } catch (error) {
        console.error('評価保存エラー:', error);
        alert('評価の保存に失敗しました');
    }

    return false;
}
