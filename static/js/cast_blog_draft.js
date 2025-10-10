/**
 * キャストマイページ - ブログ下書き機能用JavaScript
 * TinyMCEエディタ、自動保存、HTMLコピー機能
 */

let editor = null;
let autosaveTimer = null;
let draftId = null;
let storeCode = null;

/**
 * 初期化
 */
function initBlogDraft(config) {
    draftId = config.draftId || null;
    storeCode = config.storeCode || 'nagano';
    
    if (config.mode === 'edit') {
        initTinyMCE();
    }
}

/**
 * TinyMCE初期化
 */
function initTinyMCE() {
    tinymce.init({
        selector: '#content',
        height: 500,
        language: 'ja',
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'media', 'table', 'code', 'help', 'wordcount'
        ],
        toolbar: 'undo redo | blocks | ' +
            'bold italic forecolor | alignleft aligncenter ' +
            'alignright alignjustify | bullist numlist outdent indent | ' +
            'image link | removeformat | code | help',
        images_upload_url: `/${storeCode}/cast/blog/upload-image`,
        automatic_uploads: true,
        file_picker_types: 'image',
        images_upload_handler: handleImageUpload,
        setup: function(ed) {
            editor = ed;
            
            // エディタ準備完了後に自動保存開始
            ed.on('init', function() {
                if (draftId) {
                    startAutosave();
                }
            });
        },
        content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.6; }'
    });
}

/**
 * 画像アップロード処理
 */
function handleImageUpload(blobInfo, success, failure) {
    const formData = new FormData();
    formData.append('file', blobInfo.blob(), blobInfo.filename());

    fetch(`/${storeCode}/cast/blog/upload-image`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.location) {
            success(data.location);
        } else {
            failure('画像のアップロードに失敗しました: ' + (data.error || '不明なエラー'));
        }
    })
    .catch(error => {
        failure('画像のアップロードに失敗しました: ' + error);
    });
}

/**
 * 自動保存開始
 */
function startAutosave() {
    if (autosaveTimer) {
        clearInterval(autosaveTimer);
    }
    
    autosaveTimer = setInterval(function() {
        autosave();
    }, 5000); // 5秒ごと
}

/**
 * 自動保存実行
 */
function autosave() {
    if (!editor) return;
    
    const title = document.getElementById('title').value;
    const content = editor.getContent();
    
    const statusEl = document.getElementById('autosave-status');
    if (statusEl) {
        statusEl.textContent = '保存中...';
        statusEl.style.color = '#f59e0b';
    }
    
    fetch(`/${storeCode}/cast/blog-drafts/autosave`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            draft_id: draftId,
            title: title,
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 新規作成の場合、draft_idを保存
            if (!draftId && data.draft_id) {
                draftId = data.draft_id;
                // URLを更新（リロードなし）
                const newUrl = `/${storeCode}/cast/blog-drafts/${draftId}/edit`;
                window.history.pushState({}, '', newUrl);
                
                // 自動保存開始
                startAutosave();
            }
            
            if (statusEl) {
                statusEl.textContent = '✓ ' + new Date().toLocaleTimeString() + ' に保存しました';
                statusEl.style.color = '#10b981';
            }
        } else {
            if (statusEl) {
                statusEl.textContent = '✗ 保存に失敗しました';
                statusEl.style.color = '#ef4444';
            }
        }
    })
    .catch(error => {
        console.error('自動保存エラー:', error);
        if (statusEl) {
            statusEl.textContent = '✗ 保存エラー';
            statusEl.style.color = '#ef4444';
        }
    });
}

/**
 * HTMLをコピー
 */
function copyHTML() {
    if (!editor) {
        alert('エディタが準備できていません');
        return;
    }
    
    const html = editor.getContent();
    
    if (!html || html.trim() === '') {
        alert('コピーする内容がありません');
        return;
    }
    
    // クリップボードにコピー
    navigator.clipboard.writeText(html).then(function() {
        alert('✅ HTMLをコピーしました！\nシティヘブンのブログ投稿画面に貼り付けてください。');
    }).catch(function(error) {
        console.error('コピー失敗:', error);
        
        // フォールバック: テキストエリアを使ったコピー
        const textarea = document.createElement('textarea');
        textarea.value = html;
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            alert('✅ HTMLをコピーしました！\nシティヘブンのブログ投稿画面に貼り付けてください。');
        } catch (err) {
            alert('❌ コピーに失敗しました。手動でコピーしてください。\n\n' + html);
        }
        
        document.body.removeChild(textarea);
    });
}

/**
 * 下書き削除（一覧ページ用）
 */
function deleteDraft(draftId, title) {
    if (!confirm(`「${title}」を削除してもよろしいですか？`)) {
        return;
    }
    
    fetch(`/${storeCode}/cast/blog-drafts/${draftId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('下書きを削除しました');
            location.reload();
        } else {
            alert('削除に失敗しました: ' + data.error);
        }
    })
    .catch(error => {
        alert('エラーが発生しました: ' + error);
    });
}

/**
 * ページ離脱前の確認
 */
window.addEventListener('beforeunload', function(e) {
    if (editor && editor.isDirty()) {
        e.preventDefault();
        e.returnValue = '';
    }
});

/**
 * フォーム送信前に自動保存を停止
 */
document.addEventListener('DOMContentLoaded', function() {
    const blogForm = document.getElementById('blog-form');
    if (blogForm) {
        blogForm.addEventListener('submit', function() {
            if (autosaveTimer) {
                clearInterval(autosaveTimer);
            }
        });
    }
});