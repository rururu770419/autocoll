// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ポイント設定ページ JavaScript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 店舗コードを取得
 */
function getStoreCode() {
    const path = window.location.pathname;
    const match = path.match(/\/([^\/]+)\//);
    return match ? match[1] : '';
}

/**
 * メッセージを表示
 */
function showMessage(message, type = 'success') {
    const messageArea = document.getElementById('messageArea');
    if (!messageArea) return;

    const alertClass = type === 'success' ? 'point-settings-alert-success' : 'point-settings-alert-danger';

    messageArea.innerHTML = `
        <div class="point-settings-alert ${alertClass}">
            ${message}
        </div>
    `;

    // ページのトップにスクロール
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // 3秒後に自動的に消す
    setTimeout(() => {
        messageArea.innerHTML = '';
    }, 3000);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 付与方式の切り替え
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * ポイント付与方式の切り替え
 */
function togglePointMethod() {
    const percentageRadio = document.querySelector('input[name="point_method"][value="percentage"]');
    const fixedPointRadio = document.querySelector('input[name="point_method"][value="course_based"]');

    const percentageArea = document.getElementById('percentageSettingsArea');
    const fixedPointArea = document.getElementById('fixedPointSettingsArea');

    if (percentageRadio.checked) {
        percentageArea.style.display = 'block';
        fixedPointArea.style.display = 'none';
    } else if (fixedPointRadio.checked) {
        percentageArea.style.display = 'none';
        fixedPointArea.style.display = 'block';
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 基本設定の保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 基本設定を保存（削除済み）
 * 新規顧客登録時のデフォルトポイント機能は削除されました
 */

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ポイント付与方式の保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * ポイント付与方式を保存
 */
async function savePointMethod() {
    const pointMethod = document.querySelector('input[name="point_method"]:checked').value;

    const data = {
        save_type: 'basic',
        point_method: pointMethod,
        new_customer_default_points: 0,  // デフォルト値として0を固定
        is_active: true
    };

    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/point_settings/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message || '保存に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// パーセンテージ一括設定
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * パーセンテージを一括適用
 */
function applyBulkPercentage() {
    const bulkValue = document.getElementById('bulkPercentage').value;

    if (bulkValue === '' || bulkValue < 0 || bulkValue > 100) {
        showMessage('0〜100の範囲でパーセンテージを入力してください', 'error');
        return;
    }

    const inputs = document.querySelectorAll('.percentage-input');
    inputs.forEach(input => {
        input.value = bulkValue;
    });

    showMessage('一括適用しました（保存ボタンを押してください）', 'success');
}

/**
 * 固定ポイントを一括適用
 */
function applyBulkFixedPoint() {
    const bulkValue = document.getElementById('bulkFixedPoint').value;

    if (bulkValue === '' || bulkValue < 0) {
        showMessage('0以上のポイント数を入力してください', 'error');
        return;
    }

    const inputs = document.querySelectorAll('.fixed-point-input');
    inputs.forEach(input => {
        input.value = bulkValue;
    });

    showMessage('一括適用しました（保存ボタンを押してください）', 'success');
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// パーセンテージ設定の保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * パーセンテージ設定を保存
 */
async function savePercentageSettings() {
    const inputs = document.querySelectorAll('.percentage-input');
    const rules = [];

    inputs.forEach(input => {
        const courseId = input.dataset.courseId;
        const memberType = input.dataset.memberType;
        const value = input.value.trim();

        if (value !== '') {
            const percentageRate = parseInt(value, 10);

            // バリデーション
            if (isNaN(percentageRate) || percentageRate < 0 || percentageRate > 100) {
                showMessage('パーセンテージは0〜100の整数で入力してください', 'error');
                return;
            }

            rules.push({
                course_id: parseInt(courseId),
                member_type: memberType,
                percentage_rate: percentageRate
            });
        }
    });

    const data = {
        save_type: 'percentage',
        rules: rules
    };

    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/point_settings/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message || '保存に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 固定ポイント設定の保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 固定ポイント設定を保存
 */
async function saveFixedPointSettings() {
    const inputs = document.querySelectorAll('.fixed-point-input');
    const rules = [];

    inputs.forEach(input => {
        const courseId = input.dataset.courseId;
        const memberType = input.dataset.memberType;
        const value = input.value.trim();

        if (value !== '') {
            const pointAmount = parseInt(value);

            // バリデーション
            if (isNaN(pointAmount) || pointAmount < 0) {
                showMessage('ポイント数は0以上の整数で入力してください', 'error');
                return;
            }

            rules.push({
                course_id: parseInt(courseId),
                member_type: memberType,
                point_amount: pointAmount
            });
        }
    });

    const data = {
        save_type: 'course_based',
        rules: rules
    };

    try {
        const store = getStoreCode();
        const response = await fetch(`/${store}/point_settings/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
        } else {
            showMessage(result.message || '保存に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ポイント操作理由管理
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// グローバル変数：編集中の理由ID
let editingReasonId = null;

/**
 * 理由フォーム送信
 */
async function submitReasonForm(event) {
    event.preventDefault();

    const reasonName = document.getElementById('reason_name').value.trim();
    const isActive = document.getElementById('reason_is_active').checked;

    if (!reasonName) {
        showMessage('理由名を入力してください', 'error');
        return;
    }

    const store = getStoreCode();
    let url, method, data;

    if (editingReasonId) {
        // 更新
        url = `/${store}/point_settings/reason/update/${editingReasonId}`;
        method = 'POST';
        data = {
            reason_name: reasonName,
            is_active: isActive
        };
    } else {
        // 新規登録
        url = `/${store}/point_settings/reason/add`;
        method = 'POST';
        data = {
            reason_name: reasonName
        };
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
            resetReasonForm();
            // ページをリロードして一覧を更新
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showMessage(result.message || '保存に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

/**
 * 理由編集
 */
function editReason(reasonId, reasonName, isActive) {
    editingReasonId = reasonId;

    document.getElementById('reason_name').value = reasonName;
    document.getElementById('reason_is_active').checked = isActive;

    // 編集モードメッセージを表示
    document.getElementById('reason-edit-message').style.display = 'block';

    // ボタンを「更新」に変更
    document.getElementById('reason-submit-btn').textContent = '更新';

    // フォームまでスクロール
    document.getElementById('reasonForm').scrollIntoView({ behavior: 'smooth' });
}

/**
 * 理由削除
 */
async function deleteReason(reasonId, reasonName) {
    if (!confirm(`「${reasonName}」を削除しますか？`)) {
        return;
    }

    const store = getStoreCode();

    try {
        const response = await fetch(`/${store}/point_settings/reason/delete/${reasonId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            showMessage(result.message, 'success');
            // ページをリロードして一覧を更新
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showMessage(result.message || '削除に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

/**
 * 理由フォームリセット
 */
function resetReasonForm() {
    editingReasonId = null;

    document.getElementById('reason_name').value = '';
    document.getElementById('reason_is_active').checked = true;

    // 編集モードメッセージを非表示
    document.getElementById('reason-edit-message').style.display = 'none';

    // ボタンを「登録」に戻す
    document.getElementById('reason-submit-btn').textContent = '登録';
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ページロード時の初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    // 初期表示の切り替え
    togglePointMethod();
});
