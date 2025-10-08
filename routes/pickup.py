from flask import render_template, request
from datetime import datetime
from database.db_access import (
    get_display_name, get_db, get_all_courses, get_all_casts,
    get_all_hotels_with_details
)
from database.pickup_db import register_pickup_record

def pickup_register(store):
    display_name = get_display_name(store)
    if display_name is None:
        return "店舗が見つかりません。", 404
    
    db = get_db(store)
    if db is None:
        return "店舗が見つかりません。", 404

    # データ取得
    courses = get_all_courses(db)
    casts = get_all_casts(db)
    hotels = get_all_hotels_with_details(db)
    
    if request.method == "GET":
        return render_template("pickup_register.html", 
                             store=store, 
                             display_name=display_name,
                             courses=courses,
                             casts=casts,
                             hotels=hotels)
    
    elif request.method == "POST":
        # 共通フィールド：日付
        record_date = request.form.get("record_date")
        record_type = request.form.get("type")
        
        # 日付のバリデーション
        if not record_date:
            return render_template("pickup_register.html", 
                                 store=store, 
                                 display_name=display_name,
                                 courses=courses,
                                 casts=casts,
                                 hotels=hotels,
                                 error="登録日を選択してください。")
        
        # 日付形式の確認
        try:
            parsed_date = datetime.strptime(record_date, '%Y-%m-%d').date()
        except ValueError:
            return render_template("pickup_register.html", 
                                 store=store, 
                                 display_name=display_name,
                                 courses=courses,
                                 casts=casts,
                                 hotels=hotels,
                                 error="正しい日付を入力してください。")
        
        if record_type == "pickup":
            # 送迎登録処理
            entry_time = request.form.get("entry_time")
            course_id = request.form.get("course_id")
            cast_id = request.form.get("cast_id")
            hotel_id = request.form.get("hotel_id")
            nomination_type = request.form.get("nomination_type") 
            
            # バリデーション
            if not all([entry_time, course_id, cast_id, hotel_id, nomination_type]):
                return render_template("pickup_register.html", 
                                     store=store, 
                                     display_name=display_name,
                                     courses=courses,
                                     casts=casts,
                                     hotels=hotels,
                                     error="全ての項目を入力してください。")
            
            # データベースに登録（日付を追加）
            success = register_pickup_record(
                db=db,
                type="pickup",
                cast_id=int(cast_id),
                hotel_id=int(hotel_id),
                course_id=int(course_id),
                entry_time=entry_time,
                nomination_type=nomination_type,
                record_date=parsed_date  # 日付を追加
            )
            
            if success:
                return render_template("pickup_register.html", 
                                     store=store, 
                                     display_name=display_name,
                                     courses=courses,
                                     casts=casts,
                                     hotels=hotels,
                                     success="送迎記録を登録しました。")
            else:
                return render_template("pickup_register.html", 
                                     store=store, 
                                     display_name=display_name,
                                     courses=courses,
                                     casts=casts,
                                     hotels=hotels,
                                     error="登録中にエラーが発生しました。")
        
        elif record_type == "other":
            # その他登録処理
            content = request.form.get("content")
            start_time = request.form.get("start_time")
            
            # バリデーション
            if not all([content, start_time]):
                return render_template("pickup_register.html", 
                                     store=store, 
                                     display_name=display_name,
                                     courses=courses,
                                     casts=casts,
                                     hotels=hotels,
                                     error="全ての項目を入力してください。")
            
            # データベースに登録（日付を追加）
            success = register_pickup_record(
                db=db,
                type="other",
                content=content,
                entry_time=start_time,
                record_date=parsed_date  # 日付を追加
            )
            
            if success:
                return render_template("pickup_register.html", 
                                     store=store, 
                                     display_name=display_name,
                                     courses=courses,
                                     casts=casts,
                                     hotels=hotels,
                                     success="その他記録を登録しました。")
            else:
                return render_template("pickup_register.html", 
                                     store=store, 
                                     display_name=display_name,
                                     courses=courses,
                                     casts=casts,
                                     hotels=hotels,
                                     error="登録中にエラーが発生しました。")
        
        else:
            return render_template("pickup_register.html", 
                                 store=store, 
                                 display_name=display_name,
                                 courses=courses,
                                 casts=casts,
                                 hotels=hotels,
                                 error="不正なリクエストです。")