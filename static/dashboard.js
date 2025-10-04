// 変更された項目を追跡するためのオブジェクト
let pendingChanges = {};

// お釣りモーダル関連の変数
let currentChangeRecord = null;

// お知らせの表示状態
let announcementVisible = false;

// 保存完了メッセージを表示する関数
function showSaveMessage() {
  const messageElement = document.getElementById('saveMessage');
  messageElement.style.display = 'inline';
  
  // 3秒後に自動で非表示にする
  setTimeout(() => {
    messageElement.style.display = 'none';
  }, 3000);
}

// お知らせの表示/非表示切り替え
function toggleAnnouncement() {
  const announcementArea = document.getElementById('announcementArea');
  const currentDisplay = announcementArea.style.display;
  
  if (currentDisplay === 'none' || currentDisplay === '') {
    announcementArea.style.display = 'block';
    announcementVisible = true;
  } else {
    announcementArea.style.display = 'none';
    announcementVisible = false;
  }
  
  // 表示状態をサーバーに保存
  updateAnnouncement('is_visible', announcementVisible);
}

// スタッフ選択時の背景色変更（即座に反映、でも保存は後で）
function updateStaffColor(recordId, selectElement) {
  const selectedOption = selectElement.options[selectElement.selectedIndex];
  const color = selectedOption.getAttribute('data-color') || '#ffffff';
  selectElement.style.backgroundColor = color;
  
  // 変更を記録（保存は後で）
  recordChange(recordId, 'staff_id', selectElement.value);
}

// 変更を記録する関数
function recordChange(recordId, field, value) {
  if (!pendingChanges[recordId]) {
    pendingChanges[recordId] = {};
  }
  pendingChanges[recordId][field] = value;
  console.log('Change recorded:', recordId, field, value); // デバッグ用
}

// 済みボタンの切り替え（お釣り確認付き）
function toggleCompleted(recordId) {
  const row = document.getElementById(`record-${recordId}`);
  const button = event.target;
  
  // 現在未完了で、完了にしようとしている場合のみチェック
  if (row.style.opacity !== '0.2') {
    // お釣り登録済みかどうかをチェック
    fetch(window.dashboardUrls.store + '/dashboard/check_change', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        record_id: recordId
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        if (data.is_exit && !data.has_change) {
          // 退室レコードでお釣り未登録の場合 - 赤い警告ダイアログ
          showChangeNotEnteredDialog('お釣りの入力がまだ済んでいません');
          return; // 完了状態を変更しない
        } else {
          // お釣り登録済みまたは入室レコードの場合は通常処理
          executeToggleCompleted(recordId, row, button, true);
        }
      } else {
        // エラーの場合はとりあえず通常処理
        console.error('Change check error:', data.error);
        executeToggleCompleted(recordId, row, button, true);
      }
    })
    .catch(error => {
      console.error('Change check failed:', error);
      // エラーの場合はとりあえず通常処理
      executeToggleCompleted(recordId, row, button, true);
    });
  } else {
    // 完了→未完了への変更は常に許可
    executeToggleCompleted(recordId, row, button, false);
  }
}

// 実際の完了状態切り替え処理
function executeToggleCompleted(recordId, row, button, newCompleted) {
  if (newCompleted) {
    // 完了にする
    row.style.opacity = '0.2';
    button.textContent = '済';
    button.className = 'dashboard-btn dashboard-btn-completed';
  } else {
    // 未完了にする
    row.style.opacity = '1';
    button.textContent = '未';
    button.className = 'dashboard-btn dashboard-btn-uncompleted';
  }
  
  // 済み状態の変更を記録
  recordChange(recordId, 'is_completed', newCompleted);
}

// メモの表示/非表示切り替え（展開状態も記録）
function toggleMemo(recordId) {
  const memoRow = document.getElementById(`memo-row-${recordId}`);
  let isExpanded;
  
  if (memoRow.style.display === 'none') {
    memoRow.style.display = '';
    isExpanded = true;
  } else {
    memoRow.style.display = 'none';
    isExpanded = false;
  }
  
  // 展開状態の変更を記録
  recordChange(recordId, 'memo_expanded', isExpanded);
}

