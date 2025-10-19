/**
 * スタッフ管理ページのJavaScript
 */

// 並び順変更：上に移動
function moveUp(staffId) {
    const store = getStoreFromUrl();
    fetch(`/${store}/staff/sort`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            staff_id: staffId,
            direction: 'up'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('並び順の変更に失敗しました');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('エラーが発生しました');
    });
}

// 並び順変更：下に移動
function moveDown(staffId) {
    const store = getStoreFromUrl();
    fetch(`/${store}/staff/sort`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            staff_id: staffId,
            direction: 'down'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('並び順の変更に失敗しました');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('エラーが発生しました');
    });
}

// 通知設定のトグル
function toggleNotification(staffId) {
    const store = getStoreFromUrl();
    const checkbox = event.target;
    const isEnabled = checkbox.checked;

    fetch(`/${store}/staff/notification`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            staff_id: staffId,
            notification_enabled: isEnabled
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('通知設定の変更に失敗しました');
            checkbox.checked = !isEnabled; // 元に戻す
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('エラーが発生しました');
        checkbox.checked = !isEnabled; // 元に戻す
    });
}

// LINE連携
function connectLine(staffId) {
    const store = getStoreFromUrl();
    // LINE連携のロジックを実装
    alert(`スタッフID ${staffId} のLINE連携処理を実装してください`);
    // 実際には以下のような処理になる
    /*
    window.location.href = `/${store}/staff/line-connect?staff_id=${staffId}`;
    */
}

// URLから店舗名を取得
function getStoreFromUrl() {
    const path = window.location.pathname;
    const parts = path.split('/');
    return parts[1]; // /nagano/... の場合 'nagano'
}
