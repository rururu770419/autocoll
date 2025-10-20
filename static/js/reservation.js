/**
 * 予約登録ページのJavaScript
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
    loadMasterData();
    loadCardFeeRate();
    initializeCustomSelect();
    initializeDateTimeSelects();
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
            console.log('キャストデータ取得:', data);
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
            console.log('コースデータ取得:', data);
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

    console.log('updateCourseColors 呼び出し');

    if (!castSelect.value || !courseSelect) {
        console.log('キャストが選択されていないかコースセレクトが存在しません');
        return;
    }

    // 選択されたキャストのデータを取得
    const selectedCastId = parseInt(castSelect.value);
    const selectedCast = castsData.find(c => c.cast_id === selectedCastId);

    console.log('選択されたキャスト:', selectedCast);

    if (!selectedCast || !selectedCast.course_category_id) {
        // キャストのカテゴリが設定されていない場合は全てデフォルト色
        console.log('キャストのカテゴリが設定されていません');
        Array.from(courseSelect.options).forEach(option => {
            if (option.value) {
                option.style.backgroundColor = '';
                option.style.color = '';
            }
        });
        return;
    }

    const castCategoryId = selectedCast.course_category_id;
    console.log('キャストのカテゴリID:', castCategoryId);

    // 各コースオプションの背景色を設定
    Array.from(courseSelect.options).forEach(option => {
        if (option.value) {
            const courseId = parseInt(option.value);
            const course = coursesData.find(c => c.course_id === courseId);

            console.log(`コースID: ${courseId}, カテゴリID: ${course?.category_id}`);

            if (course && course.category_id !== castCategoryId) {
                // カテゴリが一致しない場合は赤背景
                console.log(`コース ${courseId} を赤に設定`);
                option.style.backgroundColor = '#ffcccc';
                option.style.color = '#000';
            } else {
                // カテゴリが一致する場合は通常色
                console.log(`コース ${courseId} を通常色に設定`);
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

    // 割引を適用（複数選択対応）
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

// フォーム送信
document.getElementById('reservation_form').addEventListener('submit', function(e) {
    e.preventDefault();

    const store = getStoreFromUrl();
    const formData = new FormData(this);

    // デバッグ: 送信されるデータを確認
    console.log('=== 送信されるフォームデータ ===');
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }
    console.log('hotel_id value:', document.getElementById('hotel_id').value);
    console.log('hotel_id element:', document.getElementById('hotel_id'));
    console.log('===========================');

    fetch(`/${store}/reservations/register`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('予約を登録しました');
            window.location.href = `/${store}/reservations`;
        } else {
            alert('予約登録に失敗しました: ' + data.message);
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
    // 今日の日付を取得
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth() + 1; // 0-11 → 1-12
    const currentDay = today.getDate();

    // 年のセレクトボックスを初期化（2024-2026年）
    const yearSelect = document.getElementById('year');
    for (let year = 2024; year <= 2026; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    }
    yearSelect.value = currentYear; // デフォルト: 今年

    // 月のセレクトボックスを初期化（1-12月）
    const monthSelect = document.getElementById('month');
    for (let month = 1; month <= 12; month++) {
        const option = document.createElement('option');
        option.value = String(month).padStart(2, '0');
        option.textContent = month;
        monthSelect.appendChild(option);
    }
    monthSelect.value = String(currentMonth).padStart(2, '0'); // デフォルト: 今月

    // 日のセレクトボックスを初期化（1-31日）
    updateDayOptions();
    const daySelect = document.getElementById('day');
    daySelect.value = String(currentDay).padStart(2, '0'); // デフォルト: 今日

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
