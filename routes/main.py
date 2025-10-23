from flask import Blueprint

# 各機能モジュールからインポート
from .auth import index, login, logout
# スタッフ関連に新しい関数を追加（get_line_bot_idを追加）
from .staff import register_staff, edit_staff, delete_staff, new_staff, save_staff, get_line_bot_info, get_line_bot_id, staff_sort, staff_notification, get_staff_api
# キャスト関連（save_cast_ng_settingsを削除）
from .cast import register_cast, cast_management, get_casts_api
from .cast import edit_cast, delete_cast
# コース関連（move_course_up, move_course_down + カテゴリ管理関数を追加）
from .course import (
    course_registration,
    edit_course,
    delete_course,
    move_course_up,
    move_course_down,
    update_course_endpoint,  # コース更新API
    get_courses_api,  # コース一覧API（予約登録画面用）
    # カテゴリ管理関数
    course_category_management_view,
    course_category_registration_view,
    course_category_edit_view,
    add_category_endpoint,
    update_category_endpoint,
    delete_category_endpoint,
    move_category_up,
    move_category_down
)
from .hotel import (
    register_hotel, 
    edit_hotel, 
    delete_hotel, 
    register_category, 
    register_area, 
    move_hotel_up_route, 
    move_hotel_down_route,
    # ホテル管理種別API
    get_hotel_types_api,
    add_hotel_type_api,
    update_hotel_type_api,
    delete_hotel_type_api,
    # エリア管理API
    get_areas_api,
    add_area_api,
    update_area_api,
    delete_area_api,
    # ホテル管理API
    get_hotels_api,
    get_hotel_api,
    add_hotel_api,
    update_hotel_api,
    delete_hotel_api,
    # 並び替えAPI（追加）
    move_area_up_api,
    move_area_down_api,
    move_hotel_up_api,
    move_hotel_down_api
)
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
from .option import options, register_option, edit_option, update_option_route, delete_option_route, move_option_up_route, move_option_down_route, get_options_api
# 延長管理を追加
from .extension import (
    extension_management,
    register_extension_route,
    update_extension_route,
    delete_extension_route,
    move_extension_up_route,
    move_extension_down_route,
    get_extensions_api  # 延長一覧API（予約登録画面用）
)
# 指名管理を追加
from .nominate import (
    nominate_management,
    register_nomination_type,
    update_nomination_type_route,
    delete_nomination_type_route,
    move_nomination_type_up_route,
    move_nomination_type_down_route,
    get_nomination_types_api  # 指名種類一覧API（予約登録画面用）
)
# 割引管理を追加
from .discount import (
    discount_management, 
    get_discounts_api,
    get_discount_api,
    register_discount_api,
    update_discount_api,
    delete_discount_api,
    move_discount_api
)
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
    api_search_customers_endpoint,
    get_usage_history_api,
    get_cast_usage_api
)
# ポイント履歴を追加
from .point import point_history_view
# ポイント設定を追加
from .point_settings import (
    point_settings_view,
    point_settings_save,
    add_point_reason_endpoint,
    update_point_reason_endpoint,
    delete_point_reason_endpoint,
    move_point_reason_up_endpoint,
    move_point_reason_down_endpoint,
    get_point_reasons_api,
    calculate_reservation_points_api,
    get_member_types_api
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
main_routes.add_url_rule('/<store>/staff/sort', 'staff_sort', staff_sort, methods=['POST'])
main_routes.add_url_rule('/<store>/staff/notification', 'staff_notification', staff_notification, methods=['POST'])
# API: スタッフ一覧取得（予約登録画面用）
main_routes.add_url_rule('/<store>/staff/api', 'get_staff_api', get_staff_api, methods=['GET'])

# キャスト管理
main_routes.add_url_rule('/<store>/cast_management', 'cast_management', cast_management, methods=['GET'])
main_routes.add_url_rule('/<store>/register_cast', 'register_cast', register_cast, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_cast/<int:cast_id>', 'edit_cast', edit_cast, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_cast/<int:cast_id>', 'delete_cast', delete_cast, methods=['GET'])
# API: キャスト一覧取得（予約登録画面用）
main_routes.add_url_rule('/<store>/casts/api', 'get_casts_api', get_casts_api, methods=['GET'])

# コース管理（既存のルート + 並び順変更を追加）
main_routes.add_url_rule('/<store>/course_registration', 'course_registration', course_registration, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_course/<int:course_id>', 'edit_course', edit_course, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_course/<int:course_id>', 'delete_course', delete_course, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/move_course_up/<int:course_id>', 'move_course_up', move_course_up, methods=['GET'])
main_routes.add_url_rule('/<store>/move_course_down/<int:course_id>', 'move_course_down', move_course_down, methods=['GET'])
# API: コース更新
main_routes.add_url_rule('/<store>/api/course/update', 'update_course_endpoint', update_course_endpoint, methods=['POST'])
# API: コース一覧取得（予約登録画面用）
main_routes.add_url_rule('/<store>/courses/api', 'get_courses_api', get_courses_api, methods=['GET'])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# コースカテゴリ管理（新規追加）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# カテゴリ管理一覧
main_routes.add_url_rule('/<store>/course_category_management', 'course_category_management', course_category_management_view, methods=['GET'])
# カテゴリ登録ページ
main_routes.add_url_rule('/<store>/course_category_registration', 'course_category_registration', course_category_registration_view, methods=['GET'])
# カテゴリ編集ページ
main_routes.add_url_rule('/<store>/course_category_edit', 'course_category_edit', course_category_edit_view, methods=['GET'])
# API: カテゴリ追加
main_routes.add_url_rule('/<store>/api/course_category/add', 'api_add_course_category', add_category_endpoint, methods=['POST'])
# API: カテゴリ更新
main_routes.add_url_rule('/<store>/api/course_category/update', 'api_update_course_category', update_category_endpoint, methods=['POST'])
# API: カテゴリ削除
main_routes.add_url_rule('/<store>/api/course_category/delete', 'api_delete_course_category', delete_category_endpoint, methods=['POST'])
# カテゴリ並び順変更（上）
main_routes.add_url_rule('/<store>/move_category_up/<int:category_id>', 'move_category_up_route', move_category_up, methods=['GET'])
# カテゴリ並び順変更（下）
main_routes.add_url_rule('/<store>/move_category_down/<int:category_id>', 'move_category_down_route', move_category_down, methods=['GET'])

# カテゴリ・エリア管理
main_routes.add_url_rule('/<store>/register_category', 'register_category', register_category, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/register_area', 'register_area', register_area, methods=['GET', 'POST'])

# ホテル管理
main_routes.add_url_rule('/<store>/hotel_management', 'register_hotel', register_hotel, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/edit_hotel/<int:hotel_id>', 'edit_hotel', edit_hotel, methods=['GET', 'POST'])
main_routes.add_url_rule('/<store>/delete_hotel/<int:hotel_id>', 'delete_hotel', delete_hotel, methods=['POST'])
main_routes.add_url_rule('/<store>/move_hotel_up/<int:hotel_id>', 'move_hotel_up', move_hotel_up_route, methods=['GET'])
main_routes.add_url_rule('/<store>/move_hotel_down/<int:hotel_id>', 'move_hotel_down', move_hotel_down_route, methods=['GET'])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ホテル管理API（新規追加）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ホテル管理種別API
main_routes.add_url_rule('/<store>/hotel-management/hotel_types', 'get_hotel_types_api', get_hotel_types_api, methods=['GET'])
main_routes.add_url_rule('/<store>/hotel-management/hotel_types', 'add_hotel_type_api', add_hotel_type_api, methods=['POST'])
main_routes.add_url_rule('/<store>/hotel-management/hotel_types/<int:id>', 'update_hotel_type_api', update_hotel_type_api, methods=['PUT'])
main_routes.add_url_rule('/<store>/hotel-management/hotel_types/<int:id>', 'delete_hotel_type_api', delete_hotel_type_api, methods=['DELETE'])

# エリア管理API
main_routes.add_url_rule('/<store>/hotel-management/areas', 'get_areas_api', get_areas_api, methods=['GET'])
main_routes.add_url_rule('/<store>/hotel-management/areas', 'add_area_api', add_area_api, methods=['POST'])
main_routes.add_url_rule('/<store>/hotel-management/areas/<int:id>', 'update_area_api', update_area_api, methods=['PUT'])
main_routes.add_url_rule('/<store>/hotel-management/areas/<int:id>', 'delete_area_api', delete_area_api, methods=['DELETE'])

# ホテル管理API
main_routes.add_url_rule('/<store>/hotel-management/hotels', 'get_hotels_api', get_hotels_api, methods=['GET'])
main_routes.add_url_rule('/<store>/hotel-management/hotels/<int:id>', 'get_hotel_api', get_hotel_api, methods=['GET'])
main_routes.add_url_rule('/<store>/hotel-management/hotels', 'add_hotel_api', add_hotel_api, methods=['POST'])
main_routes.add_url_rule('/<store>/hotel-management/hotels/<int:id>', 'update_hotel_api', update_hotel_api, methods=['PUT'])
main_routes.add_url_rule('/<store>/hotel-management/hotels/<int:id>', 'delete_hotel_api', delete_hotel_api, methods=['DELETE'])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 並び替えAPI（追加）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エリア並び替え
main_routes.add_url_rule('/<store>/hotel-management/areas/<int:id>/move-up', 
                        'move_area_up_api', move_area_up_api, methods=['POST'])
main_routes.add_url_rule('/<store>/hotel-management/areas/<int:id>/move-down', 
                        'move_area_down_api', move_area_down_api, methods=['POST'])

# ホテル並び替え
main_routes.add_url_rule('/<store>/hotel-management/hotels/<int:id>/move-up', 
                        'move_hotel_up_api', move_hotel_up_api, methods=['POST'])
main_routes.add_url_rule('/<store>/hotel-management/hotels/<int:id>/move-down', 
                        'move_hotel_down_api', move_hotel_down_api, methods=['POST'])

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
# API: オプション一覧取得（予約登録画面用）
main_routes.add_url_rule('/<store>/options/api', 'get_options_api', get_options_api, methods=['GET'])

# 延長管理
main_routes.add_url_rule('/<store>/extension', 'extension_management', extension_management, methods=['GET'])
main_routes.add_url_rule('/<store>/extension/register', 'register_extension', register_extension_route, methods=['POST'])
main_routes.add_url_rule('/<store>/extension/<int:extension_id>/update', 'update_extension', update_extension_route, methods=['POST'])
main_routes.add_url_rule('/<store>/extension/<int:extension_id>/delete', 'delete_extension', delete_extension_route, methods=['GET'])
main_routes.add_url_rule('/<store>/extension/<int:extension_id>/move_up', 'move_extension_up', move_extension_up_route, methods=['GET'])
main_routes.add_url_rule('/<store>/extension/<int:extension_id>/move_down', 'move_extension_down', move_extension_down_route, methods=['GET'])
# API: 延長一覧取得（予約登録画面用）
main_routes.add_url_rule('/<store>/extensions/api', 'get_extensions_api', get_extensions_api, methods=['GET'])

# 指名管理
main_routes.add_url_rule('/<store>/nominate', 'nominate_management', nominate_management, methods=['GET'])
main_routes.add_url_rule('/<store>/nominate/register', 'register_nomination_type', register_nomination_type, methods=['POST'])
main_routes.add_url_rule('/<store>/nominate/<int:nomination_type_id>/update', 'update_nomination_type', update_nomination_type_route, methods=['POST'])
main_routes.add_url_rule('/<store>/nominate/<int:nomination_type_id>/delete', 'delete_nomination_type', delete_nomination_type_route, methods=['GET'])
main_routes.add_url_rule('/<store>/nominate/<int:nomination_type_id>/move_up', 'move_nomination_type_up', move_nomination_type_up_route, methods=['GET'])
main_routes.add_url_rule('/<store>/nominate/<int:nomination_type_id>/move_down', 'move_nomination_type_down', move_nomination_type_down_route, methods=['GET'])
# API: 指名種類一覧取得（予約登録画面用）
main_routes.add_url_rule('/<store>/nomination-types/api', 'get_nomination_types_api', get_nomination_types_api, methods=['GET'])

# 割引管理（画面）
main_routes.add_url_rule('/<store>/discount_management', 'discount_management', discount_management, methods=['GET'])

# 割引管理（API）
main_routes.add_url_rule('/<store>/discount_management/api/list', 'get_discounts_api', get_discounts_api, methods=['GET'])
main_routes.add_url_rule('/<store>/discount_management/api/get/<int:discount_id>', 'get_discount_api', get_discount_api, methods=['GET'])
main_routes.add_url_rule('/<store>/discount_management/api/register', 'register_discount_api', register_discount_api, methods=['POST'])
main_routes.add_url_rule('/<store>/discount_management/api/update/<int:discount_id>', 'update_discount_api', update_discount_api, methods=['POST'])
main_routes.add_url_rule('/<store>/discount_management/api/delete/<int:discount_id>', 'delete_discount_api', delete_discount_api, methods=['POST'])
main_routes.add_url_rule('/<store>/discount_management/api/move/<int:discount_id>', 'move_discount_api', move_discount_api, methods=['POST'])

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
# ポイント履歴
main_routes.add_url_rule('/<store>/point_history', 'point_history', point_history_view, methods=['GET'])
# ポイント設定
main_routes.add_url_rule('/<store>/point_settings', 'point_settings', point_settings_view, methods=['GET'])
main_routes.add_url_rule('/<store>/point_settings/save', 'point_settings_save', point_settings_save, methods=['POST'])
# ポイント操作理由管理
main_routes.add_url_rule('/<store>/point_settings/reason/add', 'add_point_reason', add_point_reason_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/point_settings/reason/update/<int:reason_id>', 'update_point_reason', update_point_reason_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/point_settings/reason/delete/<int:reason_id>', 'delete_point_reason', delete_point_reason_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/point_settings/reason/move_up/<int:reason_id>', 'move_point_reason_up', move_point_reason_up_endpoint, methods=['GET'])
main_routes.add_url_rule('/<store>/point_settings/reason/move_down/<int:reason_id>', 'move_point_reason_down', move_point_reason_down_endpoint, methods=['GET'])
main_routes.add_url_rule('/<store>/point_settings/api/reasons', 'get_point_reasons_api', get_point_reasons_api, methods=['GET'])
main_routes.add_url_rule('/<store>/point_settings/api/calculate_points', 'calculate_reservation_points_api', calculate_reservation_points_api, methods=['POST'])
main_routes.add_url_rule('/<store>/point_settings/api/member_types', 'get_member_types_api', get_member_types_api, methods=['GET'])

# 顧客管理（API）
main_routes.add_url_rule('/<store>/api/customers', 'api_get_customers', api_get_customers_endpoint, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customers/<int:customer_id>', 'api_get_customer', api_get_customer_endpoint, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customers/add', 'api_add_customer', api_add_customer_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customers/<int:customer_id>/update', 'api_update_customer', api_update_customer_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customers/<int:customer_id>/delete', 'api_delete_customer', api_delete_customer_endpoint, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customers/search', 'api_search_customers', api_search_customers_endpoint, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customer/<int:customer_id>/usage_history', 'get_usage_history', get_usage_history_api, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customer/<int:customer_id>/cast_usage', 'get_cast_usage', get_cast_usage_api, methods=['GET'])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 顧客情報設定API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
main_routes.add_url_rule('/<store>/api/customer_fields', 'api_get_customer_fields', api_get_customer_fields, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customer_fields/options', 'api_get_customer_field_options', api_get_customer_field_options_for_edit, methods=['GET'])
main_routes.add_url_rule('/<store>/api/customer_fields/category', 'api_update_category_label', api_update_category_label, methods=['PUT'])
main_routes.add_url_rule('/<store>/api/customer_fields/option', 'api_add_field_option', api_add_field_option, methods=['POST'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>', 'api_update_field_option', api_update_field_option, methods=['PUT'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>/visibility', 'api_toggle_field_option_visibility', api_toggle_field_option_visibility, methods=['PUT'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>', 'api_delete_field_option', api_delete_field_option, methods=['DELETE'])
main_routes.add_url_rule('/<store>/api/customer_fields/option/<int:option_id>/move', 'api_move_field_option', api_move_field_option, methods=['PUT'])