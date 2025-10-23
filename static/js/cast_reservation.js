/**
 * キャスト予約一覧ページ用JavaScript
 * 日付ナビゲーション、カレンダーモーダル、予約件数表示
 */

// ============================================
// グローバル変数
// ============================================

let currentViewDate = new Date(currentDate); // 現在表示中の日付（HTMLから渡される）
let calendarYear = currentViewDate.getFullYear();
let calendarMonth = currentViewDate.getMonth() + 1; // 1-12
let reservationCounts = {}; // 月間予約件数（キャッシュ）

// ============================================
// 日付ナビゲーション
// ============================================

/**
 * 日付を変更（前日・翌日）
 * @param {number} days - 変更する日数（-1: 前日, 1: 翌日）
 */
function changeDate(days) {
    const newDate = new Date(currentViewDate);
    newDate.setDate(newDate.getDate() + days);

    const dateStr = formatDateForURL(newDate);
    window.location.href = `/${store}/cast/reservation_list?date=${dateStr}`;
}

/**
 * 今日に戻る
 */
function goToToday() {
    window.location.href = `/${store}/cast/reservation_list`;
}

/**
 * URLパラメータ用の日付フォーマット
 * @param {Date} date - 日付オブジェクト
 * @returns {string} YYYY-MM-DD形式の文字列
 */
function formatDateForURL(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// ============================================
// カレンダーモーダル
// ============================================

/**
 * カレンダーモーダルを開く
 */
async function openCalendarModal() {
    const modal = document.getElementById('calendarModal');
    if (!modal) return;

    // 現在表示中の月に設定
    calendarYear = currentViewDate.getFullYear();
    calendarMonth = currentViewDate.getMonth() + 1;

    // 月間予約件数を取得
    await loadReservationCounts(calendarYear, calendarMonth);

    // カレンダーを描画
    renderCalendar();

    // モーダル表示
    modal.classList.add('cr-modal-show');
    document.body.style.overflow = 'hidden'; // スクロール禁止
}

/**
 * カレンダーモーダルを閉じる
 */
function closeCalendarModal() {
    const modal = document.getElementById('calendarModal');
    if (!modal) return;

    modal.classList.remove('cr-modal-show');
    document.body.style.overflow = ''; // スクロール解除
}

/**
 * 月を変更（前月・翌月）
 * @param {number} months - 変更する月数（-1: 前月, 1: 翌月）
 */
async function changeMonth(months) {
    calendarMonth += months;

    // 月の範囲チェック
    if (calendarMonth < 1) {
        calendarMonth = 12;
        calendarYear--;
    } else if (calendarMonth > 12) {
        calendarMonth = 1;
        calendarYear++;
    }

    // 月間予約件数を取得
    await loadReservationCounts(calendarYear, calendarMonth);

    // カレンダーを再描画
    renderCalendar();
}

/**
 * 月間予約件数をAPIから取得
 * @param {number} year - 年
 * @param {number} month - 月
 */
async function loadReservationCounts(year, month) {
    try {
        const response = await fetch(`/${store}/cast/api/reservation_counts?year=${year}&month=${month}`);
        const data = await response.json();

        if (data.success) {
            reservationCounts = data.counts || {};
            console.log('[DEBUG] 予約件数取得成功:', reservationCounts);
        } else {
            console.error('[ERROR] 予約件数取得失敗:', data.error);
            reservationCounts = {};
        }
    } catch (error) {
        console.error('[ERROR] API通信エラー:', error);
        reservationCounts = {};
    }
}

/**
 * カレンダーを描画
 */
function renderCalendar() {
    const calendar = document.getElementById('calendar');
    const monthTitle = document.getElementById('monthTitle');

    if (!calendar || !monthTitle) return;

    // タイトル更新
    monthTitle.textContent = `${calendarYear}年${calendarMonth}月`;

    // カレンダークリア
    calendar.innerHTML = '';

    // 曜日ヘッダー
    const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
    weekdays.forEach(day => {
        const weekdayEl = document.createElement('div');
        weekdayEl.className = 'cr-weekday';
        weekdayEl.textContent = day;
        calendar.appendChild(weekdayEl);
    });

    // カレンダー日付生成
    const firstDay = new Date(calendarYear, calendarMonth - 1, 1);
    const lastDay = new Date(calendarYear, calendarMonth, 0);
    const firstDayOfWeek = firstDay.getDay(); // 0=日曜
    const daysInMonth = lastDay.getDate();

    // 前月の末尾日付を追加
    const prevMonthLastDay = new Date(calendarYear, calendarMonth - 1, 0).getDate();
    for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const day = prevMonthLastDay - i;
        const dayEl = createDayElement(day, true); // 他月
        calendar.appendChild(dayEl);
    }

    // 当月の日付を追加
    for (let day = 1; day <= daysInMonth; day++) {
        const dayEl = createDayElement(day, false);
        calendar.appendChild(dayEl);
    }

    // 翌月の先頭日付を追加（42マス埋める）
    const totalCells = firstDayOfWeek + daysInMonth;
    const remainingCells = 42 - totalCells;
    for (let day = 1; day <= remainingCells; day++) {
        const dayEl = createDayElement(day, true); // 他月
        calendar.appendChild(dayEl);
    }
}

