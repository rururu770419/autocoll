/**
 * 予約編集ページのJavaScript
 */

// 現在の顧客PT（初期値）
let currentCustomerPT = 0;

// マスタデータ保存用グローバル変数
let castsData = [];
let coursesData = [];
let nominationsData = [];
let extensionsData = [];
let optionsData = [];
let discountsData = [];
let hotelsData = [];

// カード手数料率（デフォルト5%）
let cardFeeRate = 5;

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOMContentLoaded 開始 ===');
    console.log('予約データ:', window.reservationData);

    loadMasterData();
    loadCardFeeRate();
    initializeCustomSelect();
    initializeDateTimeSelects();
    // 既存データをロード（マスタデータ読み込み後、十分な時間を確保）
    setTimeout(() => {
        console.log('=== loadExistingReservationData 実行 ===');
        loadExistingReservationData();
    }, 1500);
});

// カスタムセレクトボックスの初期化
function initializeCustomSelect() {
    // オプションのカスタムセレクト
    const optionsSelectDisplay = document.getElementById('options_select_display');
    const optionsDropdown = document.getElementById('options_container');

    if (optionsSelectDisplay && optionsDropdown) {
        optionsSelectDisplay.addEventListener('click', function(e) {
            e.stopPropagation();
            optionsDropdown.classList.toggle('collapsed');
            const arrow = this.querySelector('.select-arrow');
            arrow.textContent = optionsDropdown.classList.contains('collapsed') ? '▼' : '▲';
        });

        optionsDropdown.addEventListener('change', function(e) {
            if (e.target.type === 'checkbox') {
                updateSelectDisplay();
                calculateTotal();
            }
        });
    }

    // 割引のカスタムセレクト
    const discountSelectDisplay = document.getElementById('discount_select_display');
    const discountDropdown = document.getElementById('discount_container');

    if (discountSelectDisplay && discountDropdown) {
        discountSelectDisplay.addEventListener('click', function(e) {
            e.stopPropagation();
            discountDropdown.classList.toggle('collapsed');
            const arrow = this.querySelector('.select-arrow');
            arrow.textContent = discountDropdown.classList.contains('collapsed') ? '▼' : '▲';
        });

        discountDropdown.addEventListener('change', function(e) {
            if (e.target.type === 'checkbox') {
                updateDiscountDisplay();
                calculateTotal();
            }
        });
    }

    // 外側をクリックしたら全て閉じる
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.custom-select-wrapper')) {
            if (optionsDropdown) {
                optionsDropdown.classList.add('collapsed');
                const arrow = optionsSelectDisplay?.querySelector('.select-arrow');
                if (arrow) arrow.textContent = '▼';
            }
            if (discountDropdown) {
                discountDropdown.classList.add('collapsed');
                const arrow = discountSelectDisplay?.querySelector('.select-arrow');
                if (arrow) arrow.textContent = '▼';
            }
        }
    });
}

// セレクトボックスの表示を更新
function updateSelectDisplay() {
    const checkedBoxes = document.querySelectorAll('.options-dropdown input[type="checkbox"]:checked');
    const displayText = document.querySelector('.select-placeholder');

    if (!displayText) return;

    if (checkedBoxes.length === 0) {
        displayText.textContent = 'オプションを選択してください';
    } else if (checkedBoxes.length === 1) {
        const optionName = checkedBoxes[0].parentElement.querySelector('.option-name');
        if (optionName) {
            displayText.textContent = optionName.textContent;
        }
    } else {
        displayText.textContent = `${checkedBoxes.length}件選択中`;
    }
}

