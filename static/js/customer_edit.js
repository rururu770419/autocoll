// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 顧客編集画面スクリプト
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Customer edit page initialized');

    // ローディング表示
    showLoading();

    try {
        // すべてのデータを並列で取得
        await Promise.all([
            loadCustomerFieldOptions(),
            loadPointReasons(),
            loadCustomerData()
        ]);

        // フォーム送信イベント
        document.getElementById('customerForm').addEventListener('submit', handleFormSubmit);

        // 年齢自動計算
        const birthdayInput = document.getElementById('birthday');
        if (birthdayInput) {
            birthdayInput.addEventListener('change', calculateAge);
        }

        // 削除ボタン
        const deleteBtn = document.getElementById('deleteBtn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', deleteCustomer);
        }

        // 入力制限を設定
        setupInputRestrictions();

        // セレクトボックスの変更イベント（色を反映）
        setupSelectChangeEvents();

        // 🆕 コメント欄の自動リサイズ機能
        setupTextareaAutoResize();

        // ローディングを非表示にしてコンテンツを表示
        hideLoading();

    } catch (error) {
        console.error('データ読み込みエラー:', error);
        alert('データの読み込みに失敗しました。ページを再読み込みしてください。');
        hideLoading();
    }
});

/**
 * ローディング表示
 */
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    const mainContent = document.getElementById('mainContent');
    if (overlay) overlay.classList.remove('hidden');
    if (mainContent) {
        mainContent.style.opacity = '0';
        mainContent.style.pointerEvents = 'none';
    }
}

/**
 * ローディング非表示
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    const mainContent = document.getElementById('mainContent');

    if (overlay) {
        overlay.classList.add('hidden');
    }

    if (mainContent) {
        // フェードイン効果
        mainContent.style.transition = 'opacity 0.3s ease';
        mainContent.style.opacity = '1';
        mainContent.style.pointerEvents = 'auto';
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 選択肢データ読み込み
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function loadCustomerFieldOptions() {
    const store = getStoreCode();

    try {
        const response = await fetch(`/${store}/api/customer_fields/options`);
        const result = await response.json();

        if (result.success && result.options) {
            // 会員種別
            populateSelect('member_type', result.options.member_type || []);

            // ステータス
            populateSelect('status', result.options.status || []);

            // WEB会員
            populateSelect('web_member', result.options.web_member || []);

            // 募集媒体
            populateSelect('recruitment_source', result.options.recruitment_source || []);
        }
    } catch (error) {
        console.error('選択肢の読み込みエラー:', error);
    }
}

/**
 * ポイント操作理由を読み込む
 */
