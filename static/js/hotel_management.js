// ホテル管理用JavaScript - 完全版

// ==== 共通のユーティリティ関数 ====
function toggleEditMode(type, id, isEditing) {
  const nameElement = document.getElementById(`${type}-name-${id}`);
  const editElement = document.getElementById(`${type}-edit-${id}`);
  const editButton = document.querySelector(`[onclick="edit${type.charAt(0).toUpperCase() + type.slice(1)}(${id})"]`);
  const saveButton = document.querySelector(`[onclick="save${type.charAt(0).toUpperCase() + type.slice(1)}(${id})"]`);
  const cancelButton = document.querySelector(`[onclick="cancelEdit${type.charAt(0).toUpperCase() + type.slice(1)}(${id})"]`);

  if (isEditing) {
      if (nameElement) nameElement.classList.add('hidden');
      if (editElement) editElement.classList.remove('hidden');
      if (editButton) editButton.classList.add('hidden');
      if (saveButton) saveButton.classList.remove('hidden');
      if (cancelButton) cancelButton.classList.remove('hidden');
  } else {
      if (nameElement) nameElement.classList.remove('hidden');
      if (editElement) editElement.classList.add('hidden');
      if (editButton) editButton.classList.remove('hidden');
      if (saveButton) saveButton.classList.add('hidden');
      if (cancelButton) cancelButton.classList.add('hidden');
  }
}

// ==== カテゴリ（ホテル種別）管理 ====
function editCategory(id) {
  console.log(`カテゴリ編集開始: ID=${id}`);
  toggleEditMode('category', id, true);
}

function cancelEditCategory(id) {
  console.log(`カテゴリ編集キャンセル: ID=${id}`);
  toggleEditMode('category', id, false);
}

function saveCategory(id) {
  console.log(`カテゴリ保存開始: ID=${id}`);
  const newName = document.getElementById(`category-edit-${id}`).value.trim();
  if (!newName) {
      alert('ホテル種別名を入力してください。');
      return;
  }
  
  console.log(`新しいカテゴリ名: "${newName}"`);
  
  // 隠しフォームのinput要素に値を設定
  const hiddenInput = document.getElementById(`category-name-input-${id}`);
  if (hiddenInput) {
      hiddenInput.value = newName;
      console.log(`隠しフィールドに値設定完了`);
  } else {
      console.error(`隠しフィールドが見つかりません: category-name-input-${id}`);
      return;
  }
  
  // フォームを送信
  const form = document.getElementById(`category-form-${id}`);
  if (form) {
      console.log(`フォーム送信開始`);
      form.submit();
  } else {
      console.error(`フォームが見つかりません: category-form-${id}`);
  }
}

// ==== エリア管理（交通費・所要時間対応完全版） ====
function editArea(id) {
  console.log(`エリア編集開始: ID=${id}`);
  
  // 表示要素を取得
  const nameElement = document.getElementById(`area-name-${id}`);
  const feeDisplayElement = document.getElementById(`area-fee-display-${id}`);
  const editFieldsElement = document.getElementById(`area-edit-fields-${id}`);
  const editButton = document.getElementById(`area-edit-btn-${id}`);
  const saveButton = document.getElementById(`area-save-btn-${id}`);
  const cancelButton = document.getElementById(`area-cancel-btn-${id}`);

  // 要素の存在確認
  if (!nameElement || !feeDisplayElement || !editFieldsElement || !editButton || !saveButton || !cancelButton) {
      console.error('エリア編集: 必要な要素が見つかりません', {
          nameElement: !!nameElement,
          feeDisplayElement: !!feeDisplayElement,
          editFieldsElement: !!editFieldsElement,
          editButton: !!editButton,
          saveButton: !!saveButton,
          cancelButton: !!cancelButton
      });
      return;
  }

  // 編集モードに切り替え
  nameElement.classList.add('hidden');
  feeDisplayElement.classList.add('hidden');
  editFieldsElement.classList.remove('hidden');
  editButton.classList.add('hidden');
  saveButton.classList.remove('hidden');
  cancelButton.classList.remove('hidden');
  
  console.log(`エリア編集モード切り替え完了: ID=${id}`);
}

function cancelEditArea(id) {
  console.log(`エリア編集キャンセル: ID=${id}`);
  
  // 表示要素を取得
  const nameElement = document.getElementById(`area-name-${id}`);
  const feeDisplayElement = document.getElementById(`area-fee-display-${id}`);
  const editFieldsElement = document.getElementById(`area-edit-fields-${id}`);
  const editButton = document.getElementById(`area-edit-btn-${id}`);
  const saveButton = document.getElementById(`area-save-btn-${id}`);
  const cancelButton = document.getElementById(`area-cancel-btn-${id}`);

  if (nameElement && feeDisplayElement && editFieldsElement && editButton && saveButton && cancelButton) {
      // 表示モードに戻す
      nameElement.classList.remove('hidden');
      feeDisplayElement.classList.remove('hidden');
      editFieldsElement.classList.add('hidden');
      editButton.classList.remove('hidden');
      saveButton.classList.add('hidden');
      cancelButton.classList.add('hidden');
      
      console.log(`エリア編集キャンセル完了: ID=${id}`);
  } else {
      console.error(`エリア編集キャンセル: 要素が見つかりません ID=${id}`);
  }
}