// マスタデータの読み込み
function loadMasterData() {
    const store = getStoreFromUrl();

    // キャスト一覧
    fetch(`/${store}/casts/api`)
        .then(response => response.json())
        .then(data => {
            castsData = data;
            populateSelect('cast_id', data, 'cast_id', 'name');
            // キャスト選択時のイベントリスナーを追加
            document.getElementById('cast_id').addEventListener('change', updateCourseColors);
        })
        .catch(error => console.error('Error loading casts:', error));

    // コース一覧
    fetch(`/${store}/courses/api`)
        .then(response => response.json())
        .then(data => {
            coursesData = data;
            populateSelect('course_id', data, 'course_id', 'course_name');
        })
        .catch(error => console.error('Error loading courses:', error));

    // 指名種類
    fetch(`/${store}/nomination-types/api`)
        .then(response => response.json())
        .then(data => {
            nominationsData = data;
            populateSelect('nomination_type', data, 'nomination_type_id', 'type_name');
        })
        .catch(error => console.error('Error loading nomination types:', error));

    // 延長
    fetch(`/${store}/extensions/api`)
        .then(response => response.json())
        .then(data => {
            extensionsData = data;
            populateSelect('extension', data, 'extension_id', 'extension_name');
        })
        .catch(error => console.error('Error loading extensions:', error));

    // オプション（チェックボックス）
    fetch(`/${store}/options/api`)
        .then(response => response.json())
        .then(data => {
            console.log('オプションデータ取得成功:', data);
            console.log('オプション件数:', data.length);
            optionsData = data;
            populateOptionsCheckboxes(data);
        })
        .catch(error => console.error('Error loading options:', error));

    // 割引
    fetch(`/${store}/discount_management/api/list`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.discounts) {
                discountsData = data.discounts;
                populateDiscountsCheckboxes(data.discounts);
            }
        })
        .catch(error => console.error('Error loading discounts:', error));

    // キャンセル理由
    fetch(`/${store}/reservation-settings/cancellation_reasons`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                populateSelect('cancellation_reason', data.data, 'reason_id', 'reason_name');
            }
        })
        .catch(error => console.error('Error loading cancellation reasons:', error));

    // 予約方法
    fetch(`/${store}/settings/reservation_methods`)
        .then(response => response.json())
        .then(data => populateSelect('reservation_method', data, 'method_id', 'method_name'))
        .catch(error => console.error('Error loading reservation methods:', error));

    // 支払い方法（固定値）
    const paymentMethods = [
        { method_id: 'cash', method_name: '現金' },
        { method_id: 'card', method_name: 'カード' }
    ];
    populateSelect('payment_method', paymentMethods, 'method_id', 'method_name');

    // 待ち合わせ場所
    fetch(`/${store}/reservation-settings/meeting_places`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                populateSelect('meeting_place', data.data, 'place_id', 'place_name');
            }
        })
        .catch(error => console.error('Error loading meeting places:', error));

    // ホテル
    fetch(`/${store}/hotel-management/hotels`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                hotelsData = data.data;
                populateSelect('hotel_id', data.data, 'hotel_id', 'hotel_name');
                // ホテル選択時に交通費を自動設定
                document.getElementById('hotel_id').addEventListener('change', updateTransportationFeeFromHotel);
            }
        })
        .catch(error => console.error('Error loading hotels:', error));

    // 交通費（エリア）
    fetch(`/${store}/hotel-management/areas`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                const select = document.getElementById('transportation_fee');
                data.data.forEach(area => {
                    const option = document.createElement('option');
                    option.value = area.transportation_fee;
                    option.textContent = `${area.area_name} - ¥${area.transportation_fee.toLocaleString()}`;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading areas:', error));

    // スタッフ一覧
    fetch(`/${store}/staff/api`)
        .then(response => response.json())
        .then(data => {
            populateSelect('staff_id', data, 'id', 'name');

            // ログイン中のスタッフを自動選択
            if (window.currentStaffId) {
                const staffSelect = document.getElementById('staff_id');
                staffSelect.value = window.currentStaffId;
            }
        })
        .catch(error => console.error('Error loading staff:', error));
}

// カード手数料率の読み込み
function loadCardFeeRate() {
    const store = getStoreFromUrl();
    fetch(`/${store}/reservation-settings/card_fee_rate`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cardFeeRate = Math.floor(data.rate) || 5;
            }
        })
        .catch(error => console.error('Error loading card fee rate:', error));
}

// ログイン中のスタッフを取得してデフォルト選択
// ※ この関数は使用されていません（window.currentStaffIdを使用）
function loadCurrentStaff() {
    // HTMLテンプレートから渡されたwindow.currentStaffIdを使用するため、
    // この関数は呼び出されません
}

// SELECTに選択肢を追加
function populateSelect(selectId, data, valueKey, textKey) {
    const select = document.getElementById(selectId);
    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item[valueKey];
        option.textContent = item[textKey];
        select.appendChild(option);
    });
}

