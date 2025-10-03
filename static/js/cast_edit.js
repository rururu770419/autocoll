// タブ切り替え機能
function initTabs() {
    const tabs = document.querySelectorAll('.cast-edit-tab');
    const tabContents = document.querySelectorAll('.cast-edit-tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;

            // 全てのタブとコンテンツを非アクティブに
            tabs.forEach(t => t.classList.remove('cast-edit-tab-active'));
            tabContents.forEach(content => content.classList.remove('cast-edit-tab-active'));

            // クリックされたタブと対応するコンテンツをアクティブに
            this.classList.add('cast-edit-tab-active');
            document.getElementById(`cast-edit-tab-${targetTab}`).classList.add('cast-edit-tab-active');
        });
    });
}

// 年齢自動計算機能
function initAgeCalculation() {
    const birthDateInput = document.getElementById('birth_date');
    const ageInput = document.getElementById('age');

    function calculateAge(birthDateString) {
        if (!birthDateString) return '';
        
        const today = new Date();
        const birthDate = new Date(birthDateString);
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        
        return age >= 0 ? age + '歳' : '';
    }

    if (birthDateInput && ageInput) {
        // ページ読み込み時に年齢を計算
        if (birthDateInput.value) {
            const age = calculateAge(birthDateInput.value);
            ageInput.value = age || '未設定';
        }
        
        // 生年月日変更時に年齢を再計算
        birthDateInput.addEventListener('change', function() {
            const age = calculateAge(this.value);
            ageInput.value = age || '未設定';
        });
    }
}

// ファイルアップロード機能
function initFileUpload() {
    const fileInputs = document.querySelectorAll('.cast-edit-file-input');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const maxFiles = parseInt(this.dataset.maxFiles);
            const files = Array.from(this.files);
            
            if (files.length > maxFiles) {
                alert(`最大${maxFiles}枚まで選択できます。`);
                this.value = '';
                return;
            }
            
            // ファイルサイズチェック（5MB以下）
            const maxSize = 5 * 1024 * 1024; // 5MB
            for (let file of files) {
                if (file.size > maxSize) {
                    alert(`ファイルサイズは5MB以下にしてください：${file.name}`);
                    this.value = '';
                    return;
                }
            }
            
            // プレビュー表示
            const previewContainer = this.parentElement.querySelector('.cast-edit-file-preview');
            
            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'cast-edit-file-item cast-edit-file-item-new';
                    fileItem.innerHTML = `
                        <img src="${e.target.result}" alt="プレビュー" class="cast-edit-file-thumbnail">
                        <button type="button" class="cast-edit-file-remove-new">×</button>
                        <span class="cast-edit-file-name">${file.name}</span>
                    `;
                    previewContainer.appendChild(fileItem);
                };
                reader.readAsDataURL(file);
            });
        });
    });
}

// ファイル削除機能
function initFileRemoval() {
    document.addEventListener('click', function(e) {
        // 既存ファイル削除
        if (e.target.classList.contains('cast-edit-file-remove')) {
            if (confirm('このファイルを削除しますか？')) {
                const filePath = e.target.dataset.filePath;
                const fileItem = e.target.closest('.cast-edit-file-item');
                const fileType = fileItem.closest('[id*="document"]').id.includes('id') ? 'id_documents' : 'contract_documents';
                
                // 隠しフィールドで削除対象を記録
                const deleteInput = document.createElement('input');
                deleteInput.type = 'hidden';
                deleteInput.name = 'deleted_' + fileType;
                deleteInput.value = filePath;
                document.querySelector('.cast-edit-form').appendChild(deleteInput);
                
                // プレビューから削除
                fileItem.remove();
            }
        }
        
        // 新規ファイル削除
        if (e.target.classList.contains('cast-edit-file-remove-new')) {
            const fileItem = e.target.parentElement;
            fileItem.remove();
            // 対応するfile inputをクリア
            const container = e.target.closest('.cast-edit-form-group');
            const fileInput = container.querySelector('.cast-edit-file-input');
            if (fileInput) {
                fileInput.value = '';
            }
        }
    });
}

// DOMContentLoaded時に全ての機能を初期化
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initAgeCalculation();
    initFileUpload();
    initFileRemoval();
});