// お知らせ更新関数を修正
function updateAnnouncement(field, value) {
  const storeUrl = window.dashboardUrls.store;
  const currentDate = window.currentDate; // 現在表示中の日付
  
  fetch(`${storeUrl}/dashboard/update_announcement`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      field: field,
      value: value,
      date: currentDate // 日付を追加
    })
  })
  .then(response => response.json())
  .then(data => {
    if (!data.success) {
      console.error('お知らせ更新失敗:', data);
    }
  })
  .catch(error => {
    console.error('お知らせ更新エラー:', error);
  });
}

// 日付変更時にお知らせも更新
function changeDate(direction) {
    const currentDateElement = document.getElementById('currentDateDisplay');
    const currentDate = new Date(window.currentDate);
    
    // 現在のお知らせを保存してから移動
    saveCurrentAnnouncement();
    
    // 日付を変更
    currentDate.setDate(currentDate.getDate() + direction);
    
    // 日付文字列を更新
    const newDateString = formatDateForUrl(currentDate);
    
    // URLパラメータを付けてページ遷移
    const storeUrl = window.dashboardUrls.store;
    window.location.href = `${storeUrl}/dashboard?date=${newDateString}`;
}

// 現在のお知らせ内容を保存
function saveCurrentAnnouncement() {
    const announcementTextarea = document.getElementById('announcementContent');
    if (announcementTextarea && announcementTextarea.value !== announcementTextarea.defaultValue) {
        updateAnnouncement('content', announcementTextarea.value);
    }
}

// カレンダーから日付選択時も保存
function selectCalendarDate(selectedDate) {
    // 現在のお知らせを保存
    saveCurrentAnnouncement();
    
    // 新しい日付に移動
    const storeUrl = window.dashboardUrls.store;
    window.location.href = `${storeUrl}/dashboard?date=${selectedDate}`;
}

// 警告確認ダイアログ（赤いスタイル）
function showRedConfirm(message, callback) {
  // ダイアログ作成
  const overlay = document.createElement('div');
  overlay.innerHTML = `
    <div style="
      position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
      background: rgba(0,0,0,0.5); display: flex; align-items: center; 
      justify-content: center; z-index: 10000;
    ">
      <div style="
        background: #ffe6e6; border: 3px solid #ff0000; border-radius: 8px; 
        padding: 20px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
      ">
        <p style="color: #cc0000; font-weight: bold; font-size: 16px; margin-bottom: 20px;">
          ${message}
        </p>
        <button id="confirmYes" style="
          background: #ff4444; color: white; border: none; padding: 10px 20px; 
          margin: 5px; border-radius: 4px; cursor: pointer; font-weight: bold;
        ">削除する</button>
        <button id="confirmNo" style="
          background: #999; color: white; border: none; padding: 10px 20px; 
          margin: 5px; border-radius: 4px; cursor: pointer;
        ">キャンセル</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // イベント設定
  document.getElementById('confirmYes').onclick = function() {
    document.body.removeChild(overlay);
    callback(true);
  };
  
  document.getElementById('confirmNo').onclick = function() {
    document.body.removeChild(overlay);
    callback(false);
  };
  
  // 背景クリックで閉じる
  overlay.onclick = function(e) {
    if (e.target === overlay) {
      document.body.removeChild(overlay);
      callback(false);
    }
  };
}

// 登録済み警告ダイアログ（青いスタイル）
function showAlreadyRegisteredDialog(message) {
  // ダイアログ作成
  const overlay = document.createElement('div');
  overlay.innerHTML = `
    <div style="
      position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
      background: rgba(0,0,0,0.5); display: flex; align-items: center; 
      justify-content: center; z-index: 10000;
    ">
      <div style="
        background: #e6f3ff; border: 3px solid #0066cc; border-radius: 8px; 
        padding: 20px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
      ">
        <p style="color: #004080; font-weight: bold; font-size: 16px; margin-bottom: 20px;">
          ${message}
        </p>
        <button id="registeredOk" style="
          background: #0066cc; color: white; border: none; padding: 10px 30px; 
          margin: 5px; border-radius: 4px; cursor: pointer; font-weight: bold;
        ">OK</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // イベント設定
  document.getElementById('registeredOk').onclick = function() {
    document.body.removeChild(overlay);
  };
  
  // 背景クリックで閉じる
  overlay.onclick = function(e) {
    if (e.target === overlay) {
      document.body.removeChild(overlay);
    }
  };
}

