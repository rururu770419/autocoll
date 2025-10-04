// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// グローバル変数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1; // 1-12
let staffList = [];
let shiftTypes = [];
let shiftsData = [];
let dateMemos = {}; // 日付別備考データ

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    loadShiftData();
    
    // フォーム送信イベント
    document.getElementById('shift-form').addEventListener('submit', function(e) {
        e.preventDefault();
        saveShift();
    });
    
    // シフト種別変更時にアルバイト判定
    document.getElementById('shift-type-id').addEventListener('change', function() {
        checkIfPartTime();
    });
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// データ読み込み
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function loadShiftData() {
    showLoading(true);
    
    fetch(`/${store}/shift_management/get_shifts?year=${currentYear}&month=${currentMonth}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                staffList = data.staff_list;
                shiftTypes = data.shift_types;
                shiftsData = data.shifts;
                dateMemos = data.date_memos || {}; // 日付別備考を読み込み
                
                updateMonthDisplay();
                renderShiftTable();
                loadShiftTypesIntoSelect();
            } else {
                alert('データの読み込みに失敗しました: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('通信エラーが発生しました');
        })
        .finally(() => {
            showLoading(false);
        });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シフト表の描画
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function renderShiftTable() {
    const headerRow = document.getElementById('staff-header');
    const tbody = document.getElementById('shift-body');
    
    // ヘッダー作成（スタッフ名 + 備考）
    headerRow.innerHTML = '<th class="shift-date-column">日付</th>';
    staffList.forEach(staff => {
        const th = document.createElement('th');
        th.textContent = staff.staff_name;
        th.dataset.staffId = staff.staff_id;
        headerRow.appendChild(th);
    });
    
    // 備考列を追加
    const memoHeader = document.createElement('th');
    memoHeader.textContent = '備考';
    memoHeader.style.minWidth = '200px';
    headerRow.appendChild(memoHeader);
    
    // ボディ作成（日付×スタッフのマトリックス）
    tbody.innerHTML = '';
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    
    for (let day = 1; day <= daysInMonth; day++) {
        const date = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dateObj = new Date(currentYear, currentMonth - 1, day);
        const dayOfWeek = dateObj.getDay(); // 0=日, 6=土
        
        const tr = document.createElement('tr');
        if (dayOfWeek === 0 || dayOfWeek === 6) {
            tr.classList.add('shift-weekend');
        }
        
        // 日付セル
        const dateCell = document.createElement('td');
        dateCell.classList.add('shift-date-cell');
        dateCell.textContent = `${currentMonth}/${day}（${['日','月','火','水','木','金','土'][dayOfWeek]}）`;
        tr.appendChild(dateCell);
        
        // スタッフごとのシフトセル
        staffList.forEach(staff => {
            const shiftCell = document.createElement('td');
            shiftCell.dataset.date = date;
            shiftCell.dataset.staffId = staff.staff_id;
            shiftCell.dataset.staffName = staff.staff_name;
            shiftCell.dataset.userRole = staff.user_role;
            
            // シフトデータを検索
            const shift = shiftsData.find(s => 
                s.staff_id === staff.staff_id && s.shift_date === date
            );
            
            if (shift) {
                shiftCell.innerHTML = createShiftCellContent(shift);
                shiftCell.dataset.shiftId = shift.shift_id;
            } else {
                shiftCell.innerHTML = '<div class="shift-management-empty-cell">未登録</div>';
            }
            
            // クリックイベント
            shiftCell.addEventListener('click', function() {
                openShiftModal(this);
            });
            
            tr.appendChild(shiftCell);
        });
        
        // 備考セルを追加
        const memoCell = document.createElement('td');
        memoCell.classList.add('shift-memo-cell');
        memoCell.dataset.date = date;
        memoCell.style.background = dayOfWeek === 0 || dayOfWeek === 6 ? '#fff3cd' : 'white';
        memoCell.style.minWidth = '200px';
        memoCell.style.padding = '10px';
        memoCell.style.borderLeft = '2px solid #dee2e6';
        memoCell.style.cursor = 'text';
        
        // 該当日の備考データを取得
        const existingMemo = dateMemos[date] || '';
        
        const memoInput = document.createElement('textarea');
        memoInput.value = existingMemo;
        memoInput.placeholder = '備考を入力...';
        memoInput.style.width = '100%';
        memoInput.style.border = 'none';
        memoInput.style.resize = 'vertical';
        memoInput.style.minHeight = '30px';
        memoInput.style.fontSize = '13px';
        memoInput.dataset.date = date;
        
        // 備考保存イベント（フォーカスアウト時に保存）
        memoInput.addEventListener('blur', function() {
            saveDateMemo(date, this.value);
        });
        
        memoCell.appendChild(memoInput);
        tr.appendChild(memoCell);
        
        tbody.appendChild(tr);
    }
}

function createShiftCellContent(shift) {
    const shiftType = shiftTypes.find(t => t.shift_type_id === shift.shift_type_id);
    if (!shiftType) return '<div class="shift-management-empty-cell">不明</div>';
    
    let html = '<div class="shift-management-cell">';
    
    // シフト種別バッジ
    html += `<span class="shift-management-badge" style="background-color: ${shiftType.color};">
                ${shiftType.shift_name}
             </span>`;
    
    // 時間表示（あれば）
    if (shift.start_time && shift.end_time) {
        html += `<span class="shift-management-time">${shift.start_time} - ${shift.end_time}</span>`;

    } else if (shift.start_time || shift.end_time) {
        const time = shift.start_time || shift.end_time;
        html += `<span class="shift-management-time">${time}</span>`;

    }
    
    html += '</div>';
    return html;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// モーダル操作
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function openShiftModal(cell) {
    const shiftId = cell.dataset.shiftId || '';
    const staffId = cell.dataset.staffId;
    const staffName = cell.dataset.staffName;
    const date = cell.dataset.date;
    const userRole = cell.dataset.userRole;
    
    // フォームをリセット
    document.getElementById('shift-form').reset();
    document.getElementById('shift-id').value = shiftId;
    document.getElementById('staff-id').value = staffId;
    document.getElementById('staff-name').value = staffName;
    document.getElementById('shift-date').value = date;
    document.getElementById('date-display').value = formatDate(date);
    
    // シフトデータがあれば読み込み
    const shift = shiftsData.find(s => s.staff_id == staffId && s.shift_date === date);
    
    if (shift) {
        document.getElementById('shift-type-id').value = shift.shift_type_id;
        document.getElementById('start-time').value = shift.start_time || '';
        document.getElementById('end-time').value = shift.end_time || '';
        document.getElementById('memo').value = shift.memo || '';
        
        // 削除ボタン表示
        document.getElementById('delete-btn').style.display = 'inline-block';
    } else {
        document.getElementById('delete-btn').style.display = 'none';
    }
    
    // アルバイトの場合は時間入力を表示
    checkIfPartTime();
    
    // モーダル表示
    document.getElementById('shift-modal').style.display = 'block';
}

function closeShiftModal() {
    document.getElementById('shift-modal').style.display = 'none';
}

function checkIfPartTime() {
    const staffId = document.getElementById('staff-id').value;
    const staff = staffList.find(s => s.staff_id == staffId);
    
    const timeInputs = document.getElementById('time-inputs');
    
    // ドライバー = アルバイト
    if (staff && staff.user_role === 'ドライバー') {
        timeInputs.style.display = 'block';
    } else {
        timeInputs.style.display = 'none';
        document.getElementById('start-time').value = '';
        document.getElementById('end-time').value = '';
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シフト保存・削除
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function saveShift() {
    const shiftId = document.getElementById('shift-id').value || null;
    const staffId = document.getElementById('staff-id').value;
    const shiftDate = document.getElementById('shift-date').value;
    const shiftTypeId = document.getElementById('shift-type-id').value;
    const startTime = document.getElementById('start-time').value || null;
    const endTime = document.getElementById('end-time').value || null;
    const memo = document.getElementById('memo').value || '';
    
    if (!shiftTypeId) {
        alert('シフト種別を選択してください');
        return;
    }
    
    const requestData = {
        shift_id: shiftId,
        staff_id: staffId,  // parseIntを削除（文字列のまま送信）
        shift_date: shiftDate,
        shift_type_id: parseInt(shiftTypeId),
        start_time: startTime,
        end_time: endTime,
        memo: memo
    };
    
    showLoading(true);
    
    fetch(`/${store}/shift_management/save_shift`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            closeShiftModal();
            loadShiftData(); // 再読み込み
        } else {
            alert('保存に失敗しました: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('通信エラーが発生しました');
    })
    .finally(() => {
        showLoading(false);
    });
}

function deleteShift() {
    if (!confirm('このシフトを削除してもよろしいですか？')) {
        return;
    }
    
    const staffId = document.getElementById('staff-id').value;
    const shiftDate = document.getElementById('shift-date').value;
    
    if (!staffId || !shiftDate) {
        alert('削除対象のシフトが見つかりません');
        return;
    }
    
    showLoading(true);
    
    fetch(`/${store}/shift_management/delete_shift`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            staff_id: staffId,  // parseIntを削除（文字列のまま送信）
            shift_date: shiftDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            closeShiftModal();
            loadShiftData(); // 再読み込み
        } else {
            alert('削除に失敗しました: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('通信エラーが発生しました');
    })
    .finally(() => {
        showLoading(false);
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 月の切り替え
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function changeMonth(delta) {
    currentMonth += delta;
    
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    } else if (currentMonth < 1) {
        currentMonth = 12;
        currentYear--;
    }
    
    loadShiftData();
}

function updateMonthDisplay() {
    document.getElementById('current-month').textContent = 
        `${currentYear}年 ${currentMonth}月`;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ユーティリティ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function loadShiftTypesIntoSelect() {
    const select = document.getElementById('shift-type-id');
    select.innerHTML = '<option value="">選択してください</option>';
    
    shiftTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type.shift_type_id;
        option.textContent = type.shift_name;
        select.appendChild(option);
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const dayOfWeek = ['日','月','火','水','木','金','土'][date.getDay()];
    
    return `${year}年${month}月${day}日（${dayOfWeek}）`;
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

// モーダル外クリックで閉じる
window.onclick = function(event) {
    const modal = document.getElementById('shift-modal');
    if (event.target === modal) {
        closeShiftModal();
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 日付別備考の保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function saveDateMemo(date, memo) {
    fetch(`/${store}/shift_management/save_date_memo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            date: date,
            memo: memo
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // ローカルのdateMemosも更新
            if (memo.trim() === '') {
                delete dateMemos[date];
            } else {
                dateMemos[date] = memo;
            }
            console.log('備考を保存しました');
        } else {
            console.error('備考の保存に失敗しました');
            alert('備考の保存に失敗しました');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('通信エラーが発生しました');
    });
}