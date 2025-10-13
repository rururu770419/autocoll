// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// スタッフシフト管理ページ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// グローバル変数
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1;
let staffList = [];
let shiftTypes = [];
let shiftsData = {};
let memosData = {};
let daysInMonth = 31;

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    loadShiftData();
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// データ読み込み
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function loadShiftData() {
    try {
        const store = window.staffShiftStore || 'nagano';
        const response = await fetch(`/${store}/staff_shift/data?year=${currentYear}&month=${currentMonth}`);
        const data = await response.json();
        
        if (data.success) {
            staffList = data.staff_list || [];
            shiftTypes = data.shift_types || [];
            daysInMonth = data.days_in_month || 31;
            
            // シフトデータを整形
            shiftsData = {};
            (data.shifts || []).forEach(shift => {
                const key = `${shift.staff_id}_${shift.shift_date}`;
                shiftsData[key] = shift;
            });
            
            // 備考データを整形
            memosData = {};
            (data.memos || []).forEach(memo => {
                memosData[memo.memo_date] = memo.memo_text;
            });
            
            renderTable();
            updateMonthDisplay();
        } else {
            showMessage('データの読み込みに失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error loading shift data:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// テーブル描画
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function renderTable() {
    const table = document.getElementById('shiftTable');
    const thead = table.querySelector('thead tr');
    const tbody = document.getElementById('shiftTableBody');
    
    // ヘッダー行を生成（日付・曜日・スタッフ名・備考）
    thead.innerHTML = `
        <th class="staff-shift-th-date">日付</th>
        <th class="staff-shift-th-day">曜日</th>
        ${staffList.map(staff => `
            <th class="staff-shift-th-staff">${escapeHtml(staff.name)}</th>
        `).join('')}
        <th class="staff-shift-th-memo">備考</th>
    `;
    
    // ボディ行を生成（各日付）
    tbody.innerHTML = '';
    for (let day = 1; day <= daysInMonth; day++) {
        const date = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayOfWeek = getDayOfWeek(currentYear, currentMonth, day);
        const dayClass = getDayClass(dayOfWeek);
        
        const row = document.createElement('tr');
        
        // 日付セル
        row.innerHTML += `<td class="staff-shift-td-date">${day}</td>`;
        
        // 曜日セル
        row.innerHTML += `<td class="staff-shift-td-day ${dayClass}">${dayOfWeek}</td>`;
        
        // スタッフごとのシフトセル
        staffList.forEach(staff => {
            const shiftKey = `${staff.login_id}_${date}`;
            const shift = shiftsData[shiftKey];
            row.innerHTML += renderShiftCell(staff.login_id, date, shift);
        });
        
        // 備考セル
        const memo = memosData[date] || '';
        row.innerHTML += renderMemoCell(date, memo);
        
        tbody.appendChild(row);
    }
}

function renderShiftCell(staffId, date, shift) {
    if (!shift) {
        return `<td class="staff-shift-cell" onclick="openShiftModal('${staffId}', '${date}')"></td>`;
    }
    
    let content = '<div class="staff-shift-cell-content">';
    
    // シフト種別表示
    if (shift.shift_type_id && shift.shift_name) {
        const bgColor = shift.color || '#808080';
        const textColor = getContrastColor(bgColor);
        content += `<div class="staff-shift-type-badge" style="background-color: ${bgColor}; color: ${textColor};">${escapeHtml(shift.shift_name)}</div>`;
    }
    
    // 時間表示
    if (shift.start_time || shift.end_time) {
        const startTime = shift.start_time ? shift.start_time.substring(0, 5) : '--:--';
        const endTime = shift.end_time ? shift.end_time.substring(0, 5) : '--:--';
        content += `<div class="staff-shift-time-display">${startTime}～${endTime}</div>`;
    }
    
    // メモアイコン
    if (shift.memo) {
        content += `<div class="staff-shift-has-memo">📝</div>`;
    }
    
    content += '</div>';
    
    return `<td class="staff-shift-cell" onclick="openShiftModal('${staffId}', '${date}')">${content}</td>`;
}

function renderMemoCell(date, memo) {
    if (!memo) {
        return `<td class="staff-shift-memo-cell" onclick="openMemoModal('${date}')"><span class="staff-shift-memo-placeholder">クリックして入力</span></td>`;
    }
    return `<td class="staff-shift-memo-cell" onclick="openMemoModal('${date}')">${escapeHtml(memo)}</td>`;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 月切り替え
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
    const display = document.getElementById('currentMonth');
    if (display) {
        display.textContent = `${currentYear}年 ${currentMonth}月`;
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シフト入力モーダル
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function openShiftModal(staffId, date) {
    const staff = staffList.find(s => s.login_id === staffId);
    if (!staff) return;
    
    const shiftKey = `${staffId}_${date}`;
    const shift = shiftsData[shiftKey];
    
    // モーダルタイトル
    const formattedDate = formatDate(date);
    document.getElementById('modalTitle').textContent = `${staff.name} - ${formattedDate}`;
    
    // hidden fields
    document.getElementById('modalStaffId').value = staffId;
    document.getElementById('modalShiftDate').value = date;
    
    // シフト種別セレクトボックスを生成
    const shiftTypeSelect = document.getElementById('modalShiftType');
    shiftTypeSelect.innerHTML = '<option value="">選択してください</option>' +
        shiftTypes.map(type => 
            `<option value="${type.shift_type_id}" ${shift && shift.shift_type_id === type.shift_type_id ? 'selected' : ''}>${escapeHtml(type.shift_name)}</option>`
        ).join('');
    
    // 既存データを復元
    if (shift) {
        // 入力タイプを判定
        if (shift.shift_type_id) {
            document.querySelector('input[name="input_type"][value="shift_type"]').checked = true;
            toggleInputType();
        } else if (shift.start_time || shift.end_time) {
            document.querySelector('input[name="input_type"][value="custom_time"]').checked = true;
            toggleInputType();
            document.getElementById('modalStartTime').value = shift.start_time || '';
            document.getElementById('modalEndTime').value = shift.end_time || '';
        }
        
        document.getElementById('modalMemo').value = shift.memo || '';
    } else {
        // 新規入力の場合
        document.getElementById('shiftForm').reset();
        document.querySelector('input[name="input_type"][value="shift_type"]').checked = true;
        toggleInputType();
    }
    
    document.getElementById('shiftModal').style.display = 'block';
}

function closeShiftModal() {
    document.getElementById('shiftModal').style.display = 'none';
}

function toggleInputType() {
    const inputType = document.querySelector('input[name="input_type"]:checked').value;
    const shiftTypeSection = document.getElementById('shiftTypeSection');
    const customTimeSection = document.getElementById('customTimeSection');
    
    if (inputType === 'shift_type') {
        shiftTypeSection.style.display = 'block';
        customTimeSection.style.display = 'none';
        // 時間入力をクリア
        document.getElementById('modalStartTime').value = '';
        document.getElementById('modalEndTime').value = '';
    } else {
        shiftTypeSection.style.display = 'none';
        customTimeSection.style.display = 'block';
        // シフト種別をクリア
        document.getElementById('modalShiftType').value = '';
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シフト保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    const shiftForm = document.getElementById('shiftForm');
    if (shiftForm) {
        shiftForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveShift();
        });
    }
});

async function saveShift() {
    try {
        const staffId = document.getElementById('modalStaffId').value;
        const shiftDate = document.getElementById('modalShiftDate').value;
        const inputType = document.querySelector('input[name="input_type"]:checked').value;
        
        let shiftTypeId = null;
        let startTime = null;
        let endTime = null;
        
        if (inputType === 'shift_type') {
            shiftTypeId = document.getElementById('modalShiftType').value || null;
        } else {
            startTime = document.getElementById('modalStartTime').value || null;
            endTime = document.getElementById('modalEndTime').value || null;
        }
        
        const memo = document.getElementById('modalMemo').value || null;
        
        const store = window.staffShiftStore || 'nagano';
        const response = await fetch(`/${store}/staff_shift/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                staff_id: staffId,
                shift_date: shiftDate,
                shift_type_id: shiftTypeId,
                start_time: startTime,
                end_time: endTime,
                memo: memo
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('シフトを保存しました', 'success');
            closeShiftModal();
            loadShiftData();
        } else {
            showMessage(result.message || 'シフトの保存に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error saving shift:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// シフト削除
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function deleteShift() {
    if (!confirm('このシフトを削除してもよろしいですか？')) {
        return;
    }
    
    try {
        const staffId = document.getElementById('modalStaffId').value;
        const shiftDate = document.getElementById('modalShiftDate').value;
        
        const store = window.staffShiftStore || 'nagano';
        const response = await fetch(`/${store}/staff_shift/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                staff_id: staffId,
                shift_date: shiftDate
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('シフトを削除しました', 'success');
            closeShiftModal();
            loadShiftData();
        } else {
            showMessage(result.message || 'シフトの削除に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error deleting shift:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 日付別備考モーダル
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function openMemoModal(date) {
    const formattedDate = formatDate(date);
    document.getElementById('memoModalTitle').textContent = `${formattedDate} の備考`;
    document.getElementById('memoDate').value = date;
    document.getElementById('memoText').value = memosData[date] || '';
    document.getElementById('memoModal').style.display = 'block';
}

function closeMemoModal() {
    document.getElementById('memoModal').style.display = 'none';
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 備考保存
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    const memoForm = document.getElementById('memoForm');
    if (memoForm) {
        memoForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveMemo();
        });
    }
});

async function saveMemo() {
    try {
        const memoDate = document.getElementById('memoDate').value;
        const memoText = document.getElementById('memoText').value;
        
        const store = window.staffShiftStore || 'nagano';
        const response = await fetch(`/${store}/staff_shift/save_memo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                memo_date: memoDate,
                memo_text: memoText
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('備考を保存しました', 'success');
            closeMemoModal();
            loadShiftData();
        } else {
            showMessage(result.message || '備考の保存に失敗しました', 'error');
        }
    } catch (error) {
        console.error('Error saving memo:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function getDayOfWeek(year, month, day) {
    const date = new Date(year, month - 1, day);
    const days = ['日', '月', '火', '水', '木', '金', '土'];
    return days[date.getDay()];
}

function getDayClass(dayOfWeek) {
    if (dayOfWeek === '日') return 'staff-shift-day-sunday';
    if (dayOfWeek === '土') return 'staff-shift-day-saturday';
    return '';
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const dayOfWeek = getDayOfWeek(year, month, day);
    return `${year}年${month}月${day}日（${dayOfWeek}）`;
}

function getContrastColor(hexColor) {
    // 背景色の明度を計算して、読みやすい文字色を返す
    const r = parseInt(hexColor.substr(1, 2), 16);
    const g = parseInt(hexColor.substr(3, 2), 16);
    const b = parseInt(hexColor.substr(5, 2), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 155 ? '#000000' : '#ffffff';
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    if (!messageArea) return;
    
    messageArea.className = `staff-shift-message staff-shift-message-${type}`;
    messageArea.textContent = message;
    messageArea.style.display = 'block';
    
    setTimeout(() => {
        messageArea.style.display = 'none';
    }, 3000);
}

// モーダル外クリックで閉じる
window.onclick = function(event) {
    const shiftModal = document.getElementById('shiftModal');
    const memoModal = document.getElementById('memoModal');
    
    if (event.target === shiftModal) {
        closeShiftModal();
    }
    if (event.target === memoModal) {
        closeMemoModal();
    }
}