// レコード削除（お釣り確認付き）
function deleteRecord(recordId) {
  fetch(window.dashboardUrls.store + '/dashboard/check_change', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      record_id: recordId
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      if (data.is_exit && !data.has_change) {
        // 退室レコードでお釣り未登録の場合 - 赤い警告ダイアログ
        showRedConfirm('お釣り登録がまだです。削除しますか？', function(confirmed) {
          if (confirmed) {
            executeDelete(recordId);
          }
        });
      } else {
        // 通常の確認メッセージ（従来通り）
        if (confirm('この記録を削除しますか？')) {
          executeDelete(recordId);
        }
      }
    } else {
      alert('削除確認エラー: ' + (data.error || '不明なエラー'));
    }
  })
  .catch(error => {
    console.error('削除確認エラー:', error);
    if (confirm('この記録を削除しますか？')) {
      executeDelete(recordId);
    }
  });
}

// 実際の削除処理を実行
function executeDelete(recordId) {
  const storeUrl = window.dashboardUrls.store;
  
  fetch(`${storeUrl}/dashboard/delete_record`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      record_id: recordId
    })
  })
  .then(response => {
    console.log('Delete response status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('Delete response data:', data);
    if (data.success) {
      location.reload();
    } else {
      alert('削除に失敗しました: ' + (data.error || '不明なエラー'));
    }
  })
  .catch(error => {
    console.error('削除エラー:', error);
    alert('削除に失敗しました: ' + error.message);
  });
}

// レコード更新（即座に保存用）
function updateRecord(recordId, field, value) {
  const storeUrl = window.dashboardUrls.store;
  const updateUrl = `${storeUrl}/dashboard/update_record`;
  
  console.log('Update URL:', updateUrl);
  console.log('Update data:', {record_id: recordId, field: field, value: value});
  
  return fetch(updateUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      record_id: recordId,
      field: field,
      value: value
    })
  })
  .then(response => {
    console.log('Update response status:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText} - URL: ${updateUrl}`);
    }
    
    return response.json();
  })
  .then(data => {
    console.log('Update response data:', data);
    if (!data.success) {
      console.error('更新失敗:', field, value, data);
      throw new Error(data.error || '更新に失敗しました');
    }
    return data;
  })
  .catch(error => {
    console.error('Update error:', error);
    throw error;
  });
}

// 全体保存（修正版）
function saveAllChanges() {
  console.log('保存開始:', pendingChanges);
  
  // 保存前に入室時間の変更をチェックして退室時間を計算
  for (let recordId in pendingChanges) {
    if (pendingChanges[recordId]['entry_time']) {
      calculateExitTimeBeforeSave(recordId);
    }
  }
  
  // メモフィールドの現在の値を取得
  document.querySelectorAll('textarea[data-field="memo"]').forEach(textarea => {
    const recordId = textarea.getAttribute('data-record-id');
    const currentValue = textarea.value;
    if (currentValue !== textarea.defaultValue) {
      recordChange(recordId, 'memo', currentValue);
    }
  });
  
  // お知らせフィールドの現在の値を取得
  const announcementTextarea = document.getElementById('announcementContent');
  if (announcementTextarea) {
    const currentValue = announcementTextarea.value;
    if (currentValue !== announcementTextarea.defaultValue) {
      updateAnnouncement('content', currentValue);
      announcementTextarea.defaultValue = currentValue;
    }
  }
  
  if (Object.keys(pendingChanges).length === 0) {
    showSaveMessage();
    return;
  }

  // 全ての変更を順次保存
  let savePromises = [];
  
  for (let recordId in pendingChanges) {
    for (let field in pendingChanges[recordId]) {
      let value = pendingChanges[recordId][field];
      console.log('保存中:', recordId, field, value);
      let promise = updateRecord(recordId, field, value);
      savePromises.push(promise);
    }
  }
  
  Promise.all(savePromises)
    .then(results => {
      console.log('保存結果:', results);
      pendingChanges = {};
      
      document.querySelectorAll('textarea[data-field="memo"]').forEach(textarea => {
        textarea.defaultValue = textarea.value;
      });
      
      showSaveMessage();
    })
    .catch(error => {
      console.error('保存エラー:', error);
      alert('一部の保存に失敗しました: ' + error.message);
    });
}

