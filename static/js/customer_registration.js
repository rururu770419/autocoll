// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 顧客登録画面スクリプト
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 初期化
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

document.addEventListener('DOMContentLoaded', function() {
    console.log('Customer registration page initialized');

    // 選択肢を読み込む
    loadCustomerFieldOptions();

    // ポイント操作理由を読み込む
    loadPointReasons();

    // フォーム送信イベント
    document.getElementById('customerForm').addEventListener('submit', handleFormSubmit);

    // 年齢自動計算
    const birthdayInput = document.getElementById('birthday');
    if (birthdayInput) {
        birthdayInput.addEventListener('change', calculateAge);
    }

    // 入力制限を設定
    setupInputRestrictions();

    // セレクトボックスの変更イベント（色を反映）
    setupSelectChangeEvents();

    // 🆕 コメント欄の自動リサイズ機能
    setupTextareaAutoResize();
});

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
        const response = await fetch(`/${store}/api/customers/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('顧客を登録しました', 'success');
            
            // 編集ページにリダイレクト
            setTimeout(() => {
                window.location.href = `/${store}/customer_edit/${result.customer_id}`;
            }, 1000);
        } else {
            showMessage(result.message || '登録に失敗しました', 'error');
        }
    } catch (error) {
        console.error('登録エラー:', error);
        showMessage('顧客の登録に失敗しました: ' + error.message, 'error');
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