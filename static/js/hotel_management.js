// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// ホテル管理ページ JavaScript
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

(function() {
    'use strict';
    
    // ストアID
    let storeId = null;
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 初期化
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    document.addEventListener('DOMContentLoaded', function() {
        // 店舗IDを取得
        const pathParts = window.location.pathname.split('/');
        storeId = pathParts[1];
        
        // データを読み込み
        loadHotelTypes();
        loadAreas();
        loadHotels();
        
        // イベントリスナーを設定
        setupEventListeners();
    });
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // イベントリスナー設定
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function setupEventListeners() {
        // ホテル管理種別追加ボタン
        const addHotelTypeBtn = document.getElementById('add-hotel-type-btn');
        if (addHotelTypeBtn) {
            addHotelTypeBtn.addEventListener('click', showAddHotelTypeModal);
        }
        
        // エリア追加ボタン
        const addAreaBtn = document.getElementById('add-area-btn');
        if (addAreaBtn) {
            addAreaBtn.addEventListener('click', showAddAreaModal);
        }
        
        // ホテル登録フォーム
        const hotelForm = document.getElementById('hotel-form');
        if (hotelForm) {
            hotelForm.addEventListener('submit', saveHotel);
        }
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // メッセージ表示
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function showMessage(message, type = 'success') {
        const messageDiv = document.getElementById('saveMessage');
        messageDiv.textContent = message;
        messageDiv.className = `hotel-message hotel-message-${type}`;
        messageDiv.style.display = 'block';
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ホテル管理種別
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadHotelTypes() {
        fetch(`/${storeId}/hotel-management/hotel_types`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayHotelTypes(data.data);
                    updateHotelTypeSelects(data.data);
                } else {
                    console.error('Failed to load hotel types');
                }
            })
            .catch(error => {
                console.error('Error loading hotel types:', error);
            });
    }
    
    function displayHotelTypes(types) {
        const tbody = document.getElementById('hotel-types-tbody');
        
        if (!types || types.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="hotel-table-empty">登録されているホテル管理種別はありません</td></tr>';
            return;
        }
        
        tbody.innerHTML = types.map(type => `
            <tr>
                <td>${escapeHtml(type.type_name)}</td>
                <td>
                    <button type="button" class="hotel-action-btn hotel-edit-icon" 
                            onclick="window.editHotelType(${type.hotel_type_id}, '${escapeHtml(type.type_name)}')">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
                <td>
                    <button type="button" class="hotel-action-btn hotel-delete-icon" 
                            onclick="window.deleteHotelType(${type.hotel_type_id}, '${escapeHtml(type.type_name)}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    function updateHotelTypeSelects(types) {
        const selects = [
            document.getElementById('hotel-type'),
            document.getElementById('edit-hotel-type')
        ];
        
        selects.forEach(select => {
            if (!select) return;
            const currentValue = select.value;
            select.innerHTML = '<option value="">選択してください</option>' +
                types.map(type => 
                    `<option value="${type.hotel_type_id}">${escapeHtml(type.type_name)}</option>`
                ).join('');
            if (currentValue) select.value = currentValue;
        });
    }
    
    function showAddHotelTypeModal() {
        document.getElementById('hotel-type-modal-title').textContent = 'ホテル管理種別を追加';
        document.getElementById('hotel-type-id').value = '';
        document.getElementById('hotel-type-name').value = '';
        document.getElementById('hotel-type-modal').classList.add('show');
        document.getElementById('hotel-type-modal').style.display = 'flex';
    }
    
    window.editHotelType = function(id, name) {
        document.getElementById('hotel-type-modal-title').textContent = 'ホテル管理種別を編集';
        document.getElementById('hotel-type-id').value = id;
        document.getElementById('hotel-type-name').value = name;
        document.getElementById('hotel-type-modal').classList.add('show');
        document.getElementById('hotel-type-modal').style.display = 'flex';
    };
    
    window.closeHotelTypeModal = function() {
        document.getElementById('hotel-type-modal').classList.remove('show');
        document.getElementById('hotel-type-modal').style.display = 'none';
    };
    
    window.saveHotelType = function(event) {
        event.preventDefault();
        
        const id = document.getElementById('hotel-type-id').value;
        const name = document.getElementById('hotel-type-name').value;
        
        if (!name.trim()) {
            showMessage('種別名を入力してください', 'error');
            return;
        }
        
        const url = id 
            ? `/${storeId}/hotel-management/hotel_types/${id}`
            : `/${storeId}/hotel-management/hotel_types`;
        
        const method = id ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type_name: name })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                closeHotelTypeModal();
                loadHotelTypes();
            } else {
                showMessage(data.message || '保存に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving hotel type:', error);
            showMessage('保存中にエラーが発生しました', 'error');
        });
    };
    
    window.deleteHotelType = function(id, name) {
        if (!confirm(`「${name}」を削除してもよろしいですか？\n\n※ この種別が使用されているホテルがある場合は削除できません。`)) {
            return;
        }
        
        fetch(`/${storeId}/hotel-management/hotel_types/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadHotelTypes();
            } else {
                showMessage(data.message || '削除に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting hotel type:', error);
            showMessage('削除中にエラーが発生しました', 'error');
        });
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // エリア管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadAreas() {
        fetch(`/${storeId}/hotel-management/areas`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayAreas(data.data);
                    updateAreaSelects(data.data);
                } else {
                    console.error('Failed to load areas');
                }
            })
            .catch(error => {
                console.error('Error loading areas:', error);
            });
    }
    
    function displayAreas(areas) {
        const tbody = document.getElementById('areas-tbody');
        
        if (!areas || areas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="hotel-table-empty">登録されているエリアはありません</td></tr>';
            return;
        }
        
        tbody.innerHTML = areas.map((area, index) => `
            <tr>
                <td>
                    <button type="button" 
                            class="hotel-sort-btn ${index === 0 ? 'hotel-sort-btn-disabled' : ''}" 
                            ${index === 0 ? 'disabled' : ''}
                            onclick="${index === 0 ? 'return false;' : `window.moveAreaUp(${area.area_id})`}"
                            title="上に移動">
                        <i class="fas fa-chevron-up"></i>
                    </button>
                    <button type="button" 
                            class="hotel-sort-btn ${index === areas.length - 1 ? 'hotel-sort-btn-disabled' : ''}" 
                            ${index === areas.length - 1 ? 'disabled' : ''}
                            onclick="${index === areas.length - 1 ? 'return false;' : `window.moveAreaDown(${area.area_id})`}"
                            title="下に移動">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </td>
                <td>${escapeHtml(area.area_name)}</td>
                <td>${area.transportation_fee ? area.transportation_fee + '円' : '-'}</td>
                <td>${area.travel_time ? area.travel_time + '分' : '-'}</td>
                <td>
                    <button type="button" class="hotel-action-btn hotel-edit-icon" 
                            onclick="window.editArea(${area.area_id}, '${escapeHtml(area.area_name)}', ${area.transportation_fee || 0}, ${area.travel_time || 0})">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
                <td>
                    <button type="button" class="hotel-action-btn hotel-delete-icon" 
                            onclick="window.deleteArea(${area.area_id}, '${escapeHtml(area.area_name)}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    function updateAreaSelects(areas) {
        const selects = [
            document.getElementById('hotel-area'),
            document.getElementById('edit-hotel-area')
        ];
        
        selects.forEach(select => {
            if (!select) return;
            const currentValue = select.value;
            select.innerHTML = '<option value="">選択してください</option>' +
                areas.map(area => 
                    `<option value="${area.area_id}">${escapeHtml(area.area_name)}</option>`
                ).join('');
            if (currentValue) select.value = currentValue;
        });
    }
    
    function showAddAreaModal() {
        document.getElementById('area-modal-title').textContent = 'エリアを追加';
        document.getElementById('area-id').value = '';
        document.getElementById('area-name').value = '';
        document.getElementById('area-fee').value = '';
        document.getElementById('area-time').value = '';
        document.getElementById('area-modal').classList.add('show');
        document.getElementById('area-modal').style.display = 'flex';
    }
    
    window.editArea = function(id, name, fee, time) {
        document.getElementById('area-modal-title').textContent = 'エリアを編集';
        document.getElementById('area-id').value = id;
        document.getElementById('area-name').value = name;
        document.getElementById('area-fee').value = fee || '';
        document.getElementById('area-time').value = time || '';
        document.getElementById('area-modal').classList.add('show');
        document.getElementById('area-modal').style.display = 'flex';
    };
    
    window.closeAreaModal = function() {
        document.getElementById('area-modal').classList.remove('show');
        document.getElementById('area-modal').style.display = 'none';
    };
    
    window.saveArea = function(event) {
        event.preventDefault();
        
        const id = document.getElementById('area-id').value;
        const name = document.getElementById('area-name').value;
        const fee = document.getElementById('area-fee').value;
        const time = document.getElementById('area-time').value;
        
        if (!name.trim()) {
            showMessage('エリア名を入力してください', 'error');
            return;
        }
        
        const url = id 
            ? `/${storeId}/hotel-management/areas/${id}`
            : `/${storeId}/hotel-management/areas`;
        
        const method = id ? 'PUT' : 'POST';
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                area_name: name,
                transportation_fee: fee ? parseInt(fee) : 0,
                travel_time: time ? parseInt(time) : 0
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                closeAreaModal();
                loadAreas();
            } else {
                showMessage(data.message || '保存に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving area:', error);
            showMessage('保存中にエラーが発生しました', 'error');
        });
    };
    
    window.deleteArea = function(id, name) {
        if (!confirm(`「${name}」を削除してもよろしいですか？\n\n※ このエリアが使用されているホテルがある場合は削除できません。`)) {
            return;
        }
        
        fetch(`/${storeId}/hotel-management/areas/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadAreas();
            } else {
                showMessage(data.message || '削除に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting area:', error);
            showMessage('削除中にエラーが発生しました', 'error');
        });
    };
    
    // エリア並び替え関数
    window.moveAreaUp = function(id) {
        fetch(`/${storeId}/hotel-management/areas/${id}/move-up`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadAreas();
            } else {
                showMessage(data.message || '並び替えに失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error moving area up:', error);
            showMessage('並び替え中にエラーが発生しました', 'error');
        });
    };
    
    window.moveAreaDown = function(id) {
        fetch(`/${storeId}/hotel-management/areas/${id}/move-down`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadAreas();
            } else {
                showMessage(data.message || '並び替えに失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error moving area down:', error);
            showMessage('並び替え中にエラーが発生しました', 'error');
        });
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ホテル管理
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function loadHotels() {
        fetch(`/${storeId}/hotel-management/hotels`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    displayHotels(data.data);
                } else {
                    console.error('Failed to load hotels');
                }
            })
            .catch(error => {
                console.error('Error loading hotels:', error);
            });
    }
    
    function displayHotels(hotels) {
        const tbody = document.getElementById('hotels-tbody');
        
        if (!hotels || hotels.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="hotel-table-empty">登録されているホテルはありません</td></tr>';
            return;
        }
        
        tbody.innerHTML = hotels.map((hotel, index) => `
            <tr>
                <td>
                    <button type="button" 
                            class="hotel-sort-btn ${index === 0 ? 'hotel-sort-btn-disabled' : ''}" 
                            ${index === 0 ? 'disabled' : ''}
                            onclick="${index === 0 ? 'return false;' : `window.moveHotelUp(${hotel.hotel_id})`}"
                            title="上に移動">
                        <i class="fas fa-chevron-up"></i>
                    </button>
                    <button type="button" 
                            class="hotel-sort-btn ${index === hotels.length - 1 ? 'hotel-sort-btn-disabled' : ''}" 
                            ${index === hotels.length - 1 ? 'disabled' : ''}
                            onclick="${index === hotels.length - 1 ? 'return false;' : `window.moveHotelDown(${hotel.hotel_id})`}"
                            title="下に移動">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </td>
                <td>${escapeHtml(hotel.hotel_name)}</td>
                <td>${escapeHtml(hotel.type_name || '-')}</td>
                <td>${escapeHtml(hotel.area_name || '-')}</td>
                <td>
                    <button type="button" class="hotel-action-btn hotel-edit-icon" 
                            onclick="window.editHotel(${hotel.hotel_id})">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                </td>
                <td>
                    <button type="button" class="hotel-action-btn hotel-delete-icon" 
                            onclick="window.deleteHotel(${hotel.hotel_id}, '${escapeHtml(hotel.hotel_name)}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    function saveHotel(event) {
        event.preventDefault();
        
        const name = document.getElementById('hotel-name').value;
        const typeId = document.getElementById('hotel-type').value;
        const areaId = document.getElementById('hotel-area').value;
        
        if (!name.trim()) {
            showMessage('ホテル名を入力してください', 'error');
            return;
        }
        
        if (!typeId) {
            showMessage('種別を選択してください', 'error');
            return;
        }
        
        if (!areaId) {
            showMessage('エリアを選択してください', 'error');
            return;
        }
        
        fetch(`/${storeId}/hotel-management/hotels`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hotel_name: name,
                hotel_type_id: parseInt(typeId),
                area_id: parseInt(areaId)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                resetHotelForm();
                loadHotels();
            } else {
                showMessage(data.message || '登録に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving hotel:', error);
            showMessage('登録中にエラーが発生しました', 'error');
        });
    }
    
    window.resetHotelForm = function() {
        document.getElementById('hotel-form').reset();
    };
    
    window.editHotel = function(id) {
        fetch(`/${storeId}/hotel-management/hotels/${id}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const hotel = data.data;
                    document.getElementById('edit-hotel-id').value = hotel.hotel_id;
                    document.getElementById('edit-hotel-name').value = hotel.hotel_name;
                    document.getElementById('edit-hotel-type').value = hotel.hotel_type_id;
                    document.getElementById('edit-hotel-area').value = hotel.area_id;
                    document.getElementById('hotel-edit-modal').classList.add('show');
                    document.getElementById('hotel-edit-modal').style.display = 'flex';
                } else {
                    showMessage('ホテル情報の取得に失敗しました', 'error');
                }
            })
            .catch(error => {
                console.error('Error loading hotel:', error);
                showMessage('ホテル情報の取得中にエラーが発生しました', 'error');
            });
    };
    
    window.closeHotelEditModal = function() {
        document.getElementById('hotel-edit-modal').classList.remove('show');
        document.getElementById('hotel-edit-modal').style.display = 'none';
    };
    
    window.updateHotel = function(event) {
        event.preventDefault();
        
        const id = document.getElementById('edit-hotel-id').value;
        const name = document.getElementById('edit-hotel-name').value;
        const typeId = document.getElementById('edit-hotel-type').value;
        const areaId = document.getElementById('edit-hotel-area').value;
        
        if (!name.trim()) {
            showMessage('ホテル名を入力してください', 'error');
            return;
        }
        
        if (!typeId) {
            showMessage('種別を選択してください', 'error');
            return;
        }
        
        if (!areaId) {
            showMessage('エリアを選択してください', 'error');
            return;
        }
        
        fetch(`/${storeId}/hotel-management/hotels/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hotel_name: name,
                hotel_type_id: parseInt(typeId),
                area_id: parseInt(areaId)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                closeHotelEditModal();
                loadHotels();
            } else {
                showMessage(data.message || '更新に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error updating hotel:', error);
            showMessage('更新中にエラーが発生しました', 'error');
        });
    };
    
    window.deleteHotel = function(id, name) {
        if (!confirm(`「${name}」を削除してもよろしいですか？`)) {
            return;
        }
        
        fetch(`/${storeId}/hotel-management/hotels/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage(data.message, 'success');
                loadHotels();
            } else {
                showMessage(data.message || '削除に失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting hotel:', error);
            showMessage('削除中にエラーが発生しました', 'error');
        });
    };
    
    // ホテル並び替え関数
    window.moveHotelUp = function(id) {
        fetch(`/${storeId}/hotel-management/hotels/${id}/move-up`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadHotels();
            } else {
                showMessage(data.message || '並び替えに失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error moving hotel up:', error);
            showMessage('並び替え中にエラーが発生しました', 'error');
        });
    };
    
    window.moveHotelDown = function(id) {
        fetch(`/${storeId}/hotel-management/hotels/${id}/move-down`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadHotels();
            } else {
                showMessage(data.message || '並び替えに失敗しました', 'error');
            }
        })
        .catch(error => {
            console.error('Error moving hotel down:', error);
            showMessage('並び替え中にエラーが発生しました', 'error');
        });
    };
    
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ユーティリティ関数
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
})();