// 保存前に退室時間を計算する関数（新規追加）
function calculateExitTimeBeforeSave(recordId) {
  const row = document.getElementById(`record-${recordId}`);
  if (!row) return;
  
  const castSelect = row.querySelector('.dashboard-cast-select');
  const timeInput = row.querySelector('.dashboard-time-input');
  const badge = row.querySelector('.dashboard-badge');
  
  if (!castSelect || !timeInput || !badge) return;
  
  const isEntry = badge.textContent.trim() === '入';
  if (!isEntry) return;
  
  const castId = castSelect.value;
  const entryTime = timeInput.value;
  
  if (!castId || !entryTime) return;
  
  // 関連する退室レコードを探す
  const relatedRecord = findRelatedRecord(recordId, castId, isEntry);
  if (!relatedRecord) return;
  
  // コース情報を取得
  const courseId = row.getAttribute('data-course-id');
  if (!courseId || !courseCache[courseId]) return;
  
  const courseTime = courseCache[courseId];
  const exitTime = addMinutesToTime(entryTime, courseTime);
  
  // 関連する退室レコードの時間を更新
  const exitRow = relatedRecord.row;
  const exitTimeInput = exitRow.querySelector('.dashboard-time-input');
  
  if (exitTimeInput) {
    exitTimeInput.value = exitTime;
    recordChange(relatedRecord.recordId, 'exit_time', exitTime);
    console.log(`保存時に退室時間を計算: ${entryTime} + ${courseTime}分 = ${exitTime}`);
  }
}

// 更新機能
function refreshDashboard() {
  const refreshBtn = document.querySelector('.dashboard-refresh-btn');
  const refreshMessage = document.getElementById('refreshMessage');
  
  const originalText = refreshBtn.textContent;
  refreshBtn.textContent = '更新中...';
  refreshBtn.disabled = true;
  
  // メッセージを先に表示
  refreshMessage.style.display = 'inline';
  
  // 1秒後にページリロード
  setTimeout(() => {
    window.location.reload();
  }, 1000);
}

// 登録済みチェック関数
function checkIfAlreadyRegistered(recordId, castId, exitTime, onNotRegistered) {
  if (!castId || !exitTime) {
    alert('キャストと退室時間が設定されていません');
    return;
  }
  
  fetch(window.dashboardUrls.store + '/check_change_registration', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'same-origin',
    body: JSON.stringify({
      cast_id: castId,
      exit_time: exitTime
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      if (data.already_registered) {
        // カスタムダイアログを表示（標準のalertの代わり）
        showAlreadyRegisteredDialog('このお釣りは既に登録済みです');
      } else {
        onNotRegistered();
      }
    } else {
      // エラーの場合はとりあえずモーダルを開く
      console.error('Registration check error:', data.error);
      onNotRegistered();
    }
  })
  .catch(error => {
    console.error('Registration check failed:', error);
    // エラーの場合はとりあえずモーダルを開く
    onNotRegistered();
  });
}

// お釣りモーダルを開く
function openChangeModal(recordId) {
  const recordRow = document.getElementById(`record-${recordId}`);
  if (!recordRow) {
    alert('レコードが見つかりません');
    return;
  }
  
  const castSelect = recordRow.querySelector('.dashboard-cast-select');
  const timeInput = recordRow.querySelector('.dashboard-time-input');
  const staffSelect = recordRow.querySelector('.dashboard-staff-select');
  
  if (!castSelect || !timeInput || !staffSelect) {
    alert('必要な入力項目が見つかりません');
    return;
  }
  
  const castValue = castSelect.value;
  const castName = castSelect.selectedIndex > 0 ? castSelect.options[castSelect.selectedIndex].text : '';
  const exitTime = timeInput.value;
  const staffValue = staffSelect.value;
  const staffName = staffSelect.selectedIndex > 0 ? staffSelect.options[staffSelect.selectedIndex].text : '';
  
  // 登録済みかどうかをチェック
  checkIfAlreadyRegistered(recordId, castValue, exitTime, () => {
    // 未登録の場合のみモーダルを開く
    currentChangeRecord = {
      record_id: recordId,
      cast_id: castValue,
      cast_name: castName,
      exit_time: exitTime,
      staff_id: staffValue,
      staff_name: staffName
    };
    
    // キャスト名を表示
    const castNameElement = document.getElementById('changeCastName');
    if (castName) {
      castNameElement.textContent = castName;
      castNameElement.style.color = '#333';
    } else {
      castNameElement.textContent = 'キャストが選択されていません';
      castNameElement.style.color = '#ff6b6b';
    }
    
    document.getElementById('changeRecordId').value = recordId;
    document.getElementById('changeModal').style.display = 'block';
    document.getElementById('changeForm').reset();
    document.getElementById('changeRecordId').value = recordId;
  });
}

