/**
 * 予約一覧ページのJavaScript
 */

// グローバル変数
let currentDate = null;
const DAYS_TO_SHOW = 7;
let datePickerInstance = null;

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    // 初期日付を設定（サーバーから渡された日付、または今日）
    currentDate = window.initialDate ? new Date(window.initialDate) : new Date();

    // カレンダーを描画
    renderCalendar();

    // 日付ピッカートリガーのテキストを更新
    updateDatePickerTrigger();

    // flatpickrを初期化
    initializeDatePicker();

    // 予約データを取得して表示
    loadReservations(formatDate(currentDate));

    // イベントリスナーを設定
    document.getElementById('prev-week').addEventListener('click', showPrevWeek);
    document.getElementById('next-week').addEventListener('click', showNextWeek);
});

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
    currentDate = new Date(date);
    renderCalendar();
    updateDatePickerTrigger();
    loadReservations(formatDate(date));
}

/**
 * 日付ピッカートリガーのテキストを更新
 */
function updateDatePickerTrigger() {
    const trigger = document.getElementById('date-picker-trigger');
    if (trigger) {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        const day = currentDate.getDate();
        trigger.textContent = `${year}年${month}月${day}日`;
    }
}

/**
 * flatpickrを初期化
 */
function initializeDatePicker() {
    datePickerInstance = flatpickr("#date-picker-trigger", {
        locale: "ja",
        dateFormat: "Y年m月d日",
        defaultDate: currentDate,
        onChange: function(selectedDates, dateStr, instance) {
            if (selectedDates.length > 0) {
                // 選択された日付を反映
                currentDate = new Date(selectedDates[0]);
                renderCalendar();
                updateDatePickerTrigger();
                loadReservations(formatDate(currentDate));
            }
        }
    });
}

/**
 * 前の週を表示（選択日を7日前に移動）
 */
function showPrevWeek() {
    currentDate.setDate(currentDate.getDate() - 7);
    renderCalendar();
    updateDatePickerTrigger();
    if (datePickerInstance) {
        datePickerInstance.setDate(currentDate, false);
    }
    loadReservations(formatDate(currentDate));
}

/**
 * 次の週を表示（選択日を7日後に移動）
 */
