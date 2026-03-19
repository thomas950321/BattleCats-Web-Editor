document.addEventListener('DOMContentLoaded', () => {
    // 元素引用
    const loginPanel = document.getElementById('login-panel');
    const dashboard = document.getElementById('dashboard');
    const resultPanel = document.getElementById('result-panel');
    const btnLogin = document.getElementById('btnLogin');
    const btnUpload = document.getElementById('btnUpload');
    const btnRestart = document.getElementById('btnRestart');
    const notification = document.getElementById('notification');
    const resTransferCode = document.getElementById('resTransferCode');
    const resConfCode = document.getElementById('resConfCode');

    // 狀態切換 - 通知
    function showNotification(message, type = 'success') {
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.remove('hidden');
        clearTimeout(notification._t);
        notification._t = setTimeout(() => notification.classList.add('hidden'), 3000);
    }

    // 自動 Clamp (防止過大數值)
    document.addEventListener('change', e => {
        const el = e.target;
        if (el.type !== 'number' || el.value === '') return;
        const max = parseInt(el.max);
        const min = parseInt(el.min) || 0;
        const val = parseInt(el.value);
        if (!isNaN(max) && val > max) {
            el.value = max;
            showNotification(`已自動修正為上限 ${max.toLocaleString()}`, 'warn');
        } else if (val < min) {
            el.value = min;
        }
    });

    // 複製功能
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const text = document.getElementById(targetId).textContent;
            navigator.clipboard.writeText(text).then(() => {
                showNotification('已複製到剪貼簿！', 'success');
            });
        });
    });

    // 返回/重啟
    btnRestart.addEventListener('click', () => {
        location.reload();
    });

    // 分頁切換
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;

            // 按鈕狀態
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 內容狀態
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
                content.classList.remove('active');
            });
            const targetContent = document.getElementById(target);
            if (targetContent) {
                targetContent.classList.remove('hidden');
                targetContent.classList.add('active');
            }
        });
    });

    // 項目名稱映射
    const itemNames = {
        '戰鬥道具': ['加速', '寶物雷達', '土豪貓', '貓咪電腦', '洞悉先機', '狙擊手'],
        '喵力達': ['喵力達【A】', '喵力達【B】', '喵力達【C】'],
        '貓眼石': ['EX', '稀有', '激稀有', '超激稀有', '傳說', '闇'],
        '基地素材': ['紅磚', '羽毛', '備長炭', '鋼製齒輪', '黃金', '宇宙石', '神祕骨頭', '菊石'],
        '貓薄荷': [
            '紫色薄荷種子', '紅色薄荷種子', '藍色薄荷種子', '綠色薄荷種子', '黃色薄荷種子',
            '紫色貓薄荷', '紅色貓薄荷', '藍色貓薄荷', '綠色貓薄荷', '黃色貓薄荷',
            '彩虹貓薄荷', '惡魔貓薄荷', '古代貓薄荷', '黃金貓薄荷', '彩虹薄荷種子',
            '惡魔薄荷種子', '古代薄荷種子', '黃金薄荷種子'
        ]
    };

    // 輔助函式：生成動態網格 (使用新版 .flex-item 結構)
    function generateGrid(containerId, data, prefix) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';
        const maxLimit = (prefix === '貓薄荷' || prefix === '本能玉') ? 998 : 9999;
        
        data.forEach((val, i) => {
            const item = document.createElement('div');
            item.className = 'flex-item';
            
            let name = '';
            let amount = val;
            if (typeof val === 'object' && val !== null) {
                name = val.name;
                amount = val.amount;
            } else {
                name = (itemNames[prefix] && itemNames[prefix][i]) ? itemNames[prefix][i] : `${prefix} ${i + 1}`;
            }

            item.innerHTML = `
                <label>${name}</label>
                <input type="number" class="${prefix}-input" data-index="${i}" value="${amount}" min="0" max="${maxLimit}" placeholder="0">
            `;
            container.appendChild(item);
        });
    }

    // 登入讀取
    btnLogin.addEventListener('click', async () => {
        btnLogin.disabled = true;
        btnLogin.textContent = '讀取中...';

        const payload = {
            transfer_code: document.getElementById('transferCode').value.trim(),
            confirmation_code: document.getElementById('confCode').value.trim(),
            country_code: document.getElementById('countryCode').value,
            game_version: document.getElementById('gameVersion').value.trim()
        };

        if (!payload.transfer_code || !payload.confirmation_code) {
            showNotification('請輸入完整的引擬資訊', 'error');
            btnLogin.disabled = false;
            btnLogin.textContent = '下載並讀取存檔';
            return;
        }

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.status === 'success') {
                showNotification('存檔讀取成功！');
                loginPanel.classList.add('hidden');
                dashboard.classList.remove('hidden');

                // 抓取真實數據
                const saveDataRes = await fetch('/save/get');
                if (!saveDataRes.ok) throw new Error('無法獲取存檔詳細數據');
                const saveData = await saveDataRes.json();

                // 基礎物資
                document.getElementById('catfood').value = saveData.catfood;
                document.getElementById('xp').value = saveData.xp;
                document.getElementById('np').value = saveData.np || 0;
                document.getElementById('leadership').value = saveData.leadership || 0;

                // 扭蛋券
                document.getElementById('normalTickets').value = saveData.normal_tickets;
                document.getElementById('rareTickets').value = saveData.rare_tickets;
                document.getElementById('platinumTickets').value = saveData.platinum_tickets;
                document.getElementById('legendTickets').value = saveData.legend_tickets;
                document.getElementById('platinumShards').value = saveData.platinum_shards || 0;

                // 其他
                generateGrid('talent-orbs-grid', saveData.talent_orbs || [], '本能玉');
                document.getElementById('labyrinthMedals').value = saveData.labyrinth_medals || 0;
                document.getElementById('playTime').value = saveData.play_time || 0;

                // 動態生成素材列表
                generateGrid('battle-items-grid', saveData.battle_items, '戰鬥道具');
                generateGrid('catamins-grid', saveData.catamins || [], '喵力達');
                generateGrid('catseyes-grid', saveData.catseyes, '貓眼石');
                generateGrid('catfruit-grid', saveData.catfruit, '貓薄荷');
                generateGrid('base-materials-grid', saveData.base_materials, '基地素材');

                document.getElementById('inquiryCodeDisplay').textContent = `ID: ${saveData.inquiry_code || 'N/A'}`;
            } else {
                showNotification('讀取失敗: ' + (result.detail || '碼錯誤或連線失敗'), 'error');
            }
        } catch (err) {
            console.error(err);
            showNotification('操作失敗: ' + err.message, 'error');
        } finally {
            btnLogin.disabled = false;
            btnLogin.textContent = '下載並讀取存檔';
        }
    });

    // 儲存並上傳
    btnUpload.addEventListener('click', async () => {
        btnUpload.disabled = true;
        btnUpload.textContent = '處理中...';

        // 輔助函式：抓取動態列表數值
        const getListValues = (selector) => {
            return Array.from(document.querySelectorAll(selector))
                .sort((a, b) => a.dataset.index - b.dataset.index)
                .map(input => parseInt(input.value) || 0);
        };

        const payload = {
            items: {
                catfood: parseInt(document.getElementById('catfood').value) || 0,
                xp: parseInt(document.getElementById('xp').value) || 0,
                np: parseInt(document.getElementById('np').value) || 0,
                leadership: parseInt(document.getElementById('leadership').value) || 0,
                normal_tickets: parseInt(document.getElementById('normalTickets').value) || 0,
                rare_tickets: parseInt(document.getElementById('rareTickets').value) || 0,
                platinum_tickets: parseInt(document.getElementById('platinumTickets').value) || 0,
                legend_tickets: parseInt(document.getElementById('legendTickets').value) || 0,
                platinum_shards: parseInt(document.getElementById('platinumShards').value) || 0,
                talent_orbs: getListValues('.本能玉-input'),
                labyrinth_medals: parseInt(document.getElementById('labyrinthMedals').value) || 0,
                play_time: parseInt(document.getElementById('playTime').value) || 0,
                // 動態列表
                battle_items: getListValues('.戰鬥道具-input'),
                catamins: getListValues('.喵力達-input'),
                catseyes: getListValues('.貓眼石-input'),
                catfruit: getListValues('.貓薄荷-input'),
                base_materials: getListValues('.基地素材-input')
            },
            stages: {
                clear_tutorial: document.getElementById('clearTutorial').checked,
                clear_world: document.getElementById('clearWorld').checked,
                clear_future: document.getElementById('clearFuture').checked,
                clear_cosmos: document.getElementById('clearCosmos').checked,
                clear_aku: document.getElementById('clearAku').checked,
                
                // 新版主線進度
                max_treasures_world: document.getElementById('advMaxTreasuresWorld').checked,
                max_treasures_future: document.getElementById('advMaxTreasuresFuture').checked,
                max_treasures_cosmos: document.getElementById('advMaxTreasuresCosmos').checked,
                unlock_medals: document.getElementById('advUnlockMedals').checked
            },
            advanced: {
                cats: {
                    unlock_all: document.getElementById('advUnlockAll').checked,
                    max_level: document.getElementById('advMaxLevel').checked,
                    true_form: document.getElementById('advTrueForm').checked,
                    fourth_form: document.getElementById('advFourthForm').checked,
                    max_talents: document.getElementById('advMaxTalents').checked
                },
                tech: {
                    max_all_tech: document.getElementById('advMaxTech').checked
                },
                progress: {
                    max_gamatoto: document.getElementById('advMaxGamatoto').checked,
                    best_gamatoto_members: document.getElementById('advBestMembers').checked,
                },
            }
        };

        try {
            // 第一步：套用修改
            const patchResp = await fetch('/save/patch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!patchResp.ok) {
                const errData = await patchResp.json();
                throw new Error(errData.detail || '套用修改失敗');
            }

            // 第二步：執行上傳
            showNotification('正在上傳至遊戲伺服器...');
            const uploadResp = await fetch('/save/upload', { method: 'POST' });
            if (!uploadResp.ok) {
                const errData = await uploadResp.json();
                throw new Error(errData.detail || '伺服器上傳失敗');
            }

            const result = await uploadResp.json();

            if (result.status === 'success') {
                dashboard.classList.add('hidden');
                resultPanel.classList.remove('hidden');
                resTransferCode.textContent = result.new_transfer_code;
                resConfCode.textContent = result.new_confirmation_code;
                showNotification('上傳成功！請保存新碼。');
            }
        } catch (err) {
            showNotification(err.message || '操作過程發生錯誤', 'error');
        } finally {
            btnUpload.disabled = false;
            btnUpload.textContent = '儲存並上傳至伺服器';
        }
    });
});