// お釣りモーダルを閉じる
function closeChangeModal() {
  document.getElementById('changeModal').style.display = 'none';
  currentChangeRecord = null;
}

// お釣り登録を送信
function submitChange(event) {
  event.preventDefault();
  
  if (!currentChangeRecord) {
    alert('レコード情報が取得できません');
    return;
  }
  
  const formData = {
    record_id: currentChangeRecord.record_id,
    cast_id: currentChangeRecord.cast_id,
    cast_name: currentChangeRecord.cast_name,
    exit_time: currentChangeRecord.exit_time,
    staff_id: currentChangeRecord.staff_id,
    staff_name: currentChangeRecord.staff_name,
    received_amount: document.getElementById('changeReceivedAmount').value,
    change_amount: document.getElementById('changeAmount').value,
    payment_method: document.getElementById('changePaymentMethod').value
  };
  
  fetch(window.dashboardUrls.store + '/register_change', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(formData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('お釣り登録が完了しました');
      closeChangeModal();
    } else {
      alert('登録中にエラーが発生しました: ' + (data.error || '不明なエラー'));
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('通信エラーが発生しました');
  });
}

// モーダル外クリックで閉じる
window.onclick = function(event) {
  const modal = document.getElementById('changeModal');
  if (event.target === modal) {
    closeChangeModal();
  }
}

// カレンダー関連の変数
let currentCalendarMonth = new Date().getMonth();
let currentCalendarYear = new Date().getFullYear();
let recordDates = []; // 予定のある日付リスト

// カレンダーモーダルを開く
function openCalendarModal() {
    const modal = document.getElementById('calendarModal');
    
    // 現在の日付からカレンダーの月を設定
    const currentDate = new Date(window.currentDate);
    currentCalendarMonth = currentDate.getMonth();
    currentCalendarYear = currentDate.getFullYear();
    
    // 予定のある日付を取得
    fetchRecordDates();
    
    // カレンダーを描画
    renderCalendar();
    
    // モーダルを表示
    modal.style.display = 'block';
}

// カレンダーモーダルを閉じる
function closeCalendarModal() {
    const modal = document.getElementById('calendarModal');
    modal.style.display = 'none';
}

// カレンダーの月を変更
function changeCalendarMonth(direction) {
    currentCalendarMonth += direction;
    
    if (currentCalendarMonth > 11) {
        currentCalendarMonth = 0;
        currentCalendarYear++;
    } else if (currentCalendarMonth < 0) {
        currentCalendarMonth = 11;
        currentCalendarYear--;
    }
    
    renderCalendar();
}

// カレンダーを描画
function renderCalendar() {
    const monthNames = [
        '1月', '2月', '3月', '4月', '5月', '6月',
        '7月', '8月', '9月', '10月', '11月', '12月'
    ];
    
    // ヘッダー更新
    const monthYearElement = document.getElementById('calendarMonthYear');
    monthYearElement.textContent = `${currentCalendarYear}年${monthNames[currentCalendarMonth]}`;
    
    // 日付グリッドを生成
    const daysContainer = document.getElementById('calendarDays');
    daysContainer.innerHTML = '';
    
    // 月の最初の日と最後の日
    const firstDay = new Date(currentCalendarYear, currentCalendarMonth, 1);
    const lastDay = new Date(currentCalendarYear, currentCalendarMonth + 1, 0);
    
    // 最初の日の曜日（0=日曜日）
    const firstDayOfWeek = firstDay.getDay();
    
    // 前月の日付を埋める
    const prevMonth = new Date(currentCalendarYear, currentCalendarMonth, 0);
    for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const day = prevMonth.getDate() - i;
        const dayElement = createCalendarDay(day, true, currentCalendarYear, currentCalendarMonth - 1);
        daysContainer.appendChild(dayElement);
    }
    
    // 今月の日付
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const dayElement = createCalendarDay(day, false, currentCalendarYear, currentCalendarMonth);
        daysContainer.appendChild(dayElement);
    }
    
    // 次月の日付を埋める（42マス - 前月 - 今月）
    const totalCells = 42;
    const usedCells = firstDayOfWeek + lastDay.getDate();
    const nextMonthDays = totalCells - usedCells;
    
    for (let day = 1; day <= nextMonthDays; day++) {
        const dayElement = createCalendarDay(day, true, currentCalendarYear, currentCalendarMonth + 1);
        daysContainer.appendChild(dayElement);
    }
}

