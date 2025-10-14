{% extends "base.html" %}

{% block extra_head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/course.css') }}">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
{% endblock %}

{% block title %}コース管理{% endblock %}

{% block content %}
<div class="course-container">
    <!-- メッセージ表示エリア -->
    <div id="course-message-area"></div>

    <!-- ========================================
         カテゴリ管理（2列レイアウト 40:60）
         ======================================== -->
    <h2 class="course-section-title">カテゴリ登録</h2>
    
    <div class="course-two-column-layout">
        <!-- 左：カテゴリ登録フォーム（40%） -->
        <div class="course-form-card">
            <form id="categoryForm" onsubmit="submitCategoryForm(event); return false;">
                <div class="course-form-group">
                    <label class="course-form-label">カテゴリ名 <span class="course-required">*</span></label>
                    <input type="text" 
                           id="category_name"
                           name="category_name"
                           class="course-form-input" 
                           placeholder="例：VIPコース" 
                           required>
                    <div id="category-edit-message" class="course-edit-message" style="display: none;">
                        💡 編集モード：内容を変更して更新ボタンを押してください
                    </div>
                </div>

                <div class="course-form-group">
                    <label class="course-form-label">状態</label>
                    <div class="course-toggle-wrapper">
                        <span class="course-toggle-label">無効</span>
                        <label class="course-toggle-switch">
                            <input type="checkbox" 
                                   id="category_is_active"
                                   name="category_is_active"
                                   class="course-toggle-checkbox" 
                                   checked>
                            <span class="course-toggle-slider"></span>
                        </label>
                        <span class="course-toggle-label">有効</span>
                    </div>
                </div>

                <div class="course-form-buttons">
                    <button type="button" 
                            onclick="resetCategoryForm()" 
                            class="course-btn-reset">
                        リセット
                    </button>
                    <button type="submit" class="course-btn-submit" id="category-submit-btn">
                        登録
                    </button>
                </div>
            </form>
        </div>

        <!-- 右：カテゴリ一覧（60%） -->
        <div class="course-list-card">
            <table class="course-table">
                <thead>
                    <tr>
                        <th class="course-th-sort">並び順</th>
                        <th class="course-th-name">カテゴリ名</th>
                        <th class="course-th-status">状態</th>
                        <th class="course-th-edit">編集</th>
                        <th class="course-th-delete">削除</th>
                    </tr>
                </thead>
                <tbody>
                    {% if categories %}
                        {% for category in categories %}
                        <tr>
                            <td class="course-td-center">
                                <button onclick="moveCategoryUp({{ category['category_id'] }})" class="course-sort-btn {% if loop.first %}course-sort-btn-disabled{% endif %}" {% if loop.first %}disabled{% endif %} title="上に移動"><i class="fas fa-chevron-up"></i></button><button onclick="moveCategoryDown({{ category['category_id'] }})" class="course-sort-btn {% if loop.last %}course-sort-btn-disabled{% endif %}" {% if loop.last %}disabled{% endif %} title="下に移動"><i class="fas fa-chevron-down"></i></button>
                            </td>
                            <td class="course-td-center">{{ category['category_name'] }}</td>
                            <td class="course-td-center">
                                {% if category['is_active'] %}
                                    <span class="course-status-active">有効</span>
                                {% else %}
                                    <span class="course-status-inactive">無効</span>
                                {% endif %}
                            </td>
                            <td class="course-td-center">
                                <button onclick="editCategory({{ category['category_id'] }}, '{{ category['category_name'] }}', {{ 'true' if category['is_active'] else 'false' }})" 
                                        class="course-action-btn">
                                    <i class="fas fa-pencil-alt course-edit-icon"></i>
                                </button>
                            </td>
                            <td class="course-td-center">
                                <button onclick="deleteCategory({{ category['category_id'] }}, '{{ category['category_name'] }}')" 
                                        class="course-action-btn">
                                    <i class="fas fa-trash-alt course-delete-icon"></i>
                                </button>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="5" class="course-td-empty">
                                カテゴリが登録されていません
                            </td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
            <div class="course-table-note">
                💡 編集ボタンを押すと、左側が編集画面になります
            </div>
        </div>
    </div>

    <!-- ========================================
         コース管理
         ======================================== -->
    <h2 class="course-section-title course-section-title-spaced">コース登録</h2>

    <div class="course-form-card">
        <form method="POST" action="{{ url_for('main_routes.course_registration', store=store) }}">
            <!-- 2列グリッド -->
            <div class="course-form-grid">
                <!-- 左列 -->
                <div>
                    <div class="course-form-group">
                        <label class="course-form-label">コース名 <span class="course-required">*</span></label>
                        <input type="text" 
                               name="course_name" 
                               class="course-form-input" 
                               placeholder="例：90分コース" 
                               required>
                    </div>

                    <div class="course-form-group">
                        <label class="course-form-label">料金 <span class="course-required">*</span></label>
                        <input type="number" 
                               name="price" 
                               class="course-form-input" 
                               placeholder="例：15000" 
                               required
                               step="1"
                               min="0">
                        <small class="course-form-hint">金額は円単位で入力してください</small>
                    </div>
                </div>

                <!-- 右列 -->
                <div>
                    <div class="course-form-group">
                        <label class="course-form-label">カテゴリ <span class="course-required">*</span></label>
                        <select name="category_id" class="course-form-input" required>
                            <option value="">選択してください</option>
                            {% for cat in categories %}
                                {% if cat['is_active'] %}
                                    <option value="{{ cat['category_id'] }}">{{ cat['category_name'] }}</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                    </div>

                    <div class="course-form-group">
                        <label class="course-form-label">時間（分） <span class="course-required">*</span></label>
                        <input type="number" 
                               name="duration_minutes" 
                               class="course-form-input" 
                               placeholder="例：90" 
                               required
                               step="1"
                               min="1">
                        <small class="course-form-hint">コースの時間を入力してください</small>
                    </div>
                </div>
            </div>

            <!-- 状態トグル（全幅） -->
            <div class="course-form-group">
                <label class="course-form-label">状態</label>
                <div class="course-toggle-wrapper">
                    <span class="course-toggle-label">無効</span>
                    <label class="course-toggle-switch">
                        <input type="checkbox" 
                               name="is_active" 
                               class="course-toggle-checkbox" 
                               checked>
                        <span class="course-toggle-slider"></span>
                    </label>
                    <span class="course-toggle-label">有効</span>
                </div>
            </div>

            <!-- ボタン -->
            <div class="course-form-buttons">
                <button type="reset" class="course-btn-reset">リセット</button>
                <button type="submit" class="course-btn-submit">登録</button>
            </div>
        </form>
    </div>

    <!-- コース一覧 -->
    <h2 class="course-section-title course-section-title-list">コース一覧</h2>

    <div class="course-list-card">
        <div class="course-table-wrapper">
            <table class="course-table">
                <thead>
                    <tr>
                        <th class="course-th-sort-course">並び順</th>
                        <th class="course-th-category">カテゴリ</th>
                        <th class="course-th-course-name">コース名</th>
                        <th class="course-th-price">料金</th>
                        <th class="course-th-time">時間</th>
                        <th class="course-th-status">状態</th>
                        <th class="course-th-edit">編集</th>
                        <th class="course-th-delete">削除</th>
                    </tr>
                </thead>
                <tbody>
                    {% if courses %}
                        {% for course in courses %}
                        <tr>
                            <td class="course-td-center">
                                <a href="{{ url_for('main_routes.move_course_up', store=store, course_id=course['course_id']) }}" class="course-sort-btn {% if loop.first %}course-sort-btn-disabled{% endif %}" {% if loop.first %}onclick="return false;"{% endif %} title="上に移動"><i class="fas fa-chevron-up"></i></a><a href="{{ url_for('main_routes.move_course_down', store=store, course_id=course['course_id']) }}" class="course-sort-btn {% if loop.last %}course-sort-btn-disabled{% endif %}" {% if loop.last %}onclick="return false;"{% endif %} title="下に移動"><i class="fas fa-chevron-down"></i></a>
                            </td>
                            <td class="course-td-center">{{ course['category_name'] or '未分類' }}</td>
                            <td class="course-td-center">{{ course['name'] }}</td>
                            <td class="course-td-right">¥{{ "{:,}".format(course['price']) }}</td>
                            <td class="course-td-center">{{ course['time_minutes'] }}分</td>
                            <td class="course-td-center">
                                {% if course['is_active'] %}
                                    <span class="course-status-active">有効</span>
                                {% else %}
                                    <span class="course-status-inactive">無効</span>
                                {% endif %}
                            </td>
                            <td class="course-td-center">
                                <button onclick="openEditCourseModal({{ course['course_id'] }}, '{{ course['name'] }}', {{ course['category_id'] }}, {{ course['price'] }}, {{ course['time_minutes'] }}, {{ 'true' if course['is_active'] else 'false' }})" 
                                        class="course-action-btn">
                                    <i class="fas fa-pencil-alt course-edit-icon"></i>
                                </button>
                            </td>
                            <td class="course-td-center">
                                <button onclick="deleteCourse({{ course['course_id'] }}, '{{ course['name'] }}')" 
                                        class="course-action-btn">
                                    <i class="fas fa-trash-alt course-delete-icon"></i>
                                </button>
                            </td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td colspan="8" class="course-td-empty">
                                コースが登録されていません
                            </td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>

<!-- コース編集モーダル -->
<div id="editCourseModal" class="course-modal">
    <div class="course-modal-dialog">
        <div class="course-modal-content">
            <div class="course-modal-header">
                <h3 class="course-modal-title">コース編集</h3>
                <button type="button" class="course-modal-close" onclick="closeEditCourseModal()">&times;</button>
            </div>
            <form id="editCourseForm" onsubmit="updateCourse(event); return false;">
                <div class="course-modal-body">
                    <input type="hidden" id="edit_course_id">
                    
                    <div class="course-modal-group">
                        <label for="edit_course_name" class="course-modal-label">コース名 <span class="course-required">*</span></label>
                        <input type="text" 
                               class="course-modal-input" 
                               id="edit_course_name" 
                               required>
                    </div>

                    <div class="course-modal-group">
                        <label for="edit_category_id" class="course-modal-label">カテゴリ <span class="course-required">*</span></label>
                        <select class="course-modal-input" 
                                id="edit_category_id" 
                                required>
                            <option value="">選択してください</option>
                            {% for cat in categories %}
                                {% if cat['is_active'] %}
                                    <option value="{{ cat['category_id'] }}">{{ cat['category_name'] }}</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                    </div>

                    <div class="course-modal-group">
                        <label for="edit_price" class="course-modal-label">料金 <span class="course-required">*</span></label>
                        <input type="number" 
                               class="course-modal-input" 
                               id="edit_price" 
                               required 
                               min="0" 
                               step="1">
                        <small class="course-modal-hint">金額は円単位で入力してください</small>
                    </div>

                    <div class="course-modal-group">
                        <label for="edit_duration_minutes" class="course-modal-label">時間（分） <span class="course-required">*</span></label>
                        <input type="number" 
                               class="course-modal-input" 
                               id="edit_duration_minutes" 
                               required 
                               min="1" 
                               step="1">
                        <small class="course-modal-hint">コースの時間を入力してください</small>
                    </div>

                    <div class="course-modal-group">
                        <label class="course-modal-label">状態</label>
                        <div class="course-toggle-wrapper">
                            <span class="course-toggle-label">無効</span>
                            <label class="course-toggle-switch">
                                <input type="checkbox" 
                                       class="course-toggle-checkbox" 
                                       id="edit_is_active">
                                <span class="course-toggle-slider"></span>
                            </label>
                            <span class="course-toggle-label">有効</span>
                        </div>
                    </div>
                </div>
                <div class="course-modal-footer">
                    <button type="button" class="course-modal-btn-cancel" onclick="closeEditCourseModal()">キャンセル</button>
                    <button type="submit" class="course-modal-btn-save">更新</button>
                </div>
            </form>
        </div>
    </div>
</div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
// ========================================
// グローバル変数
// ========================================
let editingCategoryId = null;

// ========================================
// カテゴリ管理
// ========================================
function submitCategoryForm(event) {
    event.preventDefault();
    
    const categoryName = document.getElementById('category_name').value.trim();
    const isActive = document.getElementById('category_is_active').checked;
    
    if (!categoryName) {
        showMessage('カテゴリ名を入力してください', false);
        return;
    }
    
    const url = editingCategoryId 
        ? `/{{ store }}/api/course_category/update`
        : `/{{ store }}/api/course_category/add`;
    
    const data = editingCategoryId
        ? { category_id: editingCategoryId, category_name: categoryName, is_active: isActive }
        : { category_name: categoryName, is_active: isActive };
    
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, true);
            // フォームをリセット
            resetCategoryForm();
            setTimeout(() => location.reload(), 500);
        } else {
            showMessage(data.message || data.error, false);
        }
    })
    .catch(error => {
        showMessage('エラーが発生しました', false);
    });
}