// 複数選択SELECTに選択肢を追加
function populateMultiSelect(selectId, data, valueKey, textKey) {
    const select = document.getElementById(selectId);
    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item[valueKey];
        option.textContent = item[textKey];
        select.appendChild(option);
    });
}

// オプションをチェックボックスで表示
function populateOptionsCheckboxes(data) {
    console.log('populateOptionsCheckboxes 呼び出し:', data);
    const container = document.getElementById('options_container');
    console.log('コンテナ要素:', container);

    container.innerHTML = ''; // クリア

    data.forEach(option => {
        console.log('オプション追加:', option);

        const label = document.createElement('label');
        label.className = 'option-item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'options[]';
        checkbox.value = option.option_id;
        checkbox.className = 'option-checkbox';
        // onchangeイベントは親要素のイベントリスナーで処理

        const nameSpan = document.createElement('span');
        nameSpan.className = 'option-name';
        nameSpan.textContent = option.option_name;

        const priceSpan = document.createElement('span');
        priceSpan.className = 'option-price';
        priceSpan.textContent = '¥' + (option.price || 0).toLocaleString();

        label.appendChild(checkbox);
        label.appendChild(nameSpan);
        label.appendChild(priceSpan);
        container.appendChild(label);
    });

    console.log('オプション追加完了。コンテナの子要素数:', container.children.length);
    console.log('コンテナのHTML:', container.innerHTML.substring(0, 200));
}

// 割引をチェックボックスで表示
function populateDiscountsCheckboxes(data) {
    const container = document.getElementById('discount_container');
    if (!container) return;

    container.innerHTML = ''; // クリア

    data.forEach(discount => {
        const label = document.createElement('label');
        label.className = 'option-item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'discounts[]';
        checkbox.value = discount.discount_id;
        checkbox.className = 'option-checkbox';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'option-name';
        nameSpan.textContent = discount.name;

        const priceSpan = document.createElement('span');
        priceSpan.className = 'option-price discount-price';
        if (discount.discount_type === 'percentage') {
            priceSpan.textContent = discount.value + '%';
        } else {
            priceSpan.textContent = '¥' + Math.floor(discount.value || 0).toLocaleString();
        }

        label.appendChild(checkbox);
        label.appendChild(nameSpan);
        label.appendChild(priceSpan);
        container.appendChild(label);
    });
}

// 割引選択表示を更新
function updateDiscountDisplay() {
    const checkboxes = document.querySelectorAll('#discount_container .option-checkbox:checked');
    const placeholder = document.querySelector('#discount_select_display .select-placeholder');

    if (!placeholder) return;

    if (checkboxes.length === 0) {
        placeholder.textContent = '割引を選択してください';
    } else if (checkboxes.length === 1) {
        const discount = discountsData.find(d => d.discount_id == checkboxes[0].value);
        placeholder.textContent = discount ? discount.name : '1件選択中';
    } else {
        placeholder.textContent = `${checkboxes.length}件選択中`;
    }
}

// 成約種別の切り替え
function toggleCancellation() {
    const contractType = document.getElementById('contract_type').value;
    const cancellationSelect = document.getElementById('cancellation_reason');

    if (contractType === 'cancel') {
        cancellationSelect.disabled = false;
    } else {
        cancellationSelect.disabled = true;
        cancellationSelect.value = '';
    }
}

// キャスト選択時にコースの背景色を更新
function updateCourseColors() {
    const castSelect = document.getElementById('cast_id');
    const courseSelect = document.getElementById('course_id');

    if (!castSelect.value || !courseSelect) {
        return;
    }

    // 選択されたキャストのデータを取得
    const selectedCastId = parseInt(castSelect.value);
    const selectedCast = castsData.find(c => c.cast_id === selectedCastId);

    if (!selectedCast || !selectedCast.course_category_id) {
        // キャストのカテゴリが設定されていない場合は全てデフォルト色
        Array.from(courseSelect.options).forEach(option => {
            if (option.value) {
                option.style.backgroundColor = '';
                option.style.color = '';
            }
        });
        return;
    }

    const castCategoryId = selectedCast.course_category_id;

    // 各コースオプションの背景色を設定
    Array.from(courseSelect.options).forEach(option => {
        if (option.value) {
            const courseId = parseInt(option.value);
            const course = coursesData.find(c => c.course_id === courseId);

            if (course && course.category_id !== castCategoryId) {
                // カテゴリが一致しない場合は赤背景
                option.style.backgroundColor = '#ffcccc';
                option.style.color = '#000';
            } else {
                // カテゴリが一致する場合は通常色
                option.style.backgroundColor = '';
                option.style.color = '';
            }
        }
    });
}

