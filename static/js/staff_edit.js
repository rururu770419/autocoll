// スタッフ編集ページのJavaScript

document.addEventListener('DOMContentLoaded', function() {
    // ============================================
    // カラーピッカーとテキストの同期
    // ============================================
    const colorPicker = document.getElementById('colorPicker');
    const colorCode = document.getElementById('colorCode');

    if (colorPicker && colorCode) {
        // カラーピッカーが変更されたらテキストに反映
        colorPicker.addEventListener('input', (e) => {
            colorCode.value = e.target.value.toUpperCase();
        });

        // テキストが変更されたらカラーピッカーに反映
        colorCode.addEventListener('input', (e) => {
            if (/^#[0-9A-Fa-f]{6}$/.test(e.target.value)) {
                colorPicker.value = e.target.value;
            }
        });
    }

    // ============================================
    // 権限ボタンの切り替え
    // ============================================
    document.querySelectorAll('.permission-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // 全ボタンの active を解除
            document.querySelectorAll('.permission-btn').forEach(b =>
                b.classList.remove('permission-btn-active'));

            // クリックされたボタンを active に
            this.classList.add('permission-btn-active');

            // hidden input に値を設定
            document.querySelector('input[name="role"]').value =
                this.dataset.permission;
        });
    });

    // ============================================
    // フラッシュメッセージの自動非表示と閉じるボタン
    // ============================================
    document.querySelectorAll('.cast-edit-flash').forEach(function(flash) {
        // 5秒後に自動で消える
        setTimeout(function() {
            flash.style.opacity = '0';
            setTimeout(function() {
                flash.remove();
            }, 300);
        }, 5000);
    });
});
