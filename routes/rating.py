from flask import render_template, request, jsonify, session, redirect, url_for
from database.rating_db import (
    get_all_rating_items, 
    add_rating_item, 
    update_rating_item,
    delete_rating_item,
    update_item_order,
    get_rating_item_by_id
)
from database.db_access import get_db
import json

def rating_item_registration_view(store):
    """評価項目登録画面"""
    return render_template('rating_item_registration.html', store=store)

def rating_items_management_view(store):
    """評価項目一覧画面"""
    db = get_db(store)
    try:
        items = get_all_rating_items(db)
        print(f"取得した評価項目数: {len(items)}")
        
        # DictRowWrapperを通常の辞書に変換
        items_list = []
        for item in items:
            # 辞書に変換
            item_dict = dict(item)
            
            # options を JSON パース
            try:
                item_dict['options_list'] = json.loads(item_dict['options'])
            except:
                item_dict['options_list'] = []
            
            items_list.append(item_dict)
        
        return render_template(
            'rating_items_management.html',
            store=store,
            items=items_list
        )
    except Exception as e:
        print(f"Error in rating_items_management: {e}")
        return f"エラーが発生しました: {str(e)}", 500
    finally:
        if db:
            db.close()

def rating_item_edit_view(store, item_id):
    """評価項目編集画面"""
    db = get_db(store)
    try:
        item = get_rating_item_by_id(db, item_id)
        
        if not item:
            return redirect(url_for('main_routes.rating_items_management', store=store, error='項目が見つかりません'))
        
        # DictRowWrapperを辞書に変換
        item_dict = dict(item)
        
        # options を JSON パース
        try:
            item_dict['options_list'] = json.loads(item_dict['options'])
        except:
            item_dict['options_list'] = []
        
        return render_template(
            'rating_item_edit.html',
            store=store,
            item=item_dict
        )
    except Exception as e:
        print(f"Error in rating_item_edit_view: {e}")
        return f"エラーが発生しました: {str(e)}", 500
    finally:
        if db:
            db.close()



def add_rating_item_endpoint(store):
    """評価項目を追加するAPI"""
    db = get_db(store)
    try:
        data = request.get_json()
        
        item_name = data.get('item_name')
        item_type = data.get('item_type')
        options = data.get('options', [])
        
        if not item_name or not item_type:
            return jsonify({'success': False, 'error': '必須項目が入力されていません'})
        
        # options を JSON 文字列に変換
        options_json = json.dumps(options, ensure_ascii=False)
        
        success = add_rating_item(db, item_name, item_type, options_json)
        
        if success:
            return jsonify({'success': True, 'message': '評価項目を登録しました'})
        else:
            return jsonify({'success': False, 'error': '登録に失敗しました'})
            
    except Exception as e:
        print(f"Error in add_rating_item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})
    finally:
        if db:
            db.close()



def update_rating_item_endpoint(store):
    """評価項目を更新するAPI"""
    db = get_db(store)
    try:
        data = request.get_json()
        
        item_id = data.get('item_id')
        item_name = data.get('item_name')
        item_type = data.get('item_type')
        options = data.get('options', [])
        is_active = data.get('is_active', True)
        
        if not item_id or not item_name or not item_type:
            return jsonify({'success': False, 'error': '必須項目が入力されていません'})
        
        # options を JSON 文字列に変換
        options_json = json.dumps(options, ensure_ascii=False)
        
        success = update_rating_item(db, item_id, item_name, item_type, options_json, is_active)
        
        if success:
            return jsonify({'success': True, 'message': '評価項目を更新しました'})
        else:
            return jsonify({'success': False, 'error': '更新に失敗しました'})
            
    except Exception as e:
        print(f"Error in update_rating_item: {e}")
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})
    finally:
        if db:
            db.close()

def delete_rating_item_endpoint(store):
    """評価項目を削除するAPI"""
    db = get_db(store)
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({'success': False, 'error': 'item_idが必要です'})
        
        success = delete_rating_item(db, item_id)
        
        if success:
            return jsonify({'success': True, 'message': '評価項目を削除しました'})
        else:
            return jsonify({'success': False, 'error': '削除に失敗しました'})
            
    except Exception as e:
        print(f"Error in delete_rating_item: {e}")
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})
    finally:
        if db:
            db.close()

def move_item_order_endpoint(store):
    """評価項目の表示順を変更するAPI"""
    db = get_db(store)
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        direction = data.get('direction')  # 'up' or 'down'
        
        if not item_id or not direction:
            return jsonify({'success': False, 'error': 'パラメータが不足しています'})
        
        success = update_item_order(db, item_id, direction)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': '並び替えに失敗しました'})
            
    except Exception as e:
        print(f"Error in move_item_order: {e}")
        return jsonify({'success': False, 'error': f'エラー: {str(e)}'})
    finally:
        if db:
            db.close()