// ホテル選択時に交通費を自動設定
function updateTransportationFeeFromHotel() {
    const hotelSelect = document.getElementById('hotel_id');
    const transportationFeeSelect = document.getElementById('transportation_fee');

    if (!hotelSelect.value) {
        // ホテルが選択されていない場合は交通費を0に設定
        transportationFeeSelect.value = '0';
        calculateTotal();
        return;
    }

    // 選択されたホテルのデータを取得
    const selectedHotelId = parseInt(hotelSelect.value);
    const selectedHotel = hotelsData.find(h => h.hotel_id === selectedHotelId);

    if (!selectedHotel) {
        transportationFeeSelect.value = '0';
        calculateTotal();
        return;
    }

    // ホテルの交通費を取得して設定
    const transportationFee = selectedHotel.transportation_fee || 0;
    transportationFeeSelect.value = transportationFee.toString();

    // 料金を再計算
    calculateTotal();
}

// 料金総額の自動計算
function calculateTotal() {
    let total = 0;

    // コース料金
    const courseSelect = document.getElementById('course_id');
    if (courseSelect.selectedIndex > 0) {
        const courseId = courseSelect.value;
        const course = coursesData.find(c => c.course_id == courseId);
        if (course && course.price) {
            total += course.price;
        }
    }

    // 指名料
    const nominationSelect = document.getElementById('nomination_type');
    if (nominationSelect.selectedIndex > 0) {
        const nominationId = nominationSelect.value;
        const nomination = nominationsData.find(n => n.nomination_type_id == nominationId);
        if (nomination && nomination.fee) {
            total += nomination.fee;
        }
    }

    // オプション料金の合計（チェックボックス）
    const optionCheckboxes = document.querySelectorAll('.option-checkbox:checked');
    optionCheckboxes.forEach(checkbox => {
        const option = optionsData.find(o => o.option_id == checkbox.value);
        if (option && option.price) {
            total += option.price;
        }
    });

    // 延長料金
    const extensionSelect = document.getElementById('extension');
    if (extensionSelect.selectedIndex > 0) {
        const extensionId = extensionSelect.value;
        const extension = extensionsData.find(e => e.extension_id == extensionId);
        if (extension && extension.fee) {
            total += extension.fee;
        }
    }

    // 交通費
    const transportationFee = parseInt(document.getElementById('transportation_fee').value) || 0;
    total += transportationFee;

    // 割引を適用（複数選択可能）
    const discountCheckboxes = document.querySelectorAll('#discount_container .option-checkbox:checked');
    discountCheckboxes.forEach(checkbox => {
        const discount = discountsData.find(d => d.discount_id == checkbox.value);
        if (discount) {
            if (discount.discount_type === 'percentage') {
                // パーセンテージ割引
                const discountAmount = Math.floor(total * (discount.value / 100));
                total -= discountAmount;
            } else if (discount.discount_type === 'fixed') {
                // 固定金額割引
                total -= discount.value;
            }
        }
    });

    // カード手数料を適用（支払い方法がカードの場合）
    const paymentMethod = document.getElementById('payment_method').value;
    if (paymentMethod === 'card' && total > 0) {
        const cardFee = Math.floor(total * (cardFeeRate / 100));
        total += cardFee;
    }

    // 表示
    const totalAmountInput = document.getElementById('total_amount');
    totalAmountInput.value = total.toLocaleString() + '円';

    // マイナスの場合は赤色で表示
    if (total < 0) {
        totalAmountInput.style.color = 'red';
    } else {
        totalAmountInput.style.color = '';
    }
}

