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
let areasData = []; // エリア一覧データ（フィルタリング用）
let allHotelsData = []; // 全ホテルデータ（バックアップ用）

// カード手数料率（デフォルト5%）
let cardFeeRate = 5;

// NG項目のID（グローバル変数）
let ngCourseIds = [];
let ngHotelIds = [];
let ngOptionIds = [];
let ngExtensionIds = [];

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async function() {
    // すべてのデータを並列で取得
    await loadAllDataParallel();

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

// セレクトボックスの表示を更新（オプション専用）
function updateSelectDisplay() {
    const checkedBoxes = document.querySelectorAll('#options_container input[type="checkbox"]:checked');
    const displayText = document.querySelector('#options_select_display .select-placeholder');

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

/**
 * すべてのマスタデータを並列で取得
 */
async function loadAllDataParallel() {
    const store = getStoreFromUrl();

    try {
        // すべてのfetchを並列実行
        const results = await Promise.allSettled([
            fetch(`/${store}/casts/api`).then(r => r.json()),
            fetch(`/${store}/courses/api`).then(r => r.json()),
            fetch(`/${store}/nomination-types/api`).then(r => r.json()),
            fetch(`/${store}/extensions/api`).then(r => r.json()),
            fetch(`/${store}/options/api`).then(r => r.json()),
            fetch(`/${store}/discount_management/api/list`).then(r => r.json()),
            fetch(`/${store}/reservation-settings/cancellation_reasons`).then(r => r.json()),
            fetch(`/${store}/settings/reservation_methods`).then(r => r.json()),
            fetch(`/${store}/reservation-settings/meeting_places`).then(r => r.json()),
            fetch(`/${store}/hotel-management/hotels`).then(r => r.json()),
            fetch(`/${store}/hotel-management/areas`).then(r => r.json()),
            fetch(`/${store}/staff/api`).then(r => r.json()),
            fetch(`/${store}/reservation-settings/card_fee_rate`).then(r => r.json()).catch(() => ({ success: true, rate: 5 }))
        ]);

        // 結果を展開
        const castsResponse = results[0].status === 'fulfilled' ? results[0].value : [];
        const coursesResponse = results[1].status === 'fulfilled' ? results[1].value : [];
        const nominationsResponse = results[2].status === 'fulfilled' ? results[2].value : [];
        const extensionsResponse = results[3].status === 'fulfilled' ? results[3].value : [];
        const optionsResponse = results[4].status === 'fulfilled' ? results[4].value : [];
        const discountsResponse = results[5].status === 'fulfilled' ? results[5].value : { success: false };
        const cancellationResponse = results[6].status === 'fulfilled' ? results[6].value : { success: false };
        const methodsResponse = results[7].status === 'fulfilled' ? results[7].value : [];
        const meetingPlacesResponse = results[8].status === 'fulfilled' ? results[8].value : { success: false };
        const hotelsResponse = results[9].status === 'fulfilled' ? results[9].value : { success: false };
        const areasResponse = results[10].status === 'fulfilled' ? results[10].value : { success: false };
        const staffResponse = results[11].status === 'fulfilled' ? results[11].value : [];
        const cardFeeResponse = results[12].status === 'fulfilled' ? results[12].value : { success: true, rate: 5 };

        // データを保存
        castsData = castsResponse;
        coursesData = coursesResponse;
        nominationsData = nominationsResponse;
        extensionsData = extensionsResponse;
        optionsData = optionsResponse;

        // 割引データ
        if (discountsResponse.success && discountsResponse.discounts) {
            discountsData = discountsResponse.discounts;
        }

        // ホテルデータ
        if (hotelsResponse.success && hotelsResponse.data) {
            hotelsData = hotelsResponse.data;
            allHotelsData = hotelsResponse.data;
        }

        // エリアデータ
        if (areasResponse.success && areasResponse.data) {
            areasData = areasResponse.data;
        }

        // カード手数料
        if (cardFeeResponse.success) {
            cardFeeRate = cardFeeResponse.rate || 5;
        }

        // 一括でDOMを更新
        populateSelect('cast_id', castsData, 'cast_id', 'name');
        populateSelect('course_id', coursesData, 'course_id', 'course_name');
        populateSelect('nomination_type', nominationsData, 'nomination_type_id', 'type_name');
        populateSelect('extension', extensionsData, 'extension_id', 'extension_name');
        populateOptionsCheckboxes(optionsData);
        populateDiscountsCheckboxes(discountsData);

        if (cancellationResponse.success && cancellationResponse.data) {
            populateSelect('cancellation_reason', cancellationResponse.data, 'reason_id', 'reason_name');
        }

        populateSelect('reservation_method', methodsResponse, 'method_id', 'method_name');

        // 支払い方法（固定値）
        const paymentMethods = [
            { method_id: 'cash', method_name: '現金' },
            { method_id: 'card', method_name: 'カード' },
            { method_id: 'deferred', method_name: '後払い' }
        ];
        populateSelect('payment_method', paymentMethods, 'method_id', 'method_name');
        document.getElementById('payment_method').value = 'cash';

        if (meetingPlacesResponse.success && meetingPlacesResponse.data) {
            populateSelect('meeting_place', meetingPlacesResponse.data, 'place_id', 'place_name');
        }

        populateSelect('hotel_id', hotelsData, 'hotel_id', 'hotel_name');
        populateTransportationFees(areasData);
        populateSelect('staff_id', staffResponse, 'id', 'name');

        // ログイン中のスタッフを自動選択
        if (window.currentStaffId) {
            document.getElementById('staff_id').value = window.currentStaffId;
        }

        // イベントリスナーを追加
        document.getElementById('cast_id').addEventListener('change', function() {
            updateCourseColors();
            highlightNgItems();
        });
        document.getElementById('hotel_id').addEventListener('change', updateTransportationFeeFromHotel);
        document.getElementById('transportation_fee').addEventListener('change', filterHotelsByArea);

    } catch (error) {
        console.error('データ読み込みエラー:', error);
    }
}

/**
 * 交通費セレクトにエリアを追加（ヘルパー関数）
 */
function populateTransportationFees(areas) {
    const select = document.getElementById('transportation_fee');
    areas.forEach(area => {
        const option = document.createElement('option');
        option.value = area.area_id;
        option.setAttribute('data-transportation-fee', area.transportation_fee);
        option.textContent = `${area.area_name} - ¥${area.transportation_fee.toLocaleString()}`;
        select.appendChild(option);
    });
}

// 旧loadMasterData()とloadCardFeeRate()は削除され、loadAllDataParallel()に統合されました

// ログイン中のスタッフを取得してデフォルト選択
// ※ この関数は使用されていません（window.currentStaffIdを使用）
function loadCurrentStaff() {
    // HTMLテンプレートから渡されたwindow.currentStaffIdを使用するため、
    // この関数は呼び出されません
}

// SELECTに選択肢を追加
function populateSelect(selectId, data, valueKey, textKey, clearFirst = false) {
    const select = document.getElementById(selectId);

    // clearFirstがtrueの場合、既存の選択肢をクリア（最初の選択肢は残す）
    if (clearFirst) {
        while (select.options.length > 1) {
            select.remove(1);
        }
    }

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

            // NGコースの場合は濃い赤を維持（上書きしない）
            if (ngCourseIds.includes(courseId)) {
                option.style.backgroundColor = '#ff9999';
                option.style.color = '#000';
                return;
            }

            const course = coursesData.find(c => c.course_id === courseId);

            console.log(`コースID: ${courseId}, カテゴリID: ${course?.category_id}`);

            if (course && course.category_id !== castCategoryId) {
                // カテゴリが一致しない場合は薄い赤背景
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

/**
 * キャスト選択時にNG項目を赤背景でハイライト
 */
async function highlightNgItems() {
    const castSelect = document.getElementById('cast_id');

    console.log('highlightNgItems called, cast_id:', castSelect?.value);

    if (!castSelect || !castSelect.value) {
        // キャストが選択されていない場合は全てクリア
        console.log('キャストが選択されていないため、NGハイライトをクリア');
        clearNgHighlights();
        return;
    }

    const selectedCastId = parseInt(castSelect.value);
    const store = getStoreFromUrl();

    console.log('NG項目取得開始 - cast_id:', selectedCastId);

    try {
        // キャストのNG項目を取得
        const response = await fetch(`/${store}/casts/${selectedCastId}/ng-items`);
        const ngData = await response.json();

        console.log('NG項目データ取得:', ngData);

        // グローバル変数に保存
        ngCourseIds = ngData.ng_course_ids || [];
        ngHotelIds = ngData.ng_hotel_ids || [];
        ngOptionIds = ngData.ng_option_ids || [];
        ngExtensionIds = ngData.ng_extension_ids || [];

        // NG項目をハイライト
        highlightNgCourses(ngCourseIds);
        highlightNgHotels(ngHotelIds);
        highlightNgOptions(ngOptionIds);
        highlightNgExtensions(ngExtensionIds);

        console.log('NG項目ハイライト完了');

    } catch (error) {
        console.error('NG項目取得エラー:', error);
    }
}

/**
 * NGコースをハイライト
 */
function highlightNgCourses(ngCourseIds) {
    console.log('highlightNgCourses - NG course IDs:', ngCourseIds);
    const courseSelect = document.getElementById('course_id');
    if (!courseSelect) {
        console.log('course_id selectが見つかりません');
        return;
    }

    let highlightCount = 0;
    Array.from(courseSelect.options).forEach(option => {
        if (option.value && ngCourseIds.includes(parseInt(option.value))) {
            // NG項目は濃い赤でハイライト
            option.style.backgroundColor = '#ff9999';
            option.style.color = '#000';
            highlightCount++;
            console.log('NGコースハイライト:', option.value, option.textContent);
        }
    });
    console.log(`${highlightCount}個のコースをハイライトしました`);
}

/**
 * NGホテルをハイライト
 */
function highlightNgHotels(ngHotelIds) {
    console.log('highlightNgHotels - NG hotel IDs:', ngHotelIds);
    const hotelSelect = document.getElementById('hotel_id');
    if (!hotelSelect) {
        console.log('hotel_id selectが見つかりません');
        return;
    }

    let highlightCount = 0;
    Array.from(hotelSelect.options).forEach(option => {
        if (option.value && ngHotelIds.includes(parseInt(option.value))) {
            // NG項目は濃い赤でハイライト
            option.style.backgroundColor = '#ff9999';
            option.style.color = '#000';
            highlightCount++;
            console.log('NGホテルハイライト:', option.value, option.textContent);
        }
    });
    console.log(`${highlightCount}個のホテルをハイライトしました`);
}

/**
 * NGオプションをハイライト
 */
function highlightNgOptions(ngOptionIds) {
    console.log('highlightNgOptions - NG option IDs:', ngOptionIds);
    const optionsContainer = document.getElementById('options_container');
    if (!optionsContainer) {
        console.log('options_containerが見つかりません');
        return;
    }

    let highlightCount = 0;
    const checkboxes = optionsContainer.querySelectorAll('input[type="checkbox"]');
    console.log('オプションチェックボックス数:', checkboxes.length);

    checkboxes.forEach(checkbox => {
        const optionId = parseInt(checkbox.value);
        const label = checkbox.closest('label');

        if (ngOptionIds.includes(optionId)) {
            // NG項目は濃い赤でハイライト
            label.style.backgroundColor = '#ff9999';
            label.style.padding = '4px 8px';
            label.style.borderRadius = '4px';

            // !important を使って強制的にスタイルを適用
            label.style.setProperty('background-color', '#ff9999', 'important');

            highlightCount++;
            console.log('NGオプションハイライト:', optionId, label.textContent.trim());
        } else {
            label.style.backgroundColor = '';
            label.style.padding = '';
            label.style.borderRadius = '';
        }
    });
    console.log(`${highlightCount}個のオプションをハイライトしました`);
}

/**
 * NG延長をハイライト
 */
function highlightNgExtensions(ngExtensionIds) {
    console.log('highlightNgExtensions - NG extension IDs:', ngExtensionIds);
    const extensionSelect = document.getElementById('extension');
    if (!extensionSelect) {
        console.log('extension selectが見つかりません');
        return;
    }

    let highlightCount = 0;
    Array.from(extensionSelect.options).forEach(option => {
        if (option.value && ngExtensionIds.includes(parseInt(option.value))) {
            // NG項目は濃い赤でハイライト
            option.style.backgroundColor = '#ff9999';
            option.style.color = '#000';
            highlightCount++;
            console.log('NG延長ハイライト:', option.value, option.textContent);
        }
    });
    console.log(`${highlightCount}個の延長をハイライトしました`);
}

/**
 * 全てのNGハイライトをクリア
 */
function clearNgHighlights() {
    // コースのクリア
    const courseSelect = document.getElementById('course_id');
    if (courseSelect) {
        Array.from(courseSelect.options).forEach(option => {
            if (option.value) {
                option.style.backgroundColor = '';
                option.style.color = '';
            }
        });
    }

    // ホテルのクリア
    const hotelSelect = document.getElementById('hotel_id');
    if (hotelSelect) {
        Array.from(hotelSelect.options).forEach(option => {
            if (option.value) {
                option.style.backgroundColor = '';
                option.style.color = '';
            }
        });
    }

    // オプションのクリア
    const optionsContainer = document.getElementById('options_container');
    if (optionsContainer) {
        const labels = optionsContainer.querySelectorAll('label');
        labels.forEach(label => {
            label.style.backgroundColor = '';
            label.style.padding = '';
            label.style.borderRadius = '';
        });
    }

    // 延長のクリア
    const extensionSelect = document.getElementById('extension');
    if (extensionSelect) {
        Array.from(extensionSelect.options).forEach(option => {
            if (option.value) {
                option.style.backgroundColor = '';
                option.style.color = '';
            }
        });
    }
}

// 交通費（エリア）選択時にホテルをフィルタリング
function filterHotelsByArea() {
    const transportationFeeSelect = document.getElementById('transportation_fee');
    const hotelSelect = document.getElementById('hotel_id');
    const selectedAreaId = parseInt(transportationFeeSelect.value);

    console.log('[DEBUG] 選択されたエリアID:', selectedAreaId);

    // エリアが選択されていない場合（「なし」を選択）、全ホテルを表示
    if (!selectedAreaId || selectedAreaId === 0) {
        console.log('[DEBUG] エリア未選択 - 全ホテルを表示');
        populateSelect('hotel_id', allHotelsData, 'hotel_id', 'hotel_name', true);
        // NGホテルを再ハイライト
        highlightNgHotels(ngHotelIds);
        calculateTotal();
        return;
    }

    // 選択されたエリアに属するホテルだけをフィルタリング
    const filteredHotels = allHotelsData.filter(hotel => hotel.area_id === selectedAreaId);
    console.log('[DEBUG] フィルタリング後のホテル数:', filteredHotels.length);
    console.log('[DEBUG] フィルタリング後のホテル:', filteredHotels);

    // ホテルセレクトボックスを更新（既存の選択肢をクリア）
    populateSelect('hotel_id', filteredHotels, 'hotel_id', 'hotel_name', true);

    // NGホテルを再ハイライト
    highlightNgHotels(ngHotelIds);

    // 料金を再計算
    calculateTotal();
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
    const selectedHotel = allHotelsData.find(h => h.hotel_id === selectedHotelId);

    if (!selectedHotel) {
        transportationFeeSelect.value = '0';
        calculateTotal();
        return;
    }

    // ホテルのエリアIDを取得して、対応するエリアを設定
    const areaId = selectedHotel.area_id;
    if (areaId) {
        transportationFeeSelect.value = areaId.toString();
    } else {
        transportationFeeSelect.value = '0';
    }

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

            // コース選択時にポイントを自動計算
            calculateReservationPoints(courseId, course.price);
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
    const optionCheckboxes = document.querySelectorAll('#options_container .option-checkbox:checked');
    optionCheckboxes.forEach(checkbox => {
        const option = optionsData.find(o => o.option_id == checkbox.value);
        if (option && option.price) {
            total += option.price;
        }
    });

    // 延長料金（回数対応）
    const extensionSelect = document.getElementById('extension');
    const extensionQuantity = parseInt(document.getElementById('extension_quantity').value);
    if (extensionSelect.selectedIndex > 0 && extensionQuantity > 0) {
        const extensionId = extensionSelect.value;
        const extension = extensionsData.find(e => e.extension_id == extensionId);
        if (extension && extension.fee) {
            total += extension.fee * extensionQuantity;
        }
    }

    // 交通費
    const transportationFeeSelect = document.getElementById('transportation_fee');
    const selectedOption = transportationFeeSelect.options[transportationFeeSelect.selectedIndex];
    const transportationFee = selectedOption ? parseInt(selectedOption.getAttribute('data-transportation-fee')) || 0 : 0;
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

    // 調整金を加算
    const adjustmentAmount = parseInt(document.getElementById('adjustment_amount').value) || 0;
    total += adjustmentAmount;

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

// 予約時のポイント自動計算
async function calculateReservationPoints(courseId, coursePrice) {
    // 顧客の会員種別を使用（顧客編集ページで設定されたもの）
    const memberType = window.currentCustomerMemberType;

    // コースIDと会員種別が設定されていない場合は何もしない
    if (!courseId || !memberType) {
        return;
    }

    const store = getStoreFromUrl();

    try {
        const response = await fetch(`/${store}/point_settings/api/calculate_points`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_id: courseId,
                member_type: memberType,
                course_price: coursePrice
            })
        });

        const result = await response.json();

        if (result.success && result.points !== undefined) {
            // PT追加フィールドに自動入力
            const ptAddInput = document.getElementById('pt_add');
            if (ptAddInput) {
                ptAddInput.value = result.points;
                calculatePT(); // PT残高を再計算
            }
        }
    } catch (error) {
        console.error('ポイント計算エラー:', error);
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

        // オプションと割引のチェックボックスをすべて解除
        const allCheckboxes = document.querySelectorAll('.option-checkbox');
        allCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        updateSelectDisplay();
        updateDiscountDisplay();

        calculatePT();
    }
}

// フォーム送信
document.getElementById('reservation_form').addEventListener('submit', function(e) {
    e.preventDefault();

    const store = getStoreFromUrl();
    const formData = new FormData(this);

    // 交通費をエリアIDから金額に変換
    const transportationFeeSelect = document.getElementById('transportation_fee');
    const selectedOption = transportationFeeSelect.options[transportationFeeSelect.selectedIndex];
    const transportationFeeAmount = selectedOption ? parseInt(selectedOption.getAttribute('data-transportation-fee')) || 0 : 0;
    formData.set('transportation_fee', transportationFeeAmount);

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

// ========================================
// 顧客評価モーダル
// ========================================

/**
 * 顧客評価件数を取得してボタンに表示
 */
async function loadCustomerRatingCount() {
    if (!window.currentCustomerId) {
        return;
    }

    try {
        const store = getStoreFromUrl();
        const response = await fetch(`/${store}/reservation/customer_rating/${window.currentCustomerId}`);
        const data = await response.json();

        if (data.success && data.rating_count !== undefined) {
            const btn = document.getElementById('customerRatingBtn');
            if (btn) {
                btn.textContent = `顧客評価：${data.rating_count}件`;
            }
        }
    } catch (error) {
        console.error('評価件数取得エラー:', error);
    }
}

/**
 * 顧客評価モーダルを表示
 */
async function showCustomerRatingModal(customerId) {
    const modal = document.getElementById('ratingModal');
    const modalBody = document.getElementById('ratingModalBody');

    if (!customerId) {
        alert('顧客IDが指定されていません');
        return;
    }

    // ローディング表示
    modalBody.innerHTML = '<div class="rating-empty">読み込み中...</div>';
    modal.style.display = 'flex';

    try {
        const store = getStoreFromUrl();
        const response = await fetch(`/${store}/reservation/customer_rating/${customerId}`);
        const data = await response.json();

        if (!data.success) {
            modalBody.innerHTML = '<div class="rating-empty">評価データの取得に失敗しました</div>';
            return;
        }

        // モーダルの内容を生成
        let html = '';

        // 評価項目を表示
        const ratingItems = data.rating_items.filter(item => item.item_type !== 'textarea');

        if (ratingItems.length === 0 && data.everyone_comments.length === 0) {
            html = '<div class="rating-empty">まだ評価がありません</div>';
        } else {
            // ラジオ/セレクト項目の評価を表示
            ratingItems.forEach(item => {
                const itemId = String(item.item_id);
                const ratings = data.everyone_ratings[itemId] || [];

                html += `<div class="rating-item">`;
                html += `<span class="rating-item-name">${escapeHtml(item.item_name)}</span>`;

                if (ratings.length > 0) {
                    ratings.forEach(rating => {
                        // ratingが正しい形式か確認
                        if (rating && typeof rating === 'object' && rating.value !== undefined && rating.count !== undefined) {
                            html += `<div class="rating-option">`;
                            html += `<span class="rating-option-value">${escapeHtml(String(rating.value))}</span>`;
                            html += `<span class="rating-option-count">${rating.count}票</span>`;
                            html += `</div>`;
                        }
                    });
                } else {
                    html += '<div class="rating-empty" style="padding: 10px;">評価なし</div>';
                }

                html += `</div>`;
            });

            // コメント（備考欄）を表示
            if (data.everyone_comments.length > 0) {
                html += `<div class="rating-item">`;
                html += `<span class="rating-item-name">備考欄</span>`;
                html += `<div class="rating-comments">`;

                data.everyone_comments.forEach(comment => {
                    html += `<div class="rating-comment">`;
                    html += `<div class="rating-comment-text">${escapeHtml(comment.rating_value)}</div>`;
                    html += `<div class="rating-comment-meta">`;
                    html += `<span class="rating-comment-cast">${escapeHtml(comment.cast_name)}</span>`;
                    html += `<span class="rating-comment-date">${comment.created_at}</span>`;
                    html += `</div>`;
                    html += `</div>`;
                });

                html += `</div>`;
                html += `</div>`;
            }
        }

        modalBody.innerHTML = html;

    } catch (error) {
        console.error('Error:', error);
        modalBody.innerHTML = '<div class="rating-empty">エラーが発生しました</div>';
    }
}

/**
 * 顧客評価モーダルを閉じる
 */
function closeRatingModal() {
    const modal = document.getElementById('ratingModal');
    modal.style.display = 'none';
}

/**
 * HTMLエスケープ
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
