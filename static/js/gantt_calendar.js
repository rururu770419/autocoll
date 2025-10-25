// =========================================
// カレンダー機能
// =========================================

/**
 * カレンダーを描画（選択日から右に7日分表示）
 */
function renderCalendar() {
    const calendarDates = document.getElementById('calendar-dates');
    calendarDates.innerHTML = '';

    const weekDays = ['日', '月', '火', '水', '木', '金', '土'];

    for (let i = 0; i < DAYS_TO_SHOW; i++) {
        const date = new Date(currentDate);
        date.setDate(currentDate.getDate() + i);

        const dateItem = document.createElement('div');
        dateItem.className = 'calendar-date-item';

        // 選択中の日付かチェック（最初の日付が選択中）
        if (i === 0) {
            dateItem.classList.add('selected');
        }

        // 日付をクリックしたときの処理
        dateItem.addEventListener('click', () => selectDate(date));

        // 日付表示（1行で「月/日(曜日)」形式）
        const dateMain = document.createElement('div');
        dateMain.className = 'date-main';
        dateMain.textContent = `${date.getMonth() + 1}/${date.getDate()}(${weekDays[date.getDay()]})`;

        dateItem.appendChild(dateMain);
        calendarDates.appendChild(dateItem);
    }
}

/**
 * 日付を選択
 */
function selectDate(date) {
    // ページを遷移
    const dateStr = formatDate(date);
    window.location.href = `/${window.storeName}/gantt?date=${dateStr}`;
}

/**
 * 日付ピッカートリガーのテキストを更新（常に今日の日付を表示）
 */
function updateDatePickerTrigger() {
    const trigger = document.getElementById('date-picker-trigger');
    if (trigger) {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;
        const day = today.getDate();
        trigger.textContent = `${year}年${month}月${day}日`;
    }
}

/**
 * 今日に戻るボタンの初期化
 */
function initializeDatePicker() {
    const trigger = document.getElementById('date-picker-trigger');
    if (trigger) {
        // クリックで今日に戻る
        trigger.addEventListener('click', function() {
            const today = new Date();
            const dateStr = formatDate(today);
            window.location.href = `/${window.storeName}/gantt?date=${dateStr}`;
        });
    }
}

/**
 * 前の日を表示（選択日を1日前に移動）
 */
function showPrevWeek() {
    currentDate.setDate(currentDate.getDate() - 1);
    // ページを遷移
    const dateStr = formatDate(currentDate);
    window.location.href = `/${window.storeName}/gantt?date=${dateStr}`;
}

/**
 * 次の日を表示（選択日を1日後に移動）
 */
function showNextWeek() {
    currentDate.setDate(currentDate.getDate() + 1);
    // ページを遷移
    const dateStr = formatDate(currentDate);
    window.location.href = `/${window.storeName}/gantt?date=${dateStr}`;
}

/**
 * 日付をYYYY-MM-DD形式にフォーマット
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