function resetCategoryForm() {
    editingCategoryId = null;
    document.getElementById('category_name').value = '';
    document.getElementById('category_is_active').checked = true;
    
    const submitBtn = document.getElementById('category-submit-btn');
    submitBtn.textContent = '登録';
    submitBtn.style.backgroundColor = '#00BCD4';
    
    // 編集モードメッセージを非表示
    document.getElementById('category-edit-message').style.display = 'none';
}

function editCategory(categoryId, categoryName, isActive) {
    editingCategoryId = categoryId;
    document.getElementById('category_name').value = categoryName;
    document.getElementById('category_is_active').checked = isActive;
    
    const submitBtn = document.getElementById('category-submit-btn');
    submitBtn.textContent = '更新';
    submitBtn.style.backgroundColor = '#e91e63';
    
    // 編集モードメッセージを表示
    document.getElementById('category-edit-message').style.display = 'block';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function deleteCategory(categoryId, categoryName) {
    if (!confirm(`「${categoryName}」を削除してもよろしいですか？\n\n※このカテゴリを使用しているコースがある場合は削除できません。`)) {
        return;
    }
    
    fetch(`/{{ store }}/api/course_category/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_id: categoryId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, true);
            setTimeout(() => location.reload(), 500);
        } else {
            showMessage(data.message || data.error, false);
        }
    })
    .catch(error => {
        showMessage('削除中にエラーが発生しました', false);
    });
}

function moveCategoryUp(categoryId) {
    window.location.href = `/{{ store }}/move_category_up/${categoryId}`;
}

function moveCategoryDown(categoryId) {
    window.location.href = `/{{ store }}/move_category_down/${categoryId}`;
}


// ========================================
// コース編集モーダル
// ========================================
function openEditCourseModal(courseId, courseName, categoryId, price, timeMinutes, isActive) {
    document.getElementById('edit_course_id').value = courseId;
    document.getElementById('edit_course_name').value = courseName;
    document.getElementById('edit_category_id').value = categoryId;
    document.getElementById('edit_price').value = price;
    document.getElementById('edit_duration_minutes').value = timeMinutes;
    document.getElementById('edit_is_active').checked = isActive;
    
    const modal = document.getElementById('editCourseModal');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeEditCourseModal() {
    const modal = document.getElementById('editCourseModal');
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

function updateCourse(event) {
    event.preventDefault();
    
    const courseId = document.getElementById('edit_course_id').value;
    const courseName = document.getElementById('edit_course_name').value.trim();
    const categoryId = document.getElementById('edit_category_id').value;
    const price = document.getElementById('edit_price').value;
    const durationMinutes = document.getElementById('edit_duration_minutes').value;
    const isActive = document.getElementById('edit_is_active').checked;
    
    if (!courseName || !categoryId || !price || !durationMinutes) {
        showMessage('全ての必須項目を入力してください', false);
        return;
    }
    
    const url = `/{{ store }}/api/course/update`;
    const data = {
        course_id: courseId,
        course_name: courseName,
        category_id: parseInt(categoryId),
        price: parseInt(price),
        duration_minutes: parseInt(durationMinutes),
        is_active: isActive
    };
    
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(data.message, true);
            closeEditCourseModal();
            setTimeout(() => location.reload(), 500);
        } else {
            showMessage(data.message || data.error, false);
        }
    })
    .catch(error => {
        showMessage('エラーが発生しました', false);
    });
}

// モーダル外クリックで閉じる
window.addEventListener('click', function(event) {
    const modal = document.getElementById('editCourseModal');
    if (event.target === modal) {
        closeEditCourseModal();
    }
});

// ========================================
// コース管理
// ========================================
function deleteCourse(courseId, courseName) {
    if (!confirm(`「${courseName}」を削除してもよろしいですか？`)) {
        return;
    }
    
    window.location.href = `/{{ store }}/delete_course/${courseId}`;
}

// ========================================
// 共通
// ========================================
function showMessage(message, isSuccess) {
    const messageArea = document.getElementById('course-message-area');
    const alertClass = isSuccess ? 'course-alert-success' : 'course-alert-error';
    
    messageArea.innerHTML = `
        <div class="course-alert ${alertClass}">
            ${message}
        </div>
    `;
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    setTimeout(() => {
        messageArea.innerHTML = '';
    }, 3000);
}

// ページ読み込み時にメッセージを表示
document.addEventListener('DOMContentLoaded', function() {
    {% if success %}
        showMessage('{{ success }}', true);
    {% elif error %}
        showMessage('{{ error }}', false);
    {% endif %}
});
</script>
{% endblock %}