// PT計算
function calculatePT() {
    const ptAdd = parseInt(document.getElementById('pt_add').value) || 0;
    const ptConsume = parseInt(document.getElementById('pt_consume').value) || 0;
    const remainingPT = currentCustomerPT + ptAdd - ptConsume;

    const ptValueElement = document.getElementById('remaining_pt');
    ptValueElement.textContent = remainingPT.toLocaleString();

    // マイナスの場合は赤字
    if (remainingPT < 0) {
        ptValueElement.classList.add('pt-negative');
    } else {
        ptValueElement.classList.remove('pt-negative');
    }

    // 左側の顧客情報カードも更新
    const displayElement = document.getElementById('current_pt_display');
    if (displayElement) {
        displayElement.innerHTML = `${remainingPT.toLocaleString()} <span class="stat-unit">PT</span>`;
        if (remainingPT < 0) {
            displayElement.style.color = 'red';
        } else {
            displayElement.style.color = '#333';
        }
    }
}

// フォームリセット
function resetForm() {
    if (confirm('入力内容をリセットしますか？')) {
        document.getElementById('reservation_form').reset();
        document.getElementById('cancellation_reason').disabled = true;
        document.getElementById('total_amount').value = '0円';

        // 日付・時間のselectボックスをデフォルト値に戻す
        document.getElementById('year').value = '2025';
        document.getElementById('month').value = '10';
        updateDayOptions();
        document.getElementById('day').value = '19';
        document.getElementById('hour').value = '00';
        document.getElementById('minute').value = '00';

        // hiddenフィールドを更新
        updateHiddenDateField();
        updateHiddenTimeField();

        // オプションのチェックボックスをすべて解除
        const optionCheckboxes = document.querySelectorAll('.option-checkbox');
        optionCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        updateSelectDisplay();

        calculatePT();
    }
}

// フォーム送信（予約更新）
document.getElementById('reservation_edit_form').addEventListener('submit', function(e) {
    e.preventDefault();

    const store = getStoreFromUrl();
    const formData = new FormData(this);

    fetch(`/${store}/reservation/update`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('予約を更新しました');
            window.location.href = `/${store}/reservations`;
        } else {
            alert('予約更新に失敗しました: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('エラーが発生しました');
    });
});

// URLから店舗名を取得
function getStoreFromUrl() {
    const path = window.location.pathname;
    const parts = path.split('/');
    return parts[1];
}

// ========================================
// 日付・時間セレクトボックスの初期化
// ========================================

function initializeDateTimeSelects() {
    // 年のセレクトボックスを初期化（2024-2026年）
    const yearSelect = document.getElementById('year');
    for (let year = 2024; year <= 2026; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }
    yearSelect.value = '2025'; // デフォルト: 2025年

    // 月のセレクトボックスを初期化（1-12月）
    const monthSelect = document.getElementById('month');
    for (let month = 1; month <= 12; month++) {
        const option = document.createElement('option');
        option.value = String(month).padStart(2, '0');
        option.textContent = month;
        monthSelect.appendChild(option);
    }
    monthSelect.value = '10'; // デフォルト: 10月

    // 日のセレクトボックスを初期化（1-31日）
    updateDayOptions();
    const daySelect = document.getElementById('day');
    daySelect.value = '19'; // デフォルト: 19日

    // 時のセレクトボックスを初期化（0-23時）
    const hourSelect = document.getElementById('hour');
    for (let hour = 0; hour <= 23; hour++) {
        const option = document.createElement('option');
        option.value = String(hour).padStart(2, '0');
        option.textContent = String(hour).padStart(2, '0');
        hourSelect.appendChild(option);
    }

    // 分のセレクトボックスを初期化（5分刻み）
    const minuteSelect = document.getElementById('minute');
    for (let minute = 0; minute < 60; minute += 5) {
        const option = document.createElement('option');
        option.value = String(minute).padStart(2, '0');
        option.textContent = String(minute).padStart(2, '0');
        minuteSelect.appendChild(option);
    }

    // イベントリスナーを追加
    yearSelect.addEventListener('change', function() {
        updateDayOptions();
        updateHiddenDateField();
    });

    monthSelect.addEventListener('change', function() {
        updateDayOptions();
        updateHiddenDateField();
    });

    daySelect.addEventListener('change', updateHiddenDateField);
    hourSelect.addEventListener('change', updateHiddenTimeField);
    minuteSelect.addEventListener('change', updateHiddenTimeField);

    // 初期値でhiddenフィールドを更新
    updateHiddenDateField();
    updateHiddenTimeField();
}

