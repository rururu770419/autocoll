// HTML要素を取得
const hamburger = document.querySelector('.hamburger-menu');
const navMenu = document.querySelector('.nav-menu');

// ハンバーガーメニューのクリックイベントを監視
hamburger.addEventListener('click', () => {
    // nav-menuに'active'クラスを付け外しする
    navMenu.classList.toggle('active');
});