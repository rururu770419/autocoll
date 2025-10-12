// ガントチャート JavaScript

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', function() {
    initializeGantt();
});

// ガントチャート初期化
function initializeGantt() {
    const timeSlots = getTimeSlots();
    
    if (timeSlots.length === 0) {
        return;
    }
    
    // 出勤時間背景の位置・幅を設定
    document.querySelectorAll('.gantt-work-bg').forEach(function(element) {
        const startTime = element.getAttribute('data-start');
        const endTime = element.getAttribute('data-end');
        
        if (startTime && endTime) {
            const left = calculatePosition(startTime, timeSlots);
            const width = calculateDuration(startTime, endTime, timeSlots);
            
            element.style.left = left + '%';
            element.style.width = width + '%';
        }
    });
    
    // 予約バーの位置・幅を設定
    document.querySelectorAll('.gantt-reservation-bar').forEach(function(element) {
        const startTime = element.getAttribute('data-start');
        const endTime = element.getAttribute('data-end');
        
        if (startTime && endTime) {
            const left = calculatePosition(startTime, timeSlots);
            const width = calculateDuration(startTime, endTime, timeSlots);
            
            element.style.left = left + '%';
            element.style.width = width + '%';
        }
    });
}

// 時間スロットを取得
function getTimeSlots() {
    const timeCells = document.querySelectorAll('.gantt-time-cell');
    const slots = [];
    
    timeCells.forEach(function(cell) {
        const timeText = cell.textContent.trim();
        const time = convertTimeFormat(timeText);
        if (time) {
            slots.push(time);
        }
    });
    
    return slots;
}

// 時刻表示を "HH:MM" 形式に変換
function convertTimeFormat(timeText) {
    const match = timeText.match(/(\d{1,2}):(\d{2})/);
    if (match) {
        const hours = parseInt(match[1]);
        const minutes = match[2];
        return hours.toString().padStart(2, '0') + ':' + minutes;
    }
    return null;
}

// 時間から位置（%）を計算
function calculatePosition(time, timeSlots) {
    if (!time || timeSlots.length === 0) return 0;
    
    const targetMinutes = timeToMinutes(time);
    const startMinutes = timeToMinutes(timeSlots[0]);
    const endMinutes = timeToMinutes(timeSlots[timeSlots.length - 1]);
    const totalMinutes = endMinutes - startMinutes;
    
    if (totalMinutes === 0) return 0;
    
    return ((targetMinutes - startMinutes) / totalMinutes) * 100;
}

// 時間から幅（%）を計算
function calculateDuration(startTime, endTime, timeSlots) {
    if (!startTime || !endTime || timeSlots.length === 0) return 0;
    
    const startMinutes = timeToMinutes(startTime);
    const endMinutes = timeToMinutes(endTime);
    const duration = endMinutes - startMinutes;
    
    const totalStartMinutes = timeToMinutes(timeSlots[0]);
    const totalEndMinutes = timeToMinutes(timeSlots[timeSlots.length - 1]);
    const totalMinutes = totalEndMinutes - totalStartMinutes;
    
    if (totalMinutes === 0) return 0;
    
    return (duration / totalMinutes) * 100;
}

// 時刻を分に変換
function timeToMinutes(time) {
    const parts = time.split(':');
    if (parts.length !== 2) return 0;
    
    const hours = parseInt(parts[0]);
    const minutes = parseInt(parts[1]);
    
    return hours * 60 + minutes;
}

// 部屋番号を更新（自動保存）
function updateRoomNumber(inputElement) {
    const reservationId = inputElement.getAttribute('data-reservation-id');
    const roomNumber = inputElement.value.trim();
    
    if (!reservationId) {
        return;
    }
    
    const store = getStoreFromPath();
    
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
            inputElement.style.borderColor = 'rgba(40, 167, 69, 0.8)';
            setTimeout(() => {
                inputElement.style.borderColor = '';
            }, 1000);
        } else {
            alert('部屋番号の更新に失敗しました: ' + (data.error || '不明なエラー'));
            inputElement.style.borderColor = 'rgba(220, 53, 69, 0.8)';
        }
    })
    .catch(error => {
        alert('エラーが発生しました: ' + error.message);
        inputElement.style.borderColor = 'rgba(220, 53, 69, 0.8)';
    });
}

// URLから店舗コードを取得
function getStoreFromPath() {
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[1] || 'nagano';
}