// カレンダーの日付要素を作成（修正版）
function createCalendarDay(day, isOtherMonth, year, month) {
    const dayElement = document.createElement('div');
    dayElement.classList.add('calendar-day');
    dayElement.textContent = day;
    
    // 他の月の場合
    if (isOtherMonth) {
        dayElement.classList.add('other-month');
        return dayElement;
    }
    
    // 日付オブジェクトを作成
    const currentDate = new Date(year, month, day);
    const today = new Date();
    const selectedDate = new Date(window.currentDate);
    
    // 今日の日付
    if (currentDate.toDateString() === today.toDateString()) {
        dayElement.classList.add('today');
    }
    
    // 選択中の日付
    if (currentDate.toDateString() === selectedDate.toDateString()) {
        dayElement.classList.add('selected');
    }
    
    // 予定のある日付
    const dateString = formatDateForUrl(currentDate);
    if (recordDates.includes(dateString)) {
        dayElement.classList.add('has-records');
    }
    
    // クリックイベント（修正版）
    dayElement.addEventListener('click', function() {
        const dateString = formatDateForUrl(currentDate);
        closeCalendarModal();
        
        // 日付選択時にお知らせを保存してから移動
        selectCalendarDate(dateString);
    });
    
    return dayElement;
}

// 予定のある日付を取得
function fetchRecordDates() {
    const storeUrl = window.dashboardUrls.store;
    
    fetch(`${storeUrl}/dashboard/get_record_dates`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            year: currentCalendarYear,
            month: currentCalendarMonth + 1 // JavaScriptは0ベース、Pythonは1ベース
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            recordDates = data.dates;
            // カレンダーを再描画（予定マーク付きで）
            renderCalendar();
        }
    })
    .catch(error => {
        console.error('予定日付取得エラー:', error);
        recordDates = [];
    });
}

