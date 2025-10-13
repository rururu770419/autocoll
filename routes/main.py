from flask import Blueprint

# 各機能モジュールからインポート
from .auth import index, login, logout
# スタッフ関連に新しい関数を追加（get_line_bot_idを追加）
from .staff import register_staff, edit_staff, delete_staff, new_staff, save_staff, get_line_bot_info, get_line_bot_id
# キャスト関連にsave_cast_ng_settingsを追加
from .cast import register_cast, edit_cast, delete_cast, cast_management, save_cast_ng_settings
# コース関連（move_course_up, move_course_downを追加）
from .course import register_course, edit_course, delete_course, move_course_up, move_course_down
from .hotel import register_hotel, edit_hotel, delete_hotel, register_category, register_area, move_hotel_up_route, move_hotel_down_route
from .pickup import pickup_register
# ★ dashboard関連のインポートを修正（get_record_dates, get_course_dataを追加）
from .dashboard import (
    store_home, 
    update_record, 
    delete_record, 
    save_all, 
    dashboard_data, 
    check_change_status, 
    update_announcement_endpoint,
    get_record_dates,      # ★ 追加
    get_course_data        # ★ 追加
)
from .money import money_management, delete_money_record, register_change, check_change_registration
from .option import options, register_option, edit_option, update_option_route, delete_option_route, move_option_up_route, move_option_down_route
# 割引管理を追加
from .discount import discount_management, register_discount_page, edit_discount_page, delete_discount_route
# 評価管理を追加（修正版）
from .rating import (
    rating_items_management_view, 
    rating_item_registration_view, 
    rating_item_edit_view,
    add_rating_item_endpoint,
    update_rating_item_endpoint,
    delete_rating_item_endpoint,
    move_item_order_endpoint
)
# 顧客管理を追加
from .customer import (
    customer_management_view,
    customer_registration_view,
    customer_edit_view,
    api_get_customers_endpoint,
    api_get_customer_endpoint,
    api_add_customer_endpoint,
    api_update_customer_endpoint,
    api_delete_customer_endpoint,
    api_search_customers_endpoint
)
# 顧客情報設定APIを追加
from .settings_customer_api import (
    api_get_customer_fields,
    api_get_customer_field_options_for_edit,
    api_update_category_label,
    api_add_field_option,
    api_update_field_option,
    api_toggle_field_option_visibility,
    api_delete_field_option,
    api_move_field_option
)


# メインのBlueprint作成
main_routes = Blueprint('main_routes', __name__)

# 認証関連
main_routes.add_url_rule('/<store>/', 'index', index, methods=['GET'])
main_routes.add_url_rule('/<store>/login', 'login', login, methods=['POST'])
main_routes.add_url_rule('/<store>/logout', 'logout', logout, methods=['GET'])

# スタッフ管理（既存のルート）
main_routes.add_url_rule('/<store>/register_staff', 'register_staff', register_staff, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_staff/<login_id>', 'edit_staff', edit_staff, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_staff/<login_id>', 'delete_staff', delete_staff, methods=['GET', 'POST'])

# スタッフ管理（新しいルート）
main_routes.add_url_rule('/<store>/staff/new', 'new_staff', new_staff, methods=['GET'])
main_routes.add_url_rule('/<store>/staff/save', 'save_staff', save_staff, methods=['POST'])
main_routes.add_url_rule('/<store>/staff/edit/<int:user_id>', 'edit_staff_by_id', edit_staff, methods=['GET'])
main_routes.add_url_rule('/<store>/staff/delete/<int:user_id>', 'delete_staff_by_id', delete_staff, methods=['POST'])
main_routes.add_url_rule('/<store>/api/line/info', 'get_line_bot_info', get_line_bot_info, methods=['GET'])

# キャスト管理
main_routes.add_url_rule('/<store>/cast_management', 'cast_management', cast_management, methods=['GET'])
main_routes.add_url_rule('/<store>/register_cast', 'register_cast', register_cast, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_cast/<int:cast_id>', 'edit_cast', edit_cast, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_cast/<int:cast_id>', 'delete_cast', delete_cast, methods=['GET', 'POST'])
# キャストNG設定保存（新規追加）
main_routes.add_url_rule('/<store>/cast/<int:cast_id>/ng-settings', 'save_cast_ng_settings', save_cast_ng_settings, methods=['POST'])