async function loadPointReasons() {
    const store = getStoreCode();

    try {
        const response = await fetch(`/${store}/point_settings/api/reasons`);
        const result = await response.json();

        if (result.success && result.reasons) {
            const select = document.getElementById('point_reason');
            if (!select) return;

            // 既存のoptionを削除（「選択してください」は残す）
            while (select.options.length > 1) {
                select.remove(1);
            }

            // 理由を追加
            result.reasons.forEach(reason => {
                const option = document.createElement('option');
                option.value = reason.reason_name;
                option.textContent = reason.reason_name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('ポイント操作理由の読み込みエラー:', error);
    }
}

function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // 既存のoptionを削除（空白選択は残す）
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    // 選択肢を追加
    options.forEach(option => {
        // is_hiddenがtrueの場合はスキップ
        if (option.is_hidden) return;
        
        const optElement = document.createElement('option');
        optElement.value = option.value;
        optElement.textContent = option.value;  // labelではなくvalueを表示
        
        // 色情報があれば設定
        if (option.color) {
            optElement.style.backgroundColor = option.color;
            optElement.style.color = getContrastColor(option.color);
        }
        
        select.appendChild(optElement);
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 顧客データ読み込み
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function loadCustomerData() {
    const customerId = document.getElementById('customerId').value;
    const store = getStoreCode();
    
    try {
        const response = await fetch(`/${store}/api/customers/${customerId}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const customer = result.data;
            
            // 基本情報
            setFieldValue('name', customer.name);
            setFieldValue('furigana', customer.furigana);
            setFieldValue('phone', customer.phone);
            setFieldValue('birthday', customer.birthday);
            setFieldValue('age', customer.age);
            setFieldValue('nickname', customer.nickname);
            
            // 住所情報
            setFieldValue('prefecture', customer.prefecture);

            // 住所詳細を分割（互換性のため）
            if (customer.address_detail) {
                setFieldValue('street_address', customer.street_address || customer.address_detail);
                setFieldValue('building_name', customer.building_name || '');
            } else {
                setFieldValue('street_address', customer.street_address || '');
                setFieldValue('building_name', customer.building_name || '');
            }
            
            // 会員情報
            setFieldValue('member_type', customer.member_type);
            setFieldValue('status', customer.status);
            setFieldValue('web_member', customer.web_member);
            setFieldValue('current_points', customer.current_points);
            setFieldValue('recruitment_source', customer.recruitment_source);
            setFieldValue('customer_number', customer.customer_number);

            // マイページ情報
            setFieldValue('mypage_id', customer.mypage_id);
            setFieldValue('mypage_password', customer.mypage_password);

            // 車情報
            setFieldValue('car_info', customer.car_info);

            // コメント
            setFieldValue('comment', customer.comment);
            
            // 都道府県が選択されていたら市区町村を読み込む
            if (customer.prefecture) {
                await loadCityOptions(customer.prefecture);
                setFieldValue('city', customer.city);
            }
            
            // 選択肢の色を反映（少し待ってからトリガー）
            setTimeout(() => {
                applySelectColors();
            }, 100);
            
            // 🆕 コメント欄のリサイズをトリガー
            setTimeout(() => {
                const commentArea = document.getElementById('comment');
                if (commentArea && commentArea.value) {
                    commentArea.dispatchEvent(new Event('input'));
                }
            }, 200);
        }
    } catch (error) {
        console.error('顧客データの読み込みエラー:', error);
        showMessage('顧客データの読み込みに失敗しました', 'error');
    }
}

function setFieldValue(fieldId, value) {
    const field = document.getElementById(fieldId);
    if (field && value !== null && value !== undefined) {
        field.value = value;
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 市区町村の読み込み（address.jsと連携）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function loadCityOptions(prefecture) {
    return new Promise((resolve) => {
        // address.jsのcityDataを使用
        if (typeof cityData !== 'undefined' && cityData[prefecture]) {
            const citySelect = document.getElementById('city');
            if (citySelect) {
                // 既存の選択肢をクリア
                citySelect.innerHTML = '<option value="">選択してください</option>';
                
                // 新しい選択肢を追加
                cityData[prefecture].forEach(city => {
                    const option = document.createElement('option');
                    option.value = city;
                    option.textContent = city;
                    citySelect.appendChild(option);
                });
            }
        }
        
        // 少し待ってから完了（DOMの更新を確実にするため）
        setTimeout(resolve, 50);
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 選択肢の色を反映
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function applySelectColors() {
    const selects = ['member_type', 'status', 'web_member', 'recruitment_source'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select || !select.value) return;
        
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption && selectedOption.style.backgroundColor) {
            select.style.backgroundColor = selectedOption.style.backgroundColor;
            select.style.color = selectedOption.style.color;
        }
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 入力制限
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function setupInputRestrictions() {
    // フリガナ（カタカナのみ）
    const furiganaInput = document.getElementById('furigana');
    if (furiganaInput) {
        furiganaInput.addEventListener('compositionstart', function(e) {
            isComposing = true;
        });
        furiganaInput.addEventListener('compositionend', function(e) {
            handleCompositionEnd(this);
        });
        furiganaInput.addEventListener('input', function(e) {
            convertToKatakana(this);
        });
    }

    // 電話番号（数字のみ、11桁）
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 11);
        });
    }

    // 所持PT（数字のみ）
    const pointsInput = document.getElementById('current_points');
    if (pointsInput) {
        pointsInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^0-9]/g, '');
        });
    }

    // マイページID（半角英数字と記号のみ）
    const mypageIdInput = document.getElementById('mypage_id');
    if (mypageIdInput) {
        mypageIdInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^a-zA-Z0-9_\-@.]/g, '');
        });
    }

    // マイページパスワード（半角文字のみ）
    const passwordInput = document.getElementById('mypage_password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function(e) {
            this.value = this.value.replace(/[^\x20-\x7E]/g, '');
        });
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// セレクトボックスの色変更イベント
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function setupSelectChangeEvents() {
    const selectIds = ['member_type', 'status', 'web_member', 'recruitment_source'];
    
    selectIds.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        select.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption && selectedOption.style.backgroundColor) {
                this.style.backgroundColor = selectedOption.style.backgroundColor;
                this.style.color = selectedOption.style.color;
            } else {
                // 選択解除時は色をリセット
                this.style.backgroundColor = '';
                this.style.color = '';
            }
        });
    });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 年齢自動計算
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function calculateAge() {
    const birthdayInput = document.getElementById('birthday');
    const ageInput = document.getElementById('age');
    
    if (!birthdayInput || !birthdayInput.value || !ageInput) return;
    
    const birthday = new Date(birthdayInput.value);
    const today = new Date();
    let age = today.getFullYear() - birthday.getFullYear();
    const monthDiff = today.getMonth() - birthday.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthday.getDate())) {
        age--;
    }
    
    ageInput.value = age >= 0 ? age : '';
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 🆕 コメント欄の自動リサイズ機能
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function setupTextareaAutoResize() {
    const textarea = document.getElementById('comment');
    if (!textarea) return;
    
    // 初期スタイルを設定
    textarea.style.overflow = 'hidden';
    textarea.style.resize = 'none';
    textarea.style.minHeight = '36px';
    
    // 自動リサイズ関数
    function autoResize() {
        // 一旦リセット
        this.style.height = '36px';
        
        // 内容に合わせて高さを調整
        const newHeight = Math.max(36, this.scrollHeight);
        this.style.height = newHeight + 'px';
    }
    
    // イベントリスナーを追加
    textarea.addEventListener('input', autoResize);
    textarea.addEventListener('change', autoResize);
    
    // 初期サイズを設定
    setTimeout(() => {
        textarea.style.height = '36px';
    }, 100);
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// フォーム送信
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const customerId = document.getElementById('customerId').value;
    const store = getStoreCode();
    
    // フォームデータを取得
    const getValue = (id) => {
        const element = document.getElementById(id);
        return element ? element.value.trim() : '';
    };
    
    // 🔧 修正: 空の日付フィールドをnullに変換
    const birthdayValue = getValue('birthday');
    const ageValue = getValue('age');

    // ポイント操作のバリデーション
    const pointOperation = getValue('point_operation');
    const pointAmount = getValue('point_amount');
    const pointReason = getValue('point_reason');

    // ポイント操作のバリデーション
    if (pointOperation && !pointAmount) {
        showMessage('操作が選択されている場合は、ポイント数を入力してください', 'error');
        return;
    }

    if (pointAmount && !pointOperation) {
        showMessage('ポイント数が入力されている場合は、操作を選択してください', 'error');
        return;
    }

    if (pointOperation === 'consume' && pointAmount) {
        const currentPoints = parseInt(getValue('current_points')) || 0;
        const consumePoints = parseInt(pointAmount);
        if (consumePoints > currentPoints) {
            showMessage(`消費ポイント（${consumePoints}PT）が所持ポイント（${currentPoints}PT）を超えています`, 'error');
            return;
        }
    }

    const data = {
        name: getValue('name'),
        furigana: getValue('furigana'),
        phone: getValue('phone'),
        birthday: birthdayValue || null,  // 空文字列の場合はnull
        age: ageValue ? parseInt(ageValue) : null,  // 空文字列の場合はnull
        prefecture: getValue('prefecture'),
        city: getValue('city'),
        street_address: getValue('street_address'),
        building_name: getValue('building_name'),
        // 互換性のため、address_detailも送信（street_address + building_nameを結合）
        address_detail: [getValue('street_address'), getValue('building_name')].filter(v => v).join(' '),
        car_info: getValue('car_info'),
        member_type: getValue('member_type'),
        status: getValue('status'),
        web_member: getValue('web_member'),
        current_points: parseInt(getValue('current_points')) || 0,
        recruitment_source: getValue('recruitment_source'),
        mypage_id: getValue('mypage_id'),
        mypage_password: getValue('mypage_password'),
        comment: getValue('comment'),
        nickname: getValue('nickname') || getValue('name'),  // ニックネームが空なら名前をコピー
        // ポイント操作情報
        point_operation: pointOperation || null,
        point_amount: pointAmount ? parseInt(pointAmount) : null,
        point_reason: pointReason || null
    };

    console.log('送信データ:', data);

    // 必須チェック
    if (!data.name) {
        showMessage('名前は必須です', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/${store}/api/customers/${customerId}/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('顧客情報を更新しました', 'success');
            // データを再読み込み
            await loadCustomerData();
        } else {
            showMessage(result.message || '更新に失敗しました', 'error');
        }
    } catch (error) {
        console.error('更新エラー:', error);
        showMessage('顧客情報を更新に失敗しました: ' + error.message, 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 削除
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async function deleteCustomer() {
    if (!confirm('この顧客を削除してもよろしいですか？\nこの操作は取り消せません。')) {
        return;
    }
    
    const customerId = document.getElementById('customerId').value;
    const store = getStoreCode();
    
    try {
        const response = await fetch(`/${store}/api/customers/${customerId}/delete`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('顧客を削除しました', 'success');
            setTimeout(() => {
                window.location.href = `/${store}/customer_management`;
            }, 1000);
        } else {
            showMessage(result.message || '削除に失敗しました', 'error');
        }
    } catch (error) {
        console.error('削除エラー:', error);
        showMessage('エラーが発生しました', 'error');
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ユーティリティ関数
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function getStoreCode() {
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[1] || 'nagano';
}

function getContrastColor(hexColor) {
    if (!hexColor) return '#000000';
    
    const r = parseInt(hexColor.substr(1, 2), 16);
    const g = parseInt(hexColor.substr(3, 2), 16);
    const b = parseInt(hexColor.substr(5, 2), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 155 ? '#000000' : '#ffffff';
}

function showMessage(message, type) {
    const messageArea = document.getElementById('messageArea');
    if (!messageArea) return;

    const alertClass = type === 'success' ? 'customer-alert-success' :
                      type === 'info' ? 'customer-alert-info' :
                      'customer-alert-error';

    messageArea.innerHTML = `<div class="customer-alert ${alertClass}">${message}</div>`;
    messageArea.style.display = 'block';

    setTimeout(() => {
        messageArea.style.display = 'none';
    }, 3000);
}

// IME入力中かどうかのフラグ
let isComposing = false;

/**
 * ひらがなをカタカナに自動変換し、カタカナ以外を削除
 * @param {HTMLInputElement} input - 入力フィールド
 */
function convertToKatakana(input) {
    // IME入力中は処理をスキップ
    if (isComposing) {
        return;
    }

    let value = input.value;

    // 1. ひらがなをカタカナに変換
    // Unicode: ひらがな (U+3041-U+3096) → カタカナ (U+30A1-U+30F6)
    let converted = value.replace(/[\u3041-\u3096]/g, function(match) {
        const chr = match.charCodeAt(0) + 0x60;
        return String.fromCharCode(chr);
    });

    // 2. カタカナ、スペース、長音記号のみ許可（それ以外は削除）
    let filtered = converted.replace(/[^ァ-ヴー\s]/g, '');

    // 3. 変換後の値を設定（変更があった場合のみ）
    if (value !== filtered) {
        input.value = filtered;
    }
}

/**
 * IME変換確定時の処理
 * @param {HTMLInputElement} input - 入力フィールド
 */
function handleCompositionEnd(input) {
    isComposing = false;
    // 変換確定後に変換処理を実行
    convertToKatakana(input);
}

// ============================================
// 利用履歴・利用キャスト
// ============================================

/**
 * URLから店舗コードを取得
 */
function getStoreFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[1]; // /nagano/customer_edit/20 の場合、pathParts[1]が'nagano'
}

/**
 * 利用履歴を取得して表示
 */
async function loadUsageHistory() {
    const customerId = document.getElementById('customerId').value;
    const store = getStoreFromUrl();

    try {
        const response = await fetch(`/${store}/api/customer/${customerId}/usage_history`);
        const data = await response.json();

        const tbody = document.getElementById('usage-history-tbody');

        if (data.success && data.data.length > 0) {
            tbody.innerHTML = '';
            data.data.forEach(item => {
                const row = document.createElement('tr');

                // 成約種別
                const statusCell = document.createElement('td');
                statusCell.textContent = item.status || '-';
                row.appendChild(statusCell);

                // 予約日時
                const dateCell = document.createElement('td');
                if (item.reservation_datetime) {
                    const date = new Date(item.reservation_datetime);
                    dateCell.textContent = `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
                } else {
                    dateCell.textContent = '-';
                }
                row.appendChild(dateCell);

                // キャスト名
                const castCell = document.createElement('td');
                castCell.textContent = item.cast_name || '-';
                row.appendChild(castCell);

                // ホテル名
                const hotelCell = document.createElement('td');
                hotelCell.textContent = item.hotel_name || '-';
                row.appendChild(hotelCell);

                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="no-data-cell">利用履歴がありません</td></tr>';
        }
    } catch (error) {
        console.error('利用履歴取得エラー:', error);
        const tbody = document.getElementById('usage-history-tbody');
        tbody.innerHTML = '<tr><td colspan="4" class="no-data-cell">データの取得に失敗しました</td></tr>';
    }
}

/**
 * 利用キャストを取得して表示
 */
async function loadCastUsage() {
    const customerId = document.getElementById('customerId').value;
    const store = getStoreFromUrl();

    try {
        const response = await fetch(`/${store}/api/customer/${customerId}/cast_usage`);
        const data = await response.json();

        const tbody = document.getElementById('cast-usage-tbody');

        if (data.success && data.data.length > 0) {
            tbody.innerHTML = '';
            data.data.forEach(item => {
                const row = document.createElement('tr');

                // キャスト名
                const castCell = document.createElement('td');
                castCell.textContent = item.cast_name || '-';
                row.appendChild(castCell);

                // 利用回数
                const countCell = document.createElement('td');
                countCell.textContent = `${item.usage_count}回`;
                row.appendChild(countCell);

                // 最新日時
                const dateCell = document.createElement('td');
                if (item.latest_datetime) {
                    const date = new Date(item.latest_datetime);
                    dateCell.textContent = `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
                } else {
                    dateCell.textContent = '-';
                }
                row.appendChild(dateCell);

                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="3" class="no-data-cell">利用キャストがありません</td></tr>';
        }
    } catch (error) {
        console.error('利用キャスト取得エラー:', error);
        const tbody = document.getElementById('cast-usage-tbody');
        tbody.innerHTML = '<tr><td colspan="3" class="no-data-cell">データの取得に失敗しました</td></tr>';
    }
}

// ページ読み込み時に利用履歴と利用キャストを取得
document.addEventListener('DOMContentLoaded', function() {
    // 顧客IDが存在する場合のみ（編集画面の場合）
    const customerId = document.getElementById('customerId')?.value;
    if (customerId) {
        loadUsageHistory();
        loadCastUsage();
    }
});