// 日付をYYYY-MM-DD形式でフォーマット
function formatDateForUrl(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// モーダル外クリックでカレンダーを閉じる
window.addEventListener('click', function(event) {
    const calendarModal = document.getElementById('calendarModal');
    if (event.target === calendarModal) {
        closeCalendarModal();
    }
});

// 既存のモーダル外クリック処理を拡張
const originalWindowClick = window.onclick;
window.onclick = function(event) {
    // 既存のお釣りモーダルの処理
    const changeModal = document.getElementById('changeModal');
    if (event.target === changeModal) {
        closeChangeModal();
    }
    
    // カレンダーモーダルの処理
    const calendarModal = document.getElementById('calendarModal');
    if (event.target === calendarModal) {
        closeCalendarModal();
    }
};

// お釣り未入力警告ダイアログ（赤いスタイル）
function showChangeNotEnteredDialog(message) {
  // ダイアログ作成
  const overlay = document.createElement('div');
  overlay.innerHTML = `
    <div style="
      position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
      background: rgba(0,0,0,0.5); display: flex; align-items: center; 
      justify-content: center; z-index: 10000;
    ">
      <div style="
        background: #ffe6e6; border: 3px solid #ff0000; border-radius: 8px; 
        padding: 20px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.3);
      ">
        <p style="color: #cc0000; font-weight: bold; font-size: 16px; margin-bottom: 20px;">
          ${message}
        </p>
        <button id="changeNotEnteredOk" style="
          background: #ff4444; color: white; border: none; padding: 10px 30px; 
          margin: 5px; border-radius: 4px; cursor: pointer; font-weight: bold;
        ">OK</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // イベント設定
  document.getElementById('changeNotEnteredOk').onclick = function() {
    document.body.removeChild(overlay);
  };
  
  // 背景クリックで閉じる
  overlay.onclick = function(e) {
    if (e.target === overlay) {
      document.body.removeChild(overlay);
    }
  };
}

// ページ読み込み後の初期化とイベントリスナー設定
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOMContentLoaded - イベントリスナー設定開始');
  console.log('Store URL:', window.dashboardUrls.store);
  
  // コース情報をロード
  loadCourseData();
  
  // お知らせの初期状態を設定
  const announcementArea = document.getElementById('announcementArea');
  if (announcementArea) {
    announcementVisible = announcementArea.style.display !== 'none';
  }
  
  // 時間入力フィールドのイベントリスナー
  document.querySelectorAll('input[type="time"]').forEach(input => {
    input.addEventListener('change', function() {
      const recordId = this.getAttribute('data-record-id');
      const field = this.getAttribute('data-field');
      console.log('時間変更:', recordId, field, this.value);
      recordChange(recordId, field, this.value);
      
      // 入室時間の変更時は退室時間も自動更新
      if (field === 'entry_time') {
        updateExitTimeOnEntryChange(recordId);
      }
    });
  });
  
  // キャスト選択フィールドのイベントリスナー
  document.querySelectorAll('select[data-field="cast_id"]').forEach(select => {
    select.addEventListener('change', function() {
      const recordId = this.getAttribute('data-record-id');
      console.log('キャスト変更:', recordId, this.value);
      recordChange(recordId, 'cast_id', this.value);
    });
  });
  
  // ホテル選択フィールドのイベントリスナー
  document.querySelectorAll('select[data-field="hotel_id"]').forEach(select => {
    select.addEventListener('change', function() {
      const recordId = this.getAttribute('data-record-id');
      console.log('ホテル変更:', recordId, this.value);
      recordChange(recordId, 'hotel_id', this.value);
      
      // ホテル連動機能
      syncHotelSelection(recordId);
    });
  });
  
  // その他内容フィールドのイベントリスナー
  document.querySelectorAll('input[data-field="content"]').forEach(input => {
    input.addEventListener('change', function() {
      const recordId = this.getAttribute('data-record-id');
      console.log('内容変更:', recordId, this.value);
      recordChange(recordId, 'content', this.value);
    });
  });
  
  // スタッフ選択フィールドのイベントリスナー（色変更は既存の関数で処理）
  document.querySelectorAll('select[data-field="staff_id"]').forEach(select => {
    select.addEventListener('change', function() {
      const recordId = this.getAttribute('data-record-id');
      console.log('スタッフ変更:', recordId, this.value);
      recordChange(recordId, 'staff_id', this.value);
    });
  });
  
  // お知らせテキストエリアのイベントリスナー
  const announcementTextarea = document.getElementById('announcementContent');
  if (announcementTextarea) {
    // 初期値を保存
    announcementTextarea.defaultValue = announcementTextarea.value;
    
    // 入力変更を検知
    announcementTextarea.addEventListener('input', function() {
      // リアルタイム更新はしない（保存ボタンで一括保存）
    });
  }
  
  console.log('イベントリスナー設定完了');
});

// コース情報をキャッシュ（ページ読み込み時に取得）
let courseCache = {};

// コース情報を取得してキャッシュに保存
function loadCourseData() {
  const storeUrl = window.dashboardUrls.store;
  
  fetch(`${storeUrl}/dashboard/get_course_data`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        data.courses.forEach(course => {
          courseCache[course.course_id] = course.time;
        });
        console.log('コース情報をロードしました:', courseCache);
      }
    })
    .catch(error => {
      console.error('コース情報の取得に失敗:', error);
    });
}

// 時間文字列（HH:MM）に分数を加算する関数
function addMinutesToTime(timeStr, minutes) {
  const [hours, mins] = timeStr.split(':').map(Number);
  const totalMinutes = hours * 60 + mins + minutes;
  
  const newHours = Math.floor(totalMinutes / 60) % 24;
  const newMins = totalMinutes % 60;
  
  return `${String(newHours).padStart(2, '0')}:${String(newMins).padStart(2, '0')}`;
}

// 関連レコード（入室・退室のペア）を見つける関数（修正版）
function findRelatedRecord(recordId, castId, isEntry) {
  const allRows = document.querySelectorAll('.dashboard-record-row');
  const currentRow = document.getElementById(`record-${recordId}`);
  const currentTimeInput = currentRow.querySelector('.dashboard-time-input');
  const currentTime = currentTimeInput ? currentTimeInput.value : null;
  
  if (!currentTime) return null;
  
  let bestMatch = null;
  let minTimeDiff = Infinity;
  
  for (let row of allRows) {
    const rowRecordId = row.id.replace('record-', '');
    if (rowRecordId === recordId) continue;
    
    const rowCastSelect = row.querySelector('.dashboard-cast-select');
    const rowBadge = row.querySelector('.dashboard-badge');
    const rowTimeInput = row.querySelector('.dashboard-time-input');
    
    if (rowCastSelect && rowBadge && rowTimeInput) {
      const rowCastId = rowCastSelect.value;
      const rowIsEntry = rowBadge.textContent.trim() === '入';
      const rowTime = rowTimeInput.value;
      
      // 同じキャストで、入室・退室が逆のレコード
      if (rowCastId === castId && rowIsEntry !== isEntry && rowTime) {
        // 時間差を計算
        const currentMinutes = timeToMinutes(currentTime);
        const rowMinutes = timeToMinutes(rowTime);
        const timeDiff = Math.abs(rowMinutes - currentMinutes);
        
        // 入室の場合は未来の退室、退室の場合は過去の入室を探す
        if ((isEntry && rowMinutes > currentMinutes) || (!isEntry && rowMinutes < currentMinutes)) {
          if (timeDiff < minTimeDiff) {
            minTimeDiff = timeDiff;
            bestMatch = {
              recordId: rowRecordId,
              row: row
            };
          }
        }
      }
    }
  }
  
  return bestMatch;
}

// 時間（HH:MM）を分に変換する補助関数
function timeToMinutes(timeStr) {
  const [hours, mins] = timeStr.split(':').map(Number);
  return hours * 60 + mins;
}

// 入室時間変更時の退室時間自動計算
function updateExitTimeOnEntryChange(recordId) {
  const row = document.getElementById(`record-${recordId}`);
  if (!row) return;
  
  const castSelect = row.querySelector('.dashboard-cast-select');
  const timeInput = row.querySelector('.dashboard-time-input');
  const badge = row.querySelector('.dashboard-badge');
  
  if (!castSelect || !timeInput || !badge) return;
  
  const isEntry = badge.textContent.trim() === '入';
  if (!isEntry) return; // 入室レコードでない場合は何もしない
  
  const castId = castSelect.value;
  const entryTime = timeInput.value;
  
  if (!castId || !entryTime) return;
  
  // 関連する退室レコードを探す
  const relatedRecord = findRelatedRecord(recordId, castId, isEntry);
  if (!relatedRecord) {
    console.log('関連する退室レコードが見つかりません');
    return;
  }
  
  // コース情報を取得（data-course-id属性から）
  const courseId = row.getAttribute('data-course-id');
  console.log('コースID:', courseId, 'courseCache:', courseCache);
  
  if (!courseId || !courseCache[courseId]) {
    console.log('コース情報が見つかりません。courseId:', courseId);
    return;
  }
  
  const courseTime = courseCache[courseId];
  const exitTime = addMinutesToTime(entryTime, courseTime);
  
  // 関連する退室レコードの時間を更新
  const exitRow = relatedRecord.row;
  const exitTimeInput = exitRow.querySelector('.dashboard-time-input');
  
  if (exitTimeInput) {
    exitTimeInput.value = exitTime;
    
    // 変更を記録
    recordChange(relatedRecord.recordId, 'exit_time', exitTime);
    
    console.log(`退室時間を自動更新: ${entryTime} + ${courseTime}分 = ${exitTime}`);
  }
}

// ホテル連動機能
function syncHotelSelection(recordId) {
  const row = document.getElementById(`record-${recordId}`);
  if (!row) return;
  
  const castSelect = row.querySelector('.dashboard-cast-select');
  const hotelSelect = row.querySelector('.dashboard-hotel-select');
  const badge = row.querySelector('.dashboard-badge');
  
  if (!castSelect || !hotelSelect || !badge) return;
  
  const castId = castSelect.value;
  const hotelId = hotelSelect.value;
  const isEntry = badge.textContent.trim() === '入';
  
  if (!castId) return;
  
  // 関連する入室・退室レコードを探す
  const relatedRecord = findRelatedRecord(recordId, castId, isEntry);
  if (!relatedRecord) return;
  
  // 関連レコードのホテルを同期
  const relatedRow = relatedRecord.row;
  const relatedHotelSelect = relatedRow.querySelector('.dashboard-hotel-select');
  
  if (relatedHotelSelect && relatedHotelSelect.value !== hotelId) {
    relatedHotelSelect.value = hotelId;
    
    // 変更を記録
    recordChange(relatedRecord.recordId, 'hotel_id', hotelId);
    
    console.log(`ホテル連動: レコード${relatedRecord.recordId}のホテルを${hotelId}に更新`);
  }
}