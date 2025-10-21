// ガントチャート JavaScript - 改善版

// グローバル設定
const GANTT_CONFIG = {
    startHour: 6,      // 営業開始時間（時）
    startMinute: 0,    // 営業開始時間（分）
    endHour: 24,       // 営業終了時間（24:00 = 翌0:00）
    interval: 10,      // 時間間隔（分）
    cellWidth: 30      // 1セルの幅（px）- 30pxで見やすく
};

// カレンダー関連のグローバル変数
let currentDate = null;
const DAYS_TO_SHOW = 7;
let datePickerInstance = null;

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 ガントチャート初期化開始');
    try {
        // 初期日付を設定
        currentDate = window.initialDate ? new Date(window.initialDate) : new Date();

        // カレンダーを描画
        renderCalendar();

        // 日付ピッカートリガーのテキストを更新
        updateDatePickerTrigger();

        // flatpickrを初期化
        initializeDatePicker();

        // イベントリスナーを設定
        document.getElementById('prev-week').addEventListener('click', showPrevWeek);
        document.getElementById('next-week').addEventListener('click', showNextWeek);

        // ガントチャートを初期化
        initializeGantt();
        console.log('✅ ガントチャート初期化完了');
    } catch (error) {
        console.error('❌ ガントチャート初期化エラー:', error);
    }
});

// ガントチャート初期化
function initializeGantt() {
    console.log('📋 initializeGantt() 実行');

    // 設定を取得
    const config = document.getElementById('ganttConfig');
    if (config) {
        const startTimeStr = config.getAttribute('data-start-time') || '06:00';
        const startTimeParts = startTimeStr.split(':');
        GANTT_CONFIG.startHour = parseInt(startTimeParts[0]) || 6;
        GANTT_CONFIG.startMinute = parseInt(startTimeParts[1]) || 0;
        GANTT_CONFIG.endHour = parseInt(config.getAttribute('data-end-hour')) || 24;
        GANTT_CONFIG.interval = parseInt(config.getAttribute('data-interval')) || 10;
        console.log('⚙️ 設定:', GANTT_CONFIG);
        console.log('⚙️ 開始時間:', startTimeStr, `(${GANTT_CONFIG.startHour}時${GANTT_CONFIG.startMinute}分)`);
    } else {
        console.warn('⚠️ ganttConfig要素が見つかりません。デフォルト設定を使用します。');
    }

    // 時間スロットを生成
    const timeSlots = generateTimeSlots();
    console.log('⏰ 時間スロット生成:', timeSlots.length + '個');
    console.log('⏰ 最初のスロット:', timeSlots.length > 0 ? timeSlots[0] : 'なし');

    if (timeSlots.length === 0) {
        console.error('❌ 時間スロットが生成されませんでした');
        return;
    }

    // ヘッダーを生成
    renderTimelineHeader(timeSlots);
    console.log('📊 ヘッダー生成完了');

    // 各キャスト行のグリッドを生成
    const rowCount = renderTimelineRows(timeSlots);
    console.log('👥 キャスト行生成完了:', rowCount + '行');

    // 出勤時間背景と予約バーの位置を設定
    positionWorkBackgrounds(timeSlots);
    console.log('🎨 出勤時間背景配置完了');

    positionReservationBars(timeSlots);
    console.log('📅 予約バー配置完了');

    positionTravelBars(timeSlots);
    console.log('🚗 移動時間バー配置完了');
}