function showNextWeek() {
    currentDate.setDate(currentDate.getDate() + 7);
    renderCalendar();
    updateDatePickerTrigger();
    if (datePickerInstance) {
        datePickerInstance.setDate(currentDate, false);
    }
    loadReservations(formatDate(currentDate));
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

/**
 * 日付を日本語形式にフォーマット
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

/**
 * 予約データを取得して表示
 */
function loadReservations(date) {
    const tbody = document.getElementById('reservation-tbody');
    tbody.innerHTML = '<tr><td colspan="15" class="loading-cell">読み込み中...</td></tr>';

    // APIから予約データを取得
    fetch(`/${window.storeName}/reservations/api?date=${date}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderReservations(data.data);
            } else {
                tbody.innerHTML = `<tr><td colspan="15" class="no-data-cell">エラー: ${data.message}</td></tr>`;
            }
        })
        .catch(error => {
            console.error('Error loading reservations:', error);
            tbody.innerHTML = '<tr><td colspan="15" class="no-data-cell">予約データの取得に失敗しました</td></tr>';
        });
}

/**
 * 予約データをテーブルに描画
 */
function renderReservations(reservations) {
    const tbody = document.getElementById('reservation-tbody');

    if (reservations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="15" class="no-data-cell">この日の予約はありません</td></tr>';
        return;
    }

    tbody.innerHTML = '';

    reservations.forEach(reservation => {
        const row = document.createElement('tr');

        // 編集列
        const editCell = document.createElement('td');
        const editLink = document.createElement('a');
        editLink.href = `/${window.storeName}/reservation/edit?reservation_id=${reservation.reservation_id}`;
        editLink.className = 'edit-icon-link';
        editLink.innerHTML = '<i class="fas fa-pencil-alt"></i>';
        editCell.appendChild(editLink);
        row.appendChild(editCell);

        // 予約時間
        const timeCell = document.createElement('td');
        timeCell.className = 'time-cell';
        const reservationTime = new Date(reservation.reservation_datetime);
        timeCell.textContent = `${String(reservationTime.getHours()).padStart(2, '0')}:${String(reservationTime.getMinutes()).padStart(2, '0')}`;
        row.appendChild(timeCell);

        // キャスト名
        const castCell = document.createElement('td');
        castCell.textContent = reservation.cast_name || '未設定';
        row.appendChild(castCell);

        // 割引
        const discountCell = document.createElement('td');
        if (reservation.discount_id) {
            const badge = document.createElement('span');
            badge.className = 'discount-badge';
            if (reservation.discount_type === 'percentage') {
                badge.textContent = `${reservation.discount_value}%`;
            } else if (reservation.discount_type === 'fixed') {
                badge.textContent = `¥${reservation.discount_value.toLocaleString()}`;
            }
            discountCell.appendChild(badge);
        } else {
            discountCell.innerHTML = '<span class="no-discount">なし</span>';
        }
        row.appendChild(discountCell);

        // ホテル名
        const hotelCell = document.createElement('td');
        hotelCell.textContent = reservation.hotel_name || '-';
        row.appendChild(hotelCell);

        // 部屋番号
        const roomCell = document.createElement('td');
        roomCell.textContent = reservation.room_number || '-';
        row.appendChild(roomCell);

        // オプション
        const optionsCell = document.createElement('td');
        if (reservation.options && reservation.options.length > 0) {
            const optionList = document.createElement('div');
            optionList.className = 'option-list';
            optionList.textContent = reservation.options.map(opt => opt.name).join(', ');
            optionsCell.appendChild(optionList);
        } else {
            optionsCell.textContent = '-';
        }
        row.appendChild(optionsCell);

        // オプション金額
        const optionAmountCell = document.createElement('td');
        optionAmountCell.className = 'amount-cell';
        optionAmountCell.textContent = reservation.options_total ? `¥${reservation.options_total.toLocaleString()}` : '¥0';
        row.appendChild(optionAmountCell);

        // 合計金額
        const totalCell = document.createElement('td');
        totalCell.className = 'amount-cell';
        totalCell.textContent = `¥${reservation.total_amount.toLocaleString()}`;
        row.appendChild(totalCell);

        // 入店時間
        const checkInCell = document.createElement('td');
        checkInCell.className = 'time-cell';
        checkInCell.textContent = `${String(reservationTime.getHours()).padStart(2, '0')}:${String(reservationTime.getMinutes()).padStart(2, '0')}`;
        row.appendChild(checkInCell);

        // 退店時間
        const checkOutCell = document.createElement('td');
        checkOutCell.className = 'time-cell';
        if (reservation.end_datetime) {
            const endTime = new Date(reservation.end_datetime);
            checkOutCell.textContent = `${String(endTime.getHours()).padStart(2, '0')}:${String(endTime.getMinutes()).padStart(2, '0')}`;
        } else {
            checkOutCell.textContent = '-';
        }
        row.appendChild(checkOutCell);

        // お客様名前
        const customerCell = document.createElement('td');
        customerCell.textContent = reservation.customer_name || '-';
        row.appendChild(customerCell);

        // 電話番号
        const phoneCell = document.createElement('td');
        phoneCell.textContent = reservation.customer_phone || '-';
        row.appendChild(phoneCell);

        // 指名種別
        const nominationCell = document.createElement('td');
        nominationCell.textContent = reservation.nomination_type_name || '-';
        row.appendChild(nominationCell);

        // 追加PT
        const ptCell = document.createElement('td');
        ptCell.textContent = reservation.points_to_grant || '0';
        row.appendChild(ptCell);

        tbody.appendChild(row);
    });
}