function saveArea(id) {
  console.log(`エリア保存開始: ID=${id}`);
  
  // 入力値を取得
  const newName = document.getElementById(`area-edit-name-${id}`).value.trim();
  const newFee = document.getElementById(`area-edit-fee-${id}`).value;
  const newTime = document.getElementById(`area-edit-time-${id}`).value;
  
  console.log(`入力値確認:`, {
      name: newName,
      fee: newFee,
      time: newTime
  });
  
  // バリデーション
  if (!newName) {
      alert('エリア名を入力してください。');
      return;
  }
  
  // 数値バリデーション
  const feeValue = parseInt(newFee) || 0;
  const timeValue = parseInt(newTime) || 0;
  
  if (feeValue < 0) {
      alert('交通費は0以上で入力してください。');
      return;
  }
  
  if (timeValue < 0) {
      alert('所要時間は0以上で入力してください。');
      return;
  }
  
  console.log(`バリデーション通過: fee=${feeValue}, time=${timeValue}`);
  
  // 隠しフォームのinput要素に値を設定
  const nameInput = document.getElementById(`area-name-input-${id}`);
  const feeInput = document.getElementById(`area-fee-input-${id}`);
  const timeInput = document.getElementById(`area-time-input-${id}`);
  
  if (!nameInput || !feeInput || !timeInput) {
      console.error('エリア保存: 隠しフィールドが見つかりません', {
          nameInput: !!nameInput,
          feeInput: !!feeInput,
          timeInput: !!timeInput
      });
      alert('フォーム送信エラーが発生しました。');
      return;
  }
  
  nameInput.value = newName;
  feeInput.value = feeValue;
  timeInput.value = timeValue;
  
  console.log(`隠しフィールド設定完了`);
  
  // フォームを送信
  const form = document.getElementById(`area-form-${id}`);
  if (form) {
      console.log(`エリアフォーム送信開始`);
      form.submit();
  } else {
      console.error(`エリアフォームが見つかりません: area-form-${id}`);
      alert('フォーム送信エラーが発生しました。');
  }
}

// ==== モーダル制御 ====
function openModal(modalId) {
  console.log(`モーダル開く: ${modalId}`);
  const modal = document.getElementById(modalId);
  if (modal) {
      modal.classList.add('show');
  } else {
      console.error(`モーダルが見つかりません: ${modalId}`);
  }
}

function closeModal(modalId) {
  console.log(`モーダル閉じる: ${modalId}`);
  const modal = document.getElementById(modalId);
  if (modal) {
      modal.classList.remove('show');
  } else {
      console.error(`モーダルが見つかりません: ${modalId}`);
  }
}

// ==== DOM読み込み完了後の初期化 ====
document.addEventListener('DOMContentLoaded', function() {
  console.log('ホテル管理JS初期化開始');
  
  // すべてのモーダルに対してクリックイベントを設定
  const modals = document.querySelectorAll('.modal');
  console.log(`モーダル数: ${modals.length}`);
  
  modals.forEach(function(modal, index) {
      modal.addEventListener('click', function(event) {
          if (event.target === modal) {
              console.log(`モーダル外側クリック: ${modal.id}`);
              modal.classList.remove('show');
          }
      });
      console.log(`モーダル${index + 1}にイベント設定完了: ${modal.id}`);
  });
  
  // 並び順ボタンのクリック追跡（デバッグ用）
  const sortButtons = document.querySelectorAll('a[href*="move_hotel"]');
  console.log(`並び順ボタン数: ${sortButtons.length}`);
  
  sortButtons.forEach(function(button, index) {
      button.addEventListener('click', function(event) {
          const href = button.getAttribute('href');
          const direction = href.includes('move_hotel_up') ? '上' : '下';
          const hotelId = href.split('/').pop();
          console.log(`並び順ボタンクリック: ホテルID=${hotelId}, 方向=${direction}`);
      });
  });
  
  console.log('ホテル管理JS初期化完了');
});

// ==== エラーハンドリング ====
window.addEventListener('error', function(event) {
  console.error('JavaScript エラー:', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error
  });
});

// ==== デバッグ用ヘルパー関数 ====
function debugHotelManagement() {
  console.log('=== ホテル管理デバッグ情報 ===');
  
  // モーダルの状態
  const modals = document.querySelectorAll('.modal');
  console.log('モーダル状態:');
  modals.forEach(modal => {
      console.log(`  ${modal.id}: ${modal.classList.contains('show') ? '開' : '閉'}`);
  });
  
  // 隠し要素の状態
  const hiddenElements = document.querySelectorAll('.hidden');
  console.log(`隠し要素数: ${hiddenElements.length}`);
  
  // フォームの状態
  const forms = document.querySelectorAll('form');
  console.log(`フォーム数: ${forms.length}`);
  forms.forEach((form, index) => {
      console.log(`  フォーム${index + 1}: action="${form.action}", method="${form.method}"`);
  });
  
  console.log('=== デバッグ情報終了 ===');
}

// デバッグ関数をグローバルに公開
window.debugHotelManagement = debugHotelManagement;