// 月に応じて日のオプションを動的に変更
function updateDayOptions() {
    const yearSelect = document.getElementById('year');
    const monthSelect = document.getElementById('month');
    const daySelect = document.getElementById('day');

    const year = parseInt(yearSelect.value);
    const month = parseInt(monthSelect.value);

    // 選択中の日を保存
    const currentDay = parseInt(daySelect.value) || 1;

    // その月の日数を計算
    const daysInMonth = new Date(year, month, 0).getDate();

    // 日のオプションを再生成
    daySelect.innerHTML = '';
    for (let day = 1; day <= daysInMonth; day++) {
        const option = document.createElement('option');
        option.value = String(day).padStart(2, '0');
        option.textContent = day;
        daySelect.appendChild(option);
    }

    // 以前選択していた日が有効な場合は復元
    if (currentDay <= daysInMonth) {
        daySelect.value = String(currentDay).padStart(2, '0');
    } else {
        daySelect.value = String(daysInMonth).padStart(2, '0');
    }
}

// hiddenフィールド（reservation_date）を更新
function updateHiddenDateField() {
    const year = document.getElementById('year').value;
    const month = document.getElementById('month').value;
    const day = document.getElementById('day').value;

    if (year && month && day) {
        const dateValue = `${year}-${month}-${day}`;
        document.getElementById('reservation_date').value = dateValue;
    }
}

// hiddenフィールド（reservation_time）を更新
function updateHiddenTimeField() {
    const hour = document.getElementById('hour').value;
    const minute = document.getElementById('minute').value;

    if (hour && minute) {
        const timeValue = `${hour}:${minute}`;
        document.getElementById('reservation_time').value = timeValue;
    }
}

// ========================================
// 既存予約データをフォームにロード
// ========================================

