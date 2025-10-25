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
// 予約詳細アコーディオン
// ============================================

/**
 * 予約詳細エリアの開閉（アコーディオン）
 * @param {number} reservationId - 予約ID
 */
function toggleDetail(reservationId) {
    const detailArea = document.getElementById(`detail-${reservationId}`);
    const button = document.querySelector(`.cr-reservation-card[data-reservation-id="${reservationId}"] .cr-detail-link-top`);

    if (!detailArea) {
        console.error(`[ERROR] 詳細エリアが見つかりません: detail-${reservationId}`);
        return;
    }

    // 現在の表示状態を確認
    const isVisible = detailArea.style.display !== 'none';

    // 全ての詳細エリアを閉じる＆ボタンテキストをリセット
    document.querySelectorAll('.cr-accordion-detail').forEach(area => {
        area.style.display = 'none';
    });
    document.querySelectorAll('.cr-detail-link-top').forEach(btn => {
        btn.textContent = '詳細▼';
    });

    // クリックした詳細エリアを開閉（トグル）
    if (!isVisible) {
        detailArea.style.display = 'block';
        if (button) button.textContent = '詳細×';
        console.log(`[INFO] 予約詳細を表示: ID=${reservationId}`);
    } else {
        console.log(`[INFO] 予約詳細を非表示: ID=${reservationId}`);
    }
}

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

    /* 削除：予約詳細モーダルのタッチイベント制御（アコーディオン化により不要）
    const detailModal = document.getElementById('detailModal');
    if (detailModal) {
        const modalContent = detailModal.querySelector('.cr-detail-modal-content');
        if (modalContent) {
            modalContent.addEventListener('touchmove', function(e) {
                e.stopPropagation();
            }, { passive: true });
        }

        const overlay = detailModal.querySelector('.cr-modal-overlay');
        if (overlay) {
            overlay.addEventListener('touchmove', function(e) {
                e.preventDefault();
            }, { passive: false });
        }
    }
    */

    // お預かり金額入力の処理
    document.querySelectorAll('.cr-amount-received-input').forEach(input => {
        // input時にお釣り計算のみ（自動保存は削除）
        input.addEventListener('input', function() {
            const totalAmount = parseInt(this.dataset.totalAmount);
            const amountReceived = parseInt(this.value) || 0;
            const change = Math.max(0, amountReceived - totalAmount); // 負の値は0として表示

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
            const changeDisplay = card.querySelector('.cr-change-display');

            // 編集モードの場合、入力欄を有効化
            if (this.classList.contains('cr-edit-mode')) {
                input.disabled = false;
                input.focus();
                this.classList.remove('cr-edit-mode');
                this.textContent = '登録';
                return;
            }

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
                // 保存成功時：入力欄を無効化し、ボタンを編集モードに
                input.disabled = true;
                this.disabled = false;
                this.classList.add('cr-edit-mode');
                this.textContent = '編集をする';

                // お釣り表示を更新
                const totalAmount = parseInt(input.dataset.totalAmount) || 0;
                const change = amountReceived - totalAmount;
                if (changeDisplay) {
                    changeDisplay.textContent = '¥' + change.toLocaleString();
                }

                alert('お預かり金額を登録しました');
            } else {
                // 保存失敗時：ボタンを元に戻す
                this.disabled = false;
                this.textContent = '登録';
            }
        });
    });

    // URLパラメータから予約IDを取得して該当予約を開く
    const urlParams = new URLSearchParams(window.location.search);
    const targetReservationId = urlParams.get('reservation_id');
    if (targetReservationId) {
        // ページ読み込み後、少し待ってからアコーディオンを開く
        setTimeout(() => {
            const reservationId = parseInt(targetReservationId);
            toggleDetail(reservationId);
            // 該当予約までスクロール
            const targetCard = document.querySelector(`.cr-reservation-card[data-reservation-id="${reservationId}"]`);
            if (targetCard) {
                targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 500);
    }
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
    // 現時点では予約詳細を開く（アコーディオン）
    toggleDetail(reservationId);
    console.log(`[INFO] 入室ボタンクリック: 予約ID=${reservationId}`);
}
