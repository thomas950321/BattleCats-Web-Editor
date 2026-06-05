document.addEventListener('DOMContentLoaded', () => {
    let sessionToken = null;

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
    const inquiryCodeDisplay = document.getElementById('inquiryCodeDisplay');
    const resultTitle = document.getElementById('resultTitle');
    const resultWarning = document.getElementById('resultWarning');

    // 結果面板模式切換
    function setResultMode(isTransplant) {
        const origSection = document.getElementById('originalAccountSection');
        const cloneLabel = document.getElementById('cloneAccountLabel');
        const labelTC = document.getElementById('labelNewTC');
        const labelCC = document.getElementById('labelNewCC');
        if (isTransplant) {
            if (resultTitle) resultTitle.textContent = '移植成功！';
            if (resultWarning) resultWarning.textContent = '空殼帳號已注入強帳進度，以下是新的轉移號碼。';
            if (origSection) origSection.classList.add('hidden');
            if (cloneLabel) cloneLabel.classList.add('hidden');
            if (labelTC) labelTC.textContent = '轉移號碼 (Transfer Code)';
            if (labelCC) labelCC.textContent = '認證號碼 (Confirmation Code)';
        } else {
            if (resultTitle) resultTitle.textContent = '存檔上傳成功！';
            if (resultWarning) resultWarning.textContent = '請務必記下並妥善保存下列資訊，原有的轉移號碼已失效。';
            if (origSection) origSection.classList.add('hidden');
            if (cloneLabel) cloneLabel.classList.add('hidden');
            if (labelTC) labelTC.textContent = '新轉移號碼 (New Transfer Code)';
            if (labelCC) labelCC.textContent = '新認證號碼 (New Confirmation Code)';
        }
    }


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

    // 返回登入時，重置結果面板到一般模式
    btnRestart.addEventListener('click', () => {
        setResultMode(false);
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
            '彩虹貓薄荷',
            '古代貓薄荷種子',
            '古代貓薄荷',
            '彩虹貓薄荷種子',
            '黃金貓薄荷',
            '惡魔貓薄荷種子',
            '惡魔貓薄荷',
            '黃金貓薄荷種子',
            '紫獸石',
            '紅獸石',
            '藍獸石',
            '綠獸石',
            '黃獸石',
            '彩虹獸石',
            '紫獸結晶',
            '紅獸結晶',
            '藍獸結晶',
            '綠獸結晶',
            '黃獸結晶'
        ]
    };

    // --- 新增：批次獲得貓咪的格子管理 ---
    function addCatInput() {
        const grid = document.getElementById('catUnlockGrid');
        if (!grid) return;
        const item = document.createElement('div');
        item.className = 'flex-item';
        item.style.minWidth = '80px';
        item.innerHTML = `
            <input type="text" class="cat-unlock-input" placeholder="ID-形態" style="width: 100%; padding: 6px; border: 1px solid var(--border); border-radius: 4px;">
        `;
        grid.appendChild(item);
    }

    function initCatUnlockGrid() {
        const grid = document.getElementById('catUnlockGrid');
        if (!grid) return;
        grid.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            addCatInput();
        }
    }

    function ensureGoldPassRenewalField() {
        if (document.getElementById('goldPassRenewalTimes')) return;

        const playTimeInput = document.getElementById('playTime');
        if (!playTimeInput) return;

        const playTimeItem = playTimeInput.closest('.input-item');
        const parentGrid = playTimeItem?.parentElement;
        if (!parentGrid) return;

        const field = document.createElement('div');
        field.className = 'input-item';
        field.innerHTML = `
            <label>Gold Pass Renewal Times</label>
            <input type="number" id="goldPassRenewalTimes" min="0" max="99999" placeholder="0">
            <small class="tip">Maps to officer_pass.gold_pass.total_renewal_times</small>
        `;
        parentGrid.appendChild(field);
    }

    const btnAddCatInput = document.getElementById('btnAddCatInput');
    if (btnAddCatInput) {
        btnAddCatInput.addEventListener('click', addCatInput);
    }

    // 輔助函式：生成動態網格 (使用新版 .flex-item 結構)
    function generateGrid(containerId, data, prefix) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';

        if (!Array.isArray(data)) {
            console.warn(`[Render] ${prefix} 數據為空或非數組格式`);
            data = [];
        }

        const maxLimit = (prefix === '貓薄荷' || prefix === '本能玉') ? 998 : 9999;

        data.forEach((val, i) => {
            const item = document.createElement('div');
            item.className = 'flex-item';

            let name = '';
            let amount = val;
            let id = i;
            if (typeof val === 'object' && val !== null) {
                name = val.name;
                amount = val.amount;
                id = val.id;
            } else {
                name = (itemNames[prefix] && itemNames[prefix][i]) ? itemNames[prefix][i] : `${prefix} ${i + 1}`;
            }

            item.innerHTML = `
                <label>${name}</label>
                <input type="number" class="${prefix}-input" data-index="${id}" value="${amount}" min="0" max="${maxLimit}" placeholder="0">
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
            showNotification('請輸入完整的轉移號碼資訊', 'error');
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
                sessionToken = result.session_token;
                showNotification('存檔讀取成功！');
                loginPanel.classList.add('hidden');
                dashboard.classList.remove('hidden');

                // 抓取真實數據
                const saveDataRes = await fetch('/save/get', {
                    headers: { 'X-Session-Token': sessionToken }
                });
                if (!saveDataRes.ok) throw new Error('無法獲取存檔詳細數據');
                const saveData = await saveDataRes.json();
                window.lastSaveData = JSON.parse(JSON.stringify(saveData)); // 拍攝初始快照
                ensureGoldPassRenewalField();

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
                generateGrid('labyrinthMedalsGrid', saveData.labyrinth_medals || [], '迷宮獎牌');
                document.getElementById('playTime').value = saveData.play_time || 0;
                const goldPassRenewalInput = document.getElementById('goldPassRenewalTimes');
                if (goldPassRenewalInput) {
                    goldPassRenewalInput.value = saveData.gold_pass_renewal_times || 0;
                }

                // 動態生成素材列表 (增加安全回退值)
                generateGrid('battle-items-grid', saveData.battle_items || [], '戰鬥道具');
                generateGrid('catamins-grid', saveData.catamins || [], '喵力達');
                generateGrid('catseyes-grid', saveData.catseyes || [], '貓眼石');
                generateGrid('catfruit-grid', saveData.catfruit || [], '貓薄荷');
                generateGrid('base-materials-grid', saveData.base_materials || [], '基地素材');
                initCatUnlockGrid(); // 初始化貓咪解鎖格子

                document.getElementById('inquiryCodeDisplay').textContent = `ID: ${saveData.inquiry_code || 'N/A'}`;
                const banBadge = document.getElementById('banStatusBadge');
                banBadge.style.display = 'inline-block';
                if (saveData.banned) {
                    banBadge.style.color = '#ff4d4f';
                    banBadge.style.background = '#fff1f0';
                    banBadge.style.border = '1px solid #ffa39e';
                    banBadge.textContent = '帳號已有封號標記 (本次儲存將自動為您解除)';
                } else {
                    banBadge.style.color = '#389e0d';
                    banBadge.style.background = '#f6ffed';
                    banBadge.style.border = '1px solid #b7eb8f';
                    banBadge.textContent = '帳號狀態安全 (無異常標記)';
                }

                if (saveData.tutorial_auto_skipped) {
                    showNotification('偵測到帳號尚未完成新手教學，已自動為您跳過！', 'success');
                }
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
        if (!window.lastSaveData) return;
        btnUpload.disabled = true;
        btnUpload.textContent = '計算差異中...';

        try {
            const getListValues = (selector) => {
                return Array.from(document.querySelectorAll(selector))
                    .sort((a, b) => a.dataset.index - b.dataset.index)
                    .map(input => parseInt(input.value) || 0);
            };

            const getListMap = (selector) => {
                const map = {};
                document.querySelectorAll(selector).forEach(input => {
                    map[input.dataset.index] = parseInt(input.value) || 0;
                });
                return map;
            };

            // 核心：比對差異 (Dirty Check)
            const updates = {};
            const itemIds = [
                ['catfood', 'catfood'], ['xp', 'xp'], ['np', 'np'],
                ['leadership', 'leadership'], ['normalTickets', 'normal_tickets'],
                ['rareTickets', 'rare_tickets'], ['platinumTickets', 'platinum_tickets'],
                ['legendTickets', 'legend_tickets'], ['platinumShards', 'platinum_shards'],
                ['playTime', 'play_time'], ['goldPassRenewalTimes', 'gold_pass_renewal_times']
            ];

            // 1. 比對基礎數值 (增加安全檢查)
            itemIds.forEach(([domId, saveKey]) => {
                const el = document.getElementById(domId);
                if (el) {
                    const val = parseInt(el.value) || 0;
                    if (val !== window.lastSaveData[saveKey]) {
                        updates[saveKey] = val;
                    }
                }
            });

            // 2. 比對列表類 (數組)
            const listGrids = {
                battle_items: '.戰鬥道具-input',
                catamins: '.喵力達-input',
                catseyes: '.貓眼石-input',
                catfruit: '.貓薄荷-input',
                base_materials: '.基地素材-input',
                labyrinth_medals: '.迷宮獎牌-input'
            };

            for (const [key, selector] of Object.entries(listGrids)) {
                const currentList = getListValues(selector);
                const originalList = window.lastSaveData[key] || [];
                if (JSON.stringify(currentList) !== JSON.stringify(originalList)) {
                    updates[key] = currentList;
                }
            }

            // 3. 比對本能珠 (字典)
            const currentOrbs = getListMap('.本能玉-input');
            const originalOrbs = {};
            (window.lastSaveData.talent_orbs || []).forEach(o => originalOrbs[o.id] = o.amount);
            if (JSON.stringify(currentOrbs) !== JSON.stringify(originalOrbs)) {
                updates.talent_orbs = currentOrbs;
            }

            const payload = {
                items: updates,
                stages: {
                    clear_tutorial: document.getElementById('clearTutorial')?.checked || false,
                    clear_world: document.getElementById('clearWorld')?.checked || false,
                    clear_future: document.getElementById('clearFuture')?.checked || false,
                    clear_cosmos: document.getElementById('clearCosmos')?.checked || false,
                    clear_aku: document.getElementById('clearAku')?.checked || false,
                    max_treasures_world: document.getElementById('advMaxTreasuresWorld')?.checked || false,
                    max_treasures_future: document.getElementById('advMaxTreasuresFuture')?.checked || false,
                    max_treasures_cosmos: document.getElementById('advMaxTreasuresCosmos')?.checked || false,
                    unlock_medals: document.getElementById('advUnlockMedals')?.checked || false
                },
                advanced: {
                    cats: {
                        unlock_all: document.getElementById('advUnlockAll')?.checked || false,
                        max_level: document.getElementById('advMaxLevel')?.checked || false,
                        true_form: document.getElementById('advTrueForm')?.checked || false,
                        fourth_form: document.getElementById('advFourthForm')?.checked || false,
                        max_talents: document.getElementById('advMaxTalents')?.checked || false,
                        unlock_cat_ids: document.getElementById('advUnlockSingleCat')?.checked ? 
                            Array.from(document.querySelectorAll('.cat-unlock-input'))
                                .map(input => input.value.trim())
                                .filter(val => val !== '') : null
                    },
                    tech: {
                        max_all_tech: document.getElementById('advMaxTech')?.checked || false
                    },
                    progress: {
                        max_gamatoto: document.getElementById('advMaxGamatoto')?.checked || false,
                        best_gamatoto_members: document.getElementById('advBestMembers')?.checked || false,
                    },
                }
            };

            // 第一步：套用修改
            btnUpload.textContent = '正在通訊...';
            const patchResp = await fetch('/save/patch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-Token': sessionToken
                },
                body: JSON.stringify(payload)
            });

            if (!patchResp.ok) {
                const errData = await patchResp.json();
                throw new Error(errData.detail || '套用修改失敗');
            }

            // T-010：解析批次解鎖結果，顯示失敗明細
            const patchData = await patchResp.json();
            if (patchData.unlock_results) {
                const failed = patchData.unlock_results.filter(r => !r.ok);
                const succeeded = patchData.unlock_results.filter(r => r.ok);
                if (failed.length > 0) {
                    const failMsgs = failed.map(r => `・${r.id}：${r.msg}`).join('\n');
                    showNotification(`⚠ ${succeeded.length} 隻解鎖成功，${failed.length} 隻失敗：\n${failMsgs}`, 'warn');
                } else if (succeeded.length > 0) {
                    showNotification(`✓ ${succeeded.length} 隻貓咪全部解鎖成功！`, 'success');
                }
            }

            // 第二步：執行上傳
            showNotification('正在上傳至遊戲伺服器...');
            const uploadResp = await fetch('/save/upload', {
                method: 'POST',
                headers: { 'X-Session-Token': sessionToken }
            });
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

                // 保存至本地瀏覽器，防止刷新遺失
                localStorage.setItem('last_transfer_code', result.new_transfer_code);
                localStorage.setItem('last_conf_code', result.new_confirmation_code);

                showNotification('上傳成功！請保存新碼。');
            }
        } catch (err) {
            showNotification(err.message || '操作過程發生錯誤', 'error');
        } finally {
            btnUpload.disabled = false;
            btnUpload.textContent = '儲存並上傳至伺服器';
        }
    });

    // 找回上次代碼
    document.getElementById('btnRecoverLastCode').addEventListener('click', () => {
        const lastTC = localStorage.getItem('last_transfer_code');
        const lastCC = localStorage.getItem('last_conf_code');

        if (lastTC && lastCC) {
            document.getElementById('transferCode').value = lastTC;
            document.getElementById('confCode').value = lastCC;
            showNotification('已還原上次上傳成功的代碼！');
        } else {
            showNotification('未找到任何本地存檔代碼紀錄。', 'error');
        }
    });



    // 移植帳號按鈕
    const btnTransplant = document.getElementById('btnTransplant');
    if (btnTransplant) {
        btnTransplant.addEventListener('click', async () => {
            const srcTC = document.getElementById('srcTC').value.trim();
            const srcCC = document.getElementById('srcCC').value.trim();
            const dstTC = document.getElementById('dstTC').value.trim();
            const dstCC = document.getElementById('dstCC').value.trim();
            const cc = document.getElementById('countryCode').value;
            const gv = document.getElementById('gameVersion').value.trim();

            if (!srcTC || !srcCC || !dstTC || !dstCC) {
                showNotification('請填寫來源帳與目標帳的完整代碼', 'error');
                return;
            }

            btnTransplant.disabled = true;
            btnTransplant.textContent = '移植中...';

            try {
                const res = await fetch('/save/transplant', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        source_transfer_code: srcTC,
                        source_confirmation_code: srcCC,
                        target_transfer_code: dstTC,
                        target_confirmation_code: dstCC,
                        country_code: cc,
                        game_version: gv,
                    })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || '移植失敗');

                localStorage.setItem('last_transfer_code', data.new_transfer_code);
                localStorage.setItem('last_conf_code', data.new_confirmation_code);

                // 移植模式：顯示移植專用的標題與標籤
                setResultMode(true);
                resTransferCode.textContent = data.new_transfer_code;
                resConfCode.textContent = data.new_confirmation_code;

                loginPanel.classList.add('hidden');
                resultPanel.classList.remove('hidden');
                showNotification('移植完成！空殼帳現在擁有強帳進度。', 'success');

            } catch (err) {
                showNotification(err.message || '移植失敗', 'error');
            } finally {
                btnTransplant.disabled = false;
                btnTransplant.textContent = '開始移植';
            }
        });
    }

    // --- 歷史存檔資料庫 (後台) 功能 ---
    const navEditor = document.getElementById('nav-editor');
    const navAdmin = document.getElementById('nav-admin');
    const adminPanel = document.getElementById('admin-panel');

    if (navEditor && navAdmin && adminPanel) {
        navEditor.addEventListener('click', () => {
            navEditor.classList.add('active');
            navAdmin.classList.remove('active');
            adminPanel.classList.add('hidden');
            if (sessionToken) {
                dashboard.classList.remove('hidden');
            } else {
                loginPanel.classList.remove('hidden');
            }
            resultPanel.classList.add('hidden');
        });

        navAdmin.addEventListener('click', () => {
            navAdmin.classList.add('active');
            navEditor.classList.remove('active');
            loginPanel.classList.add('hidden');
            dashboard.classList.add('hidden');
            resultPanel.classList.add('hidden');
            adminPanel.classList.remove('hidden');
            fetchHistory();
        });
    }

    async function fetchHistory() {
        const historyList = document.getElementById('history-list');
        if (!historyList) return;
        historyList.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 20px;">載入中...</div>';

        try {
            const res = await fetch('/admin/history');
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || '獲取歷史紀錄失敗');

            const history = data.history || [];
            if (history.length === 0) {
                historyList.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 30px; border: 1px dashed var(--border); border-radius: 8px; background: #fafbfc;">目前無存檔紀錄</div>';
                return;
            }

            historyList.innerHTML = '';
            history.forEach(record => {
                const card = document.createElement('div');
                card.className = 'sub-section';
                card.style.marginBottom = '16px';
                card.style.border = '1px solid var(--border)';
                card.style.boxShadow = 'var(--shadow)';
                card.style.background = '#fff';
                card.style.padding = '16px';
                card.style.borderRadius = '8px';
                card.style.display = 'block';

                const sum = record.summary || {};
                const localTime = new Date(record.created_at + 'Z').toLocaleString('zh-TW', { hour12: false });

                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="font-weight: 700; color: var(--text); font-size: 14px;">詢問碼 ID: ${record.inquiry_code || 'N/A'}</span>
                            <span style="font-size: 11px; background: #e8f0fe; color: var(--primary); padding: 2px 6px; border-radius: 4px; margin-left: 8px; font-weight: 600;">${record.country_code.toUpperCase()} v${record.game_version}</span>
                        </div>
                        <span style="font-size: 12px; color: var(--muted);">${localTime}</span>
                    </div>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 12px;">
                        <div style="flex: 1; min-width: 200px;">
                            <div style="font-size: 11px; color: var(--muted); margin-bottom: 4px;">歷史引繼代碼</div>
                            <div style="font-family: monospace; font-size: 13px; font-weight: 600; color: var(--text); margin-bottom: 4px;">轉移: ${record.transfer_code}</div>
                            <div style="font-family: monospace; font-size: 13px; font-weight: 600; color: var(--text);">認證: ${record.confirmation_code}</div>
                        </div>
                        <div style="flex: 2; min-width: 250px;">
                            <div style="font-size: 11px; color: var(--muted); margin-bottom: 4px;">存檔概要</div>
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                                <div style="font-size: 12px;">罐頭: <b style="color: #e67e22;">${(sum.catfood || 0).toLocaleString()}</b></div>
                                <div style="font-size: 12px;">經驗: <b style="color: #3a7bd5;">${(sum.xp || 0).toLocaleString()}</b></div>
                                <div style="font-size: 12px;">NP: <b style="color: #27ae60;">${(sum.np || 0).toLocaleString()}</b></div>
                                <div style="font-size: 12px;">旗子: <b>${sum.leadership || 0}</b></div>
                                <div style="font-size: 12px;">金券: <b>${sum.rare_tickets || 0}</b></div>
                                <div style="font-size: 12px;">貓咪: <b style="color: #8e44ad;">${sum.cats_count || 0} 隻</b></div>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
                        <button class="btn-delete-record" data-id="${record.id}" style="padding: 6px 12px; font-size: 12px; background: #fdf2f2; color: #b91c1c; border: 1px solid #f87171; border-radius: 4px; font-weight: 600; cursor: pointer;">刪除紀錄</button>
                        <button class="btn-restore-record" data-id="${record.id}" data-summary="ID: ${record.inquiry_code} (${record.country_code.toUpperCase()} v${record.game_version}) | 罐頭: ${(sum.catfood || 0).toLocaleString()}, 貓咪: ${sum.cats_count || 0} 隻" style="padding: 6px 12px; font-size: 12px; background: #ecfdf5; color: #047857; border: 1px solid #34d399; border-radius: 4px; font-weight: 600; cursor: pointer;">還原此存檔至新帳號</button>
                    </div>
                `;
                historyList.appendChild(card);
            });

            document.querySelectorAll('.btn-delete-record').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const recordId = btn.dataset.id;
                    if (!confirm('確定要刪除這筆存檔備份紀錄嗎？此動作無法復原。')) return;
                    try {
                        const delRes = await fetch(`/admin/history/${recordId}`, { method: 'DELETE' });
                        const delData = await delRes.json();
                        if (!delRes.ok) throw new Error(delData.detail || '刪除失敗');
                        showNotification('備份紀錄已成功刪除');
                        fetchHistory();
                    } catch (err) {
                        showNotification(err.message, 'error');
                    }
                });
            });

            document.querySelectorAll('.btn-restore-record').forEach(btn => {
                btn.addEventListener('click', () => {
                    const recordId = btn.dataset.id;
                    const summary = btn.dataset.summary;

                    document.getElementById('restore-record-id').value = recordId;
                    document.getElementById('restore-source-summary').textContent = summary;

                    const formContainer = document.getElementById('restore-form-container');
                    formContainer.classList.remove('hidden');
                    formContainer.scrollIntoView({ behavior: 'smooth' });
                });
            });

        } catch (err) {
            historyList.innerHTML = `<div style="text-align: center; color: var(--danger); padding: 20px;">錯誤: ${err.message}</div>`;
        }
    }

    const btnCancelRestore = document.getElementById('btnCancelRestore');
    if (btnCancelRestore) {
        btnCancelRestore.addEventListener('click', () => {
            document.getElementById('restore-form-container').classList.add('hidden');
        });
    }

    const btnStartRestore = document.getElementById('btnStartRestore');
    if (btnStartRestore) {
        btnStartRestore.addEventListener('click', async () => {
            const recordId = document.getElementById('restore-record-id').value;
            const targetTC = document.getElementById('restoreDstTC').value.trim();
            const targetCC = document.getElementById('restoreDstCC').value.trim();
            const cc = document.getElementById('restoreCountryCode').value;
            const gv = document.getElementById('restoreGameVersion').value.trim();

            if (!targetTC || !targetCC) {
                showNotification('請輸入目標空殼帳號的完整代碼', 'error');
                return;
            }

            btnStartRestore.disabled = true;
            btnStartRestore.textContent = '還原中...';

            try {
                const res = await fetch('/admin/restore', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        record_id: parseInt(recordId),
                        target_transfer_code: targetTC,
                        target_confirmation_code: targetCC,
                        country_code: cc,
                        game_version: gv
                    })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || '還原失敗');

                localStorage.setItem('last_transfer_code', data.new_transfer_code);
                localStorage.setItem('last_conf_code', data.new_confirmation_code);

                setResultMode(true);
                if (typeof resultTitle !== 'undefined' && resultTitle) resultTitle.textContent = '存檔還原成功！';
                if (typeof resultWarning !== 'undefined' && resultWarning) resultWarning.textContent = '目標空殼帳號已注入所選備份存檔，以下是新的引繼代碼。';

                resTransferCode.textContent = data.new_transfer_code;
                resConfCode.textContent = data.new_confirmation_code;

                adminPanel.classList.add('hidden');
                document.getElementById('restore-form-container').classList.add('hidden');
                resultPanel.classList.remove('hidden');

                showNotification('存檔成功還原至目標空殼帳號！', 'success');

            } catch (err) {
                showNotification(err.message || '還原操作失敗', 'error');
            } finally {
                btnStartRestore.disabled = false;
                btnStartRestore.textContent = '開始複製並還原';
            }
        });
    }
});
