/**
 * 出勤管理システム - JavaScript
 */

// モーダルを開く
function openScheduleModal(cell) {
    const castId = cell.dataset.castId;
    const castName = cell.dataset.castName;
    const workDate = cell.dataset.workDate;
    
    // モーダルに情報を設定
    document.getElementById('modalCastId').value = castId;
    document.getElementById('modalCastName').textContent = castName;
    document.getElementById('modalWorkDate').textContent = formatDate(workDate);
    document.getElementById('modalWorkDateRaw').value = workDate;
    
    // 既存のスケジュール情報を取得
    fetchSchedule(castId, workDate);
    
    // モーダルを表示
    document.getElementById('scheduleModal').style.display = 'flex';
  }
  
  // モーダルを閉じる
  function closeScheduleModal() {
    document.getElementById('scheduleModal').style.display = 'none';
    resetForm();
  }
  
  // フォームをリセット
  function resetForm() {
    document.getElementById('modalStartTime').value = '';
    document.getElementById('modalEndTime').value = '';
    document.getElementById('modalIsOff').checked = false;
    document.getElementById('modalStartTime').disabled = false;
    document.getElementById('modalEndTime').disabled = false;
  }
  
  // 既存のスケジュール情報を取得
  function fetchSchedule(castId, workDate) {
    const store = getStoreFromUrl();
    
    fetch(`/${store}/schedule/get?cast_id=${castId}&work_date=${workDate}`)
      .then(response => response.json())
      .then(data => {
        if (data.success && data.schedule) {
          const schedule = data.schedule;
          
          if (schedule.status === 'off') {
            // 休みの場合
            document.getElementById('modalIsOff').checked = true;
            document.getElementById('modalStartTime').disabled = true;
            document.getElementById('modalEndTime').disabled = true;
          } else if (schedule.status === 'confirmed') {
            // 出勤の場合
            document.getElementById('modalStartTime').value = schedule.start_time;
            document.getElementById('modalEndTime').value = schedule.end_time;
          }
          
          // 削除ボタンを表示
          document.getElementById('deleteBtn').style.display = 'block';
        } else {
          // 新規登録の場合は削除ボタンを非表示
          document.getElementById('deleteBtn').style.display = 'none';
        }
      })
      .catch(error => {
        console.error('Error fetching schedule:', error);
        alert('スケジュール情報の取得に失敗しました');
      });
  }
  
  // 休みモードの切り替え
  function toggleOffMode() {
    const isOff = document.getElementById('modalIsOff').checked;
    const startTimeSelect = document.getElementById('modalStartTime');
    const endTimeSelect = document.getElementById('modalEndTime');
    
    if (isOff) {
      // 休みの場合は時間選択を無効化
      startTimeSelect.disabled = true;
      endTimeSelect.disabled = true;
      startTimeSelect.value = '';
      endTimeSelect.value = '';
    } else {
      // 出勤の場合は時間選択を有効化
      startTimeSelect.disabled = false;
      endTimeSelect.disabled = false;
    }
  }
  
  // スケジュールを保存
  function saveSchedule() {
    const store = getStoreFromUrl();
    const castId = document.getElementById('modalCastId').value;
    const workDate = document.getElementById('modalWorkDateRaw').value;
    const startTime = document.getElementById('modalStartTime').value;
    const endTime = document.getElementById('modalEndTime').value;
    const isOff = document.getElementById('modalIsOff').checked;
    
    // バリデーション
    if (!isOff && (!startTime || !endTime)) {
      alert('開始時刻と終了時刻を選択してください');
      return;
    }
    
    if (!isOff && startTime >= endTime) {
      // 翌日にまたがる場合は許可
      if (!(startTime > endTime && endTime < '06:00')) {
        alert('終了時刻は開始時刻より後にしてください');
        return;
      }
    }
    
    // データ送信
    const data = {
      cast_id: parseInt(castId),
      work_date: workDate,
      start_time: isOff ? null : startTime,
      end_time: isOff ? null : endTime,
      is_off: isOff
    };
    
    fetch(`/${store}/schedule/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          closeScheduleModal();
          // ページをリロード
          location.reload();
        } else {
          alert('保存に失敗しました: ' + (data.error || '不明なエラー'));
        }
      })
      .catch(error => {
        console.error('Error saving schedule:', error);
        alert('保存に失敗しました');
      });
  }
  
  // スケジュールを削除
  function deleteSchedule() {
    if (!confirm('出勤情報を削除してもよろしいですか？')) {
      return;
    }
    
    const store = getStoreFromUrl();
    const castId = document.getElementById('modalCastId').value;
    const workDate = document.getElementById('modalWorkDateRaw').value;
    
    const data = {
      cast_id: parseInt(castId),
      work_date: workDate
    };
    
    fetch(`/${store}/schedule/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          closeScheduleModal();
          // ページをリロード
          location.reload();
        } else {
          alert('削除に失敗しました: ' + (data.error || '不明なエラー'));
        }
      })
      .catch(error => {
        console.error('Error deleting schedule:', error);
        alert('削除に失敗しました');
      });
  }
  
  // URLから店舗コードを取得
  function getStoreFromUrl() {
    const path = window.location.pathname;
    const match = path.match(/^\/([^\/]+)/);
    return match ? match[1] : 'nagano';
  }
  
  // 日付をフォーマット
  function formatDate(dateStr) {
    const date = new Date(dateStr);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
    const weekday = weekdays[date.getDay()];
    
    return `${month}/${day} (${weekday})`;
  }
  
  // モーダル外クリックで閉じる
  document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('scheduleModal');
    if (modal) {
      modal.addEventListener('click', function(e) {
        if (e.target === modal) {
          closeScheduleModal();
        }
      });
    }
    
    // ESCキーでモーダルを閉じる
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        const modal = document.getElementById('scheduleModal');
        if (modal && modal.style.display === 'flex') {
          closeScheduleModal();
        }
      }
    });
  });