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
        ? `/${store}/api/course_category/update`
        : `/${store}/api/course_category/add`;
    
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
    
    document.getElementById('category-edit-message').style.display = 'none';
}

function editCategory(categoryId, categoryName, isActive) {
    editingCategoryId = categoryId;
    document.getElementById('category_name').value = categoryName;
    document.getElementById('category_is_active').checked = isActive;
    
    const submitBtn = document.getElementById('category-submit-btn');
    submitBtn.textContent = '更新';
    submitBtn.style.backgroundColor = '#e91e63';
    
    document.getElementById('category-edit-message').style.display = 'block';
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function deleteCategory(categoryId, categoryName) {
    if (!confirm(`「${categoryName}」を削除してもよろしいですか？\n\n※このカテゴリを使用しているコースがある場合は削除できません。`)) {
        return;
    }
    
    fetch(`/${store}/api/course_category/delete`, {
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
    window.location.href = `/${store}/move_category_up/${categoryId}`;
}

function moveCategoryDown(categoryId) {
    window.location.href = `/${store}/move_category_down/${categoryId}`;
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
    
    const url = `/${store}/api/course/update`;
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
    
    window.location.href = `/${store}/delete_course/${courseId}`;
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

// 初期化処理
function initCourseManagement(successMessage, errorMessage) {
    if (successMessage) {
        showMessage(successMessage, true);
    } else if (errorMessage) {
        showMessage(errorMessage, false);
    }
}