function loadExistingReservationData() {
    console.log('--- loadExistingReservationData 開始 ---');

    if (!window.reservationData) {
        console.error('❌ 予約データが見つかりません');
        console.log('window.reservationData:', window.reservationData);
        return;
    }

    const reservation = window.reservationData;
    console.log('✅ 予約データをロード:', reservation);
    console.log('予約ID:', reservation.reservation_id);
    console.log('顧客ID:', reservation.customer_id);
    console.log('キャストID:', reservation.cast_id);
    console.log('コースID:', reservation.course_id);

    // 成約種別
    if (reservation.status) {
        const contractType = reservation.status === 'キャンセル' ? 'cancel' : 'contract';
        document.getElementById('contract_type').value = contractType;
        toggleCancellation();
    }

    // 予約日時
    if (reservation.reservation_datetime) {
        const datetime = new Date(reservation.reservation_datetime);
        document.getElementById('year').value = datetime.getFullYear();
        document.getElementById('month').value = String(datetime.getMonth() + 1).padStart(2, '0');
        updateDayOptions();
        document.getElementById('day').value = String(datetime.getDate()).padStart(2, '0');
        document.getElementById('hour').value = String(datetime.getHours()).padStart(2, '0');
        document.getElementById('minute').value = String(datetime.getMinutes()).padStart(2, '0');
        updateHiddenDateField();
        updateHiddenTimeField();
    }

    // キャスト
    if (reservation.cast_id) {
        const castSelect = document.getElementById('cast_id');
        console.log('キャスト設定:', reservation.cast_id);
        console.log('キャストセレクトボックス:', castSelect);
        console.log('キャストオプション数:', castSelect ? castSelect.options.length : 0);
        if (castSelect) {
            castSelect.value = reservation.cast_id;
            console.log('キャスト設定後の値:', castSelect.value);
        }
    }

    // 予約方法
    if (reservation.reservation_method_id) {
        const methodSelect = document.getElementById('reservation_method');
        console.log('予約方法設定:', reservation.reservation_method_id);
        console.log('予約方法セレクトボックス:', methodSelect);
        if (methodSelect) {
            methodSelect.value = reservation.reservation_method_id;
            console.log('予約方法設定後の値:', methodSelect.value);
        }
    }

    // 指名種類
    if (reservation.nomination_type_id) {
        const nominationSelect = document.getElementById('nomination_type');
        console.log('指名種類設定:', reservation.nomination_type_id);
        if (nominationSelect) {
            nominationSelect.value = reservation.nomination_type_id;
            console.log('指名種類設定後の値:', nominationSelect.value);
        }
    }

    // コース
    if (reservation.course_id) {
        const courseSelect = document.getElementById('course_id');
        console.log('コース設定:', reservation.course_id);
        console.log('コースセレクトボックス:', courseSelect);
        console.log('コースオプション数:', courseSelect ? courseSelect.options.length : 0);
        if (courseSelect) {
            courseSelect.value = reservation.course_id;
            console.log('コース設定後の値:', courseSelect.value);
        }
    }

    // オプション
    if (reservation.option_ids && reservation.option_ids.length > 0) {
        setTimeout(() => {
            reservation.option_ids.forEach(optionId => {
                const checkbox = document.querySelector(`.option-checkbox[value="${optionId}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
            updateSelectDisplay();
        }, 600);
    }

    // 延長
    if (reservation.extension_id) {
        document.getElementById('extension').value = reservation.extension_id;
    }

    // 待ち合わせ場所
    if (reservation.meeting_place_id) {
        document.getElementById('meeting_place').value = reservation.meeting_place_id;
    }

    // 交通費
    if (reservation.transportation_fee) {
        document.getElementById('transportation_fee').value = reservation.transportation_fee;
    }

    // ホテル
    if (reservation.hotel_id) {
        const hotelSelect = document.getElementById('hotel_id');
        console.log('ホテル設定:', reservation.hotel_id);
        console.log('ホテルセレクトボックス:', hotelSelect);
        console.log('ホテルオプション数:', hotelSelect ? hotelSelect.options.length : 0);
        if (hotelSelect) {
            hotelSelect.value = reservation.hotel_id;
            console.log('ホテル設定後の値:', hotelSelect.value);
        }
    }

    // 部屋番号
    if (reservation.room_number) {
        const roomInput = document.getElementById('room_number');
        console.log('部屋番号設定:', reservation.room_number);
        if (roomInput) {
            roomInput.value = reservation.room_number;
            console.log('部屋番号設定後の値:', roomInput.value);
        }
    }

    // 支払い方法
    if (reservation.payment_method) {
        const paymentSelect = document.getElementById('payment_method');
        console.log('支払い方法設定:', reservation.payment_method);
        if (paymentSelect) {
            paymentSelect.value = reservation.payment_method;
            console.log('支払い方法設定後の値:', paymentSelect.value);
        }
    }

    // 担当スタッフ
    if (reservation.staff_id) {
        document.getElementById('staff_id').value = reservation.staff_id;
    }

    // キャンセル理由
    if (reservation.cancellation_reason_id) {
        document.getElementById('cancellation_reason').value = reservation.cancellation_reason_id;
    }

    // 割引（チェックボックス）
    if (reservation.discount_ids && reservation.discount_ids.length > 0) {
        setTimeout(() => {
            reservation.discount_ids.forEach(discountId => {
                const checkbox = document.querySelector(`#discount_container .option-checkbox[value="${discountId}"]`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
            updateDiscountDisplay();
        }, 600);
    } else if (reservation.discount_id) {
        // 旧形式の単一割引ID対応
        setTimeout(() => {
            const checkbox = document.querySelector(`#discount_container .option-checkbox[value="${reservation.discount_id}"]`);
            if (checkbox) {
                checkbox.checked = true;
            }
            updateDiscountDisplay();
        }, 600);
    }

    // PT追加
    if (reservation.points_to_grant) {
        document.getElementById('pt_add').value = reservation.points_to_grant;
    }

    // コメント
    if (reservation.customer_comment) {
        document.getElementById('comment').value = reservation.customer_comment;
    }

    // 料金を再計算
    setTimeout(() => {
        calculateTotal();
        calculatePT();
        updateCourseColors(); // キャスト選択に基づいてコースの色を更新
    }, 700);
}

// ========================================
// 予約削除機能
// ========================================

function deleteReservation() {
    if (!confirm('この予約を削除しますか？この操作は取り消せません。')) {
        return;
    }

    const store = getStoreFromUrl();
    const reservationId = document.getElementById('reservation_id').value;

    fetch(`/${store}/reservation/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            reservation_id: parseInt(reservationId)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('予約を削除しました');
            window.location.href = `/${store}/reservations`;
        } else {
            alert('削除に失敗しました: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('エラーが発生しました');
    });
}
