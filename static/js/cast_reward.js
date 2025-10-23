/**
 * キャスト報酬一覧ページ用JavaScript
 */

// ============================================
// グローバル変数
// ============================================

let currentViewDate = new Date(currentDate);
let calendarYear = currentViewDate.getFullYear();
let calendarMonth = currentViewDate.getMonth() + 1;
let monthlyRewards = {}; // 月間の日別報酬（キャッシュ）
let monthlySummary = {}; // 月間サマリー（キャッシュ）

// ============================================
// 日付ナビゲーション
// ============================================

/**
 * 日付を変更（前日・翌日）
 */
function changeDate(days) {
    const newDate = new Date(currentViewDate);
    newDate.setDate(newDate.getDate() + days);

    const dateStr = formatDateForURL(newDate);
    window.location.href = `/${store}/cast/reward_list?date=${dateStr}`;
}

/**
 * 今日に戻る
 */
function goToToday() {
    window.location.href = `/${store}/cast/reward_list`;
}

/**
 * URLパラメータ用の日付フォーマット
 */
function formatDateForURL(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}


// ============================================
// カレンダーモーダル
// ============================================

/**
 * カレンダーモーダルを開く
 */
async function openCalendarModal() {
    const modal = document.getElementById('calendarModal');
    if (!modal) return;

    // 現在表示中の月に設定
    calendarYear = currentViewDate.getFullYear();
    calendarMonth = currentViewDate.getMonth() + 1;

    // 月間報酬データを取得
    await loadMonthlyRewards(calendarYear, calendarMonth);

    // カレンダーを描画
    renderCalendar();

    // モーダル表示
    modal.classList.add('cr-modal-show');
    document.body.style.overflow = 'hidden';
}

/**
 * カレンダーモーダルを閉じる
 */
function closeCalendarModal() {
    const modal = document.getElementById('calendarModal');
    if (!modal) return;

    modal.classList.remove('cr-modal-show');
    document.body.style.overflow = 'auto';
}

/**
 * 月を変更
 */
async function changeMonth(months) {
    calendarMonth += months;

    if (calendarMonth < 1) {
        calendarMonth = 12;
        calendarYear--;
    } else if (calendarMonth > 12) {
        calendarMonth = 1;
        calendarYear++;
    }

    await loadMonthlyRewards(calendarYear, calendarMonth);
    renderCalendar();
}

/**
 * 月間報酬データをAPIから取得
 */
async function loadMonthlyRewards(year, month) {
    try {
        const response = await fetch(`/${store}/cast/api/monthly_rewards?year=${year}&month=${month}`);
        const data = await response.json();

        if (data.success) {
            monthlySummary = data.summary || {};
            monthlyRewards = data.daily_rewards || {};

            console.log('[DEBUG] 月間報酬取得成功:', monthlySummary, monthlyRewards);

            // サマリーを更新
            updateMonthlySummary();
        } else {
            console.error('[ERROR] 月間報酬取得失敗:', data.error);
            monthlyRewards = {};
            monthlySummary = {};
        }
    } catch (error) {
        console.error('[ERROR] API通信エラー:', error);
        monthlyRewards = {};
        monthlySummary = {};
    }
}

/**
 * 月間サマリーを更新
 */
function updateMonthlySummary() {
    document.getElementById('monthlyReward').textContent =
        '¥' + (monthlySummary.total_reward || 0).toLocaleString();
    document.getElementById('workDays').textContent =
        (monthlySummary.work_days || 0) + '日';
    document.getElementById('totalReservations').textContent =
        (monthlySummary.total_reservations || 0) + '件';
}

/**
 * 日別報酬リストを描画
 */
function renderCalendar() {
    const dailyList = document.getElementById('dailyList');
    const monthTitle = document.getElementById('monthTitle');

    if (!dailyList || !monthTitle) return;

    monthTitle.textContent = `${calendarYear}年${calendarMonth}月`;
    dailyList.innerHTML = '';

    // 報酬がある日のみを抽出してソート
    const rewardDays = [];
    for (const [dateStr, reward] of Object.entries(monthlyRewards)) {
        if (reward > 0) {
            const date = new Date(dateStr);
            // 選択中の月のみを表示
            if (date.getFullYear() === calendarYear && date.getMonth() + 1 === calendarMonth) {
                rewardDays.push({
                    dateStr: dateStr,
                    date: date,
                    reward: reward
                });
            }
        }
    }

    // 日付順にソート
    rewardDays.sort((a, b) => a.date - b.date);

    // リストアイテムを生成
    if (rewardDays.length === 0) {
        dailyList.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">この月の報酬はありません</div>';
        return;
    }

    rewardDays.forEach(item => {
        const dayItem = document.createElement('div');
        dayItem.className = 'crw-daily-item';

        // 日付フォーマット（10月1日(日)）
        const month = item.date.getMonth() + 1;
        const day = item.date.getDate();
        const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
        const weekday = weekdays[item.date.getDay()];
        const dateText = `${month}月${day}日(${weekday})`;

        // 日付要素
        const dateEl = document.createElement('span');
        dateEl.className = 'crw-daily-date';
        dateEl.textContent = dateText;

        // 報酬額要素（カンマ区切り）
        const amountEl = document.createElement('span');
        amountEl.className = 'crw-daily-amount';
        amountEl.textContent = `¥${item.reward.toLocaleString()}`;

        dayItem.appendChild(dateEl);
        dayItem.appendChild(amountEl);

        // クリックイベント
        dayItem.addEventListener('click', () => {
            window.location.href = `/${store}/cast/reward_list?date=${item.dateStr}`;
        });

        dailyList.appendChild(dayItem);
    });
}

// ============================================
// 初期化
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('[INFO] キャスト報酬一覧ページ初期化');

    // ESCキーでモーダルを閉じる
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeCalendarModal();
        }
    });
});