# コース管理（既存のルート + 並び順変更を追加）
main_routes.add_url_rule('/<store>/register_course', 'register_course', register_course, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_course/<int:course_id>', 'edit_course', edit_course, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_course/<int:course_id>', 'delete_course', delete_course, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/move_course_up/<int:course_id>', 'move_course_up', move_course_up, methods=['GET'])
main_routes.add_url_rule('/<store>/move_course_down/<int:course_id>', 'move_course_down', move_course_down, methods=['GET'])

# カテゴリ・エリア管理
main_routes.add_url_rule('/<store>/register_category', 'register_category', register_category, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/register_area', 'register_area', register_area, methods=['GET', 'POST'])

# ホテル管理
main_routes.add_url_rule('/<store>/hotel_management', 'register_hotel', register_hotel, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_hotel/<int:hotel_id>', 'edit_hotel', edit_hotel, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_hotel/<int:hotel_id>', 'delete_hotel', delete_hotel, methods=['POST'])
main_routes.add_url_rule('/<store>/move_hotel_up/<int:hotel_id>', 'move_hotel_up', move_hotel_up_route, methods=['GET'])
main_routes.add_url_rule('/<store>/move_hotel_down/<int:hotel_id>', 'move_hotel_down', move_hotel_down_route, methods=['GET'])

# 送迎管理
main_routes.add_url_rule('/<store>/pickup_register', 'pickup_register', pickup_register, methods=['GET', 'POST'])

# 金銭管理
main_routes.add_url_rule('/<store>/money_management', 'money_management', money_management, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_money_record/<int:record_id>', 'delete_money_record', delete_money_record, methods=['POST'])
main_routes.add_url_rule('/<store>/register_change', 'register_change', register_change, methods=['POST'])
main_routes.add_url_rule('/<store>/dashboard/check_change', 'check_change_status', check_change_status, methods=['POST'])
main_routes.add_url_rule('/<store>/dashboard_data', 'dashboard_data', dashboard_data, methods=['GET'])
main_routes.add_url_rule('/<store>/check_change_registration', 'check_change_registration', check_change_registration, methods=['POST'])

# ダッシュボード
main_routes.add_url_rule('/<store>/dashboard', 'store_home', store_home, methods=['GET'])
main_routes.add_url_rule('/<store>/dashboard/update_record', 'update_record', update_record, methods=['POST'])
main_routes.add_url_rule('/<store>/dashboard/delete_record', 'delete_record', delete_record, methods=['POST'])
main_routes.add_url_rule('/<store>/dashboard/save_all', 'save_all', save_all, methods=['POST'])
main_routes.add_url_rule('/<store>/dashboard/update_announcement', 'update_announcement_endpoint', update_announcement_endpoint, methods=['POST'])
# ★ カレンダー機能用エンドポイント（新規追加）
main_routes.add_url_rule('/<store>/dashboard/get_record_dates', 'get_record_dates', get_record_dates, methods=['POST'])
# ★ 時間自動計算機能用エンドポイント（新規追加）
main_routes.add_url_rule('/<store>/dashboard/get_course_data', 'get_course_data', get_course_data, methods=['GET'])

# オプション管理
main_routes.add_url_rule('/<store>/options', 'options', options, methods=['GET'])
main_routes.add_url_rule('/<store>/options/register', 'register_option', register_option, methods=['POST'])
main_routes.add_url_rule('/<store>/options/<int:option_id>/edit', 'edit_option', edit_option, methods=['GET'])
main_routes.add_url_rule('/<store>/options/<int:option_id>/update', 'update_option_route', update_option_route, methods=['POST'])
main_routes.add_url_rule('/<store>/options/<int:option_id>/delete', 'delete_option_route', delete_option_route, methods=['GET'])
main_routes.add_url_rule('/<store>/options/<int:option_id>/move_up', 'move_option_up_route', move_option_up_route, methods=['GET'])
main_routes.add_url_rule('/<store>/options/<int:option_id>/move_down', 'move_option_down_route', move_option_down_route, methods=['GET'])

# 割引管理
main_routes.add_url_rule('/<store>/discount_management', 'discount_management', discount_management, methods=['GET'])
main_routes.add_url_rule('/<store>/register_discount', 'register_discount', register_discount_page, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_discount/<int:discount_id>', 'edit_discount', edit_discount_page, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_discount/<int:discount_id>', 'delete_discount', delete_discount_route, methods=['GET'])

# 評価項目マスタ管理（画面）
main_routes.add_url_rule('/<store>/rating_items_management', 'rating_items_management', rating_items_management_view, methods=['GET'])
main_routes.add_url_rule('/<store>/rating_item_registration', 'rating_item_registration', rating_item_registration_view, methods=['GET'])
main_routes.add_url_rule('/<store>/rating_item_edit/<int:item_id>', 'edit_rating_item', rating_item_edit_view, methods=['GET'])

# 評価項目マスタ管理（API）
main_routes.add_url_rule('/<store>/api/rating_item/add', 'add_rating_item', add_rating_item_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/rating_item/update', 'update_rating_item', update_rating_item_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/rating_item/delete', 'delete_rating_item', delete_rating_item_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/rating_item/move', 'move_item_order', move_item_order_endpoint, methods=['POST'])

# 顧客管理（画面）
main_routes.add_url_rule('/<store>/customer_management', 'customer_management', customer_management_view, methods=['GET'])
main_routes.add_url_rule('/<store>/customer_registration', 'customer_registration', customer_registration_view, methods=['GET'])
main_routes.add_url_rule('/<store>/customer_edit/<int:customer_id>', 'edit_customer', customer_edit_view, methods=['GET'])

# 顧客管理（API）A
main_routes.add_url_rule('/<store>/api/customers', 'api_get_customers', api_get_customers_endpoint, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customers/<int:customer_id>', 'api_get_customer', api_get_customer_endpoint, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customers/add', 'api_add_customer', api_add_customer_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customers/<int:customer_id>/update', 'api_update_customer', api_update_customer_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customers/<int:customer_id>/delete', 'api_delete_customer', api_delete_customer_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customers/search', 'api_search_customers', api_search_customers_endpoint, methods=['GET'])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 顧客情報設定API（新規追加）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
main_routes.add_url_rule('/<store>/api/customer_fields', 'api_get_customer_fields', api_get_customer_fields, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customer_fields/options', 'api_get_customer_field_options', api_get_customer_field_options_for_edit, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customer_fields/category', 'api_update_category_label', api_update_category_label, methods=['PUT'])
main_routes.add_url_rule('/<store>/api/customer_fields/option', 'api_add_field_option', api_add_field_option, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>', 'api_update_field_option', api_update_field_option, methods=['PUT'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>/visibility', 'api_toggle_field_option_visibility', api_toggle_field_option_visibility, methods=['PUT'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>', 'api_delete_field_option', api_delete_field_option, methods=['DELETE'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>/move', 'api_move_field_option', api_move_field_option, methods=['PUT'])