/**
 * 日付要素を作成
 * @param {number} day - 日
 * @param {boolean} isOtherMonth - 他月かどうか
 * @returns {HTMLElement} 日付要素
 */
function createDayElement(day, isOtherMonth) {
    const dayBtn = document.createElement('button');
    dayBtn.className = 'cr-day';
    dayBtn.type = 'button';

    // 日付表示
    const dayText = document.createElement('div');
    dayText.textContent = day;
    dayBtn.appendChild(dayText);

    if (isOtherMonth) {
        dayBtn.classList.add('cr-day-other-month');
        return dayBtn;
    }

    // 日付文字列（YYYY-MM-DD）
    const dateStr = `${calendarYear}-${String(calendarMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

    // 今日かどうか
    const today = new Date();
    if (calendarYear === today.getFullYear() &&
        calendarMonth === today.getMonth() + 1 &&
        day === today.getDate()) {
        dayBtn.classList.add('cr-day-today');
    }

    // 予約件数チェック
    if (reservationCounts[dateStr]) {
        dayBtn.classList.add('cr-day-has-reservations');

        // 件数バッジ追加
        const countBadge = document.createElement('div');
        countBadge.className = 'cr-day-count';
        countBadge.textContent = `${reservationCounts[dateStr]}件`;
        dayBtn.appendChild(countBadge);
    }

    // クリックイベント
    dayBtn.addEventListener('click', () => {
        window.location.href = `/${store}/cast/reservation_list?date=${dateStr}`;
    });

    return dayBtn;
}

// ============================================
// 予約詳細モーダル
// ============================================

/**
 * 予約詳細モーダルを開く
 * @param {number} reservationId - 予約ID
 */
async function openDetailModal(reservationId) {
    const modal = document.getElementById('detailModal');
    const detailBody = document.getElementById('detailBody');

    if (!modal || !detailBody) {
        console.error('[ERROR] モーダル要素が見つかりません');
        return;
    }

    // 背景のスクロールを防ぐ
    document.body.style.overflow = 'hidden';

    // ローディング表示
    detailBody.innerHTML = '<div class="cr-loading">読み込み中...</div>';
    modal.classList.add('cr-modal-show');

    try {
        // API呼び出し
        const response = await fetch(`/${store}/cast/api/reservation_detail?reservation_id=${reservationId}`);
        const data = await response.json();

        if (data.success) {
            renderDetailContent(data.detail, data.visit_count);
        } else {
            detailBody.innerHTML = `<div class="cr-loading" style="color: #ff4444;">${data.error || '予約詳細の取得に失敗しました'}</div>`;
        }
    } catch (error) {
        console.error('[ERROR] 予約詳細取得エラー:', error);
        detailBody.innerHTML = '<div class="cr-loading" style="color: #ff4444;">予約詳細の取得に失敗しました</div>';
    }
}

/**
 * 予約詳細モーダルを閉じる
 */
function closeDetailModal() {
    // 背景のスクロールを復元
    document.body.style.overflow = '';

    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.classList.remove('cr-modal-show');
    }
}

/**
 * 詳細情報をレンダリング
 * @param {object} detail - 予約詳細データ
 * @param {number} visitCount - 接客回数
 */
function renderDetailContent(detail, visitCount) {
    const detailBody = document.getElementById('detailBody');

    // 日時フォーマット
    const businessDate = detail.business_date ? formatDateJP(detail.business_date) : '-';
    const startTime = detail.reservation_datetime ? new Date(detail.reservation_datetime).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }) : '-';
    const endTime = detail.end_datetime ? new Date(detail.end_datetime).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' }) : '-';

    // 支払い方法
    const paymentMethod = detail.payment_method === 'card' ? 'カード' : detail.payment_method === 'cash' ? '現金' : detail.payment_method || '-';

    const html = `
        <!-- 基本情報 -->
        <div class="cr-detail-section">
            <h3>基本情報</h3>
            <div class="cr-detail-row">
                <span class="cr-detail-label-badge">予約日</span>
                <span class="cr-detail-value">${businessDate}</span>
            </div>
            <div class="cr-detail-row">
                <span class="cr-detail-label-badge">予約時間</span>
                <span class="cr-detail-value">${startTime}～${endTime}</span>
            </div>
            <div class="cr-detail-row">
                <span class="cr-detail-label-badge">お客様名</span>
                <span class="cr-detail-value">${detail.customer_name || '-'}様</span>
            </div>
            <div class="cr-detail-row">
                <span class="cr-detail-label-badge">接客回数</span>
                <span class="cr-detail-value">${visitCount}回目</span>
            </div>
        </div>

        <!-- サービス内容 -->
        <div class="cr-detail-section">
            <h3>サービス内容</h3>
            <div class="cr-detail-row">
                <span class="cr-detail-label-badge">コース</span>
                <span class="cr-detail-value">${detail.course_name || '-'}</span>
            </div>
            ${detail.options_list ? `
            <div class="cr-detail-row-vertical">
                <span class="cr-detail-label-badge">オプション</span>
                <span class="cr-detail-value">${detail.options_list}</span>
            </div>
            ` : ''}
        </div>

        <!-- 場所・移動 -->
        <div class="cr-detail-section">
            <h3>場所・移動</h3>
            ${detail.hotel_name ? `
            <div class="cr-detail-row">
                <span class="cr-detail-label-badge">ホテル</span>
                <span class="cr-detail-value">${detail.hotel_name}${detail.room_number ? '　' + detail.room_number + '号室' : ''}</span>
            </div>
            ` : ''}
        </div>

        <!-- 料金・支払い -->
        <div class="cr-detail-section">
            <h3>料金・支払い</h3>
            <div class="cr-detail-row">
                <span class="cr-detail-label-badge">合計金額</span>
                <span class="cr-detail-value">${detail.payment_method && detail.payment_method.toLowerCase() === 'card' ? 'カード' : '現金'}/¥${detail.total_amount ? detail.total_amount.toLocaleString() : '0'}</span>
            </div>
        </div>

        <!-- コメント -->
        ${detail.customer_comment || detail.staff_memo ? `
        <div class="cr-detail-section">
            <h3>コメント</h3>
            ${detail.customer_comment ? `
            <div style="margin-bottom: 12px;">
                <div class="cr-detail-comment">${detail.customer_comment}</div>
            </div>
            ` : ''}
            ${detail.staff_memo ? `
            <div>
                <div class="cr-detail-comment">${detail.staff_memo}</div>
            </div>
            ` : ''}
        </div>
        ` : ''}
    `;

    detailBody.innerHTML = html;
}

/**
 * 日付を日本語形式にフォーマット
 * @param {string} dateStr - 日付文字列
 * @returns {string} YYYY年MM月DD日(曜日)形式
 */
function formatDateJP(dateStr) {
    const date = new Date(dateStr);
    const weekDays = ['日', '月', '火', '水', '木', '金', '土'];
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const dayOfWeek = weekDays[date.getDay()];

    return `${year}年${month}月${day}日(${dayOfWeek})`;
}

// ESCキーで詳細モーダルを閉じる
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeDetailModal();
    }
});

// ============================================
// お釣り機能
// ============================================

/**
 * お預かり金額を保存（API呼び出し）
 * @returns {Promise<boolean>} 保存成功時はtrue、失敗時はfalse
 */
async function saveAmountReceived(reservationId, amountReceived) {
    try {
        const response = await fetch(`/${store}/cast/api/update_amount_received`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reservation_id: reservationId,
                amount_received: amountReceived
            })
        });

        const data = await response.json();
        if (!data.success) {
            alert('保存に失敗しました');
            console.error('[ERROR] 保存失敗:', data);
            return false;
        }
        return true;
    } catch (error) {
        console.error('[ERROR] API通信エラー:', error);
        alert('保存中にエラーが発生しました');
        return false;
    }
}

// ============================================
// 初期化
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] キャスト予約一覧ページ初期化');
    console.log('[INFO] 選択日:', currentDate);

    // モーダルのタッチイベント制御（スマホ対応）
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
        // モーダル内のタッチイベントは伝播させない
        const modalContent = detailModal.querySelector('.cr-detail-modal-content');
        if (modalContent) {
            modalContent.addEventListener('touchmove', function(e) {
                e.stopPropagation();
            }, { passive: true });
        }

        // オーバーレイのタッチイベントは背景にスクロールさせない
        const overlay = detailModal.querySelector('.cr-modal-overlay');
        if (overlay) {
            overlay.addEventListener('touchmove', function(e) {
                e.preventDefault();
            }, { passive: false });
        }
    }

    // お預かり金額入力の処理
    document.querySelectorAll('.cr-amount-received-input').forEach(input => {
        // input時にお釣り計算のみ（自動保存は削除）
        input.addEventListener('input', function() {
            const totalAmount = parseInt(this.dataset.totalAmount);
            const amountReceived = parseInt(this.value) || 0;
            const change = amountReceived - totalAmount;

            const changeDisplay = this.closest('.cr-reservation-card')
                .querySelector('.cr-change-display');
            if (changeDisplay) {
                changeDisplay.textContent = '¥' + change.toLocaleString();
            }
        });
    });

    // 登録ボタンの処理
    document.querySelectorAll('.cr-save-amount-btn').forEach(button => {
        button.addEventListener('click', async function() {
            const reservationId = parseInt(this.dataset.reservationId);
            const card = this.closest('.cr-reservation-card');
            const input = card.querySelector('.cr-amount-received-input');
            const amountReceived = parseInt(input.value) || 0;

            if (amountReceived <= 0) {
                alert('お預かり金額を入力してください');
                return;
            }

            // ボタンを無効化（連続クリック防止）
            this.disabled = true;
            this.textContent = '保存中...';

            // API呼び出し
            const success = await saveAmountReceived(reservationId, amountReceived);

            if (success) {
                // 保存成功時：入力欄とボタンを無効化
                input.disabled = true;
                this.textContent = '登録済み';
                alert('お預かり金額を登録しました');
            } else {
                // 保存失敗時：ボタンを元に戻す
                this.disabled = false;
                this.textContent = '登録';
            }
        });
    });
});

// ============================================
// 入室処理
// ============================================

/**
 * 入室ボタンクリック時の処理
 * @param {number} reservationId - 予約ID
 */
function handleCheckin(reservationId) {
    // TODO: 入室処理の実装
    // 現時点では予約詳細モーダルを開く
    openDetailModal(reservationId);
}