// 時間スロットを生成（10分単位）
function generateTimeSlots() {
    const slots = [];

    // 開始時刻と終了時刻を分単位で計算
    const startTotalMinutes = GANTT_CONFIG.startHour * 60 + GANTT_CONFIG.startMinute;
    const endTotalMinutes = GANTT_CONFIG.endHour * 60;

    // 開始時刻から終了時刻まで、interval分刻みでスロットを生成
    for (let totalMinutes = startTotalMinutes; totalMinutes <= endTotalMinutes; totalMinutes += GANTT_CONFIG.interval) {
        const hour = Math.floor(totalMinutes / 60);
        const minute = totalMinutes % 60;

        // 24時を超える場合は次の日の時間として扱う
        const displayHour = hour >= 24 ? hour - 24 : hour;

        slots.push({
            hour: displayHour,
            minute: minute,
            time: `${String(displayHour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
            isHourMark: minute === 0
        });
    }

    return slots;
}

// 時間軸ヘッダーを生成
function renderTimelineHeader(timeSlots) {
    const header = document.getElementById('ganttTimelineHeader');
    if (!header) {
        console.error('❌ ganttTimelineHeader要素が見つかりません');
        return;
    }

    header.innerHTML = '';

    // すべてのスロットに対してセルを作成
    let cumulativePosition = 0;
    timeSlots.forEach(function(slot, index) {
        const cell = document.createElement('div');
        cell.className = 'gantt-time-cell';
        cell.style.width = GANTT_CONFIG.cellWidth + 'px';

        // 時間単位（:00）のみテキスト表示 + 太い罫線
        if (slot.isHourMark) {
            cell.classList.add('gantt-hour-marker');
            cell.textContent = `${slot.hour}:00`;

            // デバッグログ：時刻と位置を出力
            console.log(`  🕐 時間軸セル: ${slot.time} → セル${index} = ${cumulativePosition}px`);
        }
        // :10, :20, :30, :40, :50 は空のセル（細い罫線）

        header.appendChild(cell);
        cumulativePosition += GANTT_CONFIG.cellWidth;
    });
}

// タイムライン行のグリッドを生成
function renderTimelineRows(timeSlots) {
    const rows = document.querySelectorAll('.gantt-timeline-row');
    console.log('🔍 キャスト行数:', rows.length);
    
    rows.forEach(function(row, index) {
        // 既存のグリッドをクリア（出勤背景と予約バーは保持）
        const existingGrids = row.querySelectorAll('.gantt-time-grid');
        existingGrids.forEach(grid => grid.remove());
        
        // キャストの出勤時間を取得
        const startTime = row.getAttribute('data-start-time');
        const endTime = row.getAttribute('data-end-time');
        console.log(`  👤 キャスト${index + 1}: ${startTime}～${endTime}`);
        
        // 各時間スロットにグリッドセルを生成
        timeSlots.forEach(function(slot, slotIndex) {
            const grid = document.createElement('div');
            grid.className = 'gantt-time-grid';
            grid.style.width = GANTT_CONFIG.cellWidth + 'px';

            // 時間位置（:00）には太い罫線
            if (slot.isHourMark) {
                grid.classList.add('gantt-hour-marker');
            }

            // 出勤時間外は灰色、出勤時間内は白
            // 出勤開始時刻から出勤終了時刻まで白色
            const isWorkTime = startTime && endTime && isWithinWorkTime(slot.time, startTime, endTime);

            if (isWorkTime) {
                grid.classList.add('gantt-work-time');
            } else {
                grid.classList.add('gantt-off-time');
            }

            // デバッグログ（最初の5スロットのみ）
            if (index === 0 && slotIndex < 5) {
                console.log(`    スロット${slotIndex}: ${slot.time} → ${isWorkTime ? '白（出勤中）' : '灰（出勤外）'}`);
            }

            row.appendChild(grid);
        });
    });
    
    return rows.length;
}

// 指定時刻が出勤時間内かどうかを判定
// 13:00出勤、20:00退勤の場合:
// - 13:00のスロット（13:00～13:10） → 白色（出勤開始）
// - 13:10～19:50のスロット → 白色（出勤中）
// - 20:00のスロット（20:00～20:10） → 灰色（退勤後）
// - 20:10以降のスロット → 灰色（退勤後）
function isWithinWorkTime(time, startTime, endTime) {
    if (!startTime || !endTime || !time) return false;

    let timeMinutes = timeToMinutes(time);
    const startMinutes = timeToMinutes(startTime);
    let endMinutes = timeToMinutes(endTime);

    // 終了時刻が開始時刻より小さい場合（日をまたぐ場合）
    if (endMinutes <= startMinutes) {
        endMinutes += 24 * 60;
        // 判定する時刻も日をまたぐ処理を追加
        if (timeMinutes <= startMinutes) {
            timeMinutes += 24 * 60;
        }
    }

    // 開始時刻以上、終了時刻未満を出勤時間内とする
    // スロットは10分単位なので、終了時刻のスロットは出勤時間外とする
    return timeMinutes >= startMinutes && timeMinutes < endMinutes;
}

// 出勤時間背景の位置を設定
function positionWorkBackgrounds(timeSlots) {
    const backgrounds = document.querySelectorAll('.gantt-work-bg');
    console.log('🎨 出勤時間背景数:', backgrounds.length);
    
    backgrounds.forEach(function(element, index) {
        const startTime = element.getAttribute('data-start');
        const endTime = element.getAttribute('data-end');
        
        console.log(`  🔷 背景${index + 1}: data-start="${startTime}", data-end="${endTime}"`);
        
        if (startTime && endTime) {
            // 開始位置と幅を計算（予約バーと同じ基本計算のみ）
            const left = calculatePosition(startTime, timeSlots);
            const width = calculateDuration(startTime, endTime, timeSlots);

            element.style.left = left + 'px';
            element.style.width = width + 'px';

            // 詳細な計算ログ
            const startMinutes = timeToMinutes(startTime);
            const firstSlotMinutes = timeToMinutes(timeSlots[0].time);
            const diffMinutes = startMinutes - firstSlotMinutes;
            const cellCount = diffMinutes / GANTT_CONFIG.interval;

            console.log(`  ├─ startTime="${startTime}" → ${startMinutes}分`);
            console.log(`  ├─ timeSlots[0]="${timeSlots[0].time}" → ${firstSlotMinutes}分`);
            console.log(`  ├─ 差分=${diffMinutes}分 ÷ ${GANTT_CONFIG.interval}分 = ${cellCount}セル`);
            console.log(`  └─ left:${left}px, width:${width}px`);
        }
    });
}

// 予約バーの位置を設定
function positionReservationBars(timeSlots) {
    const bars = document.querySelectorAll('.gantt-reservation-bar');
    console.log('📅 予約バー数:', bars.length);
    
    if (bars.length === 0) {
        console.warn('⚠️ 予約バーが見つかりません。HTMLを確認してください。');
        // デバッグ: HTMLに予約バーが存在するか確認
        const rows = document.querySelectorAll('.gantt-timeline-row');
        console.log('🔍 タイムライン行数:', rows.length);
        rows.forEach((row, index) => {
            const barsInRow = row.querySelectorAll('.gantt-reservation-bar');
            console.log(`  行${index + 1}: 予約バー ${barsInRow.length}個`);
        });
        return;
    }
    
    console.log('🔍 timeSlots[0]:', timeSlots[0]);  // 最初のスロット確認
    
    bars.forEach(function(element, index) {
        const startTime = element.getAttribute('data-start');
        const endTime = element.getAttribute('data-end');
        
        console.log(`  📌 予約${index + 1}:`, element);  // HTML要素を確認
        console.log(`     data-start="${startTime}", data-end="${endTime}"`);
        
        if (startTime && endTime) {
            const left = calculatePosition(startTime, timeSlots);
            const width = calculateDuration(startTime, endTime, timeSlots);
            
            element.style.left = left + 'px';
            element.style.width = width + 'px';
            
            // 詳細な計算ログ
            const startMinutes = timeToMinutes(startTime);
            const firstSlotMinutes = timeToMinutes(timeSlots[0].time);
            const diffMinutes = startMinutes - firstSlotMinutes;
            const cellCount = diffMinutes / GANTT_CONFIG.interval;
            
            console.log(`     ├─ startTime="${startTime}" → ${startMinutes}分`);
            console.log(`     ├─ timeSlots[0]="${timeSlots[0].time}" → ${firstSlotMinutes}分`);
            console.log(`     ├─ 差分=${diffMinutes}分 ÷ ${GANTT_CONFIG.interval}分 = ${cellCount}セル`);
            console.log(`     └─ ${cellCount}セル × ${GANTT_CONFIG.cellWidth}px = left:${left}px, width:${width}px`);
        }
    });
}

// 移動時間バーの位置を設定
function positionTravelBars(timeSlots) {
    const bars = document.querySelectorAll('.gantt-travel-bar');
    console.log('🚗 移動時間バー数:', bars.length);

    if (bars.length === 0) {
        return;
    }

    bars.forEach(function(element, index) {
        const isOutbound = element.classList.contains('gantt-travel-outbound');
        const isReturn = element.classList.contains('gantt-travel-return');
        const duration = parseInt(element.getAttribute('data-duration')) || 0;

        if (duration === 0) {
            console.warn(`⚠️ 移動時間バー${index + 1}: durationが0です`);
            return;
        }

        let left = 0;
        let width = (duration / GANTT_CONFIG.interval) * GANTT_CONFIG.cellWidth;

        if (isOutbound) {
            // 往路：予約開始時間の前
            const endTime = element.getAttribute('data-end');
            if (endTime) {
                const endPosition = calculatePosition(endTime, timeSlots);
                left = endPosition - width;
                console.log(`  🔵 往路${index + 1}: ${duration}分, end=${endTime}, left=${left}px, width=${width}px`);
            }
        } else if (isReturn) {
            // 復路：予約終了時間の後
            const startTime = element.getAttribute('data-start');
            if (startTime) {
                left = calculatePosition(startTime, timeSlots);
                console.log(`  🔵 復路${index + 1}: ${duration}分, start=${startTime}, left=${left}px, width=${width}px`);
            }
        }

        element.style.left = left + 'px';
        element.style.width = width + 'px';
    });
}

// 時間から位置（px）を計算
function calculatePosition(time, timeSlots) {
    if (!time || timeSlots.length === 0) return 0;

    const targetMinutes = timeToMinutes(time);
    const startMinutes = timeToMinutes(timeSlots[0].time);

    const diffMinutes = targetMinutes - startMinutes;
    const cellCount = diffMinutes / GANTT_CONFIG.interval;

    return cellCount * GANTT_CONFIG.cellWidth;
}

// 時間から幅（px）を計算
function calculateDuration(startTime, endTime, timeSlots) {
    if (!startTime || !endTime) return 0;
    
    const startMinutes = timeToMinutes(startTime);
    let endMinutes = timeToMinutes(endTime);
    
    // 終了時刻が開始時刻より小さい場合（日をまたぐ場合）
    if (endMinutes <= startMinutes) {
        endMinutes += 24 * 60;
    }
    
    const duration = endMinutes - startMinutes;
    const cellCount = duration / GANTT_CONFIG.interval;
    
    return cellCount * GANTT_CONFIG.cellWidth;
}

// 時刻を分に変換
function timeToMinutes(time) {
    if (!time) return 0;
    
    const parts = time.split(':');
    if (parts.length < 2) return 0;
    
    const hours = parseInt(parts[0]);
    const minutes = parseInt(parts[1]);
    
    return hours * 60 + minutes;
}

// 部屋番号を更新（自動保存）
function updateRoomNumber(inputElement) {
    const reservationId = inputElement.getAttribute('data-reservation-id');
    const roomNumber = inputElement.value.trim();
    
    if (!reservationId) {
        console.warn('⚠️ 予約IDがありません');
        return;
    }
    
    const store = getStoreFromPath();
    console.log('📝 部屋番号更新:', reservationId, roomNumber);
    
    fetch(`/${store}/gantt/api/update_room_number`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            reservation_id: parseInt(reservationId),
            room_number: roomNumber
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ 部屋番号更新成功');
            inputElement.style.borderColor = 'rgba(40, 167, 69, 0.8)';
            setTimeout(() => {
                inputElement.style.borderColor = '';
            }, 1000);
        } else {
            console.error('❌ 部屋番号更新失敗:', data.error);
            alert('部屋番号の更新に失敗しました: ' + (data.error || '不明なエラー'));
            inputElement.style.borderColor = 'rgba(220, 53, 69, 0.8)';
        }
    })
    .catch(error => {
        console.error('❌ エラー:', error);
        alert('エラーが発生しました: ' + error.message);
        inputElement.style.borderColor = 'rgba(220, 53, 69, 0.8)';
    });
}

// URLから店舗コードを取得
function getStoreFromPath() {
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[1